import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🦺 HSE Executive KPI Dashboard")

# =========================
# Upload File
# =========================
uploaded_file = st.file_uploader("Upload HSE KPI File", type=["xlsx"])

if uploaded_file:

    # =========================
    # READ FILE
    # =========================
    df = pd.read_excel(uploaded_file, header=2)
    df.columns = df.columns.astype(str).str.strip()

    # =========================
    # COLUMN DETECTION
    # =========================
    def find_col(keywords):
        for col in df.columns:
            for k in keywords:
                if k in col.lower():
                    return col
        return None

    date_col = find_col(["date"])
    manhours_col = find_col(["man", "hours"])
    lti_col = find_col(["lti"])
    incident_col = find_col(["incident", "case"])

    # =========================
    # CLEAN DATA
    # =========================
    if date_col:
        df = df[df[date_col].notna()]
        df = df[df[date_col] != "Annual Planned"]
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # =========================
    # KPI CALCULATION
    # =========================
    total_manhours = df[manhours_col].sum() if manhours_col else 0
    total_incidents = df[incident_col].sum() if incident_col else len(df)
    total_lti = df[lti_col].sum() if lti_col else 0

    TRIR = (total_incidents * 200000) / total_manhours if total_manhours else 0
    LTIFR = (total_lti * 1000000) / total_manhours if total_manhours else 0

    # =========================
    # KPI TARGET INPUT
    # =========================
    st.sidebar.header("🎯 KPI Targets")

    target_trir = st.sidebar.number_input("TRIR Target", value=1.0)
    target_ltifr = st.sidebar.number_input("LTIFR Target", value=0.5)
    target_incidents = st.sidebar.number_input("Incident Target", value=10)

    # =========================
    # TRAFFIC LIGHT FUNCTION
    # =========================
    def get_status(actual, target):
        if actual <= target:
            return "🟢 Good"
        elif actual <= target * 1.2:
            return "🟡 Warning"
        else:
            return "🔴 Critical"

    trir_status = get_status(TRIR, target_trir)
    ltifr_status = get_status(LTIFR, target_ltifr)
    incident_status = get_status(total_incidents, target_incidents)

    # =========================
    # KPI DISPLAY
    # =========================
    st.subheader("📊 KPI Performance")

    col1, col2, col3 = st.columns(3)

    col1.metric("TRIR", round(TRIR, 2), trir_status)
    col2.metric("LTIFR", round(LTIFR, 2), ltifr_status)
    col3.metric("Incidents", int(total_incidents), incident_status)

    # =========================
    # TREND ANALYSIS
    # =========================
    st.subheader("📈 KPI Trends")

    if date_col:
        df["Month"] = df[date_col].dt.to_period("M").astype(str)
        trend = df.groupby("Month").sum(numeric_only=True).reset_index()

        if incident_col:
            fig1 = px.line(trend, x="Month", y=incident_col, title="Incident Trend")
            st.plotly_chart(fig1, use_container_width=True)

        if manhours_col:
            fig2 = px.line(trend, x="Month", y=manhours_col, title="Manhours Trend")
            st.plotly_chart(fig2, use_container_width=True)

    # =========================
    # KPI VS TARGET CHART
    # =========================
    st.subheader("📊 KPI vs Target")

    kpi_df = pd.DataFrame({
        "KPI": ["TRIR", "LTIFR", "Incidents"],
        "Actual": [TRIR, LTIFR, total_incidents],
        "Target": [target_trir, target_ltifr, target_incidents]
    })

    fig3 = px.bar(kpi_df, x="KPI", y=["Actual", "Target"], barmode="group",
                  title="KPI vs Target Comparison")

    st.plotly_chart(fig3, use_container_width=True)

    # =========================
    # INSIGHTS
    # =========================
    st.subheader("🤖 Executive Insights")

    st.write(f"TRIR Status: {trir_status}")
    st.write(f"LTIFR Status: {ltifr_status}")
    st.write(f"Incident Status: {incident_status}")

    if incident_col:
        worst_month = trend.loc[trend[incident_col].idxmax(), "Month"]
        st.write(f"🚨 Highest incident month: **{worst_month}**")
