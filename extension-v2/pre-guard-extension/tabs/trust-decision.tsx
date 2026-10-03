import { useEffect, useState } from "react"

type TrustData = {
  url: string
  classification: string
  risk: number
  tabId: number
}

export default function TrustDecision() {
  const [data, setData] = useState<TrustData | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)

    const url = params.get("url")
    const classification = params.get("classification")
    const risk = params.get("risk")
    const tabId = params.get("tabId")

    if (!url || !tabId) {
      return
    }

    setData({
      url,
      classification: classification || "UNKNOWN",
      risk: Number(risk || "0"),
      tabId: Number(tabId)
    })
  }, [])

  async function trustSite() {
    if (!data || saving) {
      return
    }

    setSaving(true)

    chrome.runtime.sendMessage({
      type: "SITE_TRUST_DECISION",
      tabId: data.tabId,
      url: data.url,
      decision: "trusted"
    })
  }

  async function distrustSite() {
    if (!data || saving) {
      return
    }

    setSaving(true)

    chrome.runtime.sendMessage({
      type: "SITE_TRUST_DECISION",
      tabId: data.tabId,
      url: data.url,
      decision: "untrusted"
    })
  }

  if (!data) {
    return (
      <div style={styles.loadingPage}>
        <div style={styles.loadingTitle}>
          🛡️ PRE-GUARD AI
        </div>

        <div style={styles.loadingText}>
          Preparing security decision...
        </div>
      </div>
    )
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.icon}>🛡️</div>

        <h1 style={styles.title}>
          First Visit Detected
        </h1>

        <p style={styles.description}>
          PRE-GUARD has not seen this website before.
          Please tell us whether you trust this destination.
        </p>

        <div style={styles.urlBox}>
          <div style={styles.label}>
            FINAL DESTINATION
          </div>

          <div style={styles.url}>
            {data.url}
          </div>
        </div>

        <div style={styles.aiBox}>
          <div style={styles.label}>
            AI ANALYSIS
          </div>

          <div style={styles.classification}>
            {data.classification}
          </div>

          <div style={styles.risk}>
            Risk Score:{" "}
            <strong>
              {data.risk.toFixed(2)}%
            </strong>
          </div>
        </div>

        <div style={styles.question}>
          Do you trust this website?
        </div>

        <div style={styles.buttons}>
          <button
            onClick={trustSite}
            disabled={saving}
            style={styles.trustButton}
          >
            🟢 I Trust This Website
          </button>

          <button
            onClick={distrustSite}
            disabled={saving}
            style={styles.untrustButton}
          >
            🔴 I Don't Trust This Website
          </button>
        </div>

        <div style={styles.note}>
          Your decision will be remembered for future visits.
        </div>

        <div style={styles.footer}>
          🛡️ Protected by PRE-GUARD AI
        </div>
      </div>
    </div>
  )
}

const styles = {
  loadingPage: {
    minHeight: "100vh",
    background: "#111827",
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    justifyContent: "center",
    fontFamily: "Arial, sans-serif",
    color: "#ffffff"
  },

  loadingTitle: {
    fontSize: "30px",
    fontWeight: "bold"
  },

  loadingText: {
    marginTop: "12px",
    fontSize: "16px",
    color: "#d1d5db"
  },

  page: {
    minHeight: "100vh",
    background: "#111827",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "30px",
    boxSizing: "border-box" as const,
    fontFamily: "Arial, sans-serif"
  },

  card: {
    width: "100%",
    maxWidth: "720px",
    background: "#ffffff",
    borderRadius: "18px",
    padding: "40px",
    boxSizing: "border-box" as const,
    boxShadow: "0 20px 50px rgba(0, 0, 0, 0.4)"
  },

  icon: {
    textAlign: "center" as const,
    fontSize: "58px",
    marginBottom: "15px"
  },

  title: {
    textAlign: "center" as const,
    color: "#111827",
    fontSize: "30px",
    margin: "0 0 12px 0"
  },

  description: {
    textAlign: "center" as const,
    color: "#374151",
    fontSize: "17px",
    lineHeight: "1.6",
    marginBottom: "28px"
  },

  urlBox: {
    background: "#f3f4f6",
    borderRadius: "12px",
    padding: "18px",
    marginBottom: "18px"
  },

  aiBox: {
    background: "#eff6ff",
    border: "1px solid #bfdbfe",
    borderRadius: "12px",
    padding: "18px",
    marginBottom: "24px"
  },

  label: {
    fontSize: "12px",
    fontWeight: "bold",
    color: "#6b7280",
    marginBottom: "8px"
  },

  url: {
    fontSize: "14px",
    color: "#111827",
    wordBreak: "break-all" as const,
    lineHeight: "1.5"
  },

  classification: {
    fontSize: "22px",
    fontWeight: "bold",
    color: "#1d4ed8"
  },

  risk: {
    marginTop: "8px",
    fontSize: "15px",
    color: "#374151"
  },

  question: {
    textAlign: "center" as const,
    fontSize: "21px",
    fontWeight: "bold",
    color: "#111827",
    marginBottom: "18px"
  },

  buttons: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "12px"
  },

  trustButton: {
    width: "100%",
    padding: "16px 20px",
    borderRadius: "10px",
    border: "2px solid #15803d",
    backgroundColor: "#15803d",
    color: "#ffffff",
    fontSize: "16px",
    fontWeight: "bold",
    cursor: "pointer"
  },

  untrustButton: {
    width: "100%",
    padding: "16px 20px",
    borderRadius: "10px",
    border: "2px solid #b91c1c",
    backgroundColor: "#ffffff",
    color: "#b91c1c",
    fontSize: "16px",
    fontWeight: "bold",
    cursor: "pointer"
  },

  note: {
    textAlign: "center" as const,
    marginTop: "18px",
    fontSize: "13px",
    color: "#6b7280"
  },

  footer: {
    textAlign: "center" as const,
    marginTop: "22px",
    fontSize: "12px",
    color: "#6b7280"
  }
}