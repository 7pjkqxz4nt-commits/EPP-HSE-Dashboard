import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🦺 HSE KPI Dashboard (Professional Version)")

uploaded_file = st.file_uploader("Upload Clean HSE File", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    # =========================
    # CLEAN DATA
    # =========================
    df.columns = df.columns.str.strip()

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    df["Manhours"] = pd.to_numeric(df["Manhours"], errors="coerce")
    df["Incidents"] = pd.to_numeric(df["Incidents"], errors="coerce")
    df["LTI"] = pd.to_numeric(df["LTI"], errors="coerce")

    df = df.fillna(0)

    df["Month_Year"] = df["Date"].dt.to_period("M").astype(str)

    # =========================
    # KPI
    # =========================
    total_manhours = df["Manhours"].sum()
    total_incidents = df["Incidents"].sum()
    total_lti = df["LTI"].sum()

    TRIR = (total_incidents * 1000000) / total_manhours
    LTIFR = (total_lti * 1000000) / total_manhours

    st.subheader("📊 KPIs")

    c1, c2, c3 = st.columns(3)
    c1.metric("TRIR", round(TRIR, 2))
    c2.metric("LTIFR", round(LTIFR, 2))
    c3.metric("Incidents", int(total_incidents))

    # =========================
    # TREND
    # =========================
    trend = df.groupby("Month_Year").sum().reset_index()

    st.subheader("📈 Trends")

    st.plotly_chart(px.line(trend, x="Month_Year", y="Incidents", title="Incident Trend"))
    st.plotly_chart(px.line(trend, x="Month_Year", y="Manhours", title="Manhours Trend"))

    # TRIR Trend
    trend["TRIR"] = (trend["Incidents"] * 1000000) / trend["Manhours"]

    st.plotly_chart(px.line(trend, x="Month_Year", y="TRIR", title="TRIR Trend"))

    # =========================
    # HEATMAP
    # =========================
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month_name()

    heatmap = df.pivot_table(values="Incidents", index="Year", columns="Month")

    st.subheader("🔥 Heatmap")
    st.plotly_chart(px.imshow(heatmap, text_auto=True))

    # =========================
    # INSIGHTS
    # =========================
    st.subheader("🤖 Insights")

    worst = trend.loc[trend["Incidents"].idxmax(), "Month_Year"]
    st.write(f"🚨 Highest incident month: {worst}")
