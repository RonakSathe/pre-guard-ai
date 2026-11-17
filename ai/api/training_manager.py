from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from datetime import datetime, timezone

from ai.training.train_neural_network import train_model
from ai.api.model_manager import model_manager

# ---------------------------------------------------------
# PRE-GUARD AI — BACKGROUND TRAINING MANAGER
# ---------------------------------------------------------

executor = ThreadPoolExecutor(max_workers=1)

status_lock = Lock()

training_status = {
    "status": "idle",
    "started_at": None,
    "completed_at": None,
    "message": "No training has been started.",
    "error": None,
    "model_reloaded": False,
}


def current_time():
    return datetime.now(timezone.utc).isoformat()


def get_training_status():
    """Return a safe copy of the current training status."""

    with status_lock:
        return training_status.copy()


def update_status(**kwargs):
    """Update training status safely."""

    with status_lock:
        training_status.update(kwargs)


def run_training():
    """Run MLP training in a background worker."""

    update_status(
        status="running",
        started_at=current_time(),
        completed_at=None,
        message="MLP training is in progress.",
        error=None,
        model_reloaded=False,
    )

    print("\n[PRE-GUARD] Background training started.")

    try:
        # Run the existing training pipeline.
        train_model()

        # Load the newly saved model and scaler.
        # ModelManager loads both before swapping the active pair.
        model_manager.load_model()

        update_status(
            status="completed",
            completed_at=current_time(),
            message="Training completed and model manager reloaded.",
            model_reloaded=True,
        )

        print("[PRE-GUARD] Background training completed.")

    except Exception as error:

        update_status(
            status="failed",
            completed_at=current_time(),
            message="Training failed. The previous in-memory model remains active.",
            error=str(error),
            model_reloaded=False,
        )

        print(f"[PRE-GUARD] Training failed: {error}")


def start_training():
    """Start training only when another training job is not running."""

    with status_lock:

        if training_status["status"] == "running":
            return {
                "started": False,
                "message": "Training is already running.",
                "status": training_status.copy(),
            }

        training_status.update({
            "status": "running",
            "started_at": current_time(),
            "completed_at": None,
            "message": "Training job queued.",
            "error": None,
            "model_reloaded": False,
        })

    try:
        executor.submit(run_training)

        return {
            "started": True,
            "message": "Background training started.",
        }

    except Exception as error:

        update_status(
            status="failed",
            completed_at=current_time(),
            message="Could not start training.",
            error=str(error),
        )

        return {
            "started": False,
            "message": "Could not start training.",
            "error": str(error),
        }
