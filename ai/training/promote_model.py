from pathlib import Path
from datetime import datetime
import json
import shutil

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

ARCHIVE_DIR = Path("ai/models/archive")

METADATA_PATH = Path(
    "ai/models/model_metadata.json"
)

RANDOM_STATE = 42

MAX_REGRESSION = 0.005


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(y_true, probabilities):

    predictions = (
        probabilities >= 0.5
    ).astype(int)

    return {
        "accuracy": accuracy_score(
            y_true,
            predictions
        ),
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


def print_metrics(name, metrics):

    print(f"\n{name}")
    print("-" * 45)

    for key, value in metrics.items():

        print(
            f"{key.upper():<12}: {value:.4f}"
        )


# ============================================================
# FEEDBACK FEATURES
# ============================================================

def prepare_feedback(
    feedback_df,
    feature_columns
):

    rows = []

    for url, label in zip(
        feedback_df["url"],
        feedback_df["label"]
    ):

        features = extract_url_features(url)

        features["label"] = int(label)

        rows.append(features)

    result = pd.DataFrame(rows)

    return result[
        feature_columns + ["label"]
    ]


# ============================================================
# VERSION
# ============================================================

def get_next_version(current_version):

    if not current_version:
        return "v1.0"

    try:

        version_number = float(
            current_version.lstrip("v")
        )

        next_version = version_number + 0.1

        return f"v{next_version:.1f}"

    except ValueError:

        return "v1.0"


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PRE-GUARD AI - MODEL PROMOTION CHECK")
    print("=" * 60)


    # --------------------------------------------------------
    # 1. CHECK FILES
    # --------------------------------------------------------

    print("\n[1/8] Checking files...")

    required_files = [
        DATASET_PATH,
        FEEDBACK_PATH,
        MODEL_PATH,
        SCALER_PATH,
        CANDIDATE_MODEL_PATH,
        CANDIDATE_SCALER_PATH,
        METADATA_PATH,
    ]

    for path in required_files:

        if not path.exists():

            raise FileNotFoundError(
                f"Required file not found: {path}"
            )

    print("All required files found.")


    # --------------------------------------------------------
    # 2. LOAD DATA
    # --------------------------------------------------------

    print("\n[2/8] Loading data...")

    df = pd.read_csv(
        DATASET_PATH
    )

    feature_columns = [
        column
        for column in df.columns
        if column != "label"
    ]

    feedback_df = pd.read_csv(
        FEEDBACK_PATH
    )

    feedback_df = feedback_df[
        ["url", "label"]
    ].copy()

    feedback_df["url"] = (
        feedback_df["url"]
        .astype(str)
        .str.strip()
    )

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

    feedback_df = feedback_df.drop_duplicates(
        subset=["url"],
        keep="last"
    )

    feedback_df["label"] = (
        feedback_df["label"].astype(int)
    )

    print(
        f"Original dataset : {len(df):,}"
    )

    print(
        f"Feedback samples  : {len(feedback_df)}"
    )


    # --------------------------------------------------------
    # 3. CREATE ORIGINAL TEST SPLIT
    # --------------------------------------------------------

    print(
        "\n[3/8] Creating evaluation split..."
    )

    X = df[feature_columns]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y
    )

    print(
        f"Training samples : {len(X_train):,}"
    )

    print(
        f"Test samples     : {len(X_test):,}"
    )


    # --------------------------------------------------------
    # 4. LOAD MODELS
    # --------------------------------------------------------

    print(
        "\n[4/8] Loading production and candidate..."
    )

    production_model = joblib.load(
        MODEL_PATH
    )

    production_scaler = joblib.load(
        SCALER_PATH
    )

    candidate_model = joblib.load(
        CANDIDATE_MODEL_PATH
    )

    candidate_scaler = joblib.load(
        CANDIDATE_SCALER_PATH
    )


    # --------------------------------------------------------
    # 5. ORIGINAL TEST EVALUATION
    # --------------------------------------------------------

    print(
        "\n[5/8] Evaluating original test set..."
    )

    production_scaled = (
        production_scaler.transform(
            X_test
        )
    )

    candidate_scaled = (
        candidate_scaler.transform(
            X_test
        )
    )

    production_probabilities = (
        production_model.predict_proba(
            production_scaled
        )[:, 1]
    )

    candidate_probabilities = (
        candidate_model.predict_proba(
            candidate_scaled
        )[:, 1]
    )

    production_metrics = calculate_metrics(
        y_test,
        production_probabilities
    )

    candidate_metrics = calculate_metrics(
        y_test,
        candidate_probabilities
    )

    print_metrics(
        "PRODUCTION",
        production_metrics
    )

    print_metrics(
        "CANDIDATE",
        candidate_metrics
    )


    # --------------------------------------------------------
    # 6. FEEDBACK HOLDOUT
    # --------------------------------------------------------

    print(
        "\n[6/8] Evaluating feedback holdout..."
    )

    feedback_features = prepare_feedback(
        feedback_df,
        feature_columns
    )

    X_feedback = feedback_features[
        feature_columns
    ]

    y_feedback = feedback_features[
        "label"
    ]

    production_feedback_scaled = (
        production_scaler.transform(
            X_feedback
        )
    )

    candidate_feedback_scaled = (
        candidate_scaler.transform(
            X_feedback
        )
    )

    production_feedback_probabilities = (
        production_model.predict_proba(
            production_feedback_scaled
        )[:, 1]
    )

    candidate_feedback_probabilities = (
        candidate_model.predict_proba(
            candidate_feedback_scaled
        )[:, 1]
    )

    production_feedback_predictions = (
        production_feedback_probabilities >= 0.5
    ).astype(int)

    candidate_feedback_predictions = (
        candidate_feedback_probabilities >= 0.5
    ).astype(int)

    production_feedback_accuracy = (
        accuracy_score(
            y_feedback,
            production_feedback_predictions
        )
    )

    candidate_feedback_accuracy = (
        accuracy_score(
            y_feedback,
            candidate_feedback_predictions
        )
    )

    print("\nFEEDBACK HOLDOUT")
    print("-" * 45)

    print(
        f"Production : "
        f"{production_feedback_accuracy:.4f}"
    )

    print(
        f"Candidate  : "
        f"{candidate_feedback_accuracy:.4f}"
    )

    for index, row in feedback_df.reset_index(
        drop=True
    ).iterrows():

        print(
            f"\n{row['url']}"
        )

        print(
            f"  Expected   : {int(row['label'])}"
        )

        print(
            f"  Production : "
            f"{int(production_feedback_predictions[index])} "
            f"({production_feedback_probabilities[index] * 100:.2f}%)"
        )

        print(
            f"  Candidate  : "
            f"{int(candidate_feedback_predictions[index])} "
            f"({candidate_feedback_probabilities[index] * 100:.2f}%)"
        )


    # --------------------------------------------------------
    # 7. PROMOTION RULES
    # --------------------------------------------------------

    print(
        "\n[7/8] Checking promotion rules..."
    )

    feedback_improved = (
        candidate_feedback_accuracy
        > production_feedback_accuracy
    )

    accuracy_not_worse = (
        candidate_metrics["accuracy"]
        >= production_metrics["accuracy"]
        - MAX_REGRESSION
    )

    recall_not_worse = (
        candidate_metrics["recall"]
        >= production_metrics["recall"]
        - MAX_REGRESSION
    )

    f1_not_worse = (
        candidate_metrics["f1"]
        >= production_metrics["f1"]
        - MAX_REGRESSION
    )

    roc_auc_not_worse = (
        candidate_metrics["roc_auc"]
        >= production_metrics["roc_auc"]
        - MAX_REGRESSION
    )

    print(
        f"\nFeedback improved : "
        f"{'YES' if feedback_improved else 'NO'}"
    )

    print(
        f"Accuracy allowed  : "
        f"{'YES' if accuracy_not_worse else 'NO'}"
    )

    print(
        f"Recall allowed    : "
        f"{'YES' if recall_not_worse else 'NO'}"
    )

    print(
        f"F1 allowed        : "
        f"{'YES' if f1_not_worse else 'NO'}"
    )

    print(
        f"ROC-AUC allowed   : "
        f"{'YES' if roc_auc_not_worse else 'NO'}"
    )

    should_promote = (
        feedback_improved
        and accuracy_not_worse
        and recall_not_worse
        and f1_not_worse
        and roc_auc_not_worse
    )


    # --------------------------------------------------------
    # REJECT
    # --------------------------------------------------------

    if not should_promote:

        print("\n" + "=" * 60)
        print("PROMOTION REJECTED")
        print("=" * 60)

        print(
            "\nProduction model remains unchanged."
        )

        print(
            "Candidate remains available "
            "for further analysis."
        )

        return


    # --------------------------------------------------------
    # PROMOTE
    # --------------------------------------------------------

    print(
        "\n[8/8] PROMOTING CANDIDATE..."
    )

    with open(
        METADATA_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        current_metadata = json.load(
            file
        )

    current_version = current_metadata.get(
        "version",
        "v1.0"
    )

    new_version = get_next_version(
        current_version
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    ARCHIVE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    archived_model = (
        ARCHIVE_DIR
        / f"neural_network_{current_version}_{timestamp}.joblib"
    )

    archived_scaler = (
        ARCHIVE_DIR
        / f"neural_network_scaler_{current_version}_{timestamp}.joblib"
    )

    print(
        f"\nCurrent version : {current_version}"
    )

    print(
        f"New version     : {new_version}"
    )

    print(
        "\nBacking up current production..."
    )

    shutil.copy2(
        MODEL_PATH,
        archived_model
    )

    shutil.copy2(
        SCALER_PATH,
        archived_scaler
    )

    print(
        f"Backup model  : {archived_model}"
    )

    print(
        f"Backup scaler : {archived_scaler}"
    )

    print(
        "\nInstalling candidate..."
    )

    shutil.copy2(
        CANDIDATE_MODEL_PATH,
        MODEL_PATH
    )

    shutil.copy2(
        CANDIDATE_SCALER_PATH,
        SCALER_PATH
    )

    # --------------------------------------------------------
    # SAVE NEW METADATA
    # --------------------------------------------------------

    new_metadata = {
        "project": "PRE_GUARD AI",

        "model_type": "MLPClassifier",

        "architecture": [
            64,
            32,
            16
        ],

        "version": new_version,

        "previous_version": current_version,

        "created_at": datetime.now().isoformat(),

        "model_file": str(
            MODEL_PATH
        ),

        "scaler_file": str(
            SCALER_PATH
        ),

        "metrics": {
            "accuracy": candidate_metrics[
                "accuracy"
            ],
            "precision": candidate_metrics[
                "precision"
            ],
            "recall": candidate_metrics[
                "recall"
            ],
            "f1": candidate_metrics[
                "f1"
            ],
            "roc_auc": candidate_metrics[
                "roc_auc"
            ],
            "feedback_accuracy":
                candidate_feedback_accuracy,
        },

        "promotion": {
            "promoted_at":
                datetime.now().isoformat(),

            "feedback_improved":
                feedback_improved,

            "max_allowed_regression":
                MAX_REGRESSION,
        },

        "status": "production",
    }

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            new_metadata,
            file,
            indent=4
        )

    print(
        "\nMetadata updated."
    )

    print(
        f"Version: {new_version}"
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "MODEL PROMOTION COMPLETE"
    )

    print(
        "=" * 60
    )


if __name__ == "__main__":
    main()