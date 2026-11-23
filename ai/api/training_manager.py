
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from datetime import datetime, timezone
import json
from pathlib import Path

from ai.training.train_neural_network import (
    train_model,
    ModelRejectedError,
)
from ai.api.model_manager import model_manager


# ---------------------------------------------------------
# PRE-GUARD AI — BACKGROUND TRAINING MANAGER
# ---------------------------------------------------------

executor = ThreadPoolExecutor(max_workers=1)

FEEDBACK_COUNTER_PATH = Path("ai/data/feedback_counter.json")
FEEDBACK_BATCH_SIZE = 10

status_lock = Lock()
feedback_counter_lock = Lock()
feedback_check_lock = Lock()


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


# ---------------------------------------------------------
# TRAINING STATUS
# ---------------------------------------------------------

def is_training_running():
    """Check whether a training job is currently running or queued."""

    with status_lock:
        return training_status["status"] == "running"


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


# ---------------------------------------------------------
# FEEDBACK COUNTER HELPERS
# ---------------------------------------------------------

def read_feedback_counter():
    """Read the feedback counter safely."""

    if not FEEDBACK_COUNTER_PATH.exists():
        return {
            "total_feedback": 0,
            "last_training_trigger": 0,
        }

    with open(
        FEEDBACK_COUNTER_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        counter_data = json.load(file)

    counter_data.setdefault("total_feedback", 0)
    counter_data.setdefault("last_training_trigger", 0)

    return counter_data


def save_feedback_counter(counter_data):
    """Save the feedback counter."""

    FEEDBACK_COUNTER_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        FEEDBACK_COUNTER_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            counter_data,
            file,
            indent=4
        )


# ---------------------------------------------------------
# AUTOMATIC FEEDBACK TRAINING CHECK
# ---------------------------------------------------------

def check_pending_feedback():
    """
    Check whether 200 or more unprocessed feedback submissions
    are available for another training cycle.
    """

    with feedback_check_lock:

        try:

            with feedback_counter_lock:

                counter_data = read_feedback_counter()

                total_feedback = counter_data.get(
                    "total_feedback",
                    0
                )

                last_trigger = counter_data.get(
                    "last_training_trigger",
                    0
                )

                pending_feedback = (
                    total_feedback - last_trigger
                )

                print(
                    f"[PRE-GUARD] Pending feedback: "
                    f"{pending_feedback}/{FEEDBACK_BATCH_SIZE}"
                )

                if pending_feedback < FEEDBACK_BATCH_SIZE:

                    return {
                        "triggered": False,
                        "total_feedback": total_feedback,
                        "pending_feedback": pending_feedback,
                        "message": "Feedback batch threshold not reached.",
                    }

                if is_training_running():

                    return {
                        "triggered": False,
                        "total_feedback": total_feedback,
                        "pending_feedback": pending_feedback,
                        "message": "Training is already running. Feedback will be checked after training.",
                    }

                # Save checkpoint before queueing.
                previous_trigger = last_trigger

                counter_data["last_training_trigger"] = (
                    total_feedback
                )

                save_feedback_counter(counter_data)

                result = start_training()

                if result["started"]:

                    print(
                        "[PRE-GUARD] Feedback threshold reached. "
                        "Training queued."
                    )

                    return {
                        "triggered": True,
                        "total_feedback": total_feedback,
                        "pending_feedback": 0,
                        "message": "Automatic training queued.",
                    }

                # Restore checkpoint if training could not be queued.
                counter_data["last_training_trigger"] = (
                    previous_trigger
                )

                save_feedback_counter(counter_data)

                print(
                    "[PRE-GUARD] Could not queue training: "
                    f"{result['message']}"
                )

                return {
                    "triggered": False,
                    "total_feedback": total_feedback,
                    "pending_feedback": pending_feedback,
                    "message": result["message"],
                }

        except Exception as error:

            print(
                f"[PRE-GUARD] Pending feedback check failed: "
                f"{error}"
            )

            return {
                "triggered": False,
                "message": "Feedback check failed.",
                "error": str(error),
            }


# ---------------------------------------------------------
# REGISTER FEEDBACK SUBMISSION
# ---------------------------------------------------------

def register_feedback_submission():
    """
    Register one feedback submission.

    Every submission is counted, including repeated URLs.
    Training starts when 200 unprocessed submissions accumulate.
    """

    try:

        with feedback_counter_lock:

            counter_data = read_feedback_counter()

            counter_data["total_feedback"] = (
                counter_data.get("total_feedback", 0) + 1
            )

            save_feedback_counter(counter_data)

            total_feedback = counter_data["total_feedback"]

            last_trigger = counter_data.get(
                "last_training_trigger",
                0
            )

            pending_feedback = (
                total_feedback - last_trigger
            )

        print(
            f"[PRE-GUARD] Feedback registered: "
            f"{total_feedback} total | "
            f"{pending_feedback} pending"
        )

        # Check whether this submission reached the threshold.
        check_result = check_pending_feedback()

        return {
            "total_feedback": total_feedback,
            "pending_feedback": check_result.get(
                "pending_feedback",
                pending_feedback
            ),
            "training_triggered": check_result.get(
                "triggered",
                False
            ),
            "training_status": get_training_status(),
            "message": check_result.get(
                "message",
                "Feedback registered."
            ),
        }

    except Exception as error:

        print(
            f"[PRE-GUARD] Feedback registration failed: "
            f"{error}"
        )

        return {
            "total_feedback": None,
            "pending_feedback": None,
            "training_triggered": False,
            "training_status": get_training_status(),
            "message": "Feedback was received, but counter registration failed.",
            "error": str(error),
        }


# ---------------------------------------------------------
# BACKGROUND TRAINING
# ---------------------------------------------------------

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

    # Check whether another 200 submissions accumulated
    # during this training cycle.
    check_pending_feedback()


# ---------------------------------------------------------
# START TRAINING
# ---------------------------------------------------------

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
