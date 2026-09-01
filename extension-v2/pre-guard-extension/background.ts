console.log("PRE-GUARD backgound service loaded");

const API_URL = "http://127.0.0.1:8000/predict";

chrome.runtime.onMessage.addListener(
    (message,sender,sendResponse) => {
        //ANALYZE URL

        if (
            message?.type !== "ANALYZE_URL"
        ){return;}

        const url = message.url;
        console.log("PRE-GUARD analyzing", url);

        // Validating URL
        if (typeof url !== "string" || !url.trim()){
            sendResponse({
                success: false,
                error: "URL is empty."
            });
            return;
        }

        //SEND URL to FASTAPI
        fetch(API_URL,{
            method:"POST",
            headers: {
                "Content-Type":"application/json"
            },
            body: JSON.stringify({url:url})
        })


        //API RESPONSE
        .then(async response =>{
            if (!response.ok){
                throw new Error(`API returned HTTP ${response.status}`);
            }
            return response.json();
        })

        // Send  result back to content script
        .then(result => {
            console.log("PRE-GUARD MLP result:",result);
            sendResponse({
                success: true,
                result: result
            });
            
        })

        .catch(error => {

            console.error(
                "❌ PRE-GUARD API error:",
                error
            );


            sendResponse({
                success: false,
                error:
                    error instanceof Error
                        ? error.message
                        : String(error)
            });
        });


        // IMPORTANT:
        // Tell Chrome that sendResponse()
        // will happen asynchronously.
        return true;
    }
);