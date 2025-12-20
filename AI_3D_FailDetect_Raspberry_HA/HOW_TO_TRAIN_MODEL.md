# 💡 How to train a model for AI_3D_FailDetect

This project does **not include** model weights (`best.pt`), to respect the licenses of original datasets.

This guide allows you to:

✔ obtain a public dataset  
✔ train YOLO locally  
✔ correctly insert `best.pt` into the project  

---

# 1. 📥 Obtain a dataset

You can choose between two approaches:

---

## 🔹 A) use available public datasets

There are 3D printing datasets on Roboflow Universe.

🔗 Search datasets using keywords:  

👉 https://universe.roboflow.com/search?q=dataset%203d%20print  

  - register (free)  
  - choose a dataset with a license that allows reuse or modification  
  - create a Workflow  
  - download the dataset  

---

## 🔹 B) create your own dataset

1. capture snapshots from the printer webcam  
2. annotate real defects:
   - spaghetti
   - delamination
   - bed detachment
   - abnormal extrusion strings
3. use tools like:
   - Roboflow Annotate
   - CVAT
   - Label Studio  

Then export in YOLOv5/YOLOv8 PyTorch format.

---

# 2. 🛠 Install YOLO tools

On Raspberry Pi or on a more powerful PC:

```
pip install ultralytics
```

Verify installation:

```
yolo --version
```

# 3. 🚀 Train YOLO

Run:

```
yolo detect train \
  model=yolov8n.pt \
  data=/home/user/datasets/ai_3d_fail/data.yaml \
  epochs=50 imgsz=640
```

The generated data.yaml file contains:

- paths to train / val / test images  
- class names  
- total number of classes (`nc:`)

If you move the dataset, update data.yaml accordingly.

Example of data.yaml:

```
train: /home/user/datasets/ai_3d_fail/train/images
val: /home/user/datasets/ai_3d_fail/valid/images

nc: 4
names:
  - Spaghetti
  - Detached Filament
  - Detached Layer
  - Layer Defect
```

Notes:

- you can increase epochs for better accuracy  
- bigger models require more resources (yolov8s/m/l)  

---

# 4. 📦 Retrieve trained model

YOLO creates a directory similar to:

```
runs/detect/train/weights/
```

and inside you will find:

- ```best.pt``` ← best performing weights  
- ```last.pt```

---

# 5. 📍 Insert the model into the project

Copy the file to:

```
model/best.pt
```

The AI server will automatically load it using the path defined in ```config.yaml```.

---

# 6. 🔍 Verify classes and config consistency

Make sure in ```config.yaml```:

```
error_classes:
  - "Spaghetti"
  - "Detached Filament"
  - "Detached Layer"
  - "Layer Defect"
```

Class names must match those in the dataset (`data.yaml`).

---

## 6.1. 🎯 Important note on class labels

Dataset **class names must exactly match** names defined in config.yaml.

Correct example:

```
error_classes:
  - "Spaghetti"
```

🚫 NO if the dataset uses alternate names such as:

  - "spaghetti"
  - "extrusion_spaghetti"
  - "stringing_spaghetti"

⚠ Tips:

  - check data.yaml → `names:` list  
  - copy/paste names directly  
  - avoid spaces or different capitalization  

If names don’t match, the AI node will:

  - detect the defect  
  - **but Home Assistant will not trigger the webhook**  
  - so no notification will be generated  

---

# 7. 🧪 Final test

Start the AI server:

```
./run_server.sh
```

Then from a browser:

```
http://<IP_RASPBERRY_AI>:5000/check
```

If you see:

```
{"success": true}
```

then:

✔ configuration valid  
✔ model loaded  
✔ AI ready for use  

---

# ⚠️ Suggestion

while it is technically possible to train YOLO on a Raspberry Pi,  
it is recommended to train on a PC with a more powerful CPU/GPU  
and then copy best.pt to the `model/` folder.

---

# Notes and warnings

- do not redistribute datasets or models without proper license  
- beware of false positives, especially during early training  
- you can improve the model by adding real failed print images  

---

# Contributing

- to share improvements:
  - open an Issue  
  - submit a Pull Request  
  - suggest verified public datasets  

---

# Quick FAQ

How many images are required?  
  - at least 200–300 real images per class.

Does it support multi-class datasets?  
  - yes, just add class names in config.yaml.

Which resolution is recommended?  
  - 640 or 720 px are good compromises.
