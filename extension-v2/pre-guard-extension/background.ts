console.log("🛡️ PRE-GUARD background service loaded")

const API_URL = "http://127.0.0.1:8000/predict"

// ============================================================
// TYPES
// ============================================================

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
  timestamp: number
}

type TabNavigation = {
  chain: NavigationEntry[]
  startedAt: number
  lastCommittedUrl: string | null
}

const warningTabs = new Set<number>()

const HIGH_RISK_THRESHOLD = 70

// ============================================================
// LIVE TAB MEMORY
// ============================================================

const tabNavigations = new Map<number, TabNavigation>()

// ============================================================
// URL ANALYZER
// ============================================================

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

  return response.json()
}

// ============================================================
// ADD URL TO REDIRECT CHAIN
// ============================================================

async function addToChain(tabId: number, url: string) {
  let navigation = tabNavigations.get(tabId)

  if (!navigation) {
    navigation = {
      chain: [],
      startedAt: Date.now(),
      lastCommittedUrl: null
    }

    tabNavigations.set(tabId, navigation)
  }

  const alreadyExists = navigation.chain.some(
    (entry) => entry.url === url
  )

  if (alreadyExists) {
    return
  }

  console.log("🔎 PRE-GUARD analyzing:", url)

  try {
    const result = await analyzeURL(url)

    navigation.chain.push({
      url,
      classification: result.classification,
      risk: result.risk_percentage,
      timestamp: Date.now()
    })

    console.log(
      "🤖 AI:",
      result.classification,
      "| Risk:",
      result.risk_percentage + "%"
    )
  } catch (error) {
    console.error(
      "❌ Analysis failed:",
      error
    )
  }
}

// SHOW Redirect warning
async function showRedirectWarning(
  tabId: number,
  url: string,
  risk: number,
  classification: string
) {
  if (warningTabs.has(tabId)) {
    return
  }
  warningTabs.add(tabId)
  console.log("🚨 PRE-GUARD HIGH-RISK REDIRECT")

  console.log("URL:", url)
  console.log("Risk:", risk)
  console.log("Classification:", classification)
  const warningURL =
    chrome.runtime.getURL(
      "tabs/redirect-warning.html"
    ) +
    `?url=${encodeURIComponent(url)}` +
    `&risk=${encodeURIComponent(risk)}` +
    `&classification=${encodeURIComponent(
      classification
    )}`
  try {
    await chrome.tabs.update(
      tabId,
      {
        url: warningURL
      }
    )
    } catch (error) {
    console.error(
      "❌ Could not open PRE-GUARD warning:",
      error
    )
    warningTabs.delete(tabId)
  }
}

// ============================================================
// MESSAGE HANDLER
// ============================================================

chrome.runtime.onMessage.addListener(
  (message, sender, sendResponse) => {
    if (message?.type !== "ANALYZE_URL") {
      return
    }

    const url = message.url

    if (typeof url !== "string" || !url.trim()) {
      sendResponse({
        success: false,
        error: "URL is empty."
      })

      return
    }

    analyzeURL(url)
      .then((result) => {
        console.log("🧠 MLP RESULT:", result)

        sendResponse({
          success: true,
          result
        })
      })
      .catch((error) => {
        console.error(
          "❌ PRE-GUARD API ERROR:",
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

    return true
  }
)

// ============================================================
// NAVIGATION START
// ============================================================

chrome.webNavigation.onBeforeNavigate.addListener(
  async (details) => {
    if (details.frameId !== 0) {
      return
    }

    if (
      details.url.startsWith("chrome://") ||
      details.url.startsWith("chrome-extension://")
    ) {
      return
    }

    const existing = tabNavigations.get(details.tabId)

    const isNewNavigation =
      !existing ||
      existing.lastCommittedUrl !== details.url

    if (isNewNavigation && existing?.chain.length) {
      const lastTime =
        existing.chain[
          existing.chain.length - 1
        ].timestamp

      if (Date.now() - lastTime > 3000) {
        console.log(
          "\n🆕 NEW NAVIGATION DETECTED"
        )

        tabNavigations.set(details.tabId, {
          chain: [],
          startedAt: Date.now(),
          lastCommittedUrl: null
        })
      }
    }

    console.log(
      "\n=============================="
    )

    console.log(
      "🚀 NAVIGATION START"
    )

    console.log(
      "Tab:",
      details.tabId
    )

    console.log(
      "URL:",
      details.url
    )

    await addToChain(
      details.tabId,
      details.url
    )
  }
)

// ============================================================
// NAVIGATION COMMITTED
// ============================================================

chrome.webNavigation.onCommitted.addListener(
  async (details) => {
    if (details.frameId !== 0) {
      return
    }

    if (
      details.url.startsWith("chrome://") ||
      details.url.startsWith("chrome-extension://")
    ) {
      return
    }

    let navigation =
      tabNavigations.get(details.tabId)

    if (!navigation) {
      navigation = {
        chain: [],
        startedAt: Date.now(),
        lastCommittedUrl: null
      }

      tabNavigations.set(
        details.tabId,
        navigation
      )
    }

    navigation.lastCommittedUrl =
      details.url

    const exists =
      navigation.chain.some(
        (entry) =>
          entry.url === details.url
      )

    if (!exists) {
      await addToChain(
        details.tabId,
        details.url
      )
    }

    // 
    const currentEntry =
  navigation.chain.find(
    (entry) =>
      entry.url === details.url
  )

if (
  currentEntry &&
  currentEntry.risk >= HIGH_RISK_THRESHOLD &&
  currentEntry.classification === "HIGH_RISK"
) {
  await showRedirectWarning(
    details.tabId,
    details.url,
    currentEntry.risk,
    currentEntry.classification
  )

  return
}

    console.log(
      "\n✅ NAVIGATION COMMITTED"
    )

    console.log(
      "Final URL:",
      details.url
    )

    if (
      details.transitionQualifiers.includes(
        "server_redirect"
      )
    ) {
      console.log(
        "↪ SERVER REDIRECT DETECTED"
      )
    }

    if (
      details.transitionQualifiers.includes(
        "client_redirect"
      )
    ) {
      console.log(
        "↪ CLIENT REDIRECT DETECTED"
      )
    }

    console.log(
      "\n🛡️ REDIRECT CHAIN"
    )

    navigation.chain.forEach(
      (entry, index) => {
        console.log(
          `${index + 1}. ${entry.url}`
        )

        console.log(
          `   ${entry.classification} | ${entry.risk}%`
        )
      }
    )

    console.log(
      "=============================="
    )
  }
)

// ============================================================
// CLEAN TAB MEMORY
// ============================================================

chrome.tabs.onRemoved.addListener(
  (tabId) => {
    tabNavigations.delete(tabId)
    warningTabs.delete(tabId)

    console.log(
      "🗑️ Cleared memory for tab",
      tabId
    )
  }
)