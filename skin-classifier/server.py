from __future__ import annotations

import base64
import os
import tempfile
from argparse import Namespace
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from inference import DEFAULT_CKPTS, collect_images, load_model, run_model, topk_list


app = FastAPI(title="Skin Classifier")


class PredictRequest(BaseModel):
    imageBase64: str
    mimeType: str | None = None


def _decode_image(image_base64: str, mime_type: str | None) -> tuple[bytes, str]:
    header, _, data = image_base64.partition(",")
    suffix = ".jpg"
    if mime_type and mime_type.startswith("image/"):
        suffix = ".jpg" if mime_type.endswith("jpeg") else f".{mime_type.rsplit('/', 1)[1]}"
    elif header.startswith("data:image/"):
        kind = header.split("data:image/", 1)[1].split(";", 1)[0].lower()
        suffix = ".jpg" if kind == "jpeg" else f".{kind}"
    return base64.b64decode(data or header), suffix


def _args() -> Namespace:
    return Namespace(
        batch_size=1,
        device=os.getenv("SKIN_CLASSIFIER_DEVICE", "cpu"),
        tta=os.getenv("SKIN_CLASSIFIER_TTA", "").lower() in {"1", "true", "yes"},
        weights=os.getenv("SKIN_CLASSIFIER_WEIGHTS", "auto"),
    )


@lru_cache(maxsize=1)
def _loaded():
    model_name = os.getenv("SKIN_CLASSIFIER_MODEL", "resnet50")
    weights_dir = Path(os.getenv("SKIN_CLASSIFIER_WEIGHTS_DIR", "weights"))
    ckpt_path = weights_dir / DEFAULT_CKPTS[model_name]
    return load_model(model_name, ckpt_path, _args())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
def predict(payload: PredictRequest) -> dict[str, Any]:
    image_bytes, suffix = _decode_image(payload.imageBase64, payload.mimeType)
    image_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as image_file:
            image_file.write(image_bytes)
            image_path = Path(image_file.name)
        loaded = _loaded()
        probs = run_model(loaded, collect_images(image_path), _args())[0]
        if probs is None:
            return {}
        top = topk_list(probs, loaded.classes, loaded.classes_vi, int(os.getenv("SKIN_CLASSIFIER_TOPK", "3")))
        return {
            "filepath": str(image_path),
            "model": loaded.name,
            "pred_class": top[0][0],
            "pred_class_vi": top[0][1],
            "confidence": round(top[0][2], 6),
            "top": [{"label": n, "label_vi": vi, "confidence": round(c, 6)} for n, vi, c in top],
        }
    finally:
        if image_path:
            image_path.unlink(missing_ok=True)
