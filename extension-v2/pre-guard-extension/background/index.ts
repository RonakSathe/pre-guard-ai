// ============================================================
// PRE-GUARD AI — BACKGROUND SERVICE
// Version: 2.0.0
// ============================================================

console.log(
    "🛡️ PRE-GUARD background service loaded"
);


chrome.runtime.onMessage.addListener(
    (message, sender, sendResponse) => {

        console.log(
            "📨 PRE-GUARD background received:",
            message
        );


        if (
            message?.type ===
            "ANALYZE_URL"
        ) {

            const url =
                message.url;


            console.log(
                "🔍 URL received by background:",
                url
            );


            sendResponse({
                success: true,

                message:
                    "URL received by background",

                url: url
            });
        }


        return true;
    }
);