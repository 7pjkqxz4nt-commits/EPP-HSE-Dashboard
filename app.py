import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="HSE Dashboard", layout="wide")
st.title("🦺 HSE Professional Dashboard")

# =========================
# EMAIL FUNCTION
# =========================
def send_email(pdf_buffer, receiver_email):
    sender_email = st.secrets["EMAIL"]
    app_password = st.secrets["APP_PASSWORD"]

    msg = EmailMessage()
    msg['Subject'] = "HSE KPI Report"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg.set_content("Attached is the latest HSE KPI report.")

    msg.add_attachment(
        pdf_buffer.getvalue(),
        maintype='application',
        subtype='pdf',
        filename='HSE_Report.pdf'
    )

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, app_password)
        smtp.send_message(msg)

# =========================
# PDF FUNCTION
# =========================
def create_pdf(df, trend, TRIR, LTIFR, total_recordable):

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []

    # =========================
    # TITLE PAGE
    # =========================
    content.append(Paragraph("HSE EXECUTIVE REPORT", styles['Title']))
    content.append(Spacer(1, 20))

    content.append(Paragraph("Health, Safety & Environment Performance Summary", styles['Normal']))
    content.append(Spacer(1, 40))

    content.append(PageBreak())

    # =========================
    # KPI SUMMARY
    # =========================
    content.append(Paragraph("1. KPI Summary", styles['Heading2']))
    content.append(Spacer(1, 10))

    kpi_data = [
        ["Metric", "Value"],
        ["TRIR", round(TRIR, 2)],
        ["LTIFR", round(LTIFR, 2)],
        ["Total Recordable Cases", int(total_recordable)]
    ]

    table = Table(kpi_data)
    table.setStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])

    content.append(table)
    content.append(Spacer(1, 20))

    # =========================
    # INCIDENT SUMMARY
    # =========================
    content.append(Paragraph("2. Incident Breakdown", styles['Heading2']))

    content.append(Paragraph(f"LTI Cases: {df['LWDC'].sum()}", styles['Normal']))
    content.append(Paragraph(f"Medical Cases: {df['MTC'].sum()}", styles['Normal']))
    content.append(Paragraph(f"First Aid Cases: {df['FAC'].sum()}", styles['Normal']))

    content.append(Spacer(1, 20))

    # =========================
    # CHARTS
    # =========================
    content.append(Paragraph("3. Performance Trends", styles['Heading2']))
    content.append(Spacer(1, 10))

    charts = ["lti_chart.png", "trir_chart.png", "manhours_chart.png", "nearmiss_chart.png"]

    for chart in charts:
        try:
            content.append(Image(chart, width=450, height=220))
            content.append(Spacer(1, 15))
        except:
            pass

    # =========================
    # INSIGHTS
    # =========================
    content.append(Paragraph("4. Executive Insights", styles['Heading2']))
    content.append(Spacer(1, 10))

    worst_month = trend.loc[trend["LWDC"].idxmax(), "Month"]

    content.append(Paragraph(f"Highest incident month: {worst_month}", styles['Normal']))

    if TRIR < 1:
        performance = "Excellent"
    elif TRIR < 3:
        performance = "Good"
    else:
        performance = "Needs Improvement"

    content.append(Paragraph(f"Overall Performance: {performance}", styles['Normal']))

    doc.build(content)
    buffer.seek(0)

    return buffer

# =========================
# FILE UPLOAD
# =========================
file = st.file_uploader("Upload HSE KPI File", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    numeric_cols = [
        "EPP Total  Worked Man-HRs",
        "Contractor Total  Worked Man-HRs",
        "LWDC", "MTC", "FAC",
        "Near Miss Reports",
        "Number of risk assessment"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Manhours"] = df["EPP Total  Worked Man-HRs"] + df["Contractor Total  Worked Man-HRs"]

    total_manhours = df["Manhours"].sum()
    total_lti = df["LWDC"].sum()
    total_recordable = df["LWDC"].sum() + df["MTC"].sum() + df["FAC"].sum()

    TRIR = (total_recordable * 200000) / total_manhours if total_manhours else 0
    LTIFR = (total_lti * 1000000) / total_manhours if total_manhours else 0

# =========================
# KPI DISPLAY
# =========================
st.markdown("## 📊 Executive KPI Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("TRIR", round(TRIR, 2))

with col2:
    st.metric("LTIFR", round(LTIFR, 2))

with col3:
    st.metric("Total Recordable", int(total_recordable))
# =========================
# KPI CALCULATION (OUTSIDE)
# =========================
total_manhours = df["Manhours"].sum()
total_lti = df["LWDC"].sum()
total_recordable = df["LWDC"].sum() + df["MTC"].sum() + df["FAC"].sum()

TRIR = (total_recordable * 200000) / total_manhours if total_manhours else 0
LTIFR = (total_lti * 1000000) / total_manhours if total_manhours else 0


# =========================
# KPI DISPLAY
# =========================
st.markdown("## 📊 Executive KPI Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("TRIR", round(TRIR, 2))

with col2:
    st.metric("LTIFR", round(LTIFR, 2))

with col3:
    st.metric("Total Recordable", int(total_recordable))

    # =========================
    # TREND
    # =========================
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    trend = df.groupby("Month").sum(numeric_only=True).reset_index()

    trend["TRIR"] = (trend["LWDC"] + trend["MTC"] + trend["FAC"]) * 200000 / trend["Manhours"]

    st.plotly_chart(px.line(trend, x="Month", y="LWDC", title="LTI Trend"), use_container_width=True)

    st.markdown("## 🤖 Executive Insights")

worst_month = trend.loc[trend["LWDC"].idxmax(), "Month"]

st.write(f"🔴 Highest incident month: **{worst_month}**")

if TRIR < 1:
    st.write("🟢 Overall performance is **Excellent**")
elif TRIR < 3:
    st.write("🟡 Performance is **Acceptable but needs monitoring**")
else:
    st.write("🔴 Immediate action required")

    # =========================
    # REPORTING
    # =========================
    st.subheader("📄 Reporting")

    if st.button("Generate PDF"):

        # LTI
        plt.figure(figsize=(8,4))
        plt.plot(trend["Month"], trend["LWDC"], marker='o')
        plt.xticks(rotation=45)
        plt.grid()
        plt.savefig("lti_chart.png", bbox_inches="tight")
        plt.close()

        # TRIR
        plt.figure(figsize=(8,4))
        plt.plot(trend["Month"], trend["TRIR"], marker='o')
        plt.xticks(rotation=45)
        plt.grid()
        plt.savefig("trir_chart.png", bbox_inches="tight")
        plt.close()

        # Manhours
        plt.figure(figsize=(8,4))
        plt.plot(trend["Month"], trend["Manhours"], marker='o')
        plt.xticks(rotation=45)
        plt.grid()
        plt.savefig("manhours_chart.png", bbox_inches="tight")
        plt.close()

        # Near Miss
        if "Near Miss Reports" in trend.columns:
            plt.figure(figsize=(8,4))
            plt.plot(trend["Month"], trend["Near Miss Reports"], marker='o')
            plt.xticks(rotation=45)
            plt.grid()
            plt.savefig("nearmiss_chart.png", bbox_inches="tight")
            plt.close()

        pdf = create_pdf(df, trend, TRIR, LTIFR, total_recordable)
        st.session_state["pdf"] = pdf
        st.success("PDF Generated")

    if "pdf" in st.session_state:
        st.download_button("Download PDF", st.session_state["pdf"], "HSE_Report.pdf")

    email_to = st.text_input("Enter Email")

    if st.button("Send Email"):
        if "pdf" not in st.session_state:
            st.error("Generate PDF first")
        else:
            send_email(st.session_state["pdf"], email_to)
            st.success("Email sent!")
