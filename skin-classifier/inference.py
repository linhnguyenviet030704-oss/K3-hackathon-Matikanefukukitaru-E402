"""Run skin-disease inference with either the MobileNetV4 or the ResNet-50 checkpoint.

One entry point for both architectures: the script reads `arch` out of the checkpoint and
rebuilds the right model with the right preprocessing — MobileNetV4 at 256px via timm,
ResNet-50 at 224px via torchvision. Pick one model per run with --model.

    python inference.py --model resnet50    --input path/to/photo.jpg
    python inference.py --model mobilenetv4 --input path/to/photo.jpg --topk 3

    # a whole folder, with flip TTA, saving results
    python inference.py --model resnet50 --input path/to/folder --tta --csv predictions.csv

Class names and their Vietnamese labels come from the checkpoint, so nothing needs to match
how the model was trained.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

DEFAULT_CKPTS = {
    "mobilenetv4": "mobilenetv4_best.pth",
    "resnet50": "resnet50_best.pth",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Skin-disease inference with MobileNetV4 or ResNet-50",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input", required=True, help="image file or a directory of images")
    p.add_argument("--model", default="resnet50", choices=["mobilenetv4", "resnet50"],
                   help="resnet50 is the more accurate of the two (see README)")
    p.add_argument("--weights-dir", default="weights", help="where the *_best.pth files live")
    p.add_argument("--ckpt", default=None,
                   help="explicit checkpoint path; overrides --model/--weights-dir lookup")
    p.add_argument("--topk", type=int, default=3)
    p.add_argument("--tta", action="store_true", help="average over original + hflip + vflip")
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--weights", default="auto", choices=["auto", "raw", "ema"],
                   help="which weight set inside the checkpoint to use")
    p.add_argument("--csv", default=None, help="also write predictions to this CSV")
    p.add_argument("--json", dest="json_out", default=None, help="also write predictions to this JSON")
    return p.parse_args()


# --------------------------------------------------------------------------------------
# model loading
# --------------------------------------------------------------------------------------
@dataclass
class LoadedModel:
    name: str
    model: nn.Module
    transform: object
    classes: list[str]
    classes_vi: dict[str, str]
    img_size: int
    epoch: int
    weights_tag: str


def _pick_weights(ckpt: dict, requested: str) -> str:
    if requested == "auto":
        # best_tag records which of raw/EMA actually won on validation.
        return ckpt.get("best_tag", "raw") if ckpt.get("ema") is not None else "raw"
    if requested == "ema" and ckpt.get("ema") is None:
        raise SystemExit("checkpoint has no EMA weights; use --weights raw")
    return requested


def load_model(name: str, ckpt_path: Path, args: argparse.Namespace) -> LoadedModel:
    if not ckpt_path.exists():
        raise SystemExit(
            f"checkpoint not found: {ckpt_path}\n"
            f"Pass --weights-dir, or --ckpt with an explicit path."
        )
    # weights_only=True refuses to execute pickled code, which matters for any checkpoint that
    # came off the network (see hf_download.py). Our own checkpoints load fine under it.
    try:
        ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    except Exception as exc:  # noqa: BLE001 - fall back, but say so
        print(f"  ! safe load failed ({type(exc).__name__}); retrying with weights_only=False.")
        print(f"  ! only continue if you trust the origin of {ckpt_path}")
        ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    arch = ckpt.get("arch", "")
    classes = ckpt["classes"]
    classes_vi = ckpt.get("classes_vi") or {}
    tag = _pick_weights(ckpt, args.weights)
    state = ckpt["ema"] if tag == "ema" else ckpt["model"]

    if arch == "torchvision_resnet50":
        # torchvision path: timm is not needed at all.
        from torchvision.models import resnet50
        from torchvision.transforms import v2

        model = resnet50(weights=None)
        drop = ckpt.get("drop", 0.0)
        in_features = model.fc.in_features
        # Must match the head train_resnet50.py built, or load_state_dict will not line up.
        model.fc = (nn.Sequential(nn.Dropout(drop), nn.Linear(in_features, len(classes)))
                    if drop > 0 else nn.Linear(in_features, len(classes)))
        size = ckpt.get("img_size", 224)
        crop_pct = ckpt.get("crop_pct", 0.965)
        transform = v2.Compose([
            v2.Resize(int(round(size / crop_pct)), interpolation=v2.InterpolationMode.BILINEAR,
                      antialias=True),
            v2.CenterCrop(size),
            v2.ToImage(),
            v2.ToDtype(torch.float32, scale=True),
            v2.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ])
    else:
        # timm path (MobileNetV4, or any other timm arch trained by train_mobilenetv4.py).
        import timm
        from timm.data import create_transform, resolve_data_config

        model = timm.create_model(arch, pretrained=False, num_classes=len(classes))
        size = ckpt.get("img_size")
        cfg = resolve_data_config({"input_size": (3, size, size)} if size else {}, model=model)
        size = cfg["input_size"][-1]
        transform = create_transform(
            input_size=cfg["input_size"], is_training=False, interpolation=cfg["interpolation"],
            mean=cfg["mean"], std=cfg["std"], crop_pct=cfg["crop_pct"],
        )

    model.load_state_dict(state)
    model.eval().to(args.device)
    return LoadedModel(name, model, transform, classes, classes_vi, size,
                       int(ckpt.get("epoch", -1)) + 1, tag)


# --------------------------------------------------------------------------------------
# inference
# --------------------------------------------------------------------------------------
def collect_images(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if not target.is_dir():
        raise SystemExit(f"input not found: {target}")
    files = sorted(f for f in target.rglob("*") if f.suffix.lower() in IMAGE_EXTS)
    if not files:
        raise SystemExit(f"no images under {target}")
    return files


@torch.no_grad()
def run_model(loaded: LoadedModel, files: list[Path], args: argparse.Namespace) -> list[torch.Tensor | None]:
    """One probability vector per file, or None where the image could not be read."""
    results: list[torch.Tensor | None] = [None] * len(files)
    for start in range(0, len(files), args.batch_size):
        chunk = list(enumerate(files[start:start + args.batch_size], start=start))
        batch, positions = [], []
        for pos, f in chunk:
            try:
                batch.append(loaded.transform(Image.open(f).convert("RGB")))
                positions.append(pos)
            except Exception as exc:  # noqa: BLE001 - unreadable file, keep going
                print(f"  ! skipped {f}: {exc}")
        if not batch:
            continue
        x = torch.stack(batch).to(args.device)
        views = [x, torch.flip(x, dims=[3]), torch.flip(x, dims=[2])] if args.tta else [x]
        probs = (sum(loaded.model(v).float().softmax(1) for v in views) / len(views)).cpu()
        for row, pos in enumerate(positions):
            results[pos] = probs[row]
    return results


def topk_list(probs: torch.Tensor, classes: list[str], classes_vi: dict[str, str], k: int):
    conf, idx = probs.topk(min(k, len(classes)))
    return [(classes[i], classes_vi.get(classes[i], ""), float(c))
            for i, c in zip(idx.tolist(), conf.tolist())]


def main() -> None:
    args = parse_args()
    files = collect_images(Path(args.input))
    ckpt_path = Path(args.ckpt) if args.ckpt else Path(args.weights_dir) / DEFAULT_CKPTS[args.model]
    loaded = load_model(args.model, ckpt_path, args)

    print(f"{loaded.name}  {loaded.img_size}px  {loaded.weights_tag} weights  "
          f"epoch {loaded.epoch}  {len(loaded.classes)} classes")
    print(f"device={args.device}  images={len(files)}  tta={args.tta}")

    all_probs = run_model(loaded, files, args)
    k = min(args.topk, len(loaded.classes))

    rows = []
    for f, probs in zip(files, all_probs):
        if probs is None:
            continue
        top = topk_list(probs, loaded.classes, loaded.classes_vi, k)
        print(f"\n{f}")
        for rank, (name, name_vi, conf) in enumerate(top, 1):
            marker = ">" if rank == 1 else " "
            bar = "#" * int(round(conf * 30))
            print(f" {marker}{rank}. {name:52s} {conf * 100:6.2f}%  {bar}"
                  + (f"   [{name_vi}]" if name_vi else ""))

        rows.append({
            "filepath": str(f),
            "model": loaded.name,
            "pred_class": top[0][0],
            "pred_class_vi": top[0][1],
            "confidence": round(top[0][2], 6),
            **{f"top{r}": f"{n} ({c * 100:.2f}%)" for r, (n, _, c) in enumerate(top, 1)},
        })

    if not rows:
        raise SystemExit("no images could be read")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nwrote {args.csv}")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {args.json_out}")


if __name__ == "__main__":
    main()
