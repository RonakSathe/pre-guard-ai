import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
)


# ============================================================
# CONFIG
# ============================================================

DATASET_PATH = "ai/data/processed/url_features.csv"

MODEL_PATH = "ai/models/neural_network.joblib"
SCALER_PATH = "ai/models/neural_network_scaler.joblib"

RANDOM_STATE = 42


# ============================================================
# TRAIN MODEL
# ============================================================

def train_model():

    print()
    print("=" * 65)
    print("             PRE-GUARD AI — MLP")
    print("=" * 65)

    # --------------------------------------------------------
    # 1. LOAD DATASET
    # --------------------------------------------------------

    print("\n[1/7] Loading dataset...")

    df = pd.read_csv(DATASET_PATH)

    X = df.drop(columns=["label"])
    y = df["label"]

    print(f"Samples : {len(df):,}")
    print(f"Features: {X.shape[1]}")

    print("\nClass distribution:")
    print(y.value_counts().sort_index())

    # --------------------------------------------------------
    # 2. TRAIN / TEST SPLIT
    # --------------------------------------------------------

    print("\n[2/7] Splitting dataset...")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    print(f"Training samples: {len(X_train):,}")
    print(f"Testing samples : {len(X_test):,}")

    # --------------------------------------------------------
    # 3. FEATURE SCALING
    # --------------------------------------------------------

    print("\n[3/7] Scaling features...")

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Save scaler
    joblib.dump(
        scaler,
        SCALER_PATH
    )

    print(f"Scaler saved: {SCALER_PATH}")

    # --------------------------------------------------------
    # 4. BUILD MLP
    # --------------------------------------------------------

    print("\n[4/7] Creating MLP neural network...")

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

    print("\nArchitecture:")
    print("Input  → 64 → 32 → 16 → Output")

    # --------------------------------------------------------
    # 5. TRAIN
    # --------------------------------------------------------

    print("\n[5/7] Training MLP...")
    print("-" * 65)

    model.fit(
        X_train_scaled,
        y_train
    )

    print("\nTraining complete.")

    print(
        f"Iterations: {model.n_iter_}"
    )

    print(
        f"Final loss: {model.loss_:.6f}"
    )

    # --------------------------------------------------------
    # 6. PREDICTIONS + EVALUATION
    # --------------------------------------------------------

    print("\n[6/7] Evaluating model...")
    print("-" * 65)

    predictions = model.predict(
        X_test_scaled
    )

    probabilities = model.predict_proba(
        X_test_scaled
    )[:, 1]

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities
    )

    print()
    print("=" * 65)
    print("                       RESULTS")
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
            zero_division=0
        )
    )

    # --------------------------------------------------------
    # 7. SAVE MODEL
    # --------------------------------------------------------

    print("\n[7/7] Saving MLP...")

    joblib.dump(
        model,
        MODEL_PATH
    )

    print(f"Model : {MODEL_PATH}")
    print(f"Scaler: {SCALER_PATH}")

    print()
    print("=" * 65)
    print("             PRE-GUARD MLP COMPLETE")
    print("=" * 65)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    train_model()