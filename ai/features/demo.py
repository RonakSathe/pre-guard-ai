from url_features import extract_url_features


url = "https://example.com/verify-account?user=123"

features = extract_url_features(url)

print("\nPRE-GUARD AI — URL ANALYSIS")
print("-" * 40)

for name, value in features.items():
    print(f"{name:30} {value}")