console.log("PRE-GUARD background service loaded")

const API_URL = "http://127.0.0.1:8000/predict"

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

const tabChains = new Map<number, NavigationEntry[]>()

// Analyze URL function

async function analyzeURL(url: string): Promise<Prediction> {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ url })
  })

  if (!response.ok) {
    throw new Error(`API returned HTTP ${response.status}`)
  }

  return await response.json()
}

// MESSAGE HANDLER

chrome.runtime.onMessage.addListener(
  (message, sender, sendResponse) => {

    if (message?.type !== "ANALYZE_URL") {
      return
    }

    const url = message.url

    console.log("PRE-GUARD analyzing:", url)

    // Validate URL

    if (typeof url !== "string" || !url.trim()) {
      sendResponse({
        success: false,
        error: "URL is empty."
      })

      return
    }

    // Send URL to FastAPI

    fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ url })
    })

      .then(async (response) => {

        if (!response.ok) {
          throw new Error(
            `API returned HTTP ${response.status}`
          )
        }

        return response.json()
      })

      .then((result) => {

        console.log(
          "PRE-GUARD MLP result:",
          result
        )

        sendResponse({
          success: true,
          result
        })
      })

      .catch((error) => {

        console.error(
          "❌ PRE-GUARD API error:",
          error
        )

        sendResponse({
          success: false,
          error:
            error instanceof Error
              ? error.message
              : String(error)
        })
      })

    // Response will be asynchronous

    return true
  }
)

// NAVIGATION START

chrome.webNavigation.onBeforeNavigate.addListener(
  async (details) => {

    // Ignore iframes

    if (details.frameId !== 0) {
      return
    }

    // Ignore Chrome internal pages

    if (
      details.url.startsWith("chrome://") ||
      details.url.startsWith("chrome-extension://")
    ) {
      return
    }

    console.log(
      "\n============ NAVIGATION START ============"
    )

    console.log("Tab:", details.tabId)
    console.log("URL:", details.url)

    try {

      const result = await analyzeURL(details.url)

      console.log(
        "AI:",
        result.classification
      )

      console.log(
        "Risk:",
        result.risk_percentage
      )

      const chain =
        tabChains.get(details.tabId) ?? []

      chain.push({
        url: details.url,
        classification: result.classification,
        risk: result.risk_percentage,
        time: Date.now()
      })

      tabChains.set(details.tabId, chain)

    } catch (error) {

      console.error(
        "Navigation analysis failed:",
        error
      )
    }
  }
)

// NAVIGATION COMMITTED

chrome.webNavigation.onCommitted.addListener(
  (details) => {

    if (details.frameId !== 0) {
      return
    }

    const chain =
      tabChains.get(details.tabId) ?? []

    console.log(
      "\n✅ NAVIGATION COMMITTED"
    )

    console.log(
      "Final URL:",
      details.url
    )

    // Detect server redirect

    if (
      details.transitionQualifiers.includes(
        "server_redirect"
      )
    ) {
      console.log(
        "↪ Server redirect detected"
      )
    }

    // Detect client redirect

    if (
      details.transitionQualifiers.includes(
        "client_redirect"
      )
    ) {
      console.log(
        "↪ Client redirect detected"
      )
    }

    console.log(
      "\n🛡️ REDIRECT CHAIN"
    )

    chain.forEach((item, index) => {

      console.log(
        `${index + 1}. ${item.url}`
      )

      console.log(
        `   ${item.classification} | ${item.risk}%`
      )
    })

    console.log(
      "────────────────────────"
    )

    console.log(
      "Destination:",
      details.url
    )
  }
)

// CLEAN MEMORY

chrome.tabs.onRemoved.addListener(
  (tabId) => {
    tabChains.delete(tabId)
  }
)