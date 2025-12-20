# 💡 Come addestrare un modello per AI_3D_FailDetect

Questo progetto **non include** pesi di modelli (`best.pt`), per rispetto delle licenze dei dataset originali.

Questa guida ti permette di:

✔ ottenere un dataset pubblico  
✔ addestrare YOLO in locale  
✔ inserire correttamente `best.pt` nel progetto  

---

# 1. 📥 Ottenere un dataset

Puoi scegliere tra due strade:

---

## 🔹 A) usare dataset pubblici disponibili

Esistono dataset di stampa 3D su Roboflow Universe.

🔗 Cerca dataset con parole chiave:  

👉 https://universe.roboflow.com/search?q=dataset%203d%20print  

  - Registrati (è gratuito) 
  - Seleziona dataset con licenza che permetta il riuso o la modifica.
  - Crea un Workflow
  - Scarica il Dataset
	
---

## 🔹 B) creare un dataset personale

1. cattura snapshot dalla webcam della stampante  
2. annota i difetti reali:
   - spaghetti
   - delaminazione
   - distacco dal piatto
   - cordoni anomali
3. usa strumenti come:
   - Roboflow Annotate
   - CVAT
   - Label Studio  

Poi esporta in formato YOLOv5/YOLOv8 PyTorch.

---

# 2. 🛠 Installazione degli strumenti YOLO

Su Raspberry Pi o su un PC più potente:

```
pip install ultralytics
```
Verifica installazione:

```
yolo --version

```

# 3. 🚀 Addestramento YOLO

Esegui:

```
yolo detect train \
  model=yolov8n.pt \
  data=/home/utente/datasets/ai_3d_fail/data.yaml \
  epochs=50 imgsz=640
```
Il file data.yaml generato dal dataset contiene:

   - percorso immagini train / val / test
   - nomi delle classi
   - numero totale classi (nc:)
Se sposti il dataset, aggiorna data.yaml.


Esempio di data.yaml:

```
train: /home/utente/datasets/ai_3d_fail/train/images
val: /home/utente/datasets/ai_3d_fail/valid/images

nc: 4
names:
  - Spaghetti
  - Detached Filament
  - Detached Layer
  - Layer Defect
```

Note:

   - puoi aumentare gli epochs per migliorare l'accuratezza
   - modelli più grandi richiedono più risorse (yolov8s/m/l)


# 4. 📦 Recupero del modello addestrato

YOLO crea una directory simile a:

```
runs/detect/train/weights/
```
e dentro troverai:

   - ```best.pt``` ← pesa migliore da usare
   - ```last.pt```

# 5. 📍 Inserisci il modello nel progetto

Copia il file:
```
model/best.pt
```

Il server AI lo caricherà automaticamente usando il percorso nel file ```config.yaml```.

# 6. 🔍 Verifica classi e coerenza config

Assicurati che nel file ```config.yaml```:

```
error_classes:
  - "Spaghetti"
  - "Detached Filament"
  - "Detached Layer"
  - "Layer Defect"
```

I nomi devono corrispondere a quelli nel dataset (```data.yaml```).

## 6.1. 🎯 Nota importante sulle class labels

Le **classi nel dataset** devono corrispondere **esattamente** ai nomi definiti in config.yaml.

Esempio corretto:
```
error_classes:
  - "Spaghetti"
```
🚫 NO se il dataset usa versioni diverse del nome, come:
  - "spaghetti"
  - "extrusion_spaghetti"
  - "stringing_spaghetti"

⚠ Suggerimenti:
  - controlla data.yaml → campo names:
  - copia/incolla esattamente quei valori
  - evita spazi e capitalizzazione diversa

Se i nomi non coincidono, il nodo AI:
  - rileva il difetto
  - **ma Home Assistant non triggera il webhook**
  - quindi nessuna notifica viene generata

# 7. 🧪 Test finale

Avvia il server AI:

```
./run_server.sh
```

Poi visita dal browser:
```
http://<IP_RASPBERRY_AI>:5000/check
```

Se vedi:

```
{"success": true}
```
allora:

✔ la configurazione è valida
✔ il modello è caricato
✔ l’AI è pronta per l’uso

# ⚠️ Suggerimento:
anche se è possibile addestrare YOLO su Raspberry Pi,
si consiglia di addestrare su PC con GPU/CPU più potente
e poi copiare best.pt nella cartella model/.




# Note e avvertenze

  - non redistribuire dataset o modelli senza licenza
  - fare attenzione ai falsi positivi, soprattutto in early training
  - puoi migliorare il modello aggiungendo immagini reali dei tuoi fallimenti di stampa
  
# Contribuire

  - Se vuoi condividere miglioramenti:
  - apri una Issue
  - invia una Pull Request
  - suggerisci dataset pubblici verificati
  
# FAQ rapide

Quante immagini servono?
  - almeno 200–300 immagini reali divise per classe.

Supporta dataset multi-classe?
  - sì, basta aggiungere classi in config.yaml.

Che risoluzione usare?
  - 640 o 720 px sono un buon compromesso.