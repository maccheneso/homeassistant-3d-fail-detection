# How to Train a YOLO Model for **AI_3D_FailDetect** (best.pt)

This guide shows how to:

- get a dataset (public or your own)
- train YOLO locally (recommended on a PC)
- place the resulting **`best.pt`** in the correct folder so the server loads it

---

## 1) Get a dataset

You have two options.

### A) Use a public dataset (Roboflow Universe, etc.)
- Pick a dataset with a license that allows your intended use (at minimum **reuse**, ideally **modification** too).
- Download it in a YOLO format compatible with your training workflow (see section **2**).

Tip: search using keywords like *3d print*, *spaghetti*, *failure detection*, *printer*.

### B) Create your own dataset (recommended for best accuracy)
1. Capture snapshots/frames from your printer webcam (good + bad prints).
2. Annotate real defects (examples):
   - spaghetti
   - bed detachment
   - delamination / detached layers
   - stringing / abnormal extrusion
3. Use an annotation tool:
   - **LabelImg** (offline)
   - CVAT
   - Label Studio
   - Roboflow Annotate

Export in a YOLO format (YOLOv8/YOLOv5-style TXT labels).

---

## 2) Why “format” matters when downloading (YOLO / COCO / VOC…)

Datasets contain:
- **images** (JPG/PNG)
- **annotations** (the labels)

Different tools expect different annotation formats:
- **YOLO** → one `.txt` file per image (class_id + normalized boxes)
- **COCO JSON** → a single `.json` file for a split (train/val/test)
- **Pascal VOC XML** → one `.xml` per image

✅ If you train with **Ultralytics YOLO (yolov8 / yolov11)**, download/export as:
- **YOLOv8** / **YOLOv5 PyTorch** (both are fine in practice for Ultralytics)

---

## 3) Install training tools (PC recommended)

> Training on Raspberry Pi is possible, but it’s usually **very slow** and often not practical (RAM/swap/time).
> Best practice: **train on a PC**, then copy `best.pt` to the Raspberry.

Install Ultralytics:

```bash
pip install ultralytics
```

Verify:

```bash
yolo --version
```

---

## 4) Train YOLO

Example command (Ultralytics):

```bash
yolo detect train \
  model=yolov8n.pt \
  data=/path/to/dataset/data.yaml \
  epochs=50 \
  imgsz=640
```

Where `data.yaml` includes:
- paths to **train** / **val** (and optionally **test**) images
- number of classes (`nc`)
- class names (`names`)

Example `data.yaml`:

```yaml
train: /path/to/dataset/train/images
val: /path/to/dataset/valid/images

nc: 4
names:
  - Spaghetti
  - Detached Filament
  - Detached Layer
  - Layer Defect
```

Notes:
- More **epochs** may improve results (up to a point).
- Larger models (yolov8s/m/l) require more compute.
- Keep class names consistent (next section).

---

## 5) Find the trained weights (best.pt)

After training, Ultralytics typically creates:

```text
runs/detect/train/weights/
```

Inside you will find:
- `best.pt`  ← best-performing weights
- `last.pt`

---

## 6) Put **best.pt** into THIS project (correct path)

Create the folder if it does not exist:

```text
AI_3D_FailDetect_Raspberry_HA/model/
```

Then copy your weights to:

```text
AI_3D_FailDetect_Raspberry_HA/model/best.pt
```

✅ Important: use the full path above (not only `model/best.pt` “somewhere else”).

---

## 7) Ensure class names match the project config

Your server + HA automation logic usually relies on class names.

**Rule:** names in your dataset `data.yaml -> names:` must match what you expect in the project configuration.

Example (conceptual):

```yaml
error_classes:
  - "Spaghetti"
  - "Detached Filament"
  - "Detached Layer"
  - "Layer Defect"
```

⚠️ If your dataset uses different spelling/case (e.g. `spaghetti` vs `Spaghetti`) you must:
- either change the dataset class names (preferred) OR
- update your config to match exactly

Otherwise you may see detections, but your automation/trigger logic can misbehave.

---

## 8) Quick test

Start the AI server (project script):

```bash
./run_server.sh
```

Then open:

```text
http://<RASPBERRY_IP>:5000/check
```

If you get a JSON response like `{"success": true}` (or similar), then:
- the server is up
- the model file was found
- inference is working

---

## Notes / Warnings

- Do not redistribute datasets (or derived datasets) if the license does not allow it.
- Publishing a `best.pt` is usually OK if you comply with dataset license requirements (attribution, restrictions, etc.).
- False positives are normal early on—improve by adding more **real** failure images from your printer.

---

## Contributing

Suggestions, issues, and PRs are welcome:
- verified datasets (with clear license)
- better instructions / fixes
- improvements to detection logic
