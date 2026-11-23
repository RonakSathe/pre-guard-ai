
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import csv
from datetime import datetime,timezone
from ai.features.url_features import extract_url_features
from ai.api.model_manager import model_manager
from ai.api.training_manager import start_training, get_training_status, register_feedback_submission
from threading import Lock


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

FEEDBACK_PATH = Path("ai/data/feedback.csv")
DETECTION_HISTORY_PATH = Path("ai/data/detection_history.csv")
feedback_lock = Lock()


# ---------------------------------------------------------
# FASTAPI APPLICATION
# ---------------------------------------------------------

app = FastAPI(
    title="PRE_GUARD AI",
    description="AI-Powered URL risk analysis for pre-navigation protection",
    version="0.6.0"
)


# ---------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------

class URLRequest(BaseModel):
    url: str


class FeedbackRequest(BaseModel):
    url: str
    label: int


# ---------------------------------------------------------
# RISK CLASSIFICATION
# ---------------------------------------------------------

def classify_risk(probability: float) -> str:

    if probability < 0.30:
        return "SAFE"

    elif probability < 0.70:
        return "SUSPICIOUS"

    return "HIGH_RISK"


# Detection History Logger
detection_lock = Lock()
def record_detection(probability: float, classification:str):
    try:
        DETECTION_HISTORY_PATH.parent.mkdir(
            parents=True,exist_ok=True
        )
        with detection_lock:
            file_exists = (DETECTION_HISTORY_PATH.exists() and  DETECTION_HISTORY_PATH.stat().st_size > 0)

            with open(DETECTION_HISTORY_PATH,"a",newline="",encoding="utf-8") as file:
                writer = csv.writer(file)

                if not file_exists:
                    writer.writerow([
                        "timestamp","risk_score","classification"
                    ])
                writer.writerow([
                    datetime.now(timezone.utc).isoformat(),
                    round(probability,6),
                    classification
                ])
    except Exception as error:
        print(f"[PRE-GUARD] Detection loggin failed: {error}")


# ---------------------------------------------------------
# ROOT ENDPOINT
# ---------------------------------------------------------

@app.get("/")
def root():

    return {
        "project": "PRE_GUARD AI",
        "status": "online",
        "version": "0.6.0"
    }


# ---------------------------------------------------------
# PREDICTION ENDPOINT
# ---------------------------------------------------------

@app.post("/predict")
def predict_url(request: URLRequest):

    url = request.url.strip()

    if not url:
        raise HTTPException(
            status_code=400,
            detail="URL cannot be empty"
        )

    try:
        # Extract URL features
        features = extract_url_features(url)

        # Convert features into DataFrame
        import pandas as pd
        feature_df = pd.DataFrame([features])

        # Predict using the active model manager
        probabilities = model_manager.predict(feature_df)

        probability = float(probabilities[0][1])

        classification = classify_risk(probability)

        # Recoding predictions for dashboard statisitics
        record_detection(probability,classification)

        return {
            "url": url,
            "risk_score": round(probability, 6),
            "risk_percentage": round(probability * 100, 2),
            "classification": classification,
            "features": features
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ---------------------------------------------------------
# FEEDBACK ENDPOINT
# ---------------------------------------------------------

@app.post("/feedback")
def submit_feedback(feedback: FeedbackRequest):

    if not feedback.url.strip():
        raise HTTPException(
            status_code=400,
            detail="URL cannot be empty."
        )

    if feedback.label not in (0, 1):
        raise HTTPException(
            status_code=400,
            detail="Label must be 0 (safe) or 1 (malicious)."
        )

    FEEDBACK_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------
    # SAVE FEEDBACK TO CSV
    # -----------------------------------------------------

    with feedback_lock:

        file_exists = FEEDBACK_PATH.exists()

        with open(
            FEEDBACK_PATH,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            if not file_exists:
                writer.writerow(["url", "label"])

            writer.writerow([
                feedback.url.strip(),
                feedback.label
            ])

    # -----------------------------------------------------
    # REGISTER FEEDBACK & AUTOMATIC TRAINING
    # -----------------------------------------------------

    training_info = register_feedback_submission()

    return {
        "status": "saved",
        "total_feedback": training_info["total_feedback"],
        "pending_feedback": training_info["pending_feedback"],
        "training_triggered": training_info["training_triggered"],
        "training_status": training_info["training_status"],
        "message": training_info["message"],
    }


# ---------------------------------------------------------
# MODEL STATUS ENDPOINT
# ---------------------------------------------------------

@app.get("/model/status")
def model_status():

    return model_manager.get_status()


# ---------------------------------------------------------
# MODEL RELOAD ENDPOINT
# ---------------------------------------------------------

@app.post("/model/reload")
def reload_model():

    try:
        model_manager.load_model()

        return {
            "status": "success",
            "message": "Model and scaler reloaded successfully",
            "model": model_manager.get_status()
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Model reload failed: {str(error)}"
        )

# Backgroudn Training Endpoint
# ---------------------------------------------------------

@app.post("/train")
def start_model_training():

    result = start_training()
    if not result["started"]:
        raise HTTPException(
            status_code=409, # Conflict
            detail=result
        )

    return result


# Training Status Endpoint

@app.get("/training/status")
def training_progress():

    return get_training_status()



# ---------------------------------------------------------
# ANALYTICS ENDPOINT
# ---------------------------------------------------------

@app.get("/analytics")
def get_analytics():

    safe_count = 0
    suspicious_count = 0
    high_risk_count = 0
    hourly_counts = {}

    try:

        if not DETECTION_HISTORY_PATH.exists():
            return {
                "total_scans": 0,
                "safe": 0,
                "suspicious": 0,
                "high_risk": 0,
                "threats": 0,
                "threat_rate": 0.0,
                "classification_percentages": {
                    "safe": 0.0,
                    "suspicious": 0.0,
                    "high_risk": 0.0
                },
                "hourly_activity": []
            }

        with detection_lock:

            with open(
                DETECTION_HISTORY_PATH,
                "r",
                newline="",
                encoding="utf-8"
            ) as file:

                reader = csv.DictReader(file)

                for row in reader:

                    classification = row.get("classification", "")

                    if classification == "SAFE":
                        safe_count += 1

                    elif classification == "SUSPICIOUS":
                        suspicious_count += 1

                    elif classification == "HIGH_RISK":
                        high_risk_count += 1

                    # -----------------------------------------
                    # HOURLY ACTIVITY
                    # -----------------------------------------

                    timestamp_value = row.get("timestamp", "")

                    try:
                        timestamp = datetime.fromisoformat(
                            timestamp_value
                        )

                        hour_key = timestamp.strftime(
                            "%Y-%m-%d %H:00"
                        )

                        hourly_counts[hour_key] = (
                            hourly_counts.get(hour_key, 0) + 1
                        )

                    except (ValueError, TypeError):
                        continue

        total_scans = (
            safe_count
            + suspicious_count
            + high_risk_count
        )

        threats = suspicious_count + high_risk_count

        if total_scans > 0:

            safe_percentage = round(
                (safe_count / total_scans) * 100, 2
            )

            suspicious_percentage = round(
                (suspicious_count / total_scans) * 100, 2
            )

            high_risk_percentage = round(
                (high_risk_count / total_scans) * 100, 2
            )

            threat_rate = round(
                (threats / total_scans) * 100, 2
            )

        else:

            safe_percentage = 0.0
            suspicious_percentage = 0.0
            high_risk_percentage = 0.0
            threat_rate = 0.0

        hourly_activity = [
            {
                "hour": hour,
                "scans": count
            }
            for hour, count in sorted(hourly_counts.items())
        ]

        return {
            "total_scans": total_scans,
            "safe": safe_count,
            "suspicious": suspicious_count,
            "high_risk": high_risk_count,
            "threats": threats,
            "threat_rate": threat_rate,
            "classification_percentages": {
                "safe": safe_percentage,
                "suspicious": suspicious_percentage,
                "high_risk": high_risk_percentage
            },
            "hourly_activity": hourly_activity
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Analytics calculation failed: {str(error)}"
        )


@app.get("/analytics/recent")
def get_recent_detections():
    recent_detections = []

    try:
        if not DETECTION_HISTORY_PATH.exists():
            return {"recent_detections": []}
        with detection_lock:
            with open(DETECTION_HISTORY_PATH,"r",newline="",encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    recent_detections.append(row)

        recent_detections = recent_detections[-10:]
        recent_detections.reverse()
        return {
            "recent_detections": recent_detections
        }

    except Exception as error:
        raise HTTPException(status_code=500,detail=f"Recent detections retrieval failed: {str(error)}")
