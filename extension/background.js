// ============================================================
// PRE-GUARD AI — BACKGROUND SERVICE WORKER
// Version: 0.7.3
// ============================================================

const PREDICT_API =
    "http://127.0.0.1:8000/predict";

const FEEDBACK_API =
    "http://127.0.0.1:8000/feedback";


// ============================================================
// MESSAGE LISTENER
// ============================================================

chrome.runtime.onMessage.addListener(
    (message, sender, sendResponse) => {

        // ----------------------------------------------------
        // ANALYZE URL
        // ----------------------------------------------------

        if (message.type === "ANALYZE_URL") {

            analyzeUrl(message.url)
                .then(result => {

                    sendResponse({
                        success: true,
                        result: result
                    });

                })
                .catch(error => {

                    console.error(
                        "PRE-GUARD prediction error:",
                        error
                    );

                    sendResponse({
                        success: false,
                        error: error.message
                    });

                });

            return true;
        }


        // ----------------------------------------------------
        // SAVE FEEDBACK
        // ----------------------------------------------------

        if (message.type === "SAVE_FEEDBACK") {

            saveFeedback(
                message.url,
                message.label
            )
                .then(result => {

                    sendResponse({
                        success: true,
                        result: result
                    });

                })
                .catch(error => {

                    console.error(
                        "PRE-GUARD feedback error:",
                        error
                    );

                    sendResponse({
                        success: false,
                        error: error.message
                    });

                });

            return true;
        }
    }
);


// ============================================================
// ANALYZE URL
// ============================================================

async function analyzeUrl(url) {

    if (!url) {
        throw new Error(
            "URL is empty."
        );
    }


    const response = await fetch(
        PREDICT_API,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                url: url
            })
        }
    );


    if (!response.ok) {

        throw new Error(
            `Prediction API returned ${response.status}`
        );
    }


    return await response.json();
}


// ============================================================
// SAVE FEEDBACK
// ============================================================

async function saveFeedback(
    url,
    label
) {

    if (!url) {
        throw new Error(
            "URL is empty."
        );
    }


    if (
        label !== 0 &&
        label !== 1
    ) {

        throw new Error(
            "Label must be 0 or 1."
        );
    }


    const response = await fetch(
        FEEDBACK_API,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                url: url,
                label: label
            })
        }
    );


    if (!response.ok) {

        throw new Error(
            `Feedback API returned ${response.status}`
        );
    }


    return await response.json();
}