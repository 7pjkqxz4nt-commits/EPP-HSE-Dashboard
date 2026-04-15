import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🦺 HSE Enterprise Dashboard")

# =========================
# Upload File
# =========================
uploaded_file = st.file_uploader("Upload HSE Professional File", type=["xlsx"])

if uploaded_file:

    # =========================
    # READ SHEETS
    # =========================
    lagging = pd.read_excel(uploaded_file, sheet_name="Lagging_KPI")
    leading = pd.read_excel(uploaded_file, sheet_name="Leading_KPI")

    # =========================
    # CLEAN DATA
    # =========================
    for df in [lagging, leading]:
        df.columns = df.columns.str.strip()
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df.fillna(0, inplace=True)

    # =========================
    # KPI CALCULATIONS
    # =========================
    total_manhours = lagging["Manhours"].sum()
    total_lti = lagging["LTI"].sum()
    total_recordable = lagging[["LTI", "MTC", "FAC"]].sum().sum()

    TRIR = (total_recordable * 200000) / total_manhours if total_manhours else 0
    LTIFR = (total_lti * 1000000) / total_manhours if total_manhours else 0

    # =========================
    # KPI DISPLAY
    # =========================
    st.subheader("📊 Lagging KPIs")

    c1, c2, c3 = st.columns(3)
    c1.metric("TRIR", round(TRIR, 2))
    c2.metric("LTIFR", round(LTIFR, 2))
    c3.metric("Total Recordable Cases", int(total_recordable))

    # =========================
    # TREND ANALYSIS
    # =========================
    lagging["Month"] = lagging["Date"].dt.to_period("M").astype(str)
    trend = lagging.groupby("Month").sum(numeric_only=True).reset_index()

    st.subheader("📈 Lagging Trends")

    st.plotly_chart(
        px.line(trend, x="Month", y="LTI", title="LTI Trend"),
        use_container_width=True
    )

    st.plotly_chart(
        px.line(trend, x="Month", y="Manhours", title="Manhours Trend"),
        use_container_width=True
    )

    # TRIR Trend
    trend["TRIR"] = (trend["LTI"] * 200000) / trend["Manhours"]

    st.plotly_chart(
        px.line(trend, x="Month", y="TRIR", title="TRIR Trend"),
        use_container_width=True
    )

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
    # CORRELATION (IMPORTANT)
    # =========================
    st.subheader("📊 Safety Performance Relationship")

    merged = pd.merge(trend, lead_trend, on="Month", how="inner")

    st.plotly_chart(
        px.scatter(
            merged,
            x="Trainings",
            y="LTI",
            trendline="ols",
            title="Training vs Incidents"
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

    st.plotly_chart(
        px.imshow(heatmap, text_auto=True),
        use_container_width=True
    )

    # =========================
    # INSIGHTS
    # =========================
    st.subheader("🤖 Executive Insights")

    worst = trend.loc[trend["LTI"].idxmax(), "Month"]
    st.write(f"🚨 Highest risk month: **{worst}**")

    st.write("✔ Increasing leading indicators should reduce incidents over time")
