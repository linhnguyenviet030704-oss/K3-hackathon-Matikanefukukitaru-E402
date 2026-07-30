import json

from backend import skin_classifier


def test_classify_image_base64_uses_classifier_service(monkeypatch):
    seen = {}

    def fail_run(*_args, **_kwargs):
        raise AssertionError("local subprocess should not run when CLASSIFIER_URL is set")

    def fake_post(url, **kwargs):
        seen["url"] = url
        seen["kwargs"] = kwargs

        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return {"pred_class": "Acne", "confidence": 0.9}

        return Response()

    monkeypatch.setenv("CLASSIFIER_URL", "http://classifier:8001/predict")
    monkeypatch.setattr(skin_classifier.subprocess, "run", fail_run)
    monkeypatch.setattr(skin_classifier.httpx, "post", fake_post)

    result = skin_classifier.classify_image_base64("data:image/png;base64,YWJj", "image/png")

    assert result == {"pred_class": "Acne", "confidence": 0.9}
    assert seen["url"] == "http://classifier:8001/predict"
    assert seen["kwargs"]["json"]["imageBase64"] == "data:image/png;base64,YWJj"
    assert seen["kwargs"]["json"]["mimeType"] == "image/png"


def test_classify_image_base64_reads_inference_json(monkeypatch):
    calls = {}

    def fake_run(args, **kwargs):
        calls["args"] = args
        calls["kwargs"] = kwargs
        json_path = args[args.index("--json") + 1]
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump([{"pred_class": "Acne", "confidence": 0.9}], handle)

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(skin_classifier.subprocess, "run", fake_run)

    result = skin_classifier.classify_image_base64("data:image/png;base64,YWJj", "image/png")

    assert result == {"pred_class": "Acne", "confidence": 0.9}
    assert "inference.py" in calls["args"][1]
    assert calls["kwargs"]["env"]["PYTHONIOENCODING"] == "utf-8"
