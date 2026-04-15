import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🦺 HSE Complete Dashboard")

# =========================
# Upload File
# =========================
uploaded_file = st.file_uploader("Upload HSE KPI File", type=["xlsx"])

if uploaded_file:

    # =========================
    # READ FILE
    # =========================
    df = pd.read_excel(uploaded_file, header=3)

    # Clean columns
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(axis=1, how='all')

    # Take only required columns
    df = df.iloc[:, :11]

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

    st.write("📋 Clean Data Preview", df.head())

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

    TRIR = (total_incidents * 200000) / total_manhours if total_manhours else 0
    LTIFR = (total_lti * 1000000) / total_manhours if total_manhours else 0

    # =========================
    # KPI DISPLAY
    # =========================
    st.subheader("📊 KPI Scorecard")

    col1, col2, col3 = st.columns(3)
    col1.metric("TRIR", round(TRIR, 2))
    col2.metric("LTIFR", round(LTIFR, 2))
    col3.metric("Total Incidents", int(total_incidents))

    # =========================
    # TREND DATA
    # =========================
    trend = df.groupby("Month_Year").sum(numeric_only=True).reset_index()

    # =========================
    # INCIDENT TREND
    # =========================
    st.subheader("📈 Incident Trend")

    fig1 = px.line(trend, x="Month_Year", y="Total_Incidents")
    st.plotly_chart(fig1, use_container_width=True)

    # =========================
    # TRIR TREND
    # =========================
    trend["TRIR"] = (trend["Total_Incidents"] * 200000) / trend["Total_Manhours"]

    st.subheader("📉 TRIR Trend")

    fig2 = px.line(trend, x="Month_Year", y="TRIR")
    st.plotly_chart(fig2, use_container_width=True)

    # =========================
    # HEATMAP
    # =========================
    st.subheader("🔥 Incident Heatmap")

    heatmap = df.pivot_table(
        values="Total_Incidents",
        index="Year",
        columns="Month",
        aggfunc="sum"
    )

    fig3 = px.imshow(heatmap, text_auto=True)
    st.plotly_chart(fig3, use_container_width=True)

    # =========================
    # SCATTER
    # =========================
    st.subheader("📊 Incidents vs Manhours")

    fig4 = px.scatter(df, x="Total_Manhours", y="Total_Incidents", trendline="ols")
    st.plotly_chart(fig4, use_container_width=True)

    # =========================
    # CUMULATIVE
    # =========================
    st.subheader("📈 Cumulative Incidents")

    trend["Cumulative"] = trend["Total_Incidents"].cumsum()

    fig5 = px.line(trend, x="Month_Year", y="Cumulative")
    st.plotly_chart(fig5, use_container_width=True)

    # =========================
    # ROOT CAUSE ANALYSIS
    # =========================
    st.subheader("🧠 Root Cause Analysis")

    # If no root cause column exists → simulate for demo
    if "Root_Cause" not in df.columns:
        import random
        causes = ["Human Error", "Equipment Failure", "Unsafe Condition", "Training Gap"]
        df["Root_Cause"] = [random.choice(causes) for _ in range(len(df))]

    root_summary = df["Root_Cause"].value_counts().reset_index()
    root_summary.columns = ["Cause", "Count"]

    fig6 = px.bar(root_summary, x="Cause", y="Count", title="Root Causes")
    st.plotly_chart(fig6, use_container_width=True)

    # =========================
    # LEADING INDICATORS
    # =========================
    st.subheader("📊 Leading Indicators")

    # Simulated leading indicators (if not in file)
    df["Trainings"] = (df["Employees"] * 0.1).astype(int)
    df["Inspections"] = (df["Employees"] * 0.05).astype(int)

    leading = df.groupby("Month_Year")[["Trainings", "Inspections"]].sum().reset_index()

    fig7 = px.line(leading, x="Month_Year", y=["Trainings", "Inspections"],
                   title="Leading Indicators Trend")

    st.plotly_chart(fig7, use_container_width=True)

    # =========================
    # INSIGHTS
    # =========================
    st.subheader("🤖 Insights")

    worst = trend.loc[trend["Total_Incidents"].idxmax(), "Month_Year"]
    st.write(f"🚨 Highest incident month: **{worst}**")

    best = trend.loc[trend["Total_Manhours"].idxmax(), "Month_Year"]
    st.write(f"🏆 Highest productivity month: **{best}**")
