
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from datetime import datetime, timezone

from ai.training.train_neural_network import (
    train_model,
    ModelRejectedError,
)
from ai.api.model_manager import model_manager


# ---------------------------------------------------------
# PRE-GUARD AI — BACKGROUND TRAINING MANAGER
# ---------------------------------------------------------

executor = ThreadPoolExecutor(max_workers=1)

status_lock = Lock()

training_status = {
    "status": "idle",
    "stage": "idle",
    "started_at": None,
    "completed_at": None,
    "message": "No training has been started.",
    "error": None,
    "rejection_reason": None,
    "metrics": None,
    "model_reloaded": False,
}


def current_time():
    return datetime.now(timezone.utc).isoformat()


def get_training_status():
    """Return a safe copy of the current training status."""

    with status_lock:
        result = training_status.copy()

        if training_status["metrics"] is not None:
            result["metrics"] = training_status["metrics"].copy()

        return result


def update_status(**kwargs):
    """Update training status safely."""

    with status_lock:
        training_status.update(kwargs)


def run_training():
    """Run MLP training in a background worker."""

    update_status(
        status="running",
        stage="training",
        started_at=current_time(),
        completed_at=None,
        message="MLP training is in progress.",
        error=None,
        rejection_reason=None,
        metrics=None,
        model_reloaded=False,
    )

    print("\n[PRE-GUARD] Background training started.")

    try:
        # Execute the training pipeline.
        result = train_model()

        # Validate the training result.
        if not isinstance(result, dict) or not result.get("accepted"):
            raise RuntimeError(
                "Training finished without a valid accepted result."
            )

        metrics = result.get("metrics")

        if not isinstance(metrics, dict):
            raise RuntimeError(
                "Training completed without evaluation metrics."
            )

        update_status(
            stage="deploying",
            message="Quality checks passed. Reloading the active model.",
        )

        # Reload both model and scaler.
        model_manager.load_model()

        update_status(
            status="completed",
            stage="completed",
            completed_at=current_time(),
            message="Training completed and the new model was deployed.",
            metrics=metrics,
            model_reloaded=True,
        )

        print("[PRE-GUARD] Background training completed.")

    except ModelRejectedError as error:

        update_status(
            status="rejected",
            stage="rejected",
            completed_at=current_time(),
            message="Candidate model did not meet deployment requirements.",
            rejection_reason=str(error),
            error=None,
            model_reloaded=False,
        )

        print(f"[PRE-GUARD] Model rejected: {error}")

    except Exception as error:

        update_status(
            status="failed",
            stage="failed",
            completed_at=current_time(),
            message="Training or deployment failed. Check the error details.",
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
            "stage": "queued",
            "started_at": current_time(),
            "completed_at": None,
            "message": "Training job queued.",
            "error": None,
            "rejection_reason": None,
            "metrics": None,
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
            stage="failed",
            completed_at=current_time(),
            message="Could not start training.",
            error=str(error),
            model_reloaded=False,
        )

        return {
            "started": False,
            "message": "Could not start training.",
            "error": str(error),
        }
