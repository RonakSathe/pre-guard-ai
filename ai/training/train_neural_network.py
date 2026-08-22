import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,classification_report

DATASET = "ai/data/processed/url_features.csv"
MODEL_PATH = "ai/models/neural_network.keras"
SCALER_PATH = "ai/models/neural_network_scaler.joblib"

#Reproducibility
np.random.seed(42)

def train_model():
    print("\n PRE_GUARD_AI - NEURAL NETWORK")
    print("-"*40)

    #Load Data set
    df = pd.read_csv(DATASET)
    X = df.drop(columns=["label"])
    y = df["label"]

    print(f"Samples: {len(df)}")
    print(f"Features: {X.shape[1]}")

    #Train test split

    X_train,X_test,y_train,y_test = train_test_split(
        X,y,test_size=0.30,random_state=42,stratify=y
    )

    #Feature scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)


    joblib.dump(scaler,SCALER_PATH)

    #BUild neural network
    model = MLPClassifier(
        hidden_layer_sizes=(64,32,16),
        activation="relu",
        solver="adam",
        learning_rate_init=0.001,
        batch_size=4,
        max_iter=500,
        early_stopping=True,
        validation_fraction=0.2,
        n_iter_no_change=10,random_state=42,
    )

    #Train
    print(f"\n [5/6] Training")
    print("-"*60)

    model.fit(X_train_scaled,y_train)

    print(f"\n Training COmplete.")
    print(f"Iteration : {model.n_iter_}")

    #6.  Evaluate
    print("[6/6]: Evaluate")
    print("-"*60)

    predictions = model.predict(
        X_test_scaled
    )

    probabilities = model.predict_proba(X_test_scaled)[:,1]
    accuracy = accuracy_score(y_test,predictions)
    precision = precision_score(y_test,predictions,zero_division=0)
    recall = recall_score(y_test,predictions,zero_division=0)
    f1 = f1_score(y_test,predictions,zero_division=0)

    print()
    print("="*60)
    print("                    Results")
    print("="*60)

    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1:.4f}")

    print("\n CLassification Report")

    print(classification_report(
        y_test,predictions,zero_division=0
    ))

#SHow predictions
    print("Test probabilities")
    print("="*60)

    for probability, prediction in zip(probabilities,predictions):
        label = ("SUSPICIOUS" if prediction == 1 else "BENIGN")

        print(f"Probability: {probability:.4f} | {label}")


    #Save Model
    joblib.dump(model,MODEL_PATH)

    print()
    print("=" * 60)
    print("MODEL SAVED")
    print("=" * 60)

    print(f"Model : {MODEL_PATH}")
    print(f"Scaler: {SCALER_PATH}")


if __name__ == "__main__":
    train_model()