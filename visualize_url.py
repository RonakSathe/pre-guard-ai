
from urllib.parse import urlsplit
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from ai.features.url_features import extract_url_features


URL = "https://example.com/login?user=test&id=123"

# Split URL into components
parsed = urlsplit(URL)

components = [
    ("Protocol", parsed.scheme + "://", "#dbeafe"),
    ("Hostname", parsed.hostname or "", "#dcfce7"),
    ("Path", parsed.path or "/", "#fef3c7"),
    ("Query", "?" + parsed.query if parsed.query else "", "#fce7f3"),
    ("Fragment", "#" + parsed.fragment if parsed.fragment else "", "#ede9fe"),
]

# Extract PRE-GUARD AI features
features = extract_url_features(URL)

# Visualize
fig, ax = plt.subplots(figsize=(14, 7))
ax.set_xlim(0, 14)
ax.set_ylim(0, 7)
ax.axis("off")

ax.text(
    7, 6.5,
    "PRE-GUARD AI - URL Feature Extraction",
    ha="center",
    fontsize=19,
    fontweight="bold"
)

# Display URL components
x = 0.5

for name, value, color in components:
    if not value:
        continue

    width = max(len(value) * 0.17, 1.3)

    box = FancyBboxPatch(
        (x, 5),
        width,
        0.8,
        boxstyle="round,pad=0.08",
        facecolor=color,
        edgecolor="black"
    )

    ax.add_patch(box)

    ax.text(
        x + width / 2,
        5.4,
        value,
        ha="center",
        va="center",
        fontsize=10
    )

    ax.text(
        x + width / 2,
        4.6,
        name,
        ha="center",
        fontsize=11,
        fontweight="bold"
    )

    x += width + 0.15

# Display extracted features
ax.text(
    0.5, 3.8,
    "Extracted Features",
    fontsize=15,
    fontweight="bold"
)

for i, (name, value) in enumerate(features.items()):
    col = i // 12
    row = i % 12

    ax.text(
        0.5 + col * 6.5,
        3.3 - row * 0.25,
        f"{name}: {value}",
        fontsize=9
    )

plt.tight_layout()
plt.show()
