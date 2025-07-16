import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import date
from fpdf import FPDF
from io import BytesIO

# Set page config
st.set_page_config(page_title="Admin Dashboard", layout="wide")
st.title("🔐 Admin Login")

# Admin login
password = st.text_input("Enter Admin Password", type="password")
if password != "admin123":
    st.warning("Enter valid admin password to view orders.")
    st.stop()

st.title("📊 Spice Order Dashboard")

# Google Sheets connection
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("creds.json", SCOPE)
client = gspread.authorize(CREDS)
sheet = client.open("Spice Orders").worksheet("Orders")  # Must match exactly

# Read all data into DataFrame
data = sheet.get_all_records()
df = pd.DataFrame(data)

if df.empty:
    st.info("No orders found yet.")
    st.stop()

# Summary Calculations
df["Date"] = pd.to_datetime(df["Timestamp"]).dt.date
today = date.today()
total_orders = df["Phone"].nunique()
total_revenue = df["Total"].sum()
unique_customers = df["Phone"].nunique()
todays_orders = df[df["Date"] == today]
todays_revenue = todays_orders["Total"].sum()

# Dashboard Metrics
st.subheader("📈 Summary")
cols = st.columns(3)
cols[0].metric("🛍️ Total Orders", total_orders)
cols[1].metric("👥 Unique Customers", unique_customers)
cols[2].metric("💰 Total Revenue", f"₹{total_revenue}")

cols = st.columns(2)
cols[0].metric("📅 Today's Orders", len(todays_orders))
cols[1].metric("📅 Today's Revenue", f"₹{todays_revenue}")

st.markdown("---")

# Filters
st.sidebar.header("🔎 Filter Orders")
search_name = st.sidebar.text_input("Search by Name").lower()
search_phone = st.sidebar.text_input("Search by Phone")

filtered_df = df.copy()
if search_name:
    filtered_df = filtered_df[filtered_df["Name"].str.lower().str.contains(search_name)]
if search_phone:
    filtered_df = filtered_df[filtered_df["Phone"].str.contains(search_phone)]

if filtered_df.empty:
    st.info("No orders match current filters.")
else:
    grouped = filtered_df.groupby(["Timestamp", "Name", "Phone", "Address", "Total"])
    st.subheader(f"📦 Orders ({len(grouped)} shown)")
    for (ts, name, phone, addr, total), items in grouped:
        with st.expander(f"🧾 {name} | ₹{total} | {ts[:16]}"):
            st.markdown(f"**📞 Phone:** {phone}")
            st.markdown(f"**📍 Address:** {addr if addr else '-'}")
            st.markdown(f"**🕒 Time:** {ts}")

            st.markdown("### 🛒 Items:")
            for _, row in items.iterrows():
                st.markdown(f"- {row['Spice']} ({row['Size']}): {row['Quantity']} x ₹{row['Price']}")

            if st.button("📄 Download PDF Invoice", key=ts + phone):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, "Spice Order Invoice", ln=True, align="C")
                pdf.ln(10)
                pdf.set_font("Arial", size=12)
                pdf.cell(100, 10, f"Name: {name}", ln=True)
                pdf.cell(100, 10, f"Phone: {phone}", ln=True)
                pdf.cell(100, 10, f"Address: {addr if addr else 'N/A'}", ln=True)
                pdf.cell(100, 10, f"Date: {ts[:16]}", ln=True)
                pdf.ln(10)

                pdf.set_font("Arial", 'B', 12)
                pdf.cell(80, 10, "Spice", border=1)
                pdf.cell(40, 10, "Qty", border=1)
                pdf.cell(40, 10, "Price", border=1, ln=True)
                pdf.set_font("Arial", size=12)

                for _, row in items.iterrows():
                    pdf.cell(80, 10, f"{row['Spice']} ({row['Size']})", border=1)
                    pdf.cell(40, 10, str(row['Quantity']), border=1)
                    pdf.cell(40, 10, f"₹{row['Quantity'] * row['Price']}", border=1, ln=True)

                pdf.set_font("Arial", 'B', 12)
                pdf.cell(120, 10, "Total", border=1)
                pdf.cell(40, 10, f"₹{total}", border=1, ln=True)

                pdf_output = BytesIO()
                pdf.output(pdf_output)
                st.download_button(
                    label="⬇️ Download Invoice",
                    data=pdf_output.getvalue(),
                    file_name=f"invoice_{phone}_{ts[:10]}.pdf",
                    mime="application/pdf"
                )
