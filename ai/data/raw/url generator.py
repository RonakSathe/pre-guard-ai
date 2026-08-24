import csv
import random
import string

random.seed(42)

# ============================================================
# BENIGN URL DATA
# ============================================================

benign_domains = [
    "google.com",
    "github.com",
    "wikipedia.org",
    "stackoverflow.com",
    "youtube.com",
    "nytimes.com",
    "docs.python.org",
    "developer.mozilla.org",
    "medium.com",
    "arxiv.org",
    "microsoft.com",
    "apple.com",
    "amazon.com",
    "reddit.com",
    "linkedin.com",
    "mozilla.org",
    "python.org",
    "ubuntu.com",
    "cloudflare.com",
    "npmjs.com"
]

benign_subdomains = [
    "www",
    "docs",
    "support",
    "blog",
    "developer",
    "learn",
    "help",
    "news",
    "accounts"
]

benign_paths = [
    "/search",
    "/search/results",
    "/questions",
    "/questions/12345/example",
    "/wiki/Computer_security",
    "/wiki/Artificial_intelligence",
    "/user/profile",
    "/users/12345",
    "/blog/article",
    "/blog/technology",
    "/docs/python/tutorial",
    "/documentation/getting-started",
    "/watch",
    "/video/technology",
    "/news/technology",
    "/articles/cybersecurity",
    "/products/software",
    "/download",
    "/account/settings",
    "/help/article",
    "/community/discussion",
    "/projects/example/issues/123",
    "/repositories/example",
    "/topics/python"
]

benign_queries = [
    "q=cybersecurity",
    "q=machine+learning",
    "q=python+tutorial",
    "q=artificial+intelligence",
    "q=computer+science",
    "page=2",
    "page=3",
    "sort=newest",
    "sort=popular",
    "category=technology",
    "language=en",
    "ref=homepage",
    "utm_source=google",
    "utm_medium=search",
    "id=12345",
    "user=12345",
    "topic=security",
    "year=2026"
]


def random_id():
    return str(random.randint(1000, 999999))


def generate_benign_url():
    domain = random.choice(benign_domains)

    # Sometimes add a legitimate subdomain
    if random.random() < 0.45:
        subdomain = random.choice(benign_subdomains)
        domain = f"{subdomain}.{domain}"

    path = random.choice(benign_paths)

    url = f"https://{domain}{path}"

    # Add realistic query parameters
    if random.random() < 0.65:
        query_count = random.randint(1, 3)

        queries = random.sample(
            benign_queries,
            min(query_count, len(benign_queries))
        )

        # Replace some IDs with random values
        queries = [
            q.replace("12345", random_id())
             .replace("99999", random_id())
            for q in queries
        ]

        url += "?" + "&".join(queries)

    return url


# ============================================================
# MALICIOUS URL DATA
# ============================================================

malicious_brands = [
    "paypal",
    "amazon",
    "google",
    "microsoft",
    "apple",
    "netflix",
    "facebook",
    "instagram",
    "linkedin",
    "bankofamerica",
    "chase",
    "wellsfargo",
    "icloud",
    "dhl",
    "fedex"
]

malicious_keywords = [
    "login",
    "verify",
    "verification",
    "secure",
    "security",
    "update",
    "account",
    "billing",
    "payment",
    "password",
    "signin",
    "confirm",
    "authenticate",
    "wallet",
    "invoice",
    "unlock",
    "suspended",
    "restore",
    "urgent"
]

suspicious_tlds = [
    ".xyz",
    ".top",
    ".click",
    ".online",
    ".site",
    ".live",
    ".support",
    ".info",
    ".biz",
    ".cc",
    ".tk",
    ".ml",
    ".ga"
]

malicious_extensions = [
    ".exe",
    ".scr",
    ".vbs",
    ".bat",
    ".cmd",
    ".zip",
    ".rar",
    ".js",
    ".php"
]


def random_string(length=8):
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def generate_ip():
    return (
        f"{random.randint(1, 223)}."
        f"{random.randint(0, 255)}."
        f"{random.randint(0, 255)}."
        f"{random.randint(1, 254)}"
    )


def generate_malicious_url():
    brand = random.choice(malicious_brands)
    keyword1 = random.choice(malicious_keywords)
    keyword2 = random.choice(malicious_keywords)
    tld = random.choice(suspicious_tlds)
    extension = random.choice(malicious_extensions)

    pattern = random.randint(1, 10)

    # --------------------------------------------------------
    # Brand impersonation
    # --------------------------------------------------------

    if pattern == 1:
        return (
            f"http://{brand}-{keyword1}-"
            f"secure{tld}/login"
        )

    # --------------------------------------------------------
    # Fake login page
    # --------------------------------------------------------

    elif pattern == 2:
        return (
            f"http://{random_string(6)}.{brand}"
            f"-{keyword1}{tld}/account/login"
        )

    # --------------------------------------------------------
    # Suspicious verification URL
    # --------------------------------------------------------

    elif pattern == 3:
        return (
            f"http://verify-{brand}-account"
            f"{tld}/verify?user={random_id()}"
        )

    # --------------------------------------------------------
    # IP address URL
    # --------------------------------------------------------

    elif pattern == 4:
        ip = generate_ip()

        return (
            f"http://{ip}/login/"
            f"{keyword1}?session={random_string(12)}"
        )

    # --------------------------------------------------------
    # Executable download
    # --------------------------------------------------------

    elif pattern == 5:
        return (
            f"http://{random_string(10)}{tld}/"
            f"downloads/invoice_update"
            f"{extension}"
        )

    # --------------------------------------------------------
    # Deep suspicious path
    # --------------------------------------------------------

    elif pattern == 6:
        return (
            f"http://{brand}-support{tld}/"
            f"account/security/verification/"
            f"login/confirm"
        )

    # --------------------------------------------------------
    # Fake payment page
    # --------------------------------------------------------

    elif pattern == 7:
        return (
            f"http://secure-{brand}-billing{tld}/"
            f"payment/update?account={random_id()}"
        )

    # --------------------------------------------------------
    # Multiple suspicious parameters
    # --------------------------------------------------------

    elif pattern == 8:
        return (
            f"http://{random_string(7)}{tld}/"
            f"{keyword1}?account={random_id()}"
            f"&verify=true&session={random_string(16)}"
        )

    # --------------------------------------------------------
    # Obfuscated URL
    # --------------------------------------------------------

    elif pattern == 9:
        return (
            f"http://{brand}%2D{keyword1}{tld}/"
            f"auth%2Flogin%3Fid%3D{random_id()}"
        )

    # --------------------------------------------------------
    # Suspicious redirect-style URL
    # --------------------------------------------------------

    else:
        return (
            f"http://{random_string(8)}{tld}/"
            f"redirect?url=http%3A%2F%2F"
            f"{brand}%2Ecom%2Flogin"
        )


# ============================================================
# GENERATE DATASET
# ============================================================

urls = []

NUMBER_OF_BENIGN = 2500
NUMBER_OF_MALICIOUS = 2500

for _ in range(NUMBER_OF_BENIGN):
    urls.append(
        (generate_benign_url(), 0)
    )

for _ in range(NUMBER_OF_MALICIOUS):
    urls.append(
        (generate_malicious_url(), 1)
    )


# Shuffle dataset
random.shuffle(urls)


# ============================================================
# SAVE CSV IN CURRENT FOLDER
# ============================================================

output_file = "url_dataset_5000.csv"

with open(
    output_file,
    mode="w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "url",
        "label"
    ])

    writer.writerows(urls)


print()
print("========================================")
print("URL DATASET CREATED")
print("========================================")
print(f"File: {output_file}")
print(f"Total URLs: {len(urls)}")
print(f"Benign: {NUMBER_OF_BENIGN}")
print(f"Malicious: {NUMBER_OF_MALICIOUS}")
print("========================================")