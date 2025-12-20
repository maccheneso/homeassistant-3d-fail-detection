
# AI Fail Detection – Raspberry Pi + Home Assistant  
_Rilevamento automatico errori di stampa 3D (locale, senza cloud)_


## 1. Obiettivo del progetto

Questo progetto permette di:

- rilevare automaticamente errori di stampa 3D  
  (es. spaghetti, distacco dal piatto, layer difettosi)
- usare **solo componenti locali** (nessun servizio cloud)
- inviare una **notifica sul telefono** con:
  - classe dell’errore + confidenza
  - link alla dashboard della stampante in Home Assistant
  - snapshot aggiornato dell’errore

### Architettura (alto livello)

1. Una webcam fornisce uno **stream MJPEG** della stampante.
2. Un **Raspberry Pi (3/4/5)** esegue un piccolo server Python:
   - cattura un frame
   - lo analizza con un modello AI YOLO (`best.pt`)
   - salva l’immagine
   - se trova un errore → invia un webhook a Home Assistant.
3. **Home Assistant**:
   - controlla se la stampante sta veramente stampando (potenza presa smart)
   - interroga periodicamente l’AI (`/check`)
   - quando riceve il webhook:
     - copia lo snapshot aggiornato in `/config/www/ai_3d/ultima.jpg`
     - mostra lo snapshot sulla dashboard
     - invia la notifica push sul telefono.

Tutto resta **dentro la LAN**.

---

## 2. Requisiti

### Hardware

- Raspberry Pi 4 o 5 (consigliato), con Linux (Raspberry Pi OS / Debian).
- Stampante 3D (qualsiasi marca).
- Webcam IP o USB che espone uno stream MJPEG, es.:
  - `http://IP_CAM:8080/?action=stream`
- Presa smart con sensore di potenza (es. Zigbee/Z-Wave/Wi-Fi supportata da Home Assistant).

### Software

Sul Raspberry (nodo AI):

- Python 3.10 o superiore
- Virtualenv
- Pacchetti Python (installati con `requirements.txt`):
  - `ultralytics` (YOLO)
  - `opencv-python`
  - `Flask`
  - `PyYAML`
  - `requests`
  - altri indicati nel file `requirements.txt`

Su Home Assistant:

- Home Assistant Core / OS già operativo
- integrazione **Mobile App** per le notifiche push
- una presa smart integrata con:
  - `switch.<nome_presa_stampante>`
  - `sensor.<nome_potenza_stampante>`

---

## 3. Contenuto dello ZIP (progetto da copiare sul Raspberry)

Cartella principale, ad es. `/home/pi/3d_ai_faildetect`:

```text
3d_ai_faildetect/
├─ app/
│  ├─ __init__.py
│  ├─ ai_core.py        # logica AI (YOLO + webhook)
│  └─ server.py         # server Flask con /check e /ultima.jpg
│
├─ model/
│  └─ best.pt           # modello YOLO personalizzato (difetti di stampa)
│
├─ frames/              # verranno salvati i frame "puliti"
├─ runs/                # output YOLO (bounding box)
│
├─ config.yaml          # configurazione AI lato Raspberry
├─ requirements.txt     # dipendenze Python
├─ setup.sh             # script di setup (venv + pip install)
├─ run_server.sh        # avvio del server AI
└─ README.md            # questo file

```
La cartella ```venv/``` non è inclusa nello ZIP: viene creata da ```setup.sh```.

## 4. Installazione sul Raspberry Pi (nodo AI)

### 4.1 Copia della cartella
Copia l’intera cartella ```3d_ai_faildetect``` sul Raspberry, es. in ```/home/pi/```:
```bash
scp -r 3d_ai_faildetect pi@<IP_RASPBERRY>:/home/pi/
```
oppure via Samba / chiavetta, come preferisci.

Poi accedi:
```bash
ssh pi@<IP_RASPBERRY>
cd /home/pi/3d_ai_faildetect
```
### 4.2 Script di setup (creazione virtualenv + dipendenze)
_Lo script `setup.sh` è già incluso nello ZIP, nella cartella del progetto:_
```bash
/home/pi/3d_ai_faildetect/setup.sh
```
Rendi eseguibile lo script e avvialo:
```bash
chmod +x setup.sh
./setup.sh
```
Lo script si occupa di:
1. creare una virtualenv ```venv/``` nella cartella del progetto
2. attivarla
3. installare tutti i pacchetti Python da ```requirements.txt```
4. creare se necessario le cartelle ```frames/``` e ```runs/```.

Al termine dovresti avere ```venv/``` creata e nessun errore in console.

### 4.3 Configurazione ```config.yaml```

Apri ```config.yaml``` e adatta i parametri alla tua rete:
```yaml
# Configurazione nodo AI per rilevamento guasti stampa 3D

# URL dello stream MJPEG della webcam collegata alla stampante
stream_url: "http://<IP_CAM>:8080/?action=stream"

# Percorso del modello YOLO addestrato (relativo alla cartella del progetto)
model_path: "model/best.pt"

# Dimensione immagine per YOLO (640 è un buon compromesso)
imgsz: 640

# Soglia di confidenza minima per considerare un rilevamento significativo
min_confidence: 0.60

# Classi da considerare come "guasto reale" (le altre possono essere ignorate)
# Usa esattamente i nomi definiti nel data.yaml / training Roboflow.
error_classes:
  - "Spaghetti"
  - "Detached Filament"
  - "Detached Layer"
  - "Layer Defect"

# Classi da considerare solo "avviso soft" (non fermano stampa, ma puoi loggarle)
warning_classes:
  - "Singular String"
  - "Stringing"

# Webhook di Home Assistant per segnalare un guasto
# Sostituisci <HA_IP> con l'IP del tuo Home Assistant.
ha_webhook_url: "http://<HA_IP>:8123/api/webhook/ai_3d_fail"

# Timeout in secondi per chiamare il webhook di HA
ha_webhook_timeout: 10

# Dove salvare i frame catturati (relativo alla cartella del progetto)
frames_dir: "frames"

# Dove salvare i risultati YOLO con bounding box (gestito da Ultralytics)
results_dir: "runs/detect"

# Log semplice su stdout (true/false)
log_debug: true

```
Cose importanti da personalizzare:
  - ```stream_url``` → IP/porta della tua webcam
  - ```ha_webhook_url``` → IP e porta di Home Assistant (LAN)

### 4.4 Avvio manuale del server AI

Per testare:
```
chmod +x run_server.sh
./run_server.sh
```
Se tutto è a posto, vedrai il server Flask in ascolto su ```0.0.0.0:5000```.

Puoi testare dal browser:

  - Check AI: ```http://<IP_RASPBERRY_AI>:5000/check```
  - Ultima immagine: ```http://<IP_RASPBERRY_AI>:5000/ultima.jpg```

Se ```/check``` restituisce un JSON con ```success: true```, il nodo AI è operativo.

### 4.5 (Opzionale) Avvio automatico con systemd

Crea un unit file:
```bash
sudo nano /etc/systemd/system/ai_3d_faildetect.service
```
Contenuto:
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
Poi:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai_3d_faildetect.service
sudo systemctl start ai_3d_faildetect.service
sudo systemctl status ai_3d_faildetect.service
```
## 5. Configurazione Home Assistant

### 5.1 Cartella snapshot pubblica

Sul filesystem di Home Assistant crea:
```text
/config/www/ai_3d/
```
Qui verrà salvato ```ultima.jpg```, raggiungibile come:

  - ```http://homeassistant.local:8123/local/ai_3d/ultima.jpg```
  - oppure ```https://<DOMINIO_HA>/local/ai_3d/ultima.jpg``` se esposto via HTTPS.

### 5.2 Verifica configuration.yaml

Assicurati che il tuo ```configuration.yaml``` includa i packages e permetta l’accesso a ```/config/www``` (esempio):
```yaml
homeassistant:
  packages: !include_dir_named packages
  allowlist_external_dirs:
    - /config/www/ai_3d
    # ... altri percorsi che usi già
```
Riavvia Home Assistant se modifichi questa sezione.

### 5.3 Pacchetto ```ai_3d_faildetect.yaml```

Copia il seguente file intero in:
```text
/config/packages/ai_3d_faildetect.yaml
```
Adatta gli entity_id ```sensor.printer_power``` e ```switch.printer_plug``` ai tuoi nomi reali.

```yaml
# =====================================================
#  PACCHETTO: AI – Rilevamento guasti stampa 3D
#  Stampante: generica (es. qualsiasi FDM)
#  Versione: 2025-12-XX
#
#  SCOPO:
#    - Riconoscere quando la stampante 3D sta effettivamente stampando
#      usando la potenza della presa smart.
#    - Chiamare periodicamente il nodo AI su Raspberry (REST).
#    - Ricevere una notifica da Raspberry tramite webhook quando viene
#      rilevato un possibile guasto.
#    - Mostrare una notifica persistente in HA con:
#        • link alla dashboard
#        • snapshot aggiornato
# =====================================================

# -----------------------------------------------------
# 1) TEMPLATE – Binary sensor "stampante in stampa"
# -----------------------------------------------------
template:
  - binary_sensor:
      - name: "Stampante 3D in stampa"
        unique_id: ai_3d_stampante_in_stampa
        state: >
          {{
            is_state('switch.printer_plug', 'on')
            and (states('sensor.printer_power') | float(0)) > 20
          }}
        # Evita rimbalzi: deve restare sopra soglia per 30 s
        delay_on:
          seconds: 30
        # Dopo fine stampa aspetta 2 minuti prima di dire "off"
        delay_off:
          minutes: 2
        icon: mdi:printer-3d

# -----------------------------------------------------
# 2) REST COMMAND – Chiamata al nodo AI su Raspberry
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
# 3) AUTOMAZIONI
#    3.1 Poll periodico verso il nodo AI
#    3.2 Notifica errore da webhook (persistente + push)
# -----------------------------------------------------
automation:

  # ---------------------------------------------------
  # 3.1 AI 3D – Poll quando la stampante è in stampa
  #
  # Ogni minuto:
  #   - se binary_sensor.stampante_3d_in_stampa è ON
  #     → chiama rest_command.ai_3d_check
  # ---------------------------------------------------
  - id: ai_3d_poll_quando_in_stampa
    alias: "AI 3D – Poll quando stampante in stampa"
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
  # 3.2 AI 3D – Notifica errore stampa (webhook da Raspberry)
  #
  # Trigger:
  #   - webhook_id: ai_3d_fail
  #
  # Azioni:
  #   1) Aggiorna subito lo snapshot da Raspberry.
  #   2) Crea notifica persistente in HA (con link e immagine).
  #   3) Invia notifica push su telefono.
  # ---------------------------------------------------
  - id: ai_3d_notifica_errore_stampa
    alias: "AI 3D – Notifica errore stampa"
    mode: single

    trigger:
      - platform: webhook
        webhook_id: ai_3d_fail

    variables:
      classe: "{{ trigger.json.class | default('Errore') }}"
      confidenza: "{{ (trigger.json.confidence | float(0)) | round(2) }}"
      # URL della dashboard HA dedicata alla stampa 3D
      dashboard_url: "http://homeassistant.local:8123/stampa-3d/stampa-3d"
      # URL snapshot locale servito da HA (immagine AI)
      snapshot_ha_url: "/local/ai_3d/ultima.jpg"

    action:
      # 3.2.a Aggiorna prima lo snapshot
      - service: shell_command.ai_3d_snapshot_copy

      # 3.2.b Notifica persistente in Home Assistant
      - service: persistent_notification.create
        data:
          title: "⚠️ Stampa 3D – possibile errore"
          notification_id: "ai_3d_faildetect"
          message: >
            Classe: {{ classe }} – confidenza: {{ confidenza }}

            Apri la dashboard della stampante:
            [Apri dashboard AI Stampa 3D]({{ dashboard_url }})

            Ultimo snapshot AI (cliccabile):
            [![Snapshot AI]({{ snapshot_ha_url }})]({{ snapshot_ha_url }})

      # 3.2.c Notifica push su telefono (Mobile App)
      - service: notify.mobile_app_my_phone
        data:
          title: "⚠️ Stampa 3D – possibile errore"
          message: >
            Classe: {{ classe }} – confidenza: {{ confidenza }}.
            Dashboard: {{ dashboard_url }}
          data:
            ttl: 0
            priority: high

# -----------------------------------------------------
# 4) SCRIPT – Snapshot manuale da pulsante Lovelace
# -----------------------------------------------------
script:
  ai_3d_snapshot_manual:
    alias: "AI 3D – Aggiorna snapshot manuale"
    mode: single
    sequence:
      - service: rest_command.ai_3d_check
      - service: shell_command.ai_3d_snapshot_copy

# -----------------------------------------------------
# 5) SHELL COMMAND – Copia snapshot da Raspberry a HA
# -----------------------------------------------------
shell_command:
  ai_3d_snapshot_copy: >
    curl -s "http://<IP_RASPBERRY_AI>:5000/ultima.jpg"
    --output "/config/www/ai_3d/ultima.jpg"

# -----------------------------------------------------
# 6) CAMERA – Entità per visualizzare lo snapshot in HA
# -----------------------------------------------------
camera:
  - platform: local_file
    name: "AI 3D Snapshot"
    file_path: /config/www/ai_3d/ultima.jpg

```
Sostituisci:

  - ```<IP_RASPBERRY_AI>``` con l’IP del Raspberry dove gira l’AI
  - ```mobile_app_my_phone``` con l’entity_id della tua app mobile
  - ```switch.printer_plug``` / ```sensor.printer_power``` con i tuoi entity_id.

Riavvia Home Assistant o fai “Controlla configurazione” + “Riavvia”.

## 6. Dashboard Lovelace di esempio

Puoi creare una view tipo:
```yaml
views:
  - title: AI – Stampa 3D
    path: stampa-3d
    icon: mdi:printer-3d
    cards:
      - type: picture-entity
        entity: camera.ai_3d_snapshot
        camera_view: live
        show_state: false
        show_name: false

      - type: entities
        title: Stato stampante 3D
        entities:
          - entity: binary_sensor.stampante_3d_in_stampa
            name: Stampante in stampa
          - entity: sensor.printer_power
            name: Potenza istantanea (W)
          - entity: switch.printer_plug
            name: Presa stampante (ON/OFF)

      - type: horizontal-stack
        cards:
          - type: button
            name: Forza analisi AI
            icon: mdi:robot
            tap_action:
              action: call-service
              service: rest_command.ai_3d_check

          - type: button
            name: Aggiorna snapshot
            icon: mdi:image-refresh
            tap_action:
              action: call-service
              service: script.ai_3d_snapshot_manual
```

## 7. Verifica finale

 1. La dashboard mostra l’ultimo snapshot dalla cartella ```ai_3d/```.
 2. Premendo **Forza analisi AI**:
    - HA chiama il nodo AI
    - il Raspberry salva una nuova immagine
    - puoi verificare ```http://<IP_RASPBERRY_AI>:5000/check```.

 3. In caso di errore (classe nei ```error_classes```):
    - il Raspberry manda il webhook ```ai_3d_fail```
    - HA:
        - aggiorna ```ultima.jpg```
        - crea la notifica persistente
        - invia la notifica push sul telefono.

## 8. Estensioni possibili

  - mettere in pausa o fermare la stampa (se la stampante è controllabile da HA)
  - spegnere automaticamente la presa in caso di errore grave
  - inviare report su Telegram o e-mail
  - loggare gli errori in un file o in un database per statistiche.

## 9. Note e limitazioni

**Il modello ```best.pt``` addestrato su un dataset di difetti di stampa**
**(es. tramite Roboflow + Ultralytics) non è stato inserito per rispettare le licenze**
**Questo repository contiene il framework AI + integrazione Home Assistant.**
**Per usare il modello AI serve fornire un proprio best.pt.**
**Vedi guida: HOW_TO_TRAIN_MODEL.md.**

Le prestazioni dipendono da:
  - qualità dello stream
  - luce nell’area di stampa
  - potenza del Raspberry

Il sistema non sostituisce il monitoraggio umano: è un “assistente” che intercetta errori evidenti e ripetitivi.
