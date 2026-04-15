import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🦺 HSE Smart Dashboard (Auto Mode)")

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
    # AUTO DETECT FUNCTION
    # =========================
    def find_col(keywords):
        for col in df.columns:
            for k in keywords:
                if k in col.lower():
                    return col
        return None

    date_col = find_col(["date"])
    manhours_col = find_col(["man", "hour"])
    incident_col = find_col(["incident", "case"])
    lti_col = find_col(["lti"])

    # =========================
    # DEBUG INFO
    # =========================
    st.write("Detected Columns:")
    st.write({
        "Date": date_col,
        "Manhours": manhours_col,
        "Incidents": incident_col,
        "LTI": lti_col
    })

    # =========================
    # VALIDATION (IMPORTANT)
    # =========================
    if not date_col or not manhours_col or not incident_col:
        st.error("❌ Could not detect required columns automatically")
        st.stop()

    # =========================
    # CLEAN DATA
    # =========================
    df = df[df[date_col].notna()]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    df["Year"] = df[date_col].dt.year
    df["Month"] = df[date_col].dt.month_name()
    df["Month_Year"] = df[date_col].dt.to_period("M").astype(str)

    # =========================
    # KPI CALCULATIONS
    # =========================
    total_manhours = df[manhours_col].sum()
    total_incidents = df[incident_col].sum()
    total_lti = df[lti_col].sum() if lti_col else 0

    TRIR = (total_incidents * 200000) / total_manhours if total_manhours else 0
    LTIFR = (total_lti * 1000000) / total_manhours if total_manhours else 0

    # =========================
    # KPI TARGETS
    # =========================
    st.sidebar.header("🎯 KPI Targets")

    target_trir = st.sidebar.number_input("TRIR Target", value=1.0)
    target_ltifr = st.sidebar.number_input("LTIFR Target", value=0.5)
    target_incidents = st.sidebar.number_input("Incident Target", value=10)

    # =========================
    # KPI SCORE
    # =========================
    def kpi_score(actual, target):
        if actual == 0:
            return 100
        return max(0, min(100, (target / actual) * 100))

    score_trir = kpi_score(TRIR, target_trir)
    score_ltifr = kpi_score(LTIFR, target_ltifr)
    score_incidents = kpi_score(total_incidents, target_incidents)

    # =========================
    # KPI DISPLAY
    # =========================
    st.subheader("📊 KPI Scorecard")

    col1, col2, col3 = st.columns(3)

    col1.metric("TRIR", round(TRIR, 2), f"{round(score_trir,1)}%")
    col2.metric("LTIFR", round(LTIFR, 2), f"{round(score_ltifr,1)}%")
    col3.metric("Incidents", int(total_incidents), f"{round(score_incidents,1)}%")

    # =========================
    # TREND DATA
    # =========================
    trend = df.groupby("Month_Year").sum(numeric_only=True).reset_index()

    # =========================
    # CHARTS
    # =========================
    st.subheader("📈 Trends")

    fig1 = px.line(trend, x="Month_Year", y=incident_col, title="Incident Trend")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.line(trend, x="Month_Year", y=manhours_col, title="Manhours Trend")
    st.plotly_chart(fig2, use_container_width=True)

    # TRIR Trend
    trend["TRIR"] = (trend[incident_col] * 200000) / trend[manhours_col]

    fig3 = px.line(trend, x="Month_Year", y="TRIR", title="TRIR Trend")
    st.plotly_chart(fig3, use_container_width=True)

    # =========================
    # HEATMAP
    # =========================
    st.subheader("🔥 Incident Heatmap")

    heatmap = df.pivot_table(
        values=incident_col,
        index="Year",
        columns="Month",
        aggfunc="sum"
    )

    fig4 = px.imshow(heatmap, text_auto=True, aspect="auto")
    st.plotly_chart(fig4, use_container_width=True)

    # =========================
    # SCATTER
    # =========================
    st.subheader("📊 Incidents vs Manhours")

    fig5 = px.scatter(df, x=manhours_col, y=incident_col, trendline="ols")
    st.plotly_chart(fig5, use_container_width=True)

    # =========================
    # CUMULATIVE
    # =========================
    st.subheader("📈 Cumulative Incidents")

    trend["Cumulative"] = trend[incident_col].cumsum()

    fig6 = px.line(trend, x="Month_Year", y="Cumulative")
    st.plotly_chart(fig6, use_container_width=True)

    # =========================
    # PERFORMANCE
    # =========================
    avg_score = (score_trir + score_ltifr + score_incidents) / 3

    if avg_score >= 90:
        rating = "🟢 Excellent"
    elif avg_score >= 70:
        rating = "🟡 Good"
    else:
        rating = "🔴 Needs Improvement"

    st.subheader("🏆 Overall Performance")
    st.metric("Score", f"{round(avg_score,1)}%", rating)

    # =========================
    # INSIGHTS
    # =========================
    st.subheader("🤖 Insights")

    worst_month = trend.loc[trend[incident_col].idxmax(), "Month_Year"]
    st.write(f"🚨 Highest incident month: **{worst_month}**")
