
import streamlit as st
import requests
from datetime import datetime
import pandas as pd

# ---------------------------------------------------------
# PRE-GUARD AI — DASHBOARD
# ---------------------------------------------------------

st.set_page_config(
    page_title="PRE-GUARD AI | Monitoring",
    page_icon="🛡️",
    layout="wide",
)
API_BASE_URL = "http://127.0.0.1:8000"


# ---------------------------------------------------------
# API HELPERS
# ---------------------------------------------------------

def api_get(endpoint):
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            timeout=3,
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException:
        return None


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("🛡️ PRE-GUARD AI")
st.caption("Cybersecurity Intelligence & Neural Network Monitoring")

st.divider()


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:
    st.title("PRE-GUARD")

    st.caption("MLP Threat Detection System")

    st.divider()

    st.subheader("System")

    st.write("Backend")
    st.code(API_BASE_URL)

    st.success("Live monitoring enabled")
    st.caption("Refresh interval: 2 seconds")


# ---------------------------------------------------------
# LIVE MONITORING
# ---------------------------------------------------------

@st.fragment(run_every="2s")
def live_monitoring():

    # Fetch data
    model_status = api_get("/model/status")
    training_status = api_get("/training/status")
    analytics = api_get("/analytics")
    recent_data = api_get("/analytics/recent")



    # -----------------------------------------------------
    # API CONNECTION STATUS
    # -----------------------------------------------------

    if model_status is not None:
        st.success("🟢 Backend API Connected")
    else:
        st.error("🔴 Backend API Disconnected")

    st.caption(
        f"Last dashboard refresh: {datetime.now().strftime('%H:%M:%S')}"
    )

    st.divider()

    # Threat Statistics
    st.divider()
    st.subheader("Threat Intelligence Overview")

    if analytics:

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total URLs Analyzed",
            analytics.get("total_scans", 0),
        )

        col2.metric(
            "Safe URLs",
            analytics.get("safe", 0),
            delta=f"{analytics.get('classification_percentages', {}).get('safe', 0)}%",
            delta_color="normal",
        )

        col3.metric(
            "Suspicious URLs",
            analytics.get("suspicious", 0),
            delta=f"{analytics.get('classification_percentages', {}).get('suspicious', 0)}%",
            delta_color="off",
        )

        col4.metric(
            "High-Risk URLs",
            analytics.get("high_risk", 0),
            delta=f"{analytics.get('classification_percentages', {}).get('high_risk', 0)}%",
            delta_color="inverse",
        )

        # Threat rate
        st.markdown("### Threat Rate")

        threat_rate = analytics.get("threat_rate", 0.0)

        st.progress(
            min(threat_rate / 100, 1.0),
            text=f"{threat_rate:.2f}% of analyzed URLs classified as threats",
        )

        # CLassification DIstribution
        st.markdown("### URL Classification Distribution")

        chart_data = pd.DataFrame({
            "Classification": [
                "Safe",
                "Suspicious",
                "High Risk",
            ],
            "Count": [
                analytics.get("safe", 0),
                analytics.get("suspicious", 0),
                analytics.get("high_risk", 0),
            ],
        })

        st.bar_chart(
            chart_data.set_index("Classification"),
            y="Count",
        )

        # Hourly Detection Activity
        st.markdown("### Past Hour Activities Detected")
        activity = analytics.get("hourly_activity", [])

        if activity:
            activity_df = pd.DataFrame(activity)
            activity_df["hour"] = pd.DataFrame(activity_df["hour"])
            activity_df = activity_df.sort_values("hour")
            activity_df = activity_df.set_index("hour")
            st.line_chart(activity_df["scans"])
        else:
            st.info("No Detection activity recorded yet.")


        # Recent Detection Activity
        st.markdown("### Recent Detection Activity")

        if recent_data and recent_data.get("recent_detections"):
        
            recent_df = pd.DataFrame(recent_data["recent_detections"])

            recent_df["timestamp"] = pd.to_datetime(
                recent_df["timestamp"],
                utc=True
            ).dt.tz_convert("Asia/Kolkata")

            recent_df["timestamp"] = recent_df["timestamp"].dt.strftime(
                "%d-%m-%Y %H:%M:%S"
            )

            recent_df["risk_score"] = (
                pd.to_numeric(recent_df["risk_score"]) * 100
            ).round(2)

            recent_df = recent_df.rename(
                columns={
                    "timestamp": "Time",
                    "risk_score": "Risk (%)",
                    "classification": "Classification"
                }
            )

            st.dataframe(
                recent_df,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No recent detection activity available.")


    else:
        st.warning("Analytics data unavailable.")



    # -----------------------------------------------------
    # MODEL OVERVIEW
    # -----------------------------------------------------

    st.subheader("Model Overview")

    if model_status:

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            label="Model Status",
            value="LOADED" if model_status.get("loaded") else "OFFLINE",
        )

        col2.metric(
            label="Model Architecture",
            value=model_status.get("model_type", "Unknown"),
        )

        col3.metric(
            label="Input Features",
            value=model_status.get("features", "Unknown"),
        )

        col4.metric(
            label="Training Iterations",
            value=model_status.get("iterations", "Unknown"),
        )

        # -------------------------------------------------
        # MODEL INFORMATION
        # -------------------------------------------------

        st.subheader("Model Information")

        info_col1, info_col2 = st.columns(2)

        with info_col1:
            st.write("**Model Version**")
            st.write(model_status.get("model_version", "Unknown"))

            st.write("**Loaded At**")
            st.write(model_status.get("loaded_at", "Unknown"))

        with info_col2:
            st.write("**Model Type**")
            st.write(model_status.get("model_type", "Unknown"))

            st.write("**Feature Count**")
            st.write(model_status.get("features", "Unknown"))

        with st.expander("View Full Model Status"):
            st.json(model_status)

    else:
        st.warning("Model information unavailable.")

    # -----------------------------------------------------
    # TRAINING MONITOR
    # -----------------------------------------------------

    st.divider()
    st.subheader("Training Monitor")

    if training_status:

        status = training_status.get("status", "unknown")
        stage = training_status.get("stage", "unknown")
        message = training_status.get("message", "")

        # Status indicator
        if status == "running":
            st.info("🔄 Training currently in progress")

        elif status == "completed":
            st.success("✅ Training completed successfully")

        elif status == "rejected":
            st.warning("⚠️ Candidate model rejected by quality checks")

        elif status == "failed":
            st.error("❌ Training or deployment failed")

        else:
            st.info("Training system is idle")

        # Training details
        train_col1, train_col2, train_col3 = st.columns(3)

        train_col1.metric(
            "Training Status",
            status.upper(),
        )

        train_col2.metric(
            "Current Stage",
            stage.upper(),
        )

        train_col3.metric(
            "Model Reloaded",
            "YES" if training_status.get("model_reloaded") else "NO",
        )

        st.write(message)

        with st.expander("Training Details"):
            st.json(training_status)

    else:
        st.warning("Training status unavailable.")

    # ---------------------------------------------------
    # RISK SEVERITY INDICATOR
    # ---------------------------------------------------
    st.markdown("### Risk Severity")

    threat_rate = analytics.get("threat_rate", 0)
    
    if threat_rate < 30:
        st.success(f"🟢 LOW — Threat Rate: {threat_rate}%")
        st.caption("Threat activity is currently low.")
    
    elif threat_rate < 60:
        st.warning(f"🟡 MODERATE — Threat Rate: {threat_rate}%")
        st.caption("Elevated threat activity detected.")
    
    else:
        st.error(f"🔴 HIGH — Threat Rate: {threat_rate}%")
        st.caption("High threat activity detected. Immediate attention recommended.")
    


# ---------------------------------------------------------
# RUN MONITOR
# ---------------------------------------------------------

live_monitoring()
