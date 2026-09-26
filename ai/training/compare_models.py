import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from ai.features.url_features import extract_url_features


# ============================================================
# CONFIG
# ============================================================

DATASET_PATH = "ai/data/processed/url_features.csv"
FEEDBACK_PATH = "ai/data/feedback.csv"

CURRENT_MODEL_PATH = (
    "ai/models/neural_network.joblib"
)

CURRENT_SCALER_PATH = (
    "ai/models/neural_network_scaler.joblib"
)

CANDIDATE_MODEL_PATH = (
    "ai/models/neural_network_candidate.joblib"
)

CANDIDATE_SCALER_PATH = (
    "ai/models/neural_network_candidate_scaler.joblib"
)

RANDOM_STATE = 42


# ============================================================
# EVALUATE MODEL
# ============================================================

def evaluate_model(
    model,
    scaler,
    X_test,
    y_test
):

    X_scaled = scaler.transform(X_test)

    predictions = model.predict(
        X_scaled
    )

    probabilities = model.predict_proba(
        X_scaled
    )[:, 1]

    return {
        "accuracy": accuracy_score(
            y_test,
            predictions
        ),

        "precision": precision_score(
            y_test,
            predictions,
            zero_division=0
        ),

        "recall": recall_score(
            y_test,
            predictions,
            zero_division=0
        ),

        "f1": f1_score(
            y_test,
            predictions,
            zero_division=0
        ),

        "roc_auc": roc_auc_score(
            y_test,
            probabilities
        ),
    }


# ============================================================
# TEST FEEDBACK
# ============================================================

def evaluate_feedback(
    model,
    scaler,
    feedback_df
):

    results = []

    for _, row in feedback_df.iterrows():

        url = row["url"]
        expected = int(row["label"])

        features = extract_url_features(
            url
        )

        feature_df = pd.DataFrame(
            [features]
        )

        scaled = scaler.transform(
            feature_df
        )

        probability = float(
            model.predict_proba(
                scaled
            )[0][1]
        )

        predicted = (
            1 if probability >= 0.50
            else 0
        )

        results.append({
            "url": url,
            "expected": expected,
            "predicted": predicted,
            "risk": probability,
            "correct": (
                predicted == expected
            ),
        })

    return results


# ============================================================
# MAIN
# ============================================================

def compare_models():

    print()
    print("=" * 70)
    print("          PRE-GUARD AI — MODEL COMPARISON")
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    df = pd.read_csv(
        DATASET_PATH
    )

    X = df.drop(
        columns=["label"]
    )

    y = df["label"]

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=RANDOM_STATE,
            stratify=y,
        )
    )

    # --------------------------------------------------------
    # LOAD MODELS
    # --------------------------------------------------------

    print("\nLoading production model...")

    current_model = joblib.load(
        CURRENT_MODEL_PATH
    )

    current_scaler = joblib.load(
        CURRENT_SCALER_PATH
    )

    print("Loading candidate model...")

    candidate_model = joblib.load(
        CANDIDATE_MODEL_PATH
    )

    candidate_scaler = joblib.load(
        CANDIDATE_SCALER_PATH
    )

    # --------------------------------------------------------
    # EVALUATE
    # --------------------------------------------------------

    print("\nEvaluating models...")
    print("-" * 70)

    current_metrics = evaluate_model(
        current_model,
        current_scaler,
        X_test,
        y_test
    )

    candidate_metrics = evaluate_model(
        candidate_model,
        candidate_scaler,
        X_test,
        y_test
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("                    MODEL RESULTS")
    print("=" * 70)

    print()
    print(
        f"{'Metric':<15}"
        f"{'Production':>15}"
        f"{'Candidate':>15}"
    )

    print("-" * 45)

    for metric in [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
    ]:

        print(
            f"{metric.upper():<15}"
            f"{current_metrics[metric]:>15.4f}"
            f"{candidate_metrics[metric]:>15.4f}"
        )

    # --------------------------------------------------------
    # FEEDBACK TEST
    # --------------------------------------------------------

    feedback_df = pd.read_csv(
        FEEDBACK_PATH
    )

    print()
    print("=" * 70)
    print("                 FEEDBACK TEST")
    print("=" * 70)

    current_feedback = evaluate_feedback(
        current_model,
        current_scaler,
        feedback_df
    )

    candidate_feedback = evaluate_feedback(
        candidate_model,
        candidate_scaler,
        feedback_df
    )

    print()

    for current, candidate in zip(
        current_feedback,
        candidate_feedback
    ):

        print(
            f"URL: {current['url']}"
        )

        print(
            f"Expected label : "
            f"{current['expected']}"
        )

        print(
            f"Production     : "
            f"{current['risk'] * 100:.2f}%"
        )

        print(
            f"Candidate      : "
            f"{candidate['risk'] * 100:.2f}%"
        )

        print(
            f"Production     : "
            f"{'CORRECT' if current['correct'] else 'INCORRECT'}"
        )

        print(
            f"Candidate      : "
            f"{'CORRECT' if candidate['correct'] else 'INCORRECT'}"
        )

        print("-" * 70)

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    current_feedback_correct = sum(
        result["correct"]
        for result in current_feedback
    )

    candidate_feedback_correct = sum(
        result["correct"]
        for result in candidate_feedback
    )

    print()
    print("=" * 70)
    print("                    SUMMARY")
    print("=" * 70)

    print(
        f"Production feedback accuracy: "
        f"{current_feedback_correct}/"
        f"{len(current_feedback)}"
    )

    print(
        f"Candidate feedback accuracy : "
        f"{candidate_feedback_correct}/"
        f"{len(candidate_feedback)}"
    )

    print()
    print(
        "Candidate evaluation complete."
    )

    print(
        "No model has been replaced."
    )


if __name__ == "__main__":
    compare_models()