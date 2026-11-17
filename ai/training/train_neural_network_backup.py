import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from ai.features.url_features import extract_url_features



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

MODEL_PATH = "ai/models/neural_network_feedback_test.joblib"
SCALER_PATH = "ai/models/neural_network_feedback_test_scaler.joblib"
FEEDBACK_PATH = "ai/data/feedback.csv"

RANDOM_STATE = 42


# ============================================================
# FEATURE EXTRACTION

# ============================================================
# CONVERT FEEDBACK URLS INTO MODEL FEATURES
# ============================================================

def prepare_feedback_features(feedback_df):

    if feedback_df.empty:
        return pd.DataFrame()

    feedback_features = []

    print("\nConverting feedback URLs into model features...")

    for _, row in feedback_df.iterrows():

        url = row["url"]
        label = int(row["label"])

        try:
            features = extract_url_features(url)
            features["label"] = label

            feedback_features.append(features)

            print(f"  ✓ {url}")

        except Exception as error:
            print(f"  ✗ Could not process: {url}")
            print(f"    Error: {error}")

    if not feedback_features:
        return pd.DataFrame()

    return pd.DataFrame(feedback_features)    


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

    # --------------------------------------------------------
    # 1B. LOAD FEEDBACK DATASET
    # --------------------------------------------------------

    print(f"\n [1B]: CHecking user feedback .....")

    try:
        feedback_df = pd.read_csv(FEEDBACK_PATH)
        print(f"Feedback samples: {len(feedback_df):,}")

        if not {"url","label"}.issubset(feedback_df.columns):
            print("Feedback CSV does not contain required columns. Skipping feedback integration.")

        feedback_df = feedback_df[["url", "label"]].dropna()
        feedback_df["url"] = feedback_df["url"].astype(str).str.strip()
        
        
        feedback_df["label"] = pd.to_numeric(
            feedback_df["label"],
            errors='coerce')

        feedback_df = feedback_df.dropna(subset=["label"])
        feedback_df = feedback_df[feedback_df["label"].isin([0, 1])]
        feedback_df = feedback_df.drop_duplicates(subset=["url"],keep="last")

        
        print(f"Feedback samples: {len(feedback_df):,}")
        if len(feedback_df) > 0:
            print("\n Feedback class distribution:")
            print(feedback_df["label"].astype(int).value_counts().sort_index())
    except FileNotFoundError:
        feedback_df = pd.DataFrame(columns=["url", "label"])
        print("Feedback CSV not found. Skipping feedback integration.")

    # --------------------------------------------------------
    # 1C. EXTRACT FEATURES FROM FEEDBACK
        # --------------------------------------------------------
    # 1C. CONVERT FEEDBACK TO FEATURES
    # --------------------------------------------------------

    feedback_features_df = prepare_feedback_features(feedback_df)

    if not feedback_features_df.empty:

        print("\nFeedback feature conversion complete.")

        print(
            f"Feedback feature count: "
            f"{feedback_features_df.shape[1] - 1}"
        )

        print(
            f"Feedback samples ready: "
            f"{len(feedback_features_df):,}"
        )

        print("\nFeedback feature columns:")
        print(
            list(
                feedback_features_df.drop(
                    columns=["label"]
                ).columns
            )
        )

    else:
        print("\nNo feedback features available.")

    X = df.drop(columns=["label"])
    y = df["label"]

    print(f"Samples : {len(df):,}")
    print(f"Features: {X.shape[1]}")

    print("\nClass distribution:")
    print(y.value_counts().sort_index())

    # 1D............................
    # Merge validated feedback into dataset

    if not feedback_features_df.empty:
        print("\nMErging validated ffeedback into training dataset")

        # Making sure feature columns match to the original dataset
        feature_columns = X.columns.tolist()

        feedback_features_df = feedback_features_df[feature_columns + ["label"]]

        # Add feedback samples to original dataset
        df = pd.concat([df, feedback_features_df], ignore_index=True)

        print(
            f"Original samples : {len(df) - len(feedback_features_df):,}"
        )

        print(
            f"Feedback samples : {len(feedback_features_df):,}"
        )

        print(
            f"Combined samples : {len(df):,}"
        )

        print("\nCombined class distribution:")
        print(
            df["label"]
            .astype(int)
            .value_counts()
            .sort_index()
        )

        # Rebuild X and y after merging feedback
        X = df.drop(columns=["label"])
        y = df["label"]

    else:

        print("\nNo feedback samples to merge.")

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