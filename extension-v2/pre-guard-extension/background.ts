console.log("PRE-GUARD backgound service loaded");

const API_URL = "http://127.0.0.1:8000/predict";

// Types
type Prediction = {
    url: string
    risk_score: number
    risk_percentage: number
    classification: string
}

type NavigationEntry = {
    url: string
    classification: string
    risk: number
    time: number
}

// LIVE REDIRECT MEMORY
const tabChains = new Map<number,NavigationEntry[]>()

// Analyze URL FUNCTION
// RESUED by hover + navigation intelligence
async function analyzeURL(url:string): Promise<Prediction> {
    const response = await fetch(API_URL, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({url})
    })

    if (!response.ok){throw new Error(`API returned HTTP ${response.status}`)}
    return await response.json()
}

// MESSAGE HANDLER


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

// Navigation Start
// Fires whenever a page starts navigating
chrome.webNavigation.onBeforeNavigate.addListener(
    async (details) =>{
        // Ignoring iframes
        if (details.frameId !== 0){return}

        // Ignoring chrome interal pages
        if ( details.url.startsWith("chrome://") || details.url.startsWith("chrome-extension://")){return}

        console.log("\n ============Navigation Start=============")
        console.log("Tab:", details.tabId)
        console.log("URL:", details.url)

        try{
            const result = await analyzeURL(details.url)
            console.log("AI: ", result.classification)
            console.log("Risk: ",result.risk_percentage)

            const chain = tabChains.get(details.tabId) ?? []

            chain.push({
                url: details.url,
                classification: result.classification,
                risk:result.risk_percentage,
                time:Date.now()
            })

            tabChains.set(details.tabId,chain)
        } catch (error){
            console.error("Navigation analysis failed:", error)
        }
    }
)

// Navigation Committed
// Detect redirects & final destination
chrome.webNavigation.onCommitted.addListener((details) => {
    if ()
})