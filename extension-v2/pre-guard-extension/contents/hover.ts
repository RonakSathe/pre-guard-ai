// ============================================================
// PRE-GUARD AI — CONTENT SCRIPT
// Version: 2.1.0
// ============================================================

console.log("🛡️ PRE-GUARD v2 content script loaded");

let tooltip: HTMLDivElement | null = null;
let currentLink: HTMLAnchorElement | null = null;
let requestCounter = 0;
let warningOpen = false;

// Stores the latest prediction for the link being hovered.
let currentPrediction: any = null;

// Used when the user clicks Continue.
let allowedNavigationUrl: string | null = null;


// ============================================================
// TOOLTIP
// ============================================================

function createTooltip(): HTMLDivElement {

    if (tooltip) {
        return tooltip;
    }

    tooltip = document.createElement("div");

    tooltip.id = "pre-guard-tooltip";

    Object.assign(tooltip.style, {
        position: "fixed",
        zIndex: "2147483647",
        padding: "14px 16px",
        borderRadius: "10px",
        fontFamily: "Arial, sans-serif",
        fontSize: "13px",
        lineHeight: "1.4",
        background: "#111827",
        color: "#ffffff",
        boxShadow: "0 5px 20px rgba(0,0,0,0.30)",
        minWidth: "210px",
        maxWidth: "340px",
        pointerEvents: "auto",
        display: "none"
    });

    document.body.appendChild(tooltip);

    return tooltip;
}


// ============================================================
// HIDE TOOLTIP
// ============================================================

function hideTooltip(): void {

    if (!tooltip) {
        return;
    }

    tooltip.style.display = "none";
}


// ============================================================
// SHOW ANALYZING
// ============================================================

function showAnalyzing(
    x: number,
    y: number
): void {

    const box = createTooltip();

    box.innerHTML = `
        <strong>🛡️ PRE-GUARD</strong>
        <br><br>
        🔍 Analyzing URL...
    `;

    box.style.left = `${x + 15}px`;
    box.style.top = `${y + 15}px`;
    box.style.display = "block";
}


// ============================================================
// SHOW RISK RESULT
// ============================================================

function showResult(
    result: any,
    x: number,
    y: number
): void {

    const box = createTooltip();

    const score =
        Number(result.risk_score ?? 0);

    const percentage =
        Number(
            result.risk_percentage ??
            score * 100
        );

    const classification =
        String(
            result.classification ??
            "UNKNOWN"
        );

    let icon = "🟢";
    let message = "This link appears safe.";

    if (classification === "SUSPICIOUS") {
        icon = "🟡";
        message = "This link may require caution.";
    }

    if (classification === "HIGH_RISK") {
        icon = "🔴";
        message = "Avoid this link unless you trust it.";
    }

    box.innerHTML = `
        <strong>🛡️ PRE-GUARD</strong>

        <br><br>

        ${icon}
        <strong>
            ${escapeHtml(classification)}
        </strong>

        <br>

        Risk:
        ${percentage.toFixed(2)}%

        <br><br>

        ${message}
    `;

    box.style.left = `${x + 15}px`;
    box.style.top = `${y + 15}px`;
    box.style.display = "block";
}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHtml(value: string): string {

    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


// ============================================================
// SHOW CLICK WARNING
// ============================================================

function showClickWarning(
    url: string
): void {
    warningOpen = true;
    const box = createTooltip();

    box.innerHTML = `
        <strong>🛡️ PRE-GUARD</strong>

        <br><br>

        🔴 <strong>HIGH RISK LINK</strong>

        <br><br>

        PRE-GUARD has detected
        this URL as potentially unsafe.

        <br><br>

        <strong>Do you want to continue?</strong>

        <br><br>

        <button
            id="pg-go-back"
            type="button"
        >
            Go Back
        </button>

        <button
            id="pg-continue"
            type="button"
        >
            Continue
        </button>
    `;

    // Important:
    // The tooltip remains interactive.
    box.style.pointerEvents = "auto";
    box.style.display = "block";

    const backButton =
        document.getElementById(
            "pg-go-back"
        );

    const continueButton =
        document.getElementById(
            "pg-continue"
        );

    // --------------------------------------------------------
    // GO BACK
    // --------------------------------------------------------

    backButton?.addEventListener(
        "click",
        (event) => {

            event.preventDefault();
            event.stopPropagation();

            warningOpen = false;
            hideTooltip();

            currentPrediction = null;
            currentLink = null;
        }
    );


    // --------------------------------------------------------
    // CONTINUE
    // --------------------------------------------------------

    continueButton?.addEventListener(
        "click",
        (event) => {

            event.preventDefault();
            event.stopPropagation();
            warningOpen = false;

            allowedNavigationUrl = url;

            hideTooltip();

            window.location.href = url;
        }
    );
}


// ============================================================
// ANALYZE URL
// ============================================================

function analyzeUrl(
    url: string,
    x: number,
    y: number
): void {

    if (!url) {
        return;
    }

    const requestId =
        ++requestCounter;

    currentPrediction = null;

    showAnalyzing(x, y);

    chrome.runtime.sendMessage(
        {
            type: "ANALYZE_URL",
            url: url
        },

        (response) => {

            if (chrome.runtime.lastError) {

                console.error(
                    "PRE-GUARD:",
                    chrome.runtime
                        .lastError
                        .message
                );

                hideTooltip();

                return;
            }

            // Ignore stale responses.
            if (
                requestId !==
                requestCounter
            ) {
                return;
            }

            if (
                !response ||
                !response.success ||
                !response.result
            ) {

                console.error(
                    "PRE-GUARD invalid response:",
                    response
                );

                hideTooltip();

                return;
            }

            if (!currentLink) {
                return;
            }

            currentPrediction =
                response.result;

            showResult(
                response.result,
                x,
                y
            );
        }
    );
}


// ============================================================
// MOUSE OVER
// ============================================================

document.addEventListener(
    "mouseover",
    (event) => {

        const target =
            event.target;

        if (
            !(target instanceof Element)
        ) {
            return;
        }

        const link =
            target.closest("a");

        if (!link) {
            return;
        }

        const url =
            link.href;

        if (!url) {
            return;
        }

        if (
            link === currentLink
        ) {
            return;
        }

        currentLink =
            link;

        currentPrediction =
            null;

        console.log(
            "🔗 PRE-GUARD detected URL:",
            url
        );

        analyzeUrl(
            url,
            event.clientX,
            event.clientY
        );
    }
);


// ============================================================
// CLICK INTERCEPTION
// ============================================================

document.addEventListener(
    "click",
    (event) => {

        const target =
            event.target;

        if (
            !(target instanceof Element)
        ) {
            return;
        }

        const link =
            target.closest("a");

        if (!link) {
            return;
        }

        const url =
            link.href;

        if (!url) {
            return;
        }


        // ----------------------------------------------------
        // If user already chose Continue,
        // allow this navigation.
        // ----------------------------------------------------

        if (
            allowedNavigationUrl === url
        ) {

            allowedNavigationUrl =
                null;

            return;
        }


        // ----------------------------------------------------
        // No prediction yet.
        //
        // Don't block the link.
        // ----------------------------------------------------

        if (!currentPrediction) {
            return;
        }


        const classification =
            String(
                currentPrediction
                    .classification ?? ""
            );


        // ----------------------------------------------------
        // SAFE
        // ----------------------------------------------------

        if (
            classification ===
            "SAFE"
        ) {
            return;
        }


        // ----------------------------------------------------
        // SUSPICIOUS / HIGH RISK
        // ----------------------------------------------------

        event.preventDefault();
        event.stopPropagation();


        console.log(
            "⚠️ PRE-GUARD blocked navigation:",
            url
        );


        showClickWarning(url);
    },
    true
);


// ============================================================
// MOUSE OUT
// ============================================================

// ============================================================
// MOUSE OUT
// ============================================================

document.addEventListener(
    "mouseout",
    (event) => {

        if (warningOpen){return;}

        const target =
            event.target;

        if (
            !(target instanceof Element)
        ) {
            return;
        }

        const link =
            target.closest("a");

        if (!link) {
            return;
        }

        const related =
            event.relatedTarget;


        // ----------------------------------------------------
        // Still inside the same link
        // ----------------------------------------------------

        if (
            related instanceof Node &&
            link.contains(related)
        ) {
            return;
        }


        // ----------------------------------------------------
        // IMPORTANT
        //
        // If the click warning is currently visible,
        // DO NOT hide it just because the mouse left
        // the original link.
        // ----------------------------------------------------

        if (
            tooltip &&
            tooltip.style.display === "block" &&
            tooltip.querySelector(
                "#pg-continue"
            )
        ) {
            return;
        }


        // ----------------------------------------------------
        // Normal hover behavior
        // ----------------------------------------------------

        if (
            link === currentLink
        ) {

            currentLink =
                null;

            currentPrediction =
                null;

            requestCounter++;

            hideTooltip();
        }
    }
);