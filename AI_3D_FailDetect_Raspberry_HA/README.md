# AI Fail Detection – Raspberry Pi + Home Assistant
_Automatic detection of 3D printing errors (local, no cloud)_

This folder contains the Raspberry AI server + Home Assistant integration package  
See the repository root README for the overall project overview.

## 1. Objective of the project

This project allows you to:

- automatically detect 3D printing errors  
  (e.g., spaghetti, bed detachment, layer defects)
- use **only local components** (no cloud services)
- send a **notification to the phone** with:
  - error class + confidence
  - link to the printer dashboard in Home Assistant
  - updated snapshot of the detected error

### Architecture (high level)

1. A webcam provides an **MJPEG stream** of the printer.
2. A **Raspberry Pi (3/4/5)** runs a small Python server:
   - captures a frame
   - analyzes it using a YOLO AI model (`best.pt`)
   - saves the image
   - if an error is found → sends a webhook to Home Assistant
3. **Home Assistant**:
   - checks if the printer is actually printing (smart plug power)
   - periodically queries the AI (`/check`)
   - when receiving the webhook:
     - copies the updated snapshot to `/config/www/ai_3d/ultima.jpg`
     - displays it on the dashboard
     - sends a push notification to the phone.

Everything remains **inside the LAN**.

---

## 2. Requirements

### Hardware

- Raspberry Pi 4 or 5 (recommended), with Linux (Raspberry Pi OS / Debian).
- 3D printer (any brand).
- IP or USB webcam exposing an MJPEG stream, e.g.:
  - `http://IP_CAM:8080/?action=stream`
- Smart plug with power monitoring (Zigbee / Z-Wave / Wi-Fi supported by Home Assistant).

### Software

On the Raspberry (AI node):

- Python 3.10 or newer
- Virtualenv
- Python packages (installed via `requirements.txt`):
  - `ultralytics` (YOLO)
  - `opencv-python`
  - `Flask`
  - `PyYAML`
  - `requests`
  - others listed in the requirements file

On Home Assistant:

- Home Assistant Core / OS already running
- **Mobile App** integration for push notifications
- a smart plug integrated with:
  - `switch.<printer_plug_name>`
  - `sensor.<printer_power_sensor_name>`

## 3. Contents of the repository (project to copy to Raspberry)

Main folder, e.g. `/home/pi/3d_ai_faildetect`:

```text
3d_ai_faildetect/
├─ app/
│  ├─ __init__.py
│  ├─ ai_core.py        # AI logic (YOLO + webhook)
│  └─ server.py         # Flask server with /check and /ultima.jpg
│
├─ model/
│  └─ best.pt           # custom YOLO model (print defects)
│
├─ frames/              # "clean" captured frames will be saved here
├─ runs/                # YOLO output (bounding boxes)
│
├─ config.yaml          # AI configuration on the Raspberry
├─ requirements.txt     # Python dependencies
├─ setup.sh             # setup script (venv + pip install)
├─ run_server.sh        # starts the AI server
└─ README.md            # this file
```

The ```venv/``` folder is not included in the repository: it is created by ```setup.sh```.

## 4. Installation on Raspberry Pi (AI node)

### 4.1 Copy the folder
Copy the entire ```3d_ai_faildetect``` folder to the Raspberry, e.g. in ```/home/pi/```:

```bash
scp -r 3d_ai_faildetect pi@<IP_RASPBERRY>:/home/pi/
```

or via Samba / USB drive, as you prefer.

Then access it:

```bash
ssh pi@<IP_RASPBERRY>
cd /home/pi/3d_ai_faildetect
```

### 4.2 Setup script (create virtualenv + dependencies)

_The `setup.sh` script is already included in the repository, inside the project folder:_

```bash
/home/pi/3d_ai_faildetect/setup.sh
```

Make the script executable and run it:

```bash
chmod +x setup.sh
./setup.sh
```

The script handles:

1. creating a ```venv/``` virtualenv inside the project folder  
2. activating it  
3. installing all required Python packages from ```requirements.txt```  
4. creating ```frames/``` and ```runs/``` folders if missing  

At the end you should see ```venv/``` created and no errors in console.

### 4.3 Configuration ```config.yaml```

Open ```config.yaml``` and adapt the parameters to your network:

```yaml
# Configurations for AI node – 3D print failure detection

# URL of the MJPEG stream from the webcam connected to the printer
stream_url: "http://<IP_CAM>:8080/?action=stream"

# Path to the YOLO trained model (relative to project folder)
model_path: "model/best.pt"

# Image size for YOLO (640 is a good compromise)
imgsz: 640

# Minimum confidence threshold to consider a detection valid
min_confidence: 0.60

# Classes to treat as "real failure" (others may be ignored)
# Use exactly the names defined in data.yaml / Roboflow training.
error_classes:
  - "Spaghetti"
  - "Detached Filament"
  - "Detached Layer"
  - "Layer Defect"

# Classes treated as "soft warning" (do not stop print, optional logging)
warning_classes:
  - "Singular String"
  - "Stringing"

# Webhook for Home Assistant to report a failure
# Replace <HA_IP> with the IP of your Home Assistant.
ha_webhook_url: "http://<HA_IP>:8123/api/webhook/ai_3d_fail"

# Timeout in seconds when calling HA webhook
ha_webhook_timeout: 10

# Where to save captured frames (relative to project folder)
frames_dir: "frames"

# Where YOLO stores bounding box results (Ultralytics managed)
results_dir: "runs/detect"

# Simple log to stdout (true/false)
log_debug: true

```

Important values to personalize:
- ```stream_url``` → IP/port of your webcam
- ```ha_webhook_url``` → IP and port of Home Assistant (LAN)

### 4.4 Manual start of the AI server

To test:

```
chmod +x run_server.sh
./run_server.sh
```

If everything is correct, you will see the Flask server listening on ```0.0.0.0:5000```.

You can test from browser:

- AI Check: ```http://<IP_RASPBERRY_AI>:5000/check```
- Latest snapshot: ```http://<IP_RASPBERRY_AI>:5000/ultima.jpg```

If ```/check``` returns JSON with ```success: true``` the AI node is working.

### 4.5 (Optional) automatic start with systemd

Create a systemd unit file:

```bash
sudo nano /etc/systemd/system/ai_3d_faildetect.service
```

Content:

```ini
[Unit]
Description=AI 3D Fail Detection server
After=network-online.target
Wants=network-online.target

[Service]
User=pi
WorkingDirectory=/home/pi/3d_ai_faildetect
ExecStart=/home/pi/3d_ai_faildetect/run_server.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai_3d_faildetect.service
sudo systemctl start ai_3d_faildetect.service
sudo systemctl status ai_3d_faildetect.service
```

---

## 5. Home Assistant configuration

### 5.1 Public snapshot folder

On Home Assistant filesystem create:

```text
/config/www/ai_3d/
```

This is where ```ultima.jpg``` will be stored, reachable at:

- ```http://homeassistant.local:8123/local/ai_3d/ultima.jpg```
- or ```https://<DOMINIO_HA>/local/ai_3d/ultima.jpg``` if served via HTTPS

### 5.2 Verify configuration.yaml

Ensure that your ```configuration.yaml``` includes packages and allows access to ```/config/www```:

```yaml
homeassistant:
  packages: !include_dir_named packages
  allowlist_external_dirs:
    - /config/www/ai_3d
    # ... other folders as needed
```

Restart Home Assistant after modifying this section.

### 5.3 Package ```ai_3d_faildetect.yaml```

Copy the following file entirely into:

```text
/config/packages/ai_3d_faildetect.yaml
```

Adapt entity_id values such as ```sensor.printer_power``` and ```switch.printer_plug``` to your real entities.

```yaml
# =====================================================
#  PACKAGE: AI – 3D print failure detection
#  Printer: generic (e.g. any FDM)
#  Version: 2025-12-XX
#
#  PURPOSE:
#    - Detect when the 3D printer is actually printing
#      by reading smart plug power consumption.
#    - Periodically call the AI node via REST.
#    - Receive a notification via webhook when a possible
#      print failure is detected.
#    - Create a persistent notification in HA including:
#        • link to dashboard
#        • updated AI snapshot
# =====================================================

# -----------------------------------------------------
# 1) TEMPLATE – Binary sensor "printer is printing"
# -----------------------------------------------------
template:
  - binary_sensor:
      - name: "3D Printer Printing"
        unique_id: ai_3d_printer_printing
        state: >
          {{
            is_state('switch.printer_plug', 'on')
            and (states('sensor.printer_power') | float(0)) > 20
          }}
        # Avoid bouncing: must stay above threshold for 30s
        delay_on:
          seconds: 30
        # After printing stops wait 2 minutes before turning off
        delay_off:
          minutes: 2
        icon: mdi:printer-3d

# -----------------------------------------------------
# 2) REST COMMAND – Call the AI node on Raspberry
# -----------------------------------------------------
rest_command:
  ai_3d_check:
    url: "http://<IP_RASPBERRY_AI>:5000/check"
    method: post
    timeout: 30
    verify_ssl: false
    content_type: "application/json"
    payload: >
      {
        "source": "home_assistant",
        "requested_at": "{{ now().isoformat() }}",
        "entity": "binary_sensor.stampante_3d_in_stampa"
      }

# -----------------------------------------------------
# 3) AUTOMATIONS
#    3.1 Periodic poll to AI node
#    3.2 Failure notification via webhook (persistent + push)
# -----------------------------------------------------
automation:

  # ---------------------------------------------------
  # 3.1 AI 3D – Poll when printer is printing
  #
  # Every minute:
  #   - if binary_sensor.stampante_3d_in_stampa is ON
  #     → call rest_command.ai_3d_check
  # ---------------------------------------------------
  - id: ai_3d_poll_when_printing
    alias: "AI 3D – Poll when printer printing"
    mode: single

    trigger:
      - platform: time_pattern
        minutes: "/1"

    condition:
      - condition: state
        entity_id: binary_sensor.stampante_3d_in_stampa
        state: "on"

    action:
      - service: rest_command.ai_3d_check
  # ---------------------------------------------------
  # 3.2 AI 3D – Failure notification (webhook from Raspberry)
  #
  # Trigger:
  #   - webhook_id: ai_3d_fail
  #
  # Actions:
  #   1) refresh snapshot from Raspberry
  #   2) create persistent notification
  #   3) send push message to phone
  # ---------------------------------------------------
  - id: ai_3d_failure_notification
    alias: "AI 3D – print failure detected"
    mode: single

    trigger:
      - platform: webhook
        webhook_id: ai_3d_fail

    variables:
      classe: "{{ trigger.json.class | default('Error') }}"
      confidenza: "{{ (trigger.json.confidence | float(0)) | round(2) }}"
      dashboard_url: "http://homeassistant.local:8123/stampa-3d/stampa-3d"
      snapshot_ha_url: "/local/ai_3d/ultima.jpg"

    action:
      - service: shell_command.ai_3d_snapshot_copy

      - service: persistent_notification.create
        data:
          title: "⚠️ 3D Printing – possible failure"
          notification_id: "ai_3d_faildetect"
          message: >
            Class: {{ classe }} – confidence: {{ confidenza }}

            Open the printer dashboard:
            [Open AI Print Dashboard]({{ dashboard_url }})

            Latest AI snapshot:
            [![Snapshot AI]({{ snapshot_ha_url }})]({{ snapshot_ha_url }})

      - service: notify.mobile_app_my_phone
        data:
          title: "⚠️ 3D Printing – possible failure"
          message: >
            Class: {{ classe }} – confidence: {{ confidenza }}.
            Dashboard: {{ dashboard_url }}
          data:
            ttl: 0
            priority: high
# -----------------------------------------------------
# 4) SCRIPT – manual snapshot refresh button
# -----------------------------------------------------
script:
  ai_3d_snapshot_manual:
    alias: "AI 3D – Manual snapshot refresh"
    mode: single
    sequence:
      - service: rest_command.ai_3d_check
      - service: shell_command.ai_3d_snapshot_copy

# -----------------------------------------------------
# 5) SHELL COMMAND – copy snapshot from Raspberry to HA
# -----------------------------------------------------
shell_command:
  ai_3d_snapshot_copy: >
    curl -s "http://<IP_RASPBERRY_AI>:5000/ultima.jpg"
    --output "/config/www/ai_3d/ultima.jpg"

# -----------------------------------------------------
# 6) CAMERA – entity to display snapshot in HA
# -----------------------------------------------------
camera:
  - platform: local_file
    name: "AI 3D Snapshot"
    file_path: /config/www/ai_3d/ultima.jpg

```

Replace:

- ```<IP_RASPBERRY_AI>``` with the IP of the Raspberry running AI  
- ```mobile_app_my_phone``` with your actual mobile app notify entity  
- ```switch.printer_plug``` and ```sensor.printer_power``` with your entities  

Restart HA or run “Check configuration” + “Restart”.

---

## 6. Example Lovelace Dashboard

You can create a view like:

```yaml
...
```

## 7. Final verification

1. Dashboard shows latest snapshot from ```ai_3d/```  
2. Press **Force AI analysis**:
   - HA calls the AI node
   - Raspberry saves a new frame
   - verify at ```http://<IP_RASPBERRY_AI>:5000/check```

3. If a failure class in ```error_classes``` is detected:
   - Raspberry sends webhook ```ai_3d_fail```
   - HA:
     - updates ```ultima.jpg```
     - creates persistent notification
     - sends push notification

---

## 8. Possible extensions

- pause or stop print (if supported)
- automatically power off printer on critical error
- send report via Telegram/email
- log failures to DB or file

---
