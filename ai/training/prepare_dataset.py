import pandas as pd

from ai.features.url_features import extract_url_features

INPUT_FILE = "ai/data/raw/sample_urls.csv"
OUTPUT_FILE = "ai/data/processed/url_features.csv"

def build_dataset():
    df = pd.read_csv(INPUT_FILE)
    feature_rows = []
    for _, row in df.iterrows():
        features = extract_url_features(row['url'])
        features['label'] = row['label']

        feature_rows.append(features)
    feature_df = pd.DataFrame(feature_rows)
    feature_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Dataset saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    build_dataset()