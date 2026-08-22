import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.inspection import permutation_importance
from sklearn.preprocessing import StandardScaler

DATASET_PATH = "ai/data/processed/url_features.csv"

MODEL_PATH = "ai/models/neural_network.joblib"
SCALER_PATH = "ai/models/neural_network_scaler.joblib"

#LOAD DATASET
df = pd.read_csv(DATASET_PATH)
X = df.drop(columns=["label"])
y = df["label"]

#Same Split as training
X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.20,random_state=42,stratify=y)

#Load Scaler & model
scaler =joblib.load(SCALER_PATH)
model = joblib.load(MODEL_PATH)

#Scale the test data
X_test_scaled = scaler.transform(X_test)

#PErmutation importance
print("\n Calculating feature importance")
print("THis may take a little while")

result = permutation_importance(
    model,
    X_test_scaled,
    y_test,
    n_repeats=5,
    random_state=42,
    scoring="f1",
    n_jobs=-1,
)

#Results  
importance = pd.DataFrame({
    "feature":X.columns,
    "importance_mean": result.importances_mean,
    "importance_std": result.importances_std,
    })

importance = importance.sort_values(
    "importance_mean",ascending=False,
)

print("=" * 65)
print("        PRE-GUARD — MLP FEATURE IMPORTANCE")
print("=" * 65)

print(
    importance.to_string(
        index=False
    )
)