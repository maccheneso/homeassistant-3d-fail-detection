from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request, send_file, abort

from app.ai_core import AIFailDetect

# ----------------------------------------------------
# Percorsi base del progetto
# ----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
FRAMES_DIR = BASE_DIR / "frames"
FRAMES_DIR.mkdir(exist_ok=True)

# Inizializzazione globale del nodo AI
ai_node = AIFailDetect(base_dir=BASE_DIR)

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    """
    Endpoint semplice per verificare che il server sia vivo.
    """
    return jsonify({"status": "ok"}), 200


@app.route("/check", methods=["POST", "GET"])
def check():
    """
    Endpoint chiamato da Home Assistant (rest_command.ai_3d_check).
    Esegue:
      - cattura frame
      - inferenza YOLO
      - eventuale webhook verso HA
    Ritorna JSON con il risultato sintetico.
    """
    try:
        result = ai_node.capture_and_check()
        return jsonify(
            {
                "success": True,
                "result": result,
            }
        ), 200
    except Exception as e:
        # Log basilare: in produzione useremmo logging strutturato
        print(f"[SERVER] ERRORE in /check: {e}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
            }
        ), 500


@app.get("/ultima.jpg")
def ultima_jpg():
    """
    Restituisce l'ultimo frame JPG disponibile nella cartella FRAMES_DIR.
    NON apre lo stream della stampante: legge solo i file già salvati su disco.
    """
    try:
        # Prende tutti i .jpg nella cartella frames, ordinati, e sceglie l'ultimo
        jpg_files = sorted(FRAMES_DIR.glob("*.jpg"))
        if not jpg_files:
            abort(404, description="Nessun frame JPG disponibile")

        last_jpg = jpg_files[-1]
        return send_file(last_jpg, mimetype="image/jpeg")
    except Exception as e:
        print(f"[SERVER] ERRORE in /ultima.jpg: {e}")
        abort(500, description=f"Errore nel leggere ultima immagine: {e}")


if __name__ == "__main__":
    # Avvio diretto (debug)
    # In produzione useremo run_server.sh
    app.run(host="0.0.0.0", port=5000)
