import os, time, joblib, pandas as pd, shutil
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, accuracy_score,precision_score, recall_score, f1_score,recall_score, f1_score, confusion_matrix,f1_score,roc_auc_score
from ai.features.url_features import extract_url_features


# CONFIGURATION
# ============================================================

DATASET_PATH = Path("ai/data/processed/url_features.csv")
FEEDBACK_PATH = Path("ai/data/feedback.csv")

MODEL_PATH = Path("ai/models/neural_network.joblib")
SCALER_PATH = Path("ai/models/neural_network_scaler.joblib")

RANDOM_STATE = 42

# Minimum quality required before automatic deployment
MINIMUM_ACCURACY = 0.90
MINIMUM_RECALL = 0.90

# Model Rejection Exception
class ModelRejectedError(Exception):
    pass


# FEEDBACK VALIDATION AND FEATURE EXTTRATION
def load_feedback():
    if not FEEDBACK_PATH.exists():
        print("\n NO FEEDBACK CSV found")
        return pd.DataFrame(columns=["url", "label"])

    feedback: pd.DataFrame = pd.read_csv(FEEDBACK_PATH)
    if not {"url", "label"}.issubset(feedback.columns):
        raise ValueError("Feedback CSV must contain 'url' and 'label' columns.")

    feedback = feedback[["url", "label"]].dropna()
    feedback["url"] = feedback["url"].astype(str).str.strip()
    feedback["label"] = pd.to_numeric(feedback["label"], errors='coerce')

    feedback = feedback.dropna(subset=["label"])
    feedback = feedback[feedback["label"].isin([0,1])]
    feedback = feedback[feedback["url"] != ""]

    # Latest feedback for a URL takes precedence
    feedback = feedback.drop_duplicates(subset=["url"], keep="last")
    feedback["label"] = feedback["label"].astype(int)
    print(f"Validated Feedback records: {len(feedback)}")
    return feedback


def prepare_feedback_features(feedback):
    rows = []

    print("\nExtracting feedback URL features...")

    for _, row in feedback.iterrows():
        try:
            features = extract_url_features(row["url"])
            features["url"] = row["url"]
            features["label"] = int(row["label"])
            rows.append(features)

        except Exception as error:
            print(f"Skipped URL: {row['url']} | {error}")

    return pd.DataFrame(rows)

# ============================================================
# TRAINING
# ============================================================

def train_model():

    started_at = time.time()

    print("\n" + "=" * 65)
    print("             PRE-GUARD AI — MLP")
    print("=" * 65)

    # --------------------------------------------------------
    # 1. LOAD ORIGINAL DATASET
    # --------------------------------------------------------

    print("\n[1/7] Loading original dataset...")

    original_df = pd.read_csv(DATASET_PATH)

    if "label" not in original_df.columns:
        raise ValueError("Original dataset has no label column.")

    feature_columns = [
        column for column in original_df.columns
        if column not in {"label", "url"}
    ]

    original_urls = original_df["url"].astype(str).str.strip()


    X_original = original_df[feature_columns]
    y_original = original_df["label"].astype(int)

    if not set(y_original.unique()).issubset({0, 1}):
        raise ValueError("Original dataset labels must be 0 or 1.")

    print(f"Original samples: {len(original_df):,}")
    print(f"Features: {len(feature_columns)}")

    # --------------------------------------------------------
    # 2. SPLIT ORIGINAL DATA BEFORE FEEDBACK
    # --------------------------------------------------------

    print("\n[2/7] Splitting original dataset...")

    X_train, X_test, y_train, y_test = train_test_split(
        X_original,
        y_original,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y_original,
    )

    print(f"Original training samples: {len(X_train):,}")
    print(f"Original test samples: {len(X_test):,}")

        # --------------------------------------------------------
    # 3. LOAD AND INTEGRATE FEEDBACK INTO TRAINING ONLY
    # --------------------------------------------------------

    print("\n[3/7] Integrating feedback...")

    feedback = load_feedback()
    feedback_features = prepare_feedback_features(feedback)

    feedback_count = len(feedback_features)

    if not feedback_features.empty:

        # Keep URL only for matching, never as a model feature
        feedback_features["url"] = (
            feedback_features["url"].astype(str).str.strip()
        )

        # Identify URLs in the original train/test splits
        train_url_keys = set(
            original_urls.loc[X_train.index].str.strip()
        )

        test_url_keys = set(
            original_urls.loc[X_test.index].str.strip()
        )

        # Map original training URLs to their row indexes
        train_url_to_index = {}

        for index, url in original_urls.items():
            url_key = str(url).strip()

            if index in X_train.index:
                train_url_to_index[url_key] = index

        # Reconcile feedback against the original dataset
        overridden_train_indexes = set()
        feedback_train_rows = []
        feedback_train_labels = []

        added_new_urls = 0
        overridden_labels = 0
        excluded_test_urls = 0

        # Latest feedback for a normalized URL wins
        feedback_latest = {}

        for _, row in feedback_features.iterrows():
            url_key = str(row["url"]).strip()

            feedback_latest[url_key] = row

        for url_key, row in feedback_latest.items():

            # Never train on feedback URLs that belong to the test set
            if url_key in test_url_keys:
                excluded_test_urls += 1
                continue

            # Feedback overrides an existing training sample
            if url_key in train_url_keys:

                original_index = train_url_to_index[url_key]

                overridden_train_indexes.add(original_index)
                overridden_labels += 1

            # New URLs are added to the training set
            else:
                added_new_urls += 1

            # Collect feedback features and labels
            feedback_train_rows.append(
                row[feature_columns]
            )

            feedback_train_labels.append(
                int(row["label"])
            )

        # Remove original training samples whose labels are overridden
        if overridden_train_indexes:

            keep_mask = ~X_train.index.isin(
                overridden_train_indexes
            )

            X_train = X_train.loc[keep_mask]
            y_train = y_train.loc[keep_mask]

        # Add reconciled feedback to training
        if feedback_train_rows:

            X_feedback = pd.DataFrame(
                feedback_train_rows,
                columns=feature_columns,
            )

            y_feedback = pd.Series(
                feedback_train_labels,
                dtype=int,
            )

            X_train = pd.concat(
                [X_train, X_feedback],
                ignore_index=True,
            )

            y_train = pd.concat(
                [y_train, y_feedback],
                ignore_index=True,
            )

        print(f"Feedback records processed: {feedback_count:,}")
        print(f"Training labels overridden: {overridden_labels:,}")
        print(f"New URLs added: {added_new_urls:,}")
        print(f"Test URLs excluded: {excluded_test_urls:,}")

    else:
        print("No valid feedback samples available.")

    print(f"Final training samples: {len(X_train):,}")
    # --------------------------------------------------------
    # 4. SCALE FEATURES
    # --------------------------------------------------------

    print("\n[4/7] Scaling features...")

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # --------------------------------------------------------
    # 5. TRAIN MLP
    # --------------------------------------------------------

    print("\n[5/7] Training MLP...")

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
        verbose=True,
    )

    model.fit(X_train_scaled, y_train)

    print("\nTraining complete.")
    print(f"Iterations: {model.n_iter_}")
    print(f"Final loss: {model.loss_:.6f}")

    # --------------------------------------------------------
    # 6. EVALUATION ON UNTOUCHED ORIGINAL TEST SET
    # --------------------------------------------------------

    print("\n[6/7] Evaluating model...")

    predictions = model.predict(X_test_scaled)
    probabilities = model.predict_proba(X_test_scaled)[:, 1]

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(
        y_test, predictions, zero_division=0
    )
    recall = recall_score(
        y_test, predictions, zero_division=0
    )
    f1 = f1_score(
        y_test, predictions, zero_division=0
    )
    roc_auc = roc_auc_score(y_test, probabilities)

    print("\n" + "=" * 65)
    print("                    RESULTS")
    print("=" * 65)

    print(f"Accuracy  : {accuracy:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")
    print(f"ROC-AUC   : {roc_auc:.4f}")

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )

    # --------------------------------------------------------
    # 7. AUTOMATIC MODEL DEPLOYMENT
    # --------------------------------------------------------

    print("\n[7/7] Checking deployment conditions...")

    if accuracy < MINIMUM_ACCURACY:
        raise ModelRejectedError(
            f"Deployment rejected: accuracy {accuracy:.4f} "
            f"is below {MINIMUM_ACCURACY:.2f}"
        )

    if recall < MINIMUM_RECALL:
        raise ModelRejectedError(
            f"Deployment rejected: recall {recall:.4f} "
            f"is below {MINIMUM_RECALL:.2f}"
        )

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCALER_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Temporary candidate artifacts
    temp_model = MODEL_PATH.with_suffix(".tmp")
    temp_scaler = SCALER_PATH.with_suffix(".tmp")

    # Backup paths for the currently deployed artifacts
    backup_model = MODEL_PATH.with_suffix(".bak")
    backup_scaler = SCALER_PATH.with_suffix(".bak")

    try:
        # Save both candidate artifacts first.
        joblib.dump(model, temp_model)
        joblib.dump(scaler, temp_scaler)

        # Preserve the existing active artifacts.
        if not MODEL_PATH.exists() or not SCALER_PATH.exists():
            raise FileNotFoundError(
                "Existing model or scaler is missing. "
                "Cannot safely deploy a replacement."
            )

        shutil.copy2(MODEL_PATH, backup_model)
        shutil.copy2(SCALER_PATH, backup_scaler)

        try:
            # Replace active artifacts.
            os.replace(temp_scaler, SCALER_PATH)
            os.replace(temp_model, MODEL_PATH)

        except Exception:
            # Restore the previous pair if replacement fails.
            shutil.copy2(backup_model, MODEL_PATH)
            shutil.copy2(backup_scaler, SCALER_PATH)
            raise

        # Remove backups after successful deployment.
        backup_model.unlink(missing_ok=True)
        backup_scaler.unlink(missing_ok=True)

    finally:
        # Remove any remaining temporary files.
        temp_model.unlink(missing_ok=True)
        temp_scaler.unlink(missing_ok=True)

    duration = time.time() - started_at

    metrics = {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "roc_auc": float(roc_auc),
        "iterations": int(model.n_iter_),
        "final_loss": float(model.loss_),
        "training_duration_seconds": round(duration, 2),
        "test_samples": int(len(y_test)),
    }

    print("\n" + "=" * 65)
    print("          PRE-GUARD AI — MODEL DEPLOYED")
    print("=" * 65)

    print(f"Model: {MODEL_PATH}")
    print(f"Scaler: {SCALER_PATH}")

    for name, value in metrics.items():
        print(f"{name}: {value}")

    return {
        "accepted": True,
        "metrics": metrics,
        "model_path": str(MODEL_PATH),
        "scaler_path": str(SCALER_PATH),
    }
    

if __name__ == "__main__":
    train_model()

