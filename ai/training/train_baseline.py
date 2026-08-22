import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

DATASET = "ai/data/processed/url_features.csv"
MODEL_PATH = "ai/models/url_classifier.joblib"

def train_model():
    df = pd.read_csv(DATASET)

    X = df.drop(columns=['label'])
    y = df['label']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42,stratify=y)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test,predictions)

    print("\n PRE - GUARD AI - BSELINE MOdEL")
    print("-"*40)

    print(f"Accuracy {accuracy:.4f}")
    print("Classification Report")
    print(classification_report(y_test,predictions,zero_division=0))


    joblib.dump(model,MODEL_PATH)
    print(f"\n Model save to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()