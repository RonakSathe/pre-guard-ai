import pandas as pd

from ai.features.url_features import extract_url_features

INPUT_FILE = "ai/data/raw/urls.csv"
OUTPUT_FILE = "ai/data/processed/url_features.csv"

# def build_dataset():
#     df = pd.read_csv(INPUT_FILE)
#     feature_rows = []
#     for _, row in df.iterrows():
#         features = extract_url_features(row['url'])
#         features['label'] = row['label']

#         feature_rows.append(features)
#     feature_df = pd.DataFrame(feature_rows)
#     feature_df.to_csv(OUTPUT_FILE, index=False)

#     print(f"Dataset saved to {OUTPUT_FILE}")


def prepare_dataset():
    print("\n PRE_GUARD AI - DATA PREPARATION")
    print("=" *50)

    #LOading RAW DATASET
    df = pd.read_csv(INPUT_FILE)
    print(f"Raw rows: {len(df)}")

    #Validate COlumns
    required_columns = {"url", "label"}
    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"MIssing columns: {missing}")

    #Remove missing columns
    df = df.dropna(subset=["url","label"])

    #Remove dubplicate URLS
    before = len(df)
    df = df.drop_duplicates(subset=["url"])

    print(f"Duplicates removed: {before - len(df)}")

    #Normalie Labels
    df["label"] = df["label"].astype(int)

    invalid_labels = set(df["label"].unique()) - {0,1}

    if invalid_labels:
        raise ValueError(f"Invlaid labels found: {invalid_labels}")

    #Extract features
    print("\n Extracting URL features....")

    feature_rows =[]

    for index, row in df.iterrows():
        try:
            features = extract_url_features(row["url"])
            features["label"] = row["label"]
            feature_rows.append(features)
        except Exception as error:
            print(f"SKippin row: {index}: {error}")

    #Create processe d dataset
    feature_df = pd.DataFrame(feature_rows)
    feature_df.to_csv(OUTPUT_FILE,index=False)

    #Sumarry: 

    print("\nDATASET SUMMARY")
    print("-" * 50)

    print(
        f"Processed rows : "
        f"{len(feature_df)}"
    )

    print(
        f"Features       : "
        f"{len(feature_df.columns) - 1}"
    )

    print("\nClass distribution:")

    print(
        feature_df["label"]
        .value_counts()
        .sort_index()
    )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    prepare_dataset()