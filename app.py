import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🦺 HSE Dashboard (Fixed for Your File)")

uploaded_file = st.file_uploader("Upload HSE KPI File", type=["xlsx"])

if uploaded_file:

    # =========================
    # READ FILE CORRECTLY
    # =========================
    df = pd.read_excel(uploaded_file, header=3)

    # Remove empty columns
    df = df.dropna(axis=1, how='all')

    st.write("Raw Columns:", df.columns)

    # =========================
    # RENAME COLUMNS MANUALLY (BASED ON YOUR FILE)
    # =========================
    df.columns = [
        "Date",
        "Month",
        "Year",
        "Employees",
        "Total_Manhours",
        "Safe_Manhours",
        "Safe_Man_Days",
        "Contractor_Employees",
        "Contractor_Manhours",
        "Total_Incidents",
        "LTI"
    ]

    st.write("Cleaned Data", df.head())

    # =========================
    # CLEAN DATA
    # =========================
    df = df[df["Date"].notna()]
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    df["Month_Year"] = df["Date"].dt.to_period("M").astype(str)

    # =========================
    # KPI CALCULATIONS
    # =========================
    total_manhours = df["Total_Manhours"].sum()
    total_incidents = df["Total_Incidents"].sum()
    total_lti = df["LTI"].sum()

    TRIR = (total_incidents * 200000) / total_manhours
    LTIFR = (total_lti * 1000000) / total_manhours

    st.subheader("📊 KPIs")

    col1, col2, col3 = st.columns(3)

    col1.metric("TRIR", round(TRIR, 2))
    col2.metric("LTIFR", round(LTIFR, 2))
    col3.metric("Incidents", int(total_incidents))

    # =========================
    # TREND DATA
    # =========================
    trend = df.groupby("Month_Year").sum(numeric_only=True).reset_index()

    # =========================
    # CHARTS
    # =========================
    st.subheader("📈 Trends")

    fig1 = px.line(trend, x="Month_Year", y="Total_Incidents", title="Incident Trend")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.line(trend, x="Month_Year", y="Total_Manhours", title="Manhours Trend")
    st.plotly_chart(fig2, use_container_width=True)

    # TRIR Trend
    trend["TRIR"] = (trend["Total_Incidents"] * 200000) / trend["Total_Manhours"]

    fig3 = px.line(trend, x="Month_Year", y="TRIR", title="TRIR Trend")
    st.plotly_chart(fig3, use_container_width=True)

    # =========================
    # HEATMAP
    # =========================
    st.subheader("🔥 Heatmap")

    heatmap = df.pivot_table(
        values="Total_Incidents",
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

    fig5 = px.scatter(df, x="Total_Manhours", y="Total_Incidents", trendline="ols")
    st.plotly_chart(fig5, use_container_width=True)

    # =========================
    # CUMULATIVE
    # =========================
    st.subheader("📈 Cumulative Incidents")

    trend["Cumulative"] = trend["Total_Incidents"].cumsum()

    fig6 = px.line(trend, x="Month_Year", y="Cumulative")
    st.plotly_chart(fig6, use_container_width=True)

    # =========================
    # INSIGHTS
    # =========================
    st.subheader("🤖 Insights")

    worst = trend.loc[trend["Total_Incidents"].idxmax(), "Month_Year"]
    st.write(f"🚨 Highest incident month: **{worst}**")
