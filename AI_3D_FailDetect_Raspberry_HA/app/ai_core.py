from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import requests
import yaml
from ultralytics import YOLO


@dataclass
class AIConfig:
    stream_url: str
    model_path: Path
    imgsz: int
    min_confidence: float
    error_classes: List[str]
    warning_classes: List[str]
    ha_webhook_url: str
    ha_webhook_timeout: int
    frames_dir: Path
    results_dir: Path
    log_debug: bool = False


class AIFailDetect:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.config = self._load_config()
        self.model = self._load_model()

    # --------------------------
    # CONFIG & MODEL
    # --------------------------
    def _load_config(self) -> AIConfig:
        cfg_path = self.base_dir / "config.yaml"
        if not cfg_path.exists():
            raise FileNotFoundError(f"config.yaml non trovato in {cfg_path}")

        with cfg_path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        def get(key: str, default=None):
            return raw.get(key, default)

        config = AIConfig(
            stream_url=get("stream_url"),
            model_path=(self.base_dir / get("model_path")).resolve(),
            imgsz=int(get("imgsz", 640)),
            min_confidence=float(get("min_confidence", 0.8)),
            error_classes=list(get("error_classes", [])),
            warning_classes=list(get("warning_classes", [])),
            ha_webhook_url=str(get("ha_webhook_url")),
            ha_webhook_timeout=int(get("ha_webhook_timeout", 10)),
            frames_dir=(self.base_dir / get("frames_dir", "frames")).resolve(),
            results_dir=(self.base_dir / get("results_dir", "runs/detect")).resolve(),
            log_debug=bool(get("log_debug", False)),
        )

        if config.log_debug:
            print("[AI] Config caricata:", config)

        return config

    def _load_model(self) -> YOLO:
        if not self.config.model_path.exists():
            raise FileNotFoundError(f"Modello YOLO non trovato in {self.config.model_path}")
        if self.config.log_debug:
            print(f"[AI] Carico modello YOLO da {self.config.model_path}")
        model = YOLO(str(self.config.model_path))
        return model

    # --------------------------
    # FRAME CAPTURE
    # --------------------------
    def grab_frame(self) -> Path:
        """
        Cattura un singolo frame dallo stream MJPEG e lo salva in frames_dir.
        """
        self.config.frames_dir.mkdir(parents=True, exist_ok=True)

        if self.config.log_debug:
            print(f"[AI] Apro stream: {self.config.stream_url}")

        cap = cv2.VideoCapture(self.config.stream_url)
        ok, frame = cap.read()
        cap.release()

        if not ok or frame is None:
            raise RuntimeError("Impossibile leggere frame dallo stream")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_path = self.config.frames_dir / f"frame_{ts}.jpg"

        if not cv2.imwrite(str(img_path), frame):
            raise RuntimeError(f"Impossibile salvare il frame in {img_path}")

        if self.config.log_debug:
            print(f"[AI] Frame salvato in {img_path}")

        return img_path

    # --------------------------
    # INFERENCE
    # --------------------------
    def run_inference(self, img_path: Path) -> Any:
        """
        Esegue l'inferenza YOLO su un'immagine.
        """
        if self.config.log_debug:
            print(f"[AI] Eseguo inferenza su {img_path}")

        results = self.model.predict(
            source=str(img_path),
            imgsz=self.config.imgsz,
            conf=self.config.min_confidence,
            save=True,
            project=str(self.config.results_dir),
            name="predict",
            exist_ok=True,
            verbose=self.config.log_debug,
        )
        return results

    def summarize_results(self, results: Any) -> Dict[str, Any]:
        """
        Restituisce un dizionario con:
        - error (bool)
        - warning (bool)
        - detections (lista dettagliata)
        - main_class / main_confidence
        """
        if not results:
            return {
                "error": False,
                "warning": False,
                "detections": [],
                "main_class": None,
                "main_confidence": None,
            }

        r = results[0]

        if r.boxes is None or len(r.boxes) == 0:
            return {
                "error": False,
                "warning": False,
                "detections": [],
                "main_class": None,
                "main_confidence": None,
            }

        names = r.names
        boxes = r.boxes

        detections: List[Dict[str, Any]] = []
        main_class: Optional[str] = None
        main_conf: float = 0.0
        error_flag = False
        warning_flag = False

        for box in boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            cls_name = names.get(cls_id, str(cls_id))

            det = {
                "class_id": cls_id,
                "class_name": cls_name,
                "confidence": conf,
            }
            detections.append(det)

            # aggiorna main_class
            if conf > main_conf:
                main_conf = conf
                main_class = cls_name

            # segna error/warning
            if cls_name in self.config.error_classes and conf >= self.config.min_confidence:
                error_flag = True
            if cls_name in self.config.warning_classes and conf >= self.config.min_confidence:
                warning_flag = True

        summary = {
            "error": error_flag,
            "warning": warning_flag,
            "detections": detections,
            "main_class": main_class,
            "main_confidence": main_conf,
        }

        if self.config.log_debug:
            print("[AI] Risultato sintetico:", summary)

        return summary

    # --------------------------
    # WEBHOOK HOME ASSISTANT
    # --------------------------
    def notify_home_assistant(self, summary: Dict[str, Any], img_path: Optional[Path] = None) -> bool:
        """
        Invia un webhook a Home Assistant in caso di errore.
        Ritorna True se la richiesta HTTP è andata a buon fine.
        """
        if not summary.get("error"):
            if self.config.log_debug:
                print("[AI] Nessun errore, nessun webhook inviato.")
            return False

        payload: Dict[str, Any] = {
            "class": summary.get("main_class"),
            "confidence": summary.get("main_confidence"),
            "detections": summary.get("detections", []),
            "timestamp": datetime.now().isoformat(),
        }

        if img_path is not None:
            # In futuro potremo copiare il file in una cartella accessibile a HA.
            payload["image_local_path"] = str(img_path)

        if self.config.log_debug:
            print(f"[AI] Invio webhook a Home Assistant: {self.config.ha_webhook_url}")
            print("[AI] Payload:", payload)

        try:
            resp = requests.post(
                self.config.ha_webhook_url,
                json=payload,
                timeout=self.config.ha_webhook_timeout,
            )
            if self.config.log_debug:
                print("[AI] Webhook risposta:", resp.status_code, resp.text)
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"[AI] ERRORE invio webhook a Home Assistant: {e}")
            return False

    # --------------------------
    # FUNZIONE ALTO LIVELLO
    # --------------------------
    def capture_and_check(self) -> Dict[str, Any]:
        """
        Funzione completa:
        - cattura frame
        - esegue YOLO
        - sintetizza risultato
        - se errore -> invia webhook
        - ritorna un dizionario riassuntivo
        """
        img_path = self.grab_frame()
        results = self.run_inference(img_path)
        summary = self.summarize_results(results)

        if summary.get("error"):
            self.notify_home_assistant(summary, img_path=img_path)

        return {
            "image_path": str(img_path),
            **summary,
        }
