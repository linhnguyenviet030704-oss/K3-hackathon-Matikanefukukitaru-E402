# Skin Classifier — Inference Only

Download the trained skin-disease weights from Hugging Face and run inference on an image or a
folder of images. No training code, no dataset — just the two scripts needed to go from a
photo to a prediction.

Models: MobileNetV4 (fast) and ResNet-50 (more accurate), 12 dermatological classes, with
bilingual (English / Vietnamese) labels baked into the checkpoint.

## Layout

```
skin-classifier/
├── hf_download.py     # pull weights/*.pth from a Hugging Face model repo
├── inference.py       # run either model on an image or a folder
└── requirements.txt
```

## Setup

```bash
# PyTorch first, from the CUDA index (plain pip install gives the CPU build on Windows)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
pip install -r requirements.txt
```

CPU-only inference works too — pass `--device cpu`, just slower.

## 1. Download the weights

```bash
python hf_download.py --repo zwee912/skin-disease-classifier
```

This saves `weights/mobilenetv4_best.pth` and `weights/resnet50_best.pth`, and prints each
checkpoint's architecture, input resolution, epoch, and validation scores so a bad download
fails here, loudly, rather than at inference time.

Only need one model? `--model resnet50` or `--model mobilenetv4`. Already have the files?
Re-runs skip anything already present — use `--force` to replace.

## 2. Run inference

```bash
# single image, ResNet-50 (default, more accurate)
python inference.py --model resnet50 --input photo.jpg

# MobileNetV4, with flip test-time augmentation
python inference.py --model mobilenetv4 --input photo.jpg --tta

# a whole folder, top-3 predictions, results to CSV
python inference.py --model resnet50 --input some_folder/ --topk 3 --csv predictions.csv
```

The script reads the architecture, input resolution, class names, and Vietnamese labels out of
the checkpoint, so no flags need to match how the model was trained.

Sample output:

```
resnet50  224px  raw weights  epoch 48  12 classes
device=cuda  images=1  tta=False

photo.jpg
 >1. Acne                                                  94.84%  ############################   [Mụn trứng cá]
  2. Scabies                                                0.69%     [Ghẻ]
  3. Urticaria Hives                                        0.66%     [Mề đay]
```

On Windows, if the console errors on the Vietnamese labels (`UnicodeEncodeError`), run with
`PYTHONIOENCODING=utf-8` set first.

## Notes

- Checkpoints load with `weights_only=True`, which refuses to execute pickled code — important
  for a `.pth` pulled off the network.
- This is a demonstration model (~0.74 macro-F1): useful for triage suggestions or shortlisting,
  not for diagnosis.
