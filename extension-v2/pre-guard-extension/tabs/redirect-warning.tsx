import { useEffect, useState } from "react"

type WarningData = {
  url: string
  risk: number
  classification: string
  tabId: number
}

export default function RedirectWarning() {
  const [data, setData] = useState<WarningData | null>(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)

    const url = params.get("url")
    const risk = params.get("risk")
    const classification = params.get("classification")
    const tabId = params.get("tabId")

    if (!url) {
      return
    }

    setData({
      url,
      risk: Number(risk || "0"),
      classification: classification || "HIGH_RISK",
      tabId: Number(tabId || "0")
    })
  }, [])

  function goBack() {
    window.history.back()
  }

  function continueAnyway() {
    if (!data?.url) {
      return
    }

    chrome.runtime.sendMessage({
      type: "CONTINUE_ANYWAY",
      tabId: data.tabId,
      url: data.url
    
    })
  }

  async function reportSafe(){
    if (!data?.url) {return}
    try{
      const response = await fetch("http://127.0.0.1:8000/feedback",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            url: data.url,
            label: 0
          })
        }
      )
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      console.log("✅ Successfully reported safe website:", data.url)
      alert("✅ Successfully reported safe website.")
    } catch (error) {
      console.error("❌ Failed to report safe website:", error)
      alert("❌ Failed to report safe website. Please try again later.")
    }
  }

  if (!data) {
    return (
      <div style={styles.loadingPage}>
        <div style={styles.loadingText}>
          🛡️ PRE-GUARD AI
        </div>

        <div style={styles.loadingSubtext}>
          Loading security warning...
        </div>
      </div>
    )
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>

        <div style={styles.icon}>
          ⚠️
        </div>

        <h1 style={styles.title}>
          PRE-GUARD Security Warning
        </h1>

        <p style={styles.description}>
          PRE-GUARD AI detected a potentially dangerous destination.
        </p>

        <div style={styles.riskBox}>

          <div style={styles.label}>
            AI CLASSIFICATION
          </div>

          <div style={styles.classification}>
            {data.classification}
          </div>

          <div style={styles.riskText}>
            Risk Score:{" "}
            <strong>
              {data.risk.toFixed(2)}%
            </strong>
          </div>

        </div>

        <div style={styles.urlBox}>

          <div style={styles.label}>
            DESTINATION
          </div>

          <div style={styles.url}>
            {data.url}
          </div>

        </div>

        <div style={styles.warningText}>
          This website may contain phishing, malware,
          scams, or other potentially harmful content.
        </div>

        <div style={styles.buttons}>

          <button
            onClick={goBack}
            style={styles.backButton}
          >
            ← Go Back
          </button>

          <button
            onClick={continueAnyway}
            style={styles.continueButton}
          >
            Continue Anyway
          </button>

        </div>

        <button
          onClick={reportSafe}
          style={styles.safeButton}
        >
          🛡️ I trust this site — report as safe
        </button>

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

  loadingText: {
    fontSize: "30px",
    fontWeight: "bold"
  },

  loadingSubtext: {
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
    color: "#991b1b",
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

  riskBox: {
    background: "#fef2f2",
    border: "1px solid #fecaca",
    borderRadius: "12px",
    padding: "20px",
    marginBottom: "18px"
  },

  label: {
    fontSize: "12px",
    fontWeight: "bold",
    color: "#6b7280",
    marginBottom: "8px"
  },

  classification: {
    fontSize: "24px",
    fontWeight: "bold",
    color: "#b91c1c"
  },

  riskText: {
    marginTop: "8px",
    fontSize: "16px",
    color: "#7f1d1d"
  },

  urlBox: {
    background: "#f3f4f6",
    borderRadius: "12px",
    padding: "18px",
    marginBottom: "18px"
  },

  url: {
    fontSize: "14px",
    color: "#111827",
    wordBreak: "break-all" as const,
    lineHeight: "1.5"
  },

  warningText: {
    background: "#fff7ed",
    border: "1px solid #fed7aa",
    borderRadius: "10px",
    padding: "15px",
    color: "#9a3412",
    fontSize: "14px",
    lineHeight: "1.5",
    marginBottom: "25px"
  },

  buttons: {
    display: "flex",
    gap: "14px",
    width: "100%",

  },
  backButton: {
    flex: 1,
    padding: "16px 24px",
    borderRadius: "10px",
    border: "2px solid #374151",
    backgroundColor: "#ffffff",
    color: "#111827",
    fontSize: "16px",
    fontWeight: "bold",
    cursor: "pointer",
    textAlign: "center" as const
},

  continueButton: {
  flex: 1,
  padding: "16px 24px",
  borderRadius: "10px",
  border: "2px solid #b91c1c",
  backgroundColor: "#b91c1c",
  color: "#ffffff",
  fontSize: "16px",
  fontWeight: "bold",
  cursor: "pointer",
  textAlign: "center" as const
},

safeButton: {
  width: "100%",
  marginTop: "14px",
  padding: "14px 20px",
  borderRadius: "10px",
  border: "2px solid #2563eb",
  backgroundColor: "#ffffff",
  color: "#1d4ed8",
  fontSize: "15px",
  fontWeight: "bold",
  cursor: "pointer",
  textAlign: "center" as const
},

  footer: {
    textAlign: "center" as const,
    marginTop: "22px",
    fontSize: "12px",
    color: "#6b7280"
  }
}