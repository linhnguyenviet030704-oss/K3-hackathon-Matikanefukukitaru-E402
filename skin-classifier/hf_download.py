"""Pull trained weights from a Hugging Face model repo into ./weights, ready for inference.py.

    python hf_download.py --repo YOUR_USERNAME/skin-disease-classifier
    python hf_download.py --repo YOUR_USERNAME/skin-disease-classifier --model resnet50
    python inference.py --model resnet50 --input photo.jpg     # then just works

Downloads land in --weights-dir under the names inference.py expects
(mobilenetv4_best.pth / resnet50_best.pth), so no other flags need changing.

Files are also cached in the shared Hugging Face cache (~/.cache/huggingface), so a repeated
run with an unchanged remote file copies from cache instead of re-downloading. For a private
repo, run `hf auth login` first or pass --token.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

# Filenames as stored in the HF repo -> local names inference.py looks for.
REMOTE_FILES = {
    "mobilenetv4": "weights/mobilenetv4_best.pth",
    "resnet50": "weights/resnet50_best.pth",
}
LOCAL_NAMES = {
    "mobilenetv4": "mobilenetv4_best.pth",
    "resnet50": "resnet50_best.pth",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download skin-disease model weights from Hugging Face",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--repo", required=True, help="HF model repo, e.g. username/skin-disease-classifier")
    p.add_argument("--model", default="both", choices=["mobilenetv4", "resnet50", "both"],
                   help="which checkpoint(s) to fetch")
    p.add_argument("--weights-dir", default="weights", help="where to put the .pth files")
    p.add_argument("--revision", default=None, help="branch, tag or commit SHA (default: main)")
    p.add_argument("--token", default=None,
                   help="HF token for private repos; omit to use your `hf auth login` credentials")
    p.add_argument("--remote-prefix", default="weights",
                   help="folder inside the HF repo holding the .pth files ('' if at the root)")
    p.add_argument("--force", action="store_true", help="re-download even if the local file exists")
    return p.parse_args()


def describe(path: Path) -> None:
    """Load the checkpoint and print what it contains, so a bad download fails here, loudly."""
    # weights_only=True refuses to execute pickled code — important for a file off the network.
    ckpt = torch.load(path, map_location="cpu", weights_only=True)
    classes = ckpt.get("classes", [])
    metrics = ckpt.get("metrics") or {}
    scored = ", ".join(f"{k}={v:.4f}" for k, v in metrics.items()
                       if isinstance(v, (int, float)) and k != "loss")
    print(f"    arch      : {ckpt.get('arch', '?')}")
    print(f"    input     : {ckpt.get('img_size', '?')}px")
    print(f"    epoch     : {int(ckpt.get('epoch', -1)) + 1}")
    print(f"    weights   : raw" + (" + ema" if ckpt.get("ema") is not None else "")
          + f" (best_tag={ckpt.get('best_tag', 'raw')})")
    print(f"    classes   : {len(classes)}")
    if scored:
        print(f"    val score : {scored}")


def main() -> None:
    args = parse_args()
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        raise SystemExit("huggingface_hub is not installed. Run: pip install -U huggingface_hub")

    from huggingface_hub.errors import (
        EntryNotFoundError,
        GatedRepoError,
        RepositoryNotFoundError,
    )

    wanted = ["mobilenetv4", "resnet50"] if args.model == "both" else [args.model]
    out_dir = Path(args.weights_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"repo: {args.repo}" + (f" @ {args.revision}" if args.revision else ""))
    print(f"target: {out_dir.resolve()}\n")

    fetched = []
    for name in wanted:
        local_path = out_dir / LOCAL_NAMES[name]
        if local_path.exists() and not args.force:
            size = local_path.stat().st_size / 1024**2
            print(f"[{name}] already present ({size:.1f} MB) - skipping, use --force to replace")
            describe(local_path)
            fetched.append(local_path)
            continue

        # Try <prefix>/<file> first, then the repo root, so a flat repo layout also works
        # without anyone having to pass an empty --remote-prefix (awkward to quote on Windows).
        prefix = args.remote_prefix.strip("/")
        candidates = ([f"{prefix}/{LOCAL_NAMES[name]}"] if prefix else []) + [LOCAL_NAMES[name]]

        cached, tried = None, []
        for remote in candidates:
            print(f"[{name}] downloading {remote} ...")
            try:
                cached = hf_hub_download(
                    repo_id=args.repo,
                    filename=remote,
                    repo_type="model",
                    revision=args.revision,
                    token=args.token,
                )
                break
            except EntryNotFoundError:
                tried.append(remote)
                print(f"    not at {remote}")
            except RepositoryNotFoundError:
                raise SystemExit(
                    f"repo not found: {args.repo}\n"
                    f"Check the name, and for a private repo run `hf auth login` or pass --token."
                )
            except GatedRepoError:
                raise SystemExit(f"repo {args.repo} is gated; accept its terms on the Hub first.")

        if cached is None:
            raise SystemExit(
                f"{LOCAL_NAMES[name]} not found in {args.repo} (looked at: {', '.join(tried)}).\n"
                f"Upload it with hf_upload.py, or pass --remote-prefix if it lives elsewhere."
            )

        # Copy out of the shared cache so weights/ is self-contained.
        local_path.write_bytes(Path(cached).read_bytes())
        print(f"    saved {local_path} ({local_path.stat().st_size / 1024**2:.1f} MB)")
        try:
            describe(local_path)
        except Exception as exc:  # noqa: BLE001 - a corrupt download should not look like success
            local_path.unlink(missing_ok=True)
            raise SystemExit(f"downloaded file is not a valid checkpoint ({exc}); removed it.")
        fetched.append(local_path)

    print(f"\n{len(fetched)} checkpoint(s) ready in {out_dir}/")
    print("Next:")
    for name in wanted:
        print(f"  python inference.py --model {name} --input <image-or-folder>")


if __name__ == "__main__":
    sys.exit(main())
