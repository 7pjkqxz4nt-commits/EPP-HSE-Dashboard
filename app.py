import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🦺 HSE Enterprise Dashboard")

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

        df["Year"] = df[date_col].dt.year
        df["Month"] = df[date_col].dt.month_name()

    # =========================
    # SIDEBAR FILTERS
    # =========================
    st.sidebar.header("🔎 Filters")

    if date_col:
        selected_year = st.sidebar.multiselect(
            "Select Year",
            sorted(df["Year"].dropna().unique()),
            default=sorted(df["Year"].dropna().unique())
        )

        selected_month = st.sidebar.multiselect(
            "Select Month",
            df["Month"].dropna().unique(),
            default=df["Month"].dropna().unique()
        )

        df = df[(df["Year"].isin(selected_year)) & (df["Month"].isin(selected_month))]

    # =========================
    # KPI CALCULATIONS
    # =========================
    total_manhours = df[manhours_col].sum() if manhours_col else 0
    total_incidents = df[incident_col].sum() if incident_col else len(df)
    total_lti = df[lti_col].sum() if lti_col else 0

    TRIR = (total_incidents * 200000) / total_manhours if total_manhours else 0
    LTIFR = (total_lti * 1000000) / total_manhours if total_manhours else 0

    # =========================
    # TARGETS
    # =========================
    st.sidebar.header("🎯 KPI Targets")

    target_trir = st.sidebar.number_input("TRIR Target", value=1.0)
    target_ltifr = st.sidebar.number_input("LTIFR Target", value=0.5)
    target_incidents = st.sidebar.number_input("Incident Target", value=10)

    # =========================
    # KPI SCORE
    # =========================
    def kpi_score(actual, target):
        if target == 0:
            return 0
        return max(0, min(100, (target / actual) * 100 if actual > 0 else 100))

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
    # TREND
    # =========================
    if date_col:
        df["Month_Year"] = df[date_col].dt.to_period("M").astype(str)
        trend = df.groupby("Month_Year").sum(numeric_only=True).reset_index()

        st.subheader("📈 Trends")

        if incident_col:
            fig1 = px.line(trend, x="Month_Year", y=incident_col, title="Incident Trend")
            st.plotly_chart(fig1, use_container_width=True)

        if manhours_col:
            fig2 = px.line(trend, x="Month_Year", y=manhours_col, title="Manhours Trend")
            st.plotly_chart(fig2, use_container_width=True)

    # =========================
    # TRIR / LTIFR TREND
    # =========================
    if incident_col and manhours_col:
        trend["TRIR"] = (trend[incident_col] * 200000) / trend[manhours_col]
        trend["LTIFR"] = (trend.get(lti_col, 0) * 1000000) / trend[manhours_col] if lti_col else 0

        st.subheader("📉 TRIR & LTIFR Trend")

        fig3 = px.line(trend, x="Month_Year", y="TRIR", title="TRIR Trend")
        st.plotly_chart(fig3, use_container_width=True)

        fig4 = px.line(trend, x="Month_Year", y="LTIFR", title="LTIFR Trend")
        st.plotly_chart(fig4, use_container_width=True)

    # =========================
    # HEATMAP (IMPORTANT)
    # =========================
    st.subheader("🔥 Incident Heatmap (Month vs Year)")

    if incident_col and date_col:
        heatmap_data = df.pivot_table(
            values=incident_col,
            index="Year",
            columns="Month",
            aggfunc="sum"
        )

        fig_heatmap = px.imshow(
            heatmap_data,
            text_auto=True,
            aspect="auto",
            title="Incident Heatmap"
        )

        st.plotly_chart(fig_heatmap, use_container_width=True)

    # =========================
    # SCATTER
    # =========================
    st.subheader("📊 Incidents vs Manhours")

    if incident_col and manhours_col:
        fig5 = px.scatter(
            df,
            x=manhours_col,
            y=incident_col,
            trendline="ols",
            title="Incidents vs Manhours"
        )
        st.plotly_chart(fig5, use_container_width=True)

    # =========================
    # CUMULATIVE
    # =========================
    st.subheader("📈 Cumulative Incidents")

    if incident_col:
        trend["Cumulative"] = trend[incident_col].cumsum()

        fig6 = px.line(trend, x="Month_Year", y="Cumulative", title="Cumulative Incidents")
        st.plotly_chart(fig6, use_container_width=True)

    # =========================
    # PERFORMANCE
    # =========================
    st.subheader("🏆 Overall Performance")

    avg_score = (score_trir + score_ltifr + score_incidents) / 3

    if avg_score >= 90:
        rating = "🟢 Excellent"
    elif avg_score >= 70:
        rating = "🟡 Good"
    else:
        rating = "🔴 Needs Improvement"

    st.metric("Overall Score", f"{round(avg_score,1)}%", rating)

    # =========================
    # INSIGHTS
    # =========================
    st.subheader("🤖 Insights")

    if incident_col:
        worst = trend.loc[trend[incident_col].idxmax(), "Month_Year"]
        st.write(f"🚨 Highest incident month: **{worst}**")
