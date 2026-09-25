import joblib
import pandas as pd

from ai.features.url_features import extract_url_features


MODEL_PATH = "ai/models/neural_network_feedback_test.joblib"
SCALER_PATH = "ai/models/neural_network_feedback_test_scaler.joblib"
FEEDBACK_PATH = "ai/data/feedback.csv"


def classify_risk(probability):

    if probability < 0.30:
        return "SAFE"

    if probability < 0.70:
        return "SUSPICIOUS"

    return "HIGH_RISK"


def test_feedback_model():

    print()
    print("=" * 70)
    print("        PRE-GUARD AI — FEEDBACK MODEL TEST")
    print("=" * 70)

    print("\nLoading feedback-trained model...")

    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    feedback_df = pd.read_csv(FEEDBACK_PATH)

    print(f"Feedback samples: {len(feedback_df)}")

    print("\nTesting feedback URLs...")
    print("-" * 70)

    correct = 0

    for _, row in feedback_df.iterrows():

        url = row["url"]
        expected_label = int(row["label"])

        features = extract_url_features(url)

        feature_df = pd.DataFrame([features])

        scaled_features = scaler.transform(feature_df)

        probability = float(
            model.predict_proba(scaled_features)[0][1]
        )

        classification = classify_risk(probability)

        predicted_label = 1 if probability >= 0.50 else 0

        if predicted_label == expected_label:
            result = "✓ CORRECT"
            correct += 1
        else:
            result = "✗ INCORRECT"

        print()
        print(f"URL          : {url}")
        print(f"Expected     : {expected_label}")
        print(f"Prediction   : {classification}")
        print(f"Risk         : {probability * 100:.2f}%")
        print(f"Result       : {result}")

    print()
    print("=" * 70)
    print("                    FEEDBACK RESULTS")
    print("=" * 70)

    print(
        f"Correct: {correct}/{len(feedback_df)}"
    )

    accuracy = correct / len(feedback_df)

    print(
        f"Feedback accuracy: {accuracy * 100:.2f}%"
    )

    print("=" * 70)


if __name__ == "__main__":
    test_feedback_model()