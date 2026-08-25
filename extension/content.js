// ============================================================
// PRE-GUARD AI — CONTENT SCRIPT
// Version: 0.8.0
// ============================================================

let currentLink = null;
let tooltip = null;

let requestCounter = 0;

// True when a click warning is being displayed.
let clickWarningActive = false;


// ============================================================
// CREATE TOOLTIP
// ============================================================

function createTooltip() {

    if (
        tooltip &&
        document.body.contains(tooltip)
    ) {
        return tooltip;
    }

    tooltip =
        document.createElement("div");

    tooltip.id =
        "pre-guard-tooltip";

    Object.assign(
        tooltip.style,
        {
            position: "fixed",
            zIndex: "2147483647",
            padding: "14px",
            borderRadius: "10px",
            fontFamily: "Arial, sans-serif",
            fontSize: "13px",
            lineHeight: "1.4",
            background: "#111827",
            color: "#ffffff",
            boxShadow:
                "0 5px 20px rgba(0,0,0,0.30)",
            minWidth: "240px",
            maxWidth: "450px",
            display: "none"
        }
    );

    document.body.appendChild(
        tooltip
    );

    return tooltip;
}


// ============================================================
// HIDE TOOLTIP
// ============================================================

function hideTooltip() {

    if (!tooltip) {
        return;
    }

    tooltip.style.display =
        "none";
}


// ============================================================
// GET LINK
// ============================================================

function getLink(event) {

    if (
        !event ||
        !event.target
    ) {
        return null;
    }

    if (
        !(event.target instanceof Element)
    ) {
        return null;
    }

    return event.target.closest("a");
}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHtml(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ============================================================
// SHOW ANALYZING
// ============================================================

function showAnalyzing(x, y) {

    const box =
        createTooltip();

    box.innerHTML = `
        <strong>
            🛡️ PRE-GUARD
        </strong>

        <br><br>

        Analyzing URL...
    `;

    box.style.left =
        `${x + 12}px`;

    box.style.top =
        `${y + 12}px`;

    box.style.transform =
        "none";

    box.style.display =
        "block";
}


// ============================================================
// SHOW RISK
// ============================================================

function showRisk(
    result,
    x,
    y
) {

    const box =
        createTooltip();

    const percentage =
        Number(
            result.risk_percentage || 0
        );

    const classification =
        result.classification ||
        "UNKNOWN";


    let icon = "🟢";


    if (
        classification ===
        "SUSPICIOUS"
    ) {
        icon = "🟡";
    }


    if (
        classification ===
        "HIGH_RISK"
    ) {
        icon = "🔴";
    }


    box.innerHTML = `
        <strong>
            🛡️ PRE-GUARD
        </strong>

        <br><br>

        ${icon}
        <strong>
            ${escapeHtml(classification)}
        </strong>

        <br>

        Risk:
        ${percentage.toFixed(2)}%
    `;


    box.style.left =
        `${x + 12}px`;

    box.style.top =
        `${y + 12}px`;

    box.style.transform =
        "none";

    box.style.display =
        "block";
}


// ============================================================
// SEND FEEDBACK
// ============================================================

function sendFeedback(
    url,
    label
) {

    if (!url) {

        console.error(
            "PRE-GUARD: Cannot save feedback. URL is empty."
        );

        return;
    }


    if (
        label !== 0 &&
        label !== 1
    ) {

        console.error(
            "PRE-GUARD: Invalid feedback label."
        );

        return;
    }


    if (!chrome.runtime?.id) {

        console.error(
            "PRE-GUARD: Extension context invalid."
        );

        return;
    }


    chrome.runtime.sendMessage(
        {
            type: "SAVE_FEEDBACK",

            url: String(url),

            label: Number(label)
        },

        response => {

            if (
                chrome.runtime.lastError
            ) {

                console.error(
                    "PRE-GUARD feedback error:",
                    chrome.runtime.lastError.message
                );

                return;
            }


            if (
                !response ||
                !response.success
            ) {

                console.error(
                    "PRE-GUARD feedback failed:",
                    response?.error
                );

                return;
            }


            console.log(
                "PRE-GUARD feedback saved:",
                url,
                label
            );
        }
    );
}


// ============================================================
// ANALYZE URL
// ============================================================

function analyzeUrl(
    url,
    x,
    y
) {

    if (!url) {

        console.error(
            "PRE-GUARD: analyzeUrl received empty URL."
        );

        return;
    }


    if (!chrome.runtime?.id) {

        console.error(
            "PRE-GUARD: Extension context invalid."
        );

        return;
    }


    const requestId =
        ++requestCounter;


    showAnalyzing(
        x,
        y
    );


    chrome.runtime.sendMessage(
        {
            type: "ANALYZE_URL",

            url: String(url)
        },

        response => {

            // -----------------------------------------------
            // OLD REQUEST
            // -----------------------------------------------

            if (
                requestId !==
                requestCounter
            ) {
                return;
            }


            // -----------------------------------------------
            // RUNTIME ERROR
            // -----------------------------------------------

            if (
                chrome.runtime.lastError
            ) {

                console.error(
                    "PRE-GUARD runtime error:",
                    chrome.runtime.lastError.message
                );

                hideTooltip();

                return;
            }


            // -----------------------------------------------
            // INVALID RESPONSE
            // -----------------------------------------------

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


            const result =
                response.result;


            // -----------------------------------------------
            // UNCERTAIN
            // -----------------------------------------------

            if (
                result.risk_score >= 0.30 &&
                result.risk_score <= 0.70
            ) {

                showUncertain(
                    result,
                    url,
                    x,
                    y
                );

                return;
            }


            // -----------------------------------------------
            // NORMAL
            // -----------------------------------------------

            showRisk(
                result,
                x,
                y
            );
        }
    );
}


// ============================================================
// UNCERTAIN HOVER
// ============================================================

function showUncertain(
    result,
    url,
    x,
    y
) {

    const box =
        createTooltip();


    const percentage =
        Number(
            result.risk_percentage || 0
        );


    box.innerHTML = `
        <strong>
            🛡️ PRE-GUARD
        </strong>

        <br><br>

        🟡
        <strong>
            UNCERTAIN
        </strong>

        <br>

        Risk:
        ${percentage.toFixed(2)}%

        <br><br>

        Was this website safe?

        <br><br>

        <button
            id="pg-safe"
            type="button"
        >
            SAFE
        </button>

        <button
            id="pg-suspicious"
            type="button"
        >
            SUSPICIOUS
        </button>
    `;


    box.style.left =
        `${x + 12}px`;

    box.style.top =
        `${y + 12}px`;

    box.style.display =
        "block";


    const safeButton =
        box.querySelector(
            "#pg-safe"
        );


    const suspiciousButton =
        box.querySelector(
            "#pg-suspicious"
        );


    if (safeButton) {

        safeButton.onclick =
            function(event) {

                event.preventDefault();
                event.stopPropagation();

                sendFeedback(
                    url,
                    0
                );

                box.innerHTML = `
                    <strong>
                        🛡️ PRE-GUARD
                    </strong>

                    <br><br>

                    ✅ Feedback saved.
                `;
            };
    }


    if (suspiciousButton) {

        suspiciousButton.onclick =
            function(event) {

                event.preventDefault();
                event.stopPropagation();

                sendFeedback(
                    url,
                    1
                );

                box.innerHTML = `
                    <strong>
                        🛡️ PRE-GUARD
                    </strong>

                    <br><br>

                    ⚠️ Feedback saved.
                `;
            };
    }
}


// ============================================================
// HOVER ENTER
// ============================================================

document.addEventListener(
    "mouseover",
    function(event) {

        // Ignore our own PRE-GUARD UI.
        if (
            tooltip &&
            tooltip.contains(event.target)
        ) {
            return;
        }


        const link =
            getLink(event);


        if (!link) {
            return;
        }


        if (
            link === currentLink
        ) {
            return;
        }


        currentLink =
            link;


        analyzeUrl(
            link.href,
            event.clientX,
            event.clientY
        );
    }
);


// ============================================================
// HOVER LEAVE
// ============================================================

document.addEventListener(
    "mouseout",
    function(event) {

        const link =
            getLink(event);


        if (!link) {
            return;
        }


        if (
            event.relatedTarget &&
            link.contains(
                event.relatedTarget
            )
        ) {
            return;
        }


        currentLink =
            null;


        requestCounter++;


        // Hover UI disappears.
        // Click warning stays.
        if (
            !clickWarningActive
        ) {

            hideTooltip();
        }
    }
);


// ============================================================
// CLICK PROTECTION
// ============================================================

document.addEventListener(
    "click",
    function(event) {

        // ------------------------------------------------
        // IGNORE CLICKS INSIDE PRE-GUARD
        // ------------------------------------------------

        if (
            tooltip &&
            tooltip.contains(event.target)
        ) {
            return;
        }


        // ------------------------------------------------
        // NORMAL LEFT CLICK ONLY
        // ------------------------------------------------

        if (
            event.button !== 0
        ) {
            return;
        }


        if (
            event.ctrlKey ||
            event.metaKey ||
            event.shiftKey ||
            event.altKey
        ) {
            return;
        }


        const link =
            getLink(event);


        if (
            !link ||
            !link.href
        ) {
            return;
        }


        const url =
            link.href;


        if (!url) {
            return;
        }


        const href =
            link.getAttribute(
                "href"
            );


        if (
            href &&
            href.startsWith("#")
        ) {
            return;
        }


        // ------------------------------------------------
        // STOP NAVIGATION
        // ------------------------------------------------

        event.preventDefault();
        event.stopPropagation();


        currentLink =
            null;


        requestCounter++;


        clickWarningActive =
            true;


        showClickChecking();


        // ------------------------------------------------
        // CHECK EXTENSION
        // ------------------------------------------------

        if (
            !chrome.runtime?.id
        ) {

            showServerError(
                url,
                "Extension context is no longer active."
            );

            return;
        }


        // ------------------------------------------------
        // ANALYZE CLICKED URL
        // ------------------------------------------------

        chrome.runtime.sendMessage(
            {
                type: "ANALYZE_URL",

                url: String(url)
            },

            response => {

                if (
                    chrome.runtime.lastError
                ) {

                    showServerError(
                        url,
                        chrome.runtime.lastError.message
                    );

                    return;
                }


                if (
                    !response ||
                    !response.success ||
                    !response.result
                ) {

                    showServerError(
                        url,
                        response?.error ||
                        "No response from AI server."
                    );

                    return;
                }


                const result =
                    response.result;


                // ----------------------------------------
                // SAFE
                // ----------------------------------------

                if (
                    result.classification ===
                    "SAFE"
                ) {

                    clickWarningActive =
                        false;

                    window.location.href =
                        url;

                    return;
                }


                // ----------------------------------------
                // SUSPICIOUS / HIGH RISK
                // ----------------------------------------

                showWarning(
                    result,
                    url
                );
            }
        );
    },

    true
);


// ============================================================
// CLICK CHECKING
// ============================================================

function showClickChecking() {

    const box =
        createTooltip();


    box.innerHTML = `
        <strong>
            🛡️ PRE-GUARD AI
        </strong>

        <br><br>

        Checking destination...
    `;


    box.style.left =
        "50%";

    box.style.top =
        "20px";

    box.style.transform =
        "translateX(-50%)";

    box.style.display =
        "block";
}


// ============================================================
// SERVER ERROR
// ============================================================

function showServerError(
    url,
    message
) {

    clickWarningActive =
        true;


    const box =
        createTooltip();


    box.innerHTML = `
        <strong>
            🛡️ PRE-GUARD AI
        </strong>

        <br><br>

        ⚠️ Unable to analyze this URL.

        <br><br>

        <small>
            ${escapeHtml(message)}
        </small>

        <br><br>

        <button
            id="pg-server-back"
            type="button"
        >
            GO BACK
        </button>

        <button
            id="pg-server-continue"
            type="button"
        >
            CONTINUE
        </button>
    `;


    box.style.left =
        "50%";

    box.style.top =
        "20px";

    box.style.transform =
        "translateX(-50%)";

    box.style.display =
        "block";


    const backButton =
        box.querySelector(
            "#pg-server-back"
        );


    const continueButton =
        box.querySelector(
            "#pg-server-continue"
        );


    if (backButton) {

        backButton.onclick =
            function(event) {

                event.preventDefault();
                event.stopPropagation();

                clickWarningActive =
                    false;

                hideTooltip();
            };
    }


    if (continueButton) {

        continueButton.onclick =
            function(event) {

                event.preventDefault();
                event.stopPropagation();

                clickWarningActive =
                    false;

                window.location.href =
                    url;
            };
    }
}


// ============================================================
// HIGH-RISK WARNING
// ============================================================

function showWarning(
    result,
    url
) {

    clickWarningActive =
        true;


    const box =
        createTooltip();


    const percentage =
        Number(
            result.risk_percentage || 0
        );


    const classification =
        result.classification ||
        "HIGH_RISK";


    box.innerHTML = `
        <strong>
            🛡️ PRE-GUARD AI
        </strong>

        <br><br>

        🔴
        <strong>
            WARNING
        </strong>

        <br><br>

        This destination may be unsafe.

        <br><br>

        <strong>
            Risk:
        </strong>

        ${percentage.toFixed(2)}%

        <br>

        <strong>
            Classification:
        </strong>

        ${escapeHtml(classification)}

        <br><br>

        <div style="
            word-break: break-all;
            font-size: 12px;
            opacity: 0.8;
        ">
            ${escapeHtml(url)}
        </div>

        <br>

        Are you sure you want
        to continue?

        <br><br>

        <button
            id="pg-go-back"
            type="button"
        >
            ← GO BACK
        </button>

        <button
            id="pg-continue"
            type="button"
        >
            CONTINUE
        </button>
    `;


    box.style.left =
        "50%";

    box.style.top =
        "50%";

    box.style.transform =
        "translate(-50%, -50%)";

    box.style.width =
        "min(450px, 85vw)";

    box.style.display =
        "block";


    const backButton =
        box.querySelector(
            "#pg-go-back"
        );


    const continueButton =
        box.querySelector(
            "#pg-continue"
        );


    // ------------------------------------------------
    // GO BACK
    // ------------------------------------------------

    if (backButton) {

        backButton.onclick =
            function(event) {

                event.preventDefault();
                event.stopPropagation();

                clickWarningActive =
                    false;

                hideTooltip();
            };
    }


    // ------------------------------------------------
    // CONTINUE
    // ------------------------------------------------

    if (continueButton) {

        continueButton.onclick =
            function(event) {

                event.preventDefault();
                event.stopPropagation();

                // Open first.
                clickWarningActive =
                    false;

                clickWarningActive = false;
                storePendingFeedback(url);
            };
    }
}

// ============================================================
// STORE PENDING FEEDBACK
// ============================================================

function storePendingFeedback(url) {

    if (!url) {
        console.error(
            "PRE-GUARD: Cannot store empty URL."
        );
        return;
    }

    chrome.storage.session.set(
        {
            preGuardPendingFeedback: {
                url: String(url),
                timestamp: Date.now()
            }
        },
        () => {

            if (chrome.runtime.lastError) {

                console.error(
                    "PRE-GUARD storage error:",
                    chrome.runtime.lastError.message
                );

                return;
            }

            console.log(
                "PRE-GUARD pending feedback stored:",
                url
            );

            window.location.href = url;
        }
    );
}

// ============================================================
// CHECK FOR PENDING FEEDBACK
// ============================================================

function checkPendingFeedback() {

    if (!chrome.runtime?.id) {
        return;
    }

    chrome.storage.session.get(
        "preGuardPendingFeedback",
        data => {

            if (chrome.runtime.lastError) {

                console.error(
                    "PRE-GUARD storage read error:",
                    chrome.runtime.lastError.message
                );

                return;
            }

            const pending =
                data.preGuardPendingFeedback;

            if (!pending) {
                return;
            }

            if (!pending.url) {
                return;
            }

            // Only show feedback for the URL
            // that was actually opened.
            const currentUrl =
                window.location.href;

            if (
                pending.url !== currentUrl
            ) {

                return;
            }

            showPostNavigationFeedback(
                pending.url
            );
        }
    );
}
// ============================================================
// POST-NAVIGATION FEEDBACK
// ============================================================

function showPostNavigationFeedback(url) {

    const box =
        createTooltip();

    box.innerHTML = `
        <strong>
            🛡️ PRE-GUARD AI
        </strong>

        <br><br>

        You continued to this website.

        <br><br>

        Was this URL actually safe?

        <br><br>

        <button
            id="pg-feedback-safe"
            type="button"
        >
            ✅ SAFE
        </button>

        <button
            id="pg-feedback-suspicious"
            type="button"
        >
            ⚠️ SUSPICIOUS
        </button>
    `;

    box.style.left =
        "50%";

    box.style.top =
        "20px";

    box.style.transform =
        "translateX(-50%)";

    box.style.display =
        "block";


    const safeButton =
        box.querySelector(
            "#pg-feedback-safe"
        );

    const suspiciousButton =
        box.querySelector(
            "#pg-feedback-suspicious"
        );


    // --------------------------------------------------------
    // SAFE
    // --------------------------------------------------------

    if (safeButton) {

        safeButton.onclick =
            function(event) {

                event.preventDefault();
                event.stopPropagation();

                sendFeedback(
                    url,
                    0
                );

                clearPendingFeedback();

                box.innerHTML = `
                    <strong>
                        🛡️ PRE-GUARD AI
                    </strong>

                    <br><br>

                    ✅ Thank you.

                    <br>

                    URL marked as SAFE.
                `;

                setTimeout(
                    hideTooltip,
                    2000
                );
            };
    }


    // --------------------------------------------------------
    // SUSPICIOUS
    // --------------------------------------------------------

    if (suspiciousButton) {

        suspiciousButton.onclick =
            function(event) {

                event.preventDefault();
                event.stopPropagation();

                sendFeedback(
                    url,
                    1
                );

                clearPendingFeedback();

                box.innerHTML = `
                    <strong>
                        🛡️ PRE-GUARD AI
                    </strong>

                    <br><br>

                    ⚠️ Thank you.

                    <br>

                    URL marked as SUSPICIOUS.
                `;

                setTimeout(
                    hideTooltip,
                    2000
                );
            };
    }
}

// ============================================================
// CLEAR PENDING FEEDBACK
// ============================================================

function clearPendingFeedback() {

    chrome.storage.session.remove(
        "preGuardPendingFeedback",
        () => {

            if (chrome.runtime.lastError) {

                console.error(
                    "PRE-GUARD storage cleanup error:",
                    chrome.runtime.lastError.message
                );
            }
        }
    );
}
// ============================================================
// START POST-NAVIGATION CHECK
// ============================================================

checkPendingFeedback();