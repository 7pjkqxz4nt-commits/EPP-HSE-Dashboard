import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🦺 HSE KPI Dashboard (Clean Version)")

# =========================
# Upload File
# =========================
uploaded_file = st.file_uploader("Upload HSE KPI File", type=["xlsx"])

if uploaded_file:

    # =========================
    # READ CLEAN FILE
    # =========================
    df = pd.read_excel(uploaded_file)

    # Clean column names
    df.columns = df.columns.astype(str).str.strip()

    st.subheader("📋 Data Preview")
    st.dataframe(df.head())

    # =========================
    # AUTO DETECT COLUMNS
    # =========================
    def find_col(keywords):
        for col in df.columns:
            for k in keywords:
                if k in col.lower():
                    return col
        return None

    date_col = find_col(["date"])
    manhours_col = find_col(["man", "hour"])
    incident_col = find_col(["incident"])
    lti_col = find_col(["lti"])

    st.write("Detected Columns:", {
        "Date": date_col,
        "Manhours": manhours_col,
        "Incidents": incident_col,
        "LTI": lti_col
    })

    # =========================
    # VALIDATION
    # =========================
    if not date_col or not manhours_col or not incident_col:
        st.error("❌ Please check column names in your Excel file")
        st.stop()

    # =========================
    # CLEAN DATA
    # =========================
    df = df[df[date_col].notna()]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    df["Year"] = df[date_col].dt.year
    df["Month"] = df[date_col].dt.month_name()
    df["Month_Year"] = df[date_col].dt.to_period("M").astype(str)

    # Convert numeric columns
    for col in [manhours_col, incident_col]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if lti_col:
        df[lti_col] = pd.to_numeric(df[lti_col], errors="coerce")

    df = df.fillna(0)

    # =========================
    # KPI CALCULATIONS
    # =========================
    total_manhours = df[manhours_col].sum()
    total_incidents = df[incident_col].sum()
    total_lti = df[lti_col].sum() if lti_col else 0

    TRIR = (total_incidents * 200000) / total_manhours if total_manhours else 0
    LTIFR = (total_lti * 1000000) / total_manhours if total_manhours else 0

    # =========================
    # KPI DISPLAY
    # =========================
    st.subheader("📊 KPIs")

    col1, col2, col3 = st.columns(3)

    col1.metric("TRIR", round(TRIR, 2))
    col2.metric("LTIFR", round(LTIFR, 2))
    col3.metric("Total Incidents", int(total_incidents))

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

    fig4 = px.imshow(heatmap, text_auto=True)
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
    # INSIGHTS
    # =========================
    st.subheader("🤖 Insights")

    worst = trend.loc[trend[incident_col].idxmax(), "Month_Year"]
    st.write(f"🚨 Highest incident month: **{worst}**")

    st.write("✔ Dashboard is now using clean structured data")
