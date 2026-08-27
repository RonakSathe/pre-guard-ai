// ============================================================
// PRE-GUARD AI — CONTENT SCRIPT
// ============================================================

console.log(
    "🛡️ PRE-GUARD v2 content script loaded"
);


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


        console.log(
            "🔗 PRE-GUARD detected URL:",
            url
        );


        // ----------------------------------------------------
        // SEND URL TO BACKGROUND
        // ----------------------------------------------------

        chrome.runtime.sendMessage(
            {
                type: "ANALYZE_URL",
                url: url
            },

            (response) => {

                if (
                    chrome.runtime.lastError
                ) {

                    console.error(
                        "❌ PRE-GUARD:",
                        chrome.runtime.lastError.message
                    );

                    return;
                }


                console.log(
                    "📥 PRE-GUARD AI response:",
                    response
                );
            }
        );
    }
);