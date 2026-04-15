import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🦺 HSE Annual KPI Dashboard")

# =========================
# Upload File
# =========================
uploaded_file = st.file_uploader("Upload HSE KPI File", type=["xlsx"])

if uploaded_file:

    # =========================
    # READ FILE SAFELY
    # =========================
    try:
        df = pd.read_excel(uploaded_file, header=2)  # adjust if needed
    except:
        df = pd.read_excel(uploaded_file)

    # Clean column names
    df.columns = df.columns.astype(str).str.strip()

    st.subheader("📋 Data Preview")
    st.dataframe(df.head())

    # =========================
    # DEBUG: SHOW COLUMNS
    # =========================
    st.write("Detected Columns:", list(df.columns))

    # =========================
    # DETECT IMPORTANT COLUMNS
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
    # CLEAN DATA SAFELY
    # =========================
    if date_col:
        df = df[df[date_col].notna()]
        df = df[df[date_col] != "Annual Planned"]
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    else:
        st.warning("⚠️ No Date column detected")

    # =========================
    # KPI CALCULATIONS
    # =========================
    st.subheader("📊 HSE KPIs")

    total_manhours = df[manhours_col].sum() if manhours_col else 0
    total_incidents = df[incident_col].sum() if incident_col else len(df)
    total_lti = df[lti_col].sum() if lti_col else 0

    TRIR = (total_incidents * 200000) / total_manhours if total_manhours else 0
    LTIFR = (total_lti * 1000000) / total_manhours if total_manhours else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Manhours", int(total_manhours))
    col2.metric("Total Incidents", int(total_incidents))
    col3.metric("LTI", int(total_lti))
    col4.metric("TRIR", round(TRIR, 2))

    st.metric("LTIFR", round(LTIFR, 2))

    # =========================
    # TREND ANALYSIS
    # =========================
    st.subheader("📈 Trends")

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
        # ROLLING AVERAGE
        # =========================
        if incident_col:
            trend["Rolling Avg"] = trend[incident_col].rolling(3).mean()

            fig3 = px.line(
                trend,
                x="Month",
                y="Rolling Avg",
                title="3-Month Rolling Average"
            )
            st.plotly_chart(fig3, use_container_width=True)

    # =========================
    # KPI COMPARISON
    # =========================
    st.subheader("📊 KPI Comparison")

    numeric_cols = df.select_dtypes(include="number").columns

    if len(numeric_cols) > 0 and date_col:
        selected_kpi = st.selectbox("Select KPI", numeric_cols)

        fig4 = px.bar(df, x=date_col, y=selected_kpi, title=f"{selected_kpi} Over Time")
        st.plotly_chart(fig4, use_container_width=True)

    # =========================
    # YEARLY ANALYSIS
    # =========================
    if date_col:
        st.subheader("📅 Yearly Analysis")

        df["Year"] = df[date_col].dt.year
        yearly = df.groupby("Year").sum(numeric_only=True).reset_index()

        if manhours_col:
            fig5 = px.bar(yearly, x="Year", y=manhours_col, title="Yearly Manhours")
            st.plotly_chart(fig5, use_container_width=True)

    # =========================
    # INSIGHTS
    # =========================
    st.subheader("🤖 Insights")

    if date_col and incident_col:
        worst_month = trend.loc[trend[incident_col].idxmax(), "Month"]
        st.write(f"🚨 Highest incidents in: **{worst_month}**")

    if date_col and manhours_col:
        best_month = trend.loc[trend[manhours_col].idxmax(), "Month"]
        st.write(f"🏆 Highest manhours in: **{best_month}**")

    st.write(f"Total records analyzed: {len(df)}")
