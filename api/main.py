
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import csv

from ai.features.url_features import extract_url_features
from ai.api.model_manager import model_manager
from ai.api.training_manager import start_training, get_training_status




# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

FEEDBACK_PATH = Path("ai/data/feedback.csv")


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
def save_feedback(request: FeedbackRequest):

    url = request.url.strip()

    if not url:
        raise HTTPException(
            status_code=400,
            detail="URL cannot be empty"
        )

    if request.label not in (0, 1):
        raise HTTPException(
            status_code=400,
            detail="Label must be 0 or 1"
        )

    try:
        FEEDBACK_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        file_exists = FEEDBACK_PATH.exists()

        with open(
            FEEDBACK_PATH,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            if not file_exists or FEEDBACK_PATH.stat().st_size == 0:
                writer.writerow(["url", "label"])

            writer.writerow([url, request.label])

        return {
            "status": "saved",
            "url": url,
            "label": request.label
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


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