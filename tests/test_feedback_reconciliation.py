import pandas as pd

# -----------------------------------------
# Simulated original dataset
# -----------------------------------------

original_df = pd.DataFrame({
    "url": [
        "https://train-safe.com",
        "https://train-malicious.com",
        "https://test-safe.com",
        "https://test-malicious.com",
    ],
    "f1": [10, 20, 30, 40],
    "f2": [1, 2, 3, 4],
    "label": [0, 1, 0, 1],
})

# Simulated train/test split (preserve original indexes)
X_train = original_df.loc[[0, 1], ["f1", "f2"]]
y_train = original_df.loc[[0, 1], "label"]

X_test = original_df.loc[[2, 3], ["f1", "f2"]]
y_test = original_df.loc[[2, 3], "label"]

original_urls = original_df["url"].astype(str).str.strip()

# -----------------------------------------
# Simulated feedback
# -----------------------------------------

feedback_features = pd.DataFrame({
    "url": [
        "https://train-safe.com",       # Existing training URL
        "https://new-website.com",      # New URL
        "https://test-safe.com",        # Existing test URL
    ],
    "f1": [10, 50, 30],
    "f2": [1, 5, 3],
    "label": [1, 0, 1],
})

feature_columns = ["f1", "f2"]

# -----------------------------------------
# Feedback reconciliation logic
# -----------------------------------------

train_url_keys = set(
    original_urls.loc[X_train.index].str.strip()
)

test_url_keys = set(
    original_urls.loc[X_test.index].str.strip()
)

train_url_to_index = {}

for index, url in original_urls.items():
    url_key = str(url).strip()

    if index in X_train.index:
        train_url_to_index[url_key] = index

overridden_train_indexes = set()
feedback_train_rows = []
feedback_train_labels = []

added_new_urls = 0
overridden_labels = 0
excluded_test_urls = 0

feedback_latest = {}

for _, row in feedback_features.iterrows():
    url_key = str(row["url"]).strip()
    feedback_latest[url_key] = row

for url_key, row in feedback_latest.items():

    if url_key in test_url_keys:
        excluded_test_urls += 1
        continue

    if url_key in train_url_keys:
        original_index = train_url_to_index[url_key]
        overridden_train_indexes.add(original_index)
        overridden_labels += 1
    else:
        added_new_urls += 1

    feedback_train_rows.append(row[feature_columns])
    feedback_train_labels.append(int(row["label"]))

if overridden_train_indexes:
    keep_mask = ~X_train.index.isin(overridden_train_indexes)

    X_train = X_train.loc[keep_mask]
    y_train = y_train.loc[keep_mask]

if feedback_train_rows:
    X_feedback = pd.DataFrame(
        feedback_train_rows,
        columns=feature_columns,
    )

    y_feedback = pd.Series(
        feedback_train_labels,
        dtype=int,
    )

    X_train = pd.concat(
        [X_train, X_feedback],
        ignore_index=True,
    )

    y_train = pd.concat(
        [y_train, y_feedback],
        ignore_index=True,
    )

# -----------------------------------------
# Verification
# -----------------------------------------

print("\n--- TEST RESULTS ---")

print("Training data after reconciliation:")
print(X_train)

print("\nTraining labels:")
print(y_train.tolist())

print("\nOverridden training labels:", overridden_labels)
print("New URLs added:", added_new_urls)
print("Test URLs excluded:", excluded_test_urls)

assert overridden_labels == 1
assert added_new_urls == 1
assert excluded_test_urls == 1

# Existing training URL should now have feedback label = 1
assert 1 in y_train.tolist()

# New URL should have been added
assert len(X_train) == 3

# Test set must remain completely unchanged
assert len(X_test) == 2
assert y_test.tolist() == [0, 1]

print("\nALL TESTS PASSED!")