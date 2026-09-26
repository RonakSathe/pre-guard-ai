from pathlib import Path

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
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

from ai.features.url_features import extract_url_features


# ============================================================
# PATHS
# ============================================================

DATASET_PATH = Path("ai/data/processed/url_features.csv")
FEEDBACK_PATH = Path("ai/data/feedback.csv")

MODEL_PATH = Path("ai/models/neural_network.joblib")
SCALER_PATH = Path("ai/models/neural_network_scaler.joblib")

CANDIDATE_MODEL_PATH = Path(
    "ai/models/neural_network_candidate.joblib"
)
CANDIDATE_SCALER_PATH = Path(
    "ai/models/neural_network_candidate_scaler.joblib"
)

RANDOM_STATE = 42
MIN_FEEDBACK_SAMPLES = 5


# ============================================================
# HELPERS
# ============================================================

def print_metrics(name, metrics):
    print(f"\n{name}")
    print("-" * 45)

    for key, value in metrics.items():
        print(f"{key.upper():<12}: {value:.4f}")


def calculate_metrics(y_true, probabilities):
    predictions = (probabilities >= 0.5).astype(int)

    return {
        "accuracy": accuracy_score(y_true, predictions),
        "precision": precision_score(
            y_true,
            predictions,
            zero_division=0
        ),
        "recall": recall_score(
            y_true,
            predictions,
            zero_division=0
        ),
        "f1": f1_score(
            y_true,
            predictions,
            zero_division=0
        ),
        "roc_auc": roc_auc_score(
            y_true,
            probabilities
        ),
    }


def prepare_feedback_features(feedback_df, feature_columns):
    print("\nExtracting feedback URL features...")

    rows = []

    for url, label in zip(
        feedback_df["url"],
        feedback_df["label"]
    ):
        features = extract_url_features(url)
        features["label"] = int(label)
        rows.append(features)

    result = pd.DataFrame(rows)

    missing = [
        column
        for column in feature_columns
        if column not in result.columns
    ]

    if missing:
        raise ValueError(
            f"Feedback feature mismatch. Missing: {missing}"
        )

    return result[feature_columns + ["label"]]


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PRE-GUARD AI - MODEL RENEWAL")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. LOAD ORIGINAL DATASET
    # --------------------------------------------------------

    print("\n[1/8] Loading original dataset...")

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    df = pd.read_csv(DATASET_PATH)

    if "label" not in df.columns:
        raise ValueError(
            "Dataset must contain a 'label' column."
        )

    feature_columns = [
        column
        for column in df.columns
        if column != "label"
    ]

    print(f"Original samples : {len(df):,}")
    print(f"Features         : {len(feature_columns)}")


    # --------------------------------------------------------
    # 2. LOAD FEEDBACK
    # --------------------------------------------------------

    print("\n[2/8] Loading feedback...")

    if not FEEDBACK_PATH.exists():
        print("No feedback file found.")
        print("Nothing to renew.")
        return

    feedback_df = pd.read_csv(FEEDBACK_PATH)

    required_columns = {"url", "label"}

    if not required_columns.issubset(feedback_df.columns):
        raise ValueError(
            "feedback.csv must contain exactly the columns: "
            "url,label"
        )

    feedback_df = feedback_df[["url", "label"]].copy()

    feedback_df["url"] = feedback_df["url"].astype(str).str.strip()

    feedback_df["label"] = pd.to_numeric(
        feedback_df["label"],
        errors="coerce"
    )

    feedback_df = feedback_df.dropna(
        subset=["url", "label"]
    )

    feedback_df = feedback_df[
        feedback_df["label"].isin([0, 1])
    ]

    # Latest feedback wins for duplicate URLs
    feedback_df = feedback_df.drop_duplicates(
        subset=["url"],
        keep="last"
    )

    feedback_df["label"] = feedback_df["label"].astype(int)

    feedback_count = len(feedback_df)

    print(f"Valid feedback samples : {feedback_count}")

    if feedback_count < MIN_FEEDBACK_SAMPLES:
        print(
            f"\nNeed at least {MIN_FEEDBACK_SAMPLES} "
            f"feedback samples."
        )
        print(
            f"Currently available: {feedback_count}"
        )
        return


    # --------------------------------------------------------
    # 3. PREPARE FEEDBACK FEATURES
    # --------------------------------------------------------

    print("\n[3/8] Preparing feedback features...")

    feedback_features = prepare_feedback_features(
        feedback_df,
        feature_columns
    )

    print(
        f"Feedback features prepared: "
        f"{len(feedback_features)}"
    )


    # --------------------------------------------------------
    # 4. HOLD OUT FEEDBACK
    # --------------------------------------------------------

    print("\n[4/8] Creating feedback holdout...")

    feedback_holdout = feedback_features.copy()

    print(
        f"Feedback holdout samples: "
        f"{len(feedback_holdout)}"
    )

    print(
        "\nIMPORTANT:"
        "\nFeedback holdout will NOT be included in training."
        "\nIt will only be used to test whether the candidate"
        "\nmodel learned the user corrections."
    )


    # --------------------------------------------------------
    # 5. TRAINING DATA
    # --------------------------------------------------------

    print("\n[5/8] Building candidate training dataset...")

    X_original = df[feature_columns]
    y_original = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X_original,
        y_original,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y_original
    )

    # Feedback is intentionally added ONLY to training data.
    feedback_train = feedback_features.copy()

    X_feedback = feedback_train[feature_columns]
    y_feedback = feedback_train["label"]

    X_train = pd.concat(
        [
            X_train,
            X_feedback
        ],
        ignore_index=True
    )

    y_train = pd.concat(
        [
            y_train,
            y_feedback
        ],
        ignore_index=True
    )

    print(f"Original training samples : {len(y_train) - len(y_feedback):,}")
    print(f"Feedback training samples : {len(y_feedback):,}")
    print(f"Final candidate training   : {len(y_train):,}")
    print(f"Original test samples      : {len(y_test):,}")


    # --------------------------------------------------------
    # 6. SCALE + TRAIN CANDIDATE
    # --------------------------------------------------------

    print("\n[6/8] Training candidate MLP...")

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    X_feedback_scaled = scaler.transform(
        feedback_holdout[feature_columns]
    )

    model = MLPClassifier(
        hidden_layer_sizes=(64, 32, 16),
        activation="relu",
        solver="adam",
        learning_rate_init=0.001,
        batch_size=64,
        max_iter=300,
        early_stopping=True,
        validation_fraction=0.20,
        n_iter_no_change=10,
        random_state=RANDOM_STATE,
        verbose=True
    )

    model.fit(
        X_train_scaled,
        y_train
    )

    print(
        f"\nTraining iterations: "
        f"{model.n_iter_}"
    )

    print(
        f"Final loss: "
        f"{model.loss_:.6f}"
    )


    # --------------------------------------------------------
    # 7. EVALUATE
    # --------------------------------------------------------

    print("\n[7/8] Evaluating candidate...")

    # Original test set
    test_probabilities = model.predict_proba(
        X_test_scaled
    )[:, 1]

    test_metrics = calculate_metrics(
        y_test,
        test_probabilities
    )

    print_metrics(
        "ORIGINAL DATASET TEST",
        test_metrics
    )


    # Feedback holdout
    feedback_probabilities = model.predict_proba(
        X_feedback_scaled
    )[:, 1]

    feedback_predictions = (
        feedback_probabilities >= 0.5
    ).astype(int)

    feedback_accuracy = accuracy_score(
        feedback_holdout["label"],
        feedback_predictions
    )

    print("\nFEEDBACK HOLDOUT")
    print("-" * 45)
    print(
        f"Accuracy     : "
        f"{feedback_accuracy:.4f}"
    )
    print(
        f"Correct      : "
        f"{sum(feedback_predictions == feedback_holdout['label'])}"
        f"/{len(feedback_holdout)}"
    )

    print("\nFeedback predictions:")

    for index, row in feedback_holdout.reset_index(
        drop=True
    ).iterrows():

        probability = feedback_probabilities[index]
        prediction = feedback_predictions[index]

        classification = (
            "SAFE"
            if probability < 0.30
            else "SUSPICIOUS"
            if probability < 0.70
            else "HIGH_RISK"
        )

        expected = int(row["label"])

        result = (
            "CORRECT"
            if prediction == expected
            else "INCORRECT"
        )

        print(
            f"{feedback_df.iloc[index]['url']}"
        )
        print(
            f"  Expected    : {expected}"
        )
        print(
            f"  Prediction  : {prediction}"
        )
        print(
            f"  Risk        : {probability * 100:.2f}%"
        )
        print(
            f"  Classification: {classification}"
        )
        print(
            f"  Result      : {result}"
        )


    # --------------------------------------------------------
    # 8. SAVE CANDIDATE
    # --------------------------------------------------------

    print("\n[8/8] Saving candidate model...")

    CANDIDATE_MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(
        model,
        CANDIDATE_MODEL_PATH
    )

    joblib.dump(
        scaler,
        CANDIDATE_SCALER_PATH
    )

    print(
        f"\nCandidate model saved:"
        f"\n  {CANDIDATE_MODEL_PATH}"
        f"\n  {CANDIDATE_SCALER_PATH}"
    )

    print("\n" + "=" * 60)
    print("MODEL RENEWAL COMPLETE")
    print("=" * 60)

    print("\nProduction model was NOT changed.")
    print("Candidate requires promotion before deployment.")


if __name__ == "__main__":
    main()