from ai.features.url_features import extract_url_features


def test_basic_https_url():
    url = "https://example.com/products"

    features = extract_url_features(url)

    assert features["uses_https"] == 1
    assert features["has_ip_address"] == 0
    assert features["has_at_symbol"] == 0


def test_ip_based_url():
    url = "http://192.168.1.10/login"

    features = extract_url_features(url)

    assert features["has_ip_address"] == 1


def test_encoded_url():
    url = "https://example.com/%2Flogin"

    features = extract_url_features(url)

    assert features["has_url_encoding"] == 1
    assert features["num_percent_encoded"] == 1


def test_suspicious_keywords():
    url = "https://example.com/verify-account-login"

    features = extract_url_features(url)

    assert features["suspicious_keyword_count"] >= 2


def test_shortened_url():
    url = "https://bit.ly/example"

    features = extract_url_features(url)

    assert features["is_shortened_url"] == 1


def test_query_parameters():
    url = "https://example.com/login?user=123&verify=true"

    features = extract_url_features(url)

    assert features["has_query"] == 1
    assert features["num_equals"] == 2