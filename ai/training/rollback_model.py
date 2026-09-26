from pathlib import Path
from datetime import datetime
import json
import shutil
import re


# ============================================================
# PATHS
# ============================================================

MODEL_PATH = Path(
    "ai/models/neural_network.joblib"
)

SCALER_PATH = Path(
    "ai/models/neural_network_scaler.joblib"
)

METADATA_PATH = Path(
    "ai/models/model_metadata.json"
)

ARCHIVE_DIR = Path(
    "ai/models/archive"
)


# ============================================================
# HELPERS
# ============================================================

def get_archived_versions():
    """
    Find archived model/scaler pairs.

    Expected archive names:

        neural_network_v1.0_YYYYMMDD_HHMMSS.joblib
        neural_network_scaler_v1.0_YYYYMMDD_HHMMSS.joblib
    """

    model_pattern = re.compile(
        r"^neural_network_(v[\d.]+)_(\d{8}_\d{6})\.joblib$"
    )

    scaler_pattern = re.compile(
        r"^neural_network_scaler_(v[\d.]+)_(\d{8}_\d{6})\.joblib$"
    )

    models = {}

    scalers = {}

    if not ARCHIVE_DIR.exists():
        return []

    for file in ARCHIVE_DIR.glob("*.joblib"):

        model_match = model_pattern.match(
            file.name
        )

        if model_match:

            version = model_match.group(1)
            timestamp = model_match.group(2)

            models[(version, timestamp)] = file

            continue

        scaler_match = scaler_pattern.match(
            file.name
        )

        if scaler_match:

            version = scaler_match.group(1)
            timestamp = scaler_match.group(2)

            scalers[(version, timestamp)] = file

    versions = []

    for key, model_path in models.items():

        scaler_path = scalers.get(key)

        if scaler_path is None:
            continue

        version, timestamp = key

        versions.append(
            {
                "version": version,
                "timestamp": timestamp,
                "model": model_path,
                "scaler": scaler_path,
            }
        )

    versions.sort(
        key=lambda item: item["timestamp"],
        reverse=True
    )

    return versions


def create_backup_path(prefix, original_name):

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return (
        ARCHIVE_DIR
        / f"{prefix}_{timestamp}_{original_name}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PRE-GUARD AI - MODEL ROLLBACK")
    print("=" * 60)


    # --------------------------------------------------------
    # 1. CHECK PRODUCTION FILES
    # --------------------------------------------------------

    print("\n[1/6] Checking production files...")

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            f"Production model not found:\n{MODEL_PATH}"
        )

    if not SCALER_PATH.exists():

        raise FileNotFoundError(
            f"Production scaler not found:\n{SCALER_PATH}"
        )

    if not METADATA_PATH.exists():

        raise FileNotFoundError(
            f"Model metadata not found:\n{METADATA_PATH}"
        )

    print("Production files found.")


    # --------------------------------------------------------
    # 2. LOAD METADATA
    # --------------------------------------------------------

    print("\n[2/6] Loading model metadata...")

    with open(
        METADATA_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        metadata = json.load(file)

    current_version = metadata.get(
        "version",
        "unknown"
    )

    print(
        f"Current production version: "
        f"{current_version}"
    )


    # --------------------------------------------------------
    # 3. FIND ARCHIVES
    # --------------------------------------------------------

    print("\n[3/6] Searching model archive...")

    archived_versions = (
        get_archived_versions()
    )

    if not archived_versions:

        print(
            "\nNo complete archived model versions found."
        )

        print(
            "\nRollback is currently unavailable."
        )

        print(
            "This is normal because no newer model "
            "has been successfully promoted yet."
        )

        return

    print(
        f"\nFound {len(archived_versions)} "
        f"complete archived version(s)."
    )


    # --------------------------------------------------------
    # 4. DISPLAY OPTIONS
    # --------------------------------------------------------

    print("\nAvailable rollback versions:")
    print("-" * 60)

    for index, item in enumerate(
        archived_versions,
        start=1
    ):

        print(
            f"{index}. "
            f"{item['version']} "
            f"({item['timestamp']})"
        )

        print(
            f"   Model : {item['model'].name}"
        )

        print(
            f"   Scaler: {item['scaler'].name}"
        )


    # --------------------------------------------------------
    # 5. USER SELECTION
    # --------------------------------------------------------

    print(
        "\nRollback will replace the current "
        "production model."
    )

    choice = input(
        "\nEnter the number to restore "
        "(or press Enter to cancel): "
    ).strip()

    if not choice:

        print(
            "\nRollback cancelled."
        )

        return

    try:

        selection = int(choice)

    except ValueError:

        print(
            "\nInvalid selection."
        )

        return

    if selection < 1 or selection > len(
        archived_versions
    ):

        print(
            "\nInvalid selection."
        )

        return

    selected = archived_versions[
        selection - 1
    ]

    target_version = selected[
        "version"
    ]


    # --------------------------------------------------------
    # CONFIRM
    # --------------------------------------------------------

    print("\nSelected rollback:")
    print(
        f"  Current : {current_version}"
    )
    print(
        f"  Restore : {target_version}"
    )

    print(
        "\nWARNING:"
    )

    print(
        "The current production model will first "
        "be backed up."
    )

    confirmation = input(
        "\nType ROLLBACK to continue: "
    ).strip()

    if confirmation != "ROLLBACK":

        print(
            "\nRollback cancelled."
        )

        return


    # --------------------------------------------------------
    # 6. SAFETY BACKUP
    # --------------------------------------------------------

    print(
        "\n[4/6] Backing up current production..."
    )

    ARCHIVE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    current_backup_model = (
        create_backup_path(
            "rollback_backup",
            MODEL_PATH.name
        )
    )

    current_backup_scaler = (
        create_backup_path(
            "rollback_backup",
            SCALER_PATH.name
        )
    )

    shutil.copy2(
        MODEL_PATH,
        current_backup_model
    )

    shutil.copy2(
        SCALER_PATH,
        current_backup_scaler
    )

    print(
        f"Current model backup:"
        f"\n  {current_backup_model}"
    )

    print(
        f"Current scaler backup:"
        f"\n  {current_backup_scaler}"
    )


    # --------------------------------------------------------
    # RESTORE
    # --------------------------------------------------------

    print(
        "\n[5/6] Restoring archived model..."
    )

    shutil.copy2(
        selected["model"],
        MODEL_PATH
    )

    shutil.copy2(
        selected["scaler"],
        SCALER_PATH
    )

    print(
        f"Restored model : "
        f"{selected['model'].name}"
    )

    print(
        f"Restored scaler: "
        f"{selected['scaler'].name}"
    )


    # --------------------------------------------------------
    # UPDATE METADATA
    # --------------------------------------------------------

    print(
        "\n[6/6] Updating metadata..."
    )

    metadata["version"] = target_version

    metadata["status"] = "production"

    metadata["rollback"] = {
        "performed_at":
            datetime.now().isoformat(),

        "from_version":
            current_version,

        "to_version":
            target_version,

        "source_model":
            selected["model"].name,

        "source_scaler":
            selected["scaler"].name,
    }

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


    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("ROLLBACK COMPLETE")
    print("=" * 60)

    print(
        f"\nProduction version:"
        f" {target_version}"
    )

    print(
        "\nThe previous production model was "
        "also backed up."
    )

    print(
        "\nPRE-GUARD AI is now running on "
        f"{target_version}."
    )


if __name__ == "__main__":
    main()