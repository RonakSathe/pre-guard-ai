import sys
import joblib
import pandas as pd

from ai.features.url_features import extract_url_features

MODEL_PATH = "ai/models/neural_network.joblib"
SCALER_PATH = "ai/models/neural_network_scaler.joblib"

def classify_risk(probability:float) -> str:
    return "SAFE" if probability < 0.30 else ("SUSPICIOUS" if probability < 0.70 else "HIGH RISK")

def predict_url(url: str):

    #LOAD MODEL and SCALER
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    #Extract fetures
    features = extract_url_features(url)
    features_df = pd.DataFrame([features])

    #Scale features
    scaled_features = scaler.transform(features_df)

    #Prediction
    probability = model.predict_proba(scaled_features)[0][1]

    classification = classify_risk(probability)

    return (probability,classification,features)

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m ai.predict 'URL'")
        return
    url = sys.argv[1]

    probability, classification,features = (predict_url(url))

    #Display result
    print()
    print("=" * 60)
    print("                 PRE-GUARD AI")
    print("=" * 60)

    print()
    print(f"URL: {url}")

    print()
    print(
        f"Risk Score : {probability * 100:.2f}%"
    )

    print(
        f"Classification: {classification}"
    )

    print()
    print("URL ANALYSIS")
    print("-" * 60)

    for name, value in features.items():

        print(
            f"{name:30} {value}"
        )

    print()
    print("=" * 60)

if __name__ == "__main__":
    main()