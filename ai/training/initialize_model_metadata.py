from pathlib import Path
from datetime import datetime
import json


MODEL_PATH = Path(
    "ai/models/neural_network.joblib"
)

SCALER_PATH = Path(
    "ai/models/neural_network_scaler.joblib"
)

METADATA_PATH = Path(
    "ai/models/model_metadata.json"
)


def main():

    print("=" * 60)
    print("PRE-GUARD AI - INITIALIZE MODEL METADATA")
    print("=" * 60)

    # --------------------------------------------------------
    # Check production files
    # --------------------------------------------------------

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Production model not found: {MODEL_PATH}"
        )

    if not SCALER_PATH.exists():
        raise FileNotFoundError(
            f"Production scaler not found: {SCALER_PATH}"
        )

    # --------------------------------------------------------
    # Prevent accidental overwrite
    # --------------------------------------------------------

    if METADATA_PATH.exists():

        print(
            "\nModel metadata already exists:"
        )

        print(
            f"  {METADATA_PATH}"
        )

        print(
            "\nNothing was changed."
        )

        return

    # --------------------------------------------------------
    # Create v1.0 metadata
    # --------------------------------------------------------

    metadata = {
        "project": "PRE_GUARD AI",

        "model_type": "MLPClassifier",

        "architecture": [
            64,
            32,
            16
        ],

        "version": "v1.0",

        "created_at": datetime.now().isoformat(),

        "model_file": str(
            MODEL_PATH
        ),

        "scaler_file": str(
            SCALER_PATH
        ),

        "metrics": {
            "accuracy": 0.9907,
            "precision": 0.9967,
            "recall": 0.9837,
            "f1": 0.9901,
            "roc_auc": 0.9964,
            "feedback_accuracy": 0.4000
        },

        "status": "production",

        "notes": (
            "Initial production model version. "
            "Metrics are based on the existing "
            "PRE-GUARD evaluation."
        )
    }

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    METADATA_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4
        )

    print(
        "\nProduction metadata created:"
    )

    print(
        f"  {METADATA_PATH}"
    )

    print(
        "\nProduction version: v1.0"
    )

    print(
        "\nModel files were NOT modified."
    )

    print("=" * 60)


if __name__ == "__main__":
    main()