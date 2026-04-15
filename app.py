import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🦺 HSE Enterprise KPI Dashboard")

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
    # DETECT COLUMNS
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
    # KPI CALCULATIONS
    # =========================
    total_manhours = df[manhours_col].sum() if manhours_col else 0
    total_incidents = df[incident_col].sum() if incident_col else len(df)
    total_lti = df[lti_col].sum() if lti_col else 0

    TRIR = (total_incidents * 200000) / total_manhours if total_manhours else 0
    LTIFR = (total_lti * 1000000) / total_manhours if total_manhours else 0

    # =========================
    # TARGET INPUT
    # =========================
    st.sidebar.header("🎯 KPI Targets")

    target_trir = st.sidebar.number_input("TRIR Target", value=1.0)
    target_ltifr = st.sidebar.number_input("LTIFR Target", value=0.5)
    target_incidents = st.sidebar.number_input("Incident Target", value=10)

    # =========================
    # KPI SCORE FUNCTION
    # =========================
    def kpi_score(actual, target):
        if target == 0:
            return 0
        score = max(0, min(100, (target / actual) * 100 if actual > 0 else 100))
        return round(score, 1)

    score_trir = kpi_score(TRIR, target_trir)
    score_ltifr = kpi_score(LTIFR, target_ltifr)
    score_incidents = kpi_score(total_incidents, target_incidents)

    # =========================
    # KPI DISPLAY
    # =========================
    st.subheader("📊 KPI Scorecard")

    col1, col2, col3 = st.columns(3)

    col1.metric("TRIR", round(TRIR, 2), f"Score: {score_trir}%")
    col2.metric("LTIFR", round(LTIFR, 2), f"Score: {score_ltifr}%")
    col3.metric("Incidents", int(total_incidents), f"Score: {score_incidents}%")

    # =========================
    # TREND ANALYSIS
    # =========================
    if date_col:
        df["Year"] = df[date_col].dt.year
        df["Month"] = df[date_col].dt.to_period("M").astype(str)

        trend = df.groupby("Month").sum(numeric_only=True).reset_index()
        yearly = df.groupby("Year").sum(numeric_only=True).reset_index()

        st.subheader("📈 Monthly Trend")

        if incident_col:
            fig1 = px.line(trend, x="Month", y=incident_col, title="Incident Trend")
            st.plotly_chart(fig1, use_container_width=True)

    # =========================
    # BENCHMARKING
    # =========================
    st.subheader("📊 Yearly Benchmark")

    if date_col:
        if incident_col:
            fig2 = px.bar(yearly, x="Year", y=incident_col, title="Incidents by Year")
            st.plotly_chart(fig2, use_container_width=True)

        if manhours_col:
            fig3 = px.bar(yearly, x="Year", y=manhours_col, title="Manhours by Year")
            st.plotly_chart(fig3, use_container_width=True)

    # =========================
    # PERFORMANCE RATING
    # =========================
    st.subheader("🏆 Overall Performance")

    avg_score = (score_trir + score_ltifr + score_incidents) / 3

    if avg_score >= 90:
        rating = "🟢 Excellent"
    elif avg_score >= 70:
        rating = "🟡 Good"
    else:
        rating = "🔴 Needs Improvement"

    st.metric("Overall HSE Score", f"{round(avg_score,1)}%", rating)

    # =========================
    # INSIGHTS
    # =========================
    st.subheader("🤖 Executive Insights")

    st.write(f"Overall performance rating: **{rating}**")

    if date_col and incident_col:
        worst_year = yearly.loc[yearly[incident_col].idxmax(), "Year"]
        st.write(f"🚨 Highest incident year: **{worst_year}**")
