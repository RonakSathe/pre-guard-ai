from urllib.parse import urlparse
import math
import re
import ipaddress
from collections import Counter

SUSPICIOUS_KEYWORDS = {
    "login",
    "verify",
    "verification",
    "account",
    "secure",
    "update",
    "confirm",
    "password",
    "signin",
    "bank",
    "wallet",
    "payment",
    "prize",
    "reward",
    "free",
    "claim",
}

SHORTENING_DOMAINS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "is.gd",
    "buff.ly",
    "cutt.ly",
}

def calculate_entropy(value:str) -> float:
    """Calcuating shannon entropy of a string. Higher score -> but it not shows a malicious activity"""

    if not value: return 0.0

    counts = Counter(value)
    length = len(value)

    entropy = 0.0

    for count in counts.values():
        probability = count/length
        if probability > 0:
            entropy -= (
                probability *
                math.log2(probability)
            )

    return max(0.0, entropy)

def is_ip_address(hostname:str) -> bool:
    if not hostname:return False
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False



def extract_url_features(url:str) -> dict:

    """Extract cyber-security oriented features from a url"""
    parsed = urlparse(url)

    hostname = parsed.hostname or ""
    path = parsed.path or ""
    query = parsed.query or ""

    hostname_lower = hostname.lower()
    url_lower = url.lower()

    subdomian_count = max(0,len(hostname.split("."))-2)
    suspicious_keyword_count = sum(1 for keyword in SUSPICIOUS_KEYWORDS if keyword in url_lower)

    percent_encoded_count = len(re.findall(r"%[0-9a-fA-F]{2}",url))
    tld = ""

    if "." in hostname:
        tld = hostname.split(".")[-1].lower()

    features = {
        "url_length": len(url),
        "hostname_length": len(hostname),
        "path_length": len(path),
        "query_length": len(query),

        #Characteristics
        "num_dots": url.count("."),
        "num_hyphens": url.count("-"),
        "num_underscores": url.count("_"),
        "path_slash_count": path.count("/"),
        "num_question_marks": url.count("?"),
        "num_equals": url.count("="),
        "num_digits": sum(char.isdigit() for char in url),
        "num_special_chars": sum(
            not char.isalnum()
            for char in url
        ),

        "uses_https": int(parsed.scheme.lower() == "https"),
        "has_query": int(bool(query)),
        "num_subdomains": subdomian_count,
        "has_ip_address": int(is_ip_address(hostname)),
        "has_at_symbol": int("@" in url),
        "has_url_encoding": int(percent_encoded_count > 0),
        "num_percent_encoded": percent_encoded_count,
        "has_double_slash_path": int("//" in path),
        "suspicious_keyword_count": suspicious_keyword_count,
        "is_shortened_url": int(hostname_lower in SHORTENING_DOMAINS),
        "hostname_entropy": calculate_entropy(hostname),
        "tld_length": len(tld),
        }

    return features