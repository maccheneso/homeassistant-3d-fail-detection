# 🧠 AI-based 3D Print Failure Detection  
### Raspberry Pi + Home Assistant (local, no cloud)

This project provides **local, real-time detection of 3D printing failures** using:

- a Raspberry Pi (or any local host) running a small Python AI server
- a YOLO object-detection model (**`best.pt`**)
- Home Assistant automations + notifications

No cloud services and no external AI APIs: **everything stays inside your LAN**.

---

## 🚨 What failures can be detected?

Example failure classes supported by YOLO training:

- spaghetti extrusion
- detached filament / layers
- bed detachment
- stringing / abnormal filament behavior

More classes can be added by retraining the model.

---

## 📸 Demo – Screenshots

### Home Assistant dashboard + AI push notification
<p float="left">
  <img src="AI_3D_FailDetect_Raspberry_HA/assets/screenshot_dashboard.jpg" width="33%">
  <img src="AI_3D_FailDetect_Raspberry_HA/assets/screenshot_push_notification.png" width="33%" />
</p>

### YOLO detection example (bounding box)
<img src="AI_3D_FailDetect_Raspberry_HA/assets/spaghetti_detection.png" width="600">
<img src="AI_3D_FailDetect_Raspberry_HA/assets/example_fail_frame.jpg" width="600">

---

## System Architecture (overview)

**Webcam → AI Server → Home Assistant → Notification/Actions**

### Components

1. A webcam providing an MJPEG stream (or snapshots) of the printer  
2. A local host (Raspberry Pi / Mini PC / NAS) running:
   - Python AI server (e.g. `/check` endpoint)
   - YOLO inference using `best.pt`
   - optional webhook trigger on detection  
3. Home Assistant:
   - polls the AI endpoint
   - optionally checks that the printer is actually printing (power sensor, printer status, etc.)
   - copies the last snapshot to `/config/www/ai_3d/ultima.jpg`
   - sends persistent + mobile notifications (and optional actions)

---

## 📦 Repository contents

```text
AI_3D_FailDetect_Raspberry_HA/
├ app/                      # Flask server + YOLO logic
├ assets/                   # images used for docs/examples
├ model/                    # YOLO weights folder (best.pt goes here)
├ config.yaml               # AI configuration
├ HOW_TO_TRAIN_MODEL.md
├ HOW_TO_TRAIN_MODEL_ita.md
├ README.md                 # detailed project documentation
├ README_ita.md
├ requirements.txt
├ run_server.sh
├ setup.sh
```

---

## Model weights (best.pt)

This repository **includes** the trained YOLO weights file:

`AI_3D_FailDetect_Raspberry_HA/model/best.pt`

If you want to use your own model, simply replace `best.pt` with your custom weights.

Dataset attribution / licensing notes: see `ATTRIBUTION.md`.

---

## 🚀 Quick installation (Raspberry Pi)

```bash
scp -r AI_3D_FailDetect_Raspberry_HA pi@<RASPBERRY_IP>:/home/pi/

ssh pi@<RASPBERRY_IP>
cd ~/AI_3D_FailDetect_Raspberry_HA
chmod +x setup.sh
./setup.sh
./run_server.sh
```

---

## Home Assistant integration

The AI server exposes:

```text
/check       → JSON inference response
/ultima.jpg  → last captured frame
```

Home Assistant can call `/check` periodically and (optionally) receive detection webhooks.

Full HA package documentation:

[Full HA integration](./AI_3D_FailDetect_Raspberry_HA/README.md)

---

## 🧪 Training your own model

Instructions available in:

- `HOW_TO_TRAIN_MODEL.md`
- `HOW_TO_TRAIN_MODEL_ita.md`

Datasets from Roboflow or custom annotated frames are supported.

---

## 📋 Requirements

- Raspberry Pi 3/4/5 (recommended) or any Linux host
- Python 3.10+
- Home Assistant Core/OS
- Smart plug with power monitoring (optional but recommended)
- IP camera exposing an MJPEG stream (or a snapshot endpoint)

---

## 🛡️ Privacy & local processing

This project is designed for maximum privacy:

- video never leaves the local network
- inference runs only on your own hardware
- no cloud API keys
- no proprietary services required

---

## 🤝 Contributing

Contributions are welcome:

- issues and suggestions
- PRs for improved configs / documentation
- model improvements (share datasets only if license allows)

---

### 📄 License

Code is released under the **MIT License**.  
See `LICENSE`.

---

## ⭐  Why this project?

Because 3D printers can fail silently.

Spaghetti prints waste filament, can damage prints and hardware, and may be unsafe.  
This project alerts you locally, without cloud dependence.
