
from pathlib import Path
from threading import RLock
from datetime import datetime, timezone

import joblib


# ---------------------------------------------------------
# PRE-GUARD AI — MODEL MANAGER
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = BASE_DIR / "models" / "neural_network.joblib"
SCALER_PATH = BASE_DIR / "models" / "neural_network_scaler.joblib"


class ModelManager:
    """
    Thread-safe manager for the active PRE-GUARD AI model
    and its corresponding scaler.
    """

    def __init__(self):
        self._lock = RLock()

        self._model = None
        self._scaler = None

        self._loaded_at = None
        self._model_version = None

        self.load_model()

    def load_model(self):
        """
        Load model and scaler together before replacing
        the currently active pair.
        """

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found: {MODEL_PATH}"
            )

        if not SCALER_PATH.exists():
            raise FileNotFoundError(
                f"Scaler not found: {SCALER_PATH}"
            )

        # Load both into temporary variables first.
        new_model = joblib.load(MODEL_PATH)
        new_scaler = joblib.load(SCALER_PATH)

        # Validate compatibility.
        if (
            hasattr(new_model, "n_features_in_")
            and hasattr(new_scaler, "n_features_in_")
            and new_model.n_features_in_
            != new_scaler.n_features_in_
        ):
            raise ValueError(
                "Model and scaler feature counts do not match."
            )

        # Swap the pair together.
        with self._lock:
            self._model = new_model
            self._scaler = new_scaler

            self._loaded_at = datetime.now(
                timezone.utc
            ).isoformat()

            self._model_version = (
                self._loaded_at.replace(":", "-")
            )

        print("[PRE-GUARD] Model loaded successfully.")
        print(
            "[PRE-GUARD] Features:",
            getattr(new_model, "n_features_in_", "unknown")
        )

    def predict(self, features):
        """
        Predict using the currently active model.
        """

        with self._lock:
            scaled_features = self._scaler.transform(
                features
            )

            probabilities = self._model.predict_proba(
                scaled_features
            )

            return probabilities

    def get_status(self):
        """
        Return active model information.
        """

        with self._lock:
            return {
                "loaded": self._model is not None,
                "model_type": (
                    type(self._model).__name__
                    if self._model is not None
                    else None
                ),
                "features": getattr(
                    self._model,
                    "n_features_in_",
                    None
                ),
                "iterations": getattr(
                    self._model,
                    "n_iter_",
                    None
                ),
                "model_version": self._model_version,
                "loaded_at": self._loaded_at,
            }


# ---------------------------------------------------------
# GLOBAL MODEL MANAGER
# ---------------------------------------------------------

model_manager = ModelManager()
