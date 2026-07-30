import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import httpx

from .config import project_root


def _decode_image(image_base64: str) -> tuple[bytes, str]:
    header, _, data = image_base64.partition(",")
    suffix = ".jpg"
    if header.startswith("data:image/"):
        kind = header.split("data:image/", 1)[1].split(";", 1)[0].lower()
        suffix = ".jpg" if kind == "jpeg" else f".{kind}"
    return base64.b64decode(data or header), suffix


def classify_image_base64(image_base64: str | None, mime_type: str | None = None) -> dict[str, Any] | None:
    if not image_base64:
        return None

    classifier_url = os.getenv("CLASSIFIER_URL")
    if classifier_url:
        try:
            response = httpx.post(
                classifier_url,
                json={"imageBase64": image_base64, "mimeType": mime_type},
                timeout=int(os.getenv("SKIN_CLASSIFIER_TIMEOUT", "90")),
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    root = project_root()
    classifier_dir = root / "skin-classifier"
    script = classifier_dir / "inference.py"
    if not script.exists():
        return None

    image_bytes, suffix = _decode_image(image_base64)
    if mime_type and mime_type.startswith("image/"):
        suffix = ".jpg" if mime_type.endswith("jpeg") else f".{mime_type.rsplit('/', 1)[1]}"

    image_path = json_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as image_file:
            image_file.write(image_bytes)
            image_path = Path(image_file.name)
        json_path = image_path.with_suffix(".json")

        # ponytail: subprocess reloads the model per request; cache in-process if latency matters.
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--input",
                str(image_path),
                "--model",
                os.getenv("SKIN_CLASSIFIER_MODEL", "resnet50"),
                "--weights-dir",
                str(classifier_dir / "weights"),
                "--topk",
                os.getenv("SKIN_CLASSIFIER_TOPK", "3"),
                "--json",
                str(json_path),
                "--device",
                os.getenv("SKIN_CLASSIFIER_DEVICE", "cpu"),
            ],
            cwd=classifier_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            timeout=int(os.getenv("SKIN_CLASSIFIER_TIMEOUT", "90")),
        )
        if result.returncode != 0 or not json_path.exists():
            return None
        rows = json.loads(json_path.read_text(encoding="utf-8"))
        return rows[0] if rows else None
    except Exception:
        return None
    finally:
        for path in (image_path, json_path):
            if path:
                path.unlink(missing_ok=True)
