from pathlib import Path
from datetime import datetime
import json


MODEL_PATH = Path("ai/models/neural_network.joblib")
SCALER_PATH = Path("ai/models/neural_network_scaler.joblib")

METADATA_PATH = Path(
    "ai/models/model_metadata.json"
)

ARCHIVE_DIR = Path(
    "ai/models/archive"
)


def create_metadata(
    version,
    accuracy,
    precision,
    recall,
    f1,
    roc_auc,
    feedback_accuracy,
):
    return {
        "project": "PRE_GUARD AI",

        "model_type": "MLPClassifier",

        "architecture": [
            64,
            32,
            16
        ],

        "version": version,

        "created_at": datetime.now().isoformat(),

        "model_file": str(
            MODEL_PATH
        ),

        "scaler_file": str(
            SCALER_PATH
        ),

        "metrics": {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "roc_auc": roc_auc,
            "feedback_accuracy": feedback_accuracy,
        },
    }


def save_metadata(metadata):

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


def load_metadata():

    if not METADATA_PATH.exists():
        return None

    with open(
        METADATA_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def main():

    print("=" * 60)
    print("PRE-GUARD AI - MODEL VERSION")
    print("=" * 60)

    metadata = load_metadata()

    if metadata is None:

        print(
            "\nNo model metadata found."
        )

        print(
            "Production model exists, "
            "but its version information has not "
            "yet been recorded."
        )

        print(
            "\nThis is expected for the existing model."
        )

        return

    print("\nCurrent production model:")

    print(
        f"Version : "
        f"{metadata.get('version', 'unknown')}"
    )

    print(
        f"Created : "
        f"{metadata.get('created_at', 'unknown')}"
    )

    print("\nMetrics:")

    metrics = metadata.get(
        "metrics",
        {}
    )

    for name, value in metrics.items():

        print(
            f"  {name:<20}: {value}"
        )


if __name__ == "__main__":
    main()