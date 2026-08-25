from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import csv
from pathlib import Path
from ai.features.url_features import extract_url_features

#COnfig
MODEL_PATH = "ai/models/neural_network.joblib"
SCALER_PATH = "ai/models/neural_network_scaler.joblib"
FEEDBACK_PATH = Path("ai/data/feedback.csv")

#Load mdoel once
model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

#Fastapi Application

app = FastAPI(
    title="PRE_GUARD AI",
    description= "AI- Powered URLrisk analysis for pre-navigation protection",
    version="0.5.0"
)

#Request model
class URLRequest(BaseModel):
    url:str

#FeedbackRequest
class FeedbackRequest(BaseModel):
    url: str
    label: int

#Risk classification
def classify_risk(probability:float) -> str:
    return "SAFE" if probability < 0.30 else ("SUSPICIOUS" if probability < 0.70 else "HIGH_RISK")

@app.get("/")
def root():

    return {
        "project": "PRE_GUARD AI",
        "status": "online",
        "version": "0.5.0",
    } 


#Prediction endpoint
@app.post("/predict")
def predict_url(request: URLRequest):
    url = request.url.strip()

    if not url:
        raise HTTPException(400,"URL Cannot be empty")
    try:
        #Extrct features
        features = extract_url_features(url)
        feature_df = pd.DataFrame([features])

        #Scale
        scaled_features = scaler.transform(feature_df)

        #Prediction
        probability = float(model.predict_proba(scaled_features)[0][1])

        classification = classify_risk(probability)

        #Response
        return {
            "url": url,
            "risk_score": round(probability,6),
            "risk_percentage": round(probability*100,2),
            "classification": classification,
            "features": features,
        }
    except Exception as error:
        raise HTTPException(500,str(error))

 #Feedback   
@app.post("/feedback")
def save_feedback(request:FeedbackRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(400,"URL cannot be empty")
    if request.label not in (0,1):
        raise HTTPException(400,"Label must be 0 or 1")

    FEEDBACK_PATH.parent.mkdir(parents=True,exist_ok=True)
    file_exists = FEEDBACK_PATH.exists()

    with open(FEEDBACK_PATH,"a",newline="",encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["url","label"])
        writer.writerow(
            [url,request.label]
        )

    return {
        "status": "saved"
    }

