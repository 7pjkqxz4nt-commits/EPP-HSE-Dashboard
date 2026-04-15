import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🦺 HSE Enterprise Dashboard")

uploaded_file = st.file_uploader("Upload HSE Professional File", type=["xlsx"])

if uploaded_file:

    # =========================
    # READ SHEETS
    # =========================
    try:
        lagging = pd.read_excel(uploaded_file, sheet_name="Lagging_KPI")
        leading = pd.read_excel(uploaded_file, sheet_name="Leading_KPI")
    except:
        st.error("❌ Ensure sheet names are: Lagging_KPI & Leading_KPI")
        st.stop()

    # =========================
    # CLEAN DATA
    # =========================
    for df in [lagging, leading]:
        df.columns = df.columns.str.strip()
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    lagging = lagging.fillna(0)
    leading = leading.fillna(0)

    # Ensure numeric columns
    num_cols_lag = ["Manhours", "LTI", "MTC", "FAC"]
    for col in num_cols_lag:
        lagging[col] = pd.to_numeric(lagging[col], errors="coerce").fillna(0)

    # =========================
    # KPI CALCULATIONS (FIXED)
    # =========================
    total_manhours = lagging["Manhours"].sum()
    total_lti = lagging["LTI"].sum()

    # Correct TRIR = LTI + MTC + FAC
    total_recordable = lagging[["LTI", "MTC", "FAC"]].sum(axis=1).sum()

    TRIR = (total_recordable * 200000) / total_manhours if total_manhours else 0
    LTIFR = (total_lti * 1000000) / total_manhours if total_manhours else 0

    # =========================
    # TARGETS (NEW)
    # =========================
    st.sidebar.header("🎯 KPI Targets")

    target_trir = st.sidebar.number_input("TRIR Target", value=1.0)
    target_ltifr = st.sidebar.number_input("LTIFR Target", value=0.5)

    def status(actual, target):
        if actual <= target:
            return "🟢 Good"
        elif actual <= target * 1.2:
            return "🟡 Warning"
        else:
            return "🔴 Critical"

    # =========================
    # KPI DISPLAY
    # =========================
    st.subheader("📊 Lagging KPIs")

    c1, c2, c3 = st.columns(3)

    c1.metric("TRIR", round(TRIR, 2), status(TRIR, target_trir))
    c2.metric("LTIFR", round(LTIFR, 2), status(LTIFR, target_ltifr))
    c3.metric("Total Recordable", int(total_recordable))

    # =========================
    # TREND
    # =========================
    lagging["Month"] = lagging["Date"].dt.to_period("M").astype(str)
    trend = lagging.groupby("Month").sum(numeric_only=True).reset_index()

    st.subheader("📈 Lagging Trends")

    st.plotly_chart(px.line(trend, x="Month", y="LTI", title="LTI Trend"), use_container_width=True)
    st.plotly_chart(px.line(trend, x="Month", y="Manhours", title="Manhours Trend"), use_container_width=True)

    # TRIR Trend (FIXED)
    trend["Recordable"] = trend["LTI"] + trend["MTC"] + trend["FAC"]
    trend["TRIR"] = (trend["Recordable"] * 200000) / trend["Manhours"]

    st.plotly_chart(px.line(trend, x="Month", y="TRIR", title="TRIR Trend"), use_container_width=True)

    # =========================
    # LEADING INDICATORS
    # =========================
    leading["Month"] = leading["Date"].dt.to_period("M").astype(str)
    lead_trend = leading.groupby("Month").sum(numeric_only=True).reset_index()

    st.subheader("📊 Leading Indicators")

    st.plotly_chart(
        px.line(
            lead_trend,
            x="Month",
            y=["Trainings", "Inspections", "Audits"],
            title="Leading Indicators Trend"
        ),
        use_container_width=True
    )

    # =========================
    # CORRELATION
    # =========================
    st.subheader("📊 Leading vs Lagging")

    merged = pd.merge(trend, lead_trend, on="Month", how="inner")

    st.plotly_chart(
        px.scatter(
            merged,
            x="Trainings",
            y="Recordable",
            trendline="ols",
            title="Training vs Recordable Cases"
        ),
        use_container_width=True
    )

    # =========================
    # HEATMAP
    # =========================
    lagging["Year"] = lagging["Date"].dt.year
    lagging["Month_Name"] = lagging["Date"].dt.month_name()

    heatmap = lagging.pivot_table(
        values="LTI",
        index="Year",
        columns="Month_Name",
        aggfunc="sum"
    )

    st.subheader("🔥 Risk Heatmap")
    st.plotly_chart(px.imshow(heatmap, text_auto=True), use_container_width=True)

    # =========================
    # INSIGHTS
    # =========================
    st.subheader("🤖 Executive Insights")

    worst = trend.loc[trend["Recordable"].idxmax(), "Month"]
    st.write(f"🚨 Highest risk month: **{worst}**")

    st.write("✔ Increase leading indicators to reduce incidents")
