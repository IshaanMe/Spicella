### admin.py — Admin Dashboard from Google Sheets

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from fpdf import FPDF
from io import BytesIO
from datetime import datetime, date

# Set page configuration
st.set_page_config(page_title="Admin Dashboard", layout="wide")

# Admin Login
st.title("🔐 Admin Login")
password = st.text_input("Enter Admin Password", type="password")
if password != "admin123":
    st.warning("Enter valid admin password to view orders.")
    st.stop()

st.title("📊 Spice Order Dashboard")

# Google Sheets setup
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("creds.json", scopes=SCOPE)
client = gspread.authorize(creds)
sheet = client.open("Spice Orders").worksheet("Orders")

# Pricing structure (for invoice total validation)
PRICES = {
    "Turmeric": {"250g": 40, "500g": 75, "1kg": 140},
    "Chili": {"250g": 50, "500g": 90, "1kg": 170},
    "Coriander": {"250g": 35, "500g": 65, "1kg": 120},
    "Cumin": {"250g": 60, "500g": 110, "1kg": 200},
}

# Load data from sheet
records = sheet.get_all_records()

# Dashboard summary
st.subheader("📈 Dashboard Summary")
total_orders = len(records)
total_revenue = sum(row.get("Total Amount", 0) for row in records)
unique_customers = len(set(row.get("Phone") for row in records))
today_str = date.today().strftime("%Y-%m-%d")
today_orders = [row for row in records if str(row.get("Timestamp", "")).startswith(today_str)]
todays_revenue = sum(row.get("Total Amount", 0) for row in today_orders)

cols = st.columns(3)
cols[0].metric("🛍️ Total Orders", total_orders)
cols[1].metric("👥 Unique Customers", unique_customers)
cols[2].metric("💰 Total Revenue", f"₹{total_revenue}")

cols = st.columns(2)
cols[0].metric("📅 Today's Orders", len(today_orders))
cols[1].metric("📅 Today's Revenue", f"₹{todays_revenue}")

st.markdown("---")

# Filter sidebar
st.sidebar.header("🔎 Filter Orders")
search_name = st.sidebar.text_input("Search by Name").lower()
search_phone = st.sidebar.text_input("Search by Phone")

filtered = []
for r in records:
    name = str(r.get("Name", "")).lower()
    phone = str(r.get("Phone", ""))
    if search_name and search_name not in name:
        continue
    if search_phone and search_phone not in phone:
        continue
    filtered.append(r)

if not filtered:
    st.info("No matching orders found.")
else:
    st.subheader(f"📦 Orders ({len(filtered)})")
    for i, row in enumerate(filtered):
        timestamp = row.get("Timestamp", "")
        name = row.get("Name", "")
        phone = row.get("Phone", "")
        address = row.get("Address", "")
        spice = row.get("Spice", "")
        size = row.get("Size", "")
        qty = row.get("Qty", 0)
        price = row.get("Price", 0)
        total = row.get("Total Amount", 0)

        with st.expander(f"🧾 {name} | {spice} ({size}) × {qty} | ₹{total} | {timestamp}"):
            st.markdown(f"**📞 Phone:** {phone}")
            st.markdown(f"**📍 Address:** {address if address else '-'}")
            st.markdown(f"**🕒 Time:** {timestamp}")

            st.markdown("### 🛒 Order Detail:")
            st.markdown(f"- {spice} ({size}): {qty} × ₹{price} = ₹{qty * price}")

            if st.button("📄 Download Invoice (PDF)", key=f"pdf_{i}"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, "Spice Order Invoice", ln=True, align="C")
                pdf.ln(10)

                pdf.set_font("Arial", size=12)
                pdf.cell(100, 10, f"Name: {name}", ln=True)
                pdf.cell(100, 10, f"Phone: {phone}", ln=True)
                pdf.cell(100, 10, f"Address: {address}", ln=True)
                pdf.cell(100, 10, f"Date: {timestamp}", ln=True)
                pdf.ln(5)

                pdf.set_font("Arial", 'B', 12)
                pdf.cell(80, 10, "Spice", border=1)
                pdf.cell(40, 10, "Quantity", border=1)
                pdf.cell(40, 10, "Price", border=1, ln=True)

                pdf.set_font("Arial", size=12)
                line = f"{spice} ({size})"
                pdf.cell(80, 10, line, border=1)
                pdf.cell(40, 10, str(qty), border=1)
                pdf.cell(40, 10, f"₹{qty * price}", border=1, ln=True)

                pdf.set_font("Arial", 'B', 12)
                pdf.cell(120, 10, "Total", border=1)
                pdf.cell(40, 10, f"₹{total}", border=1, ln=True)

                pdf_output = BytesIO()
                pdf.output(pdf_output)
                st.download_button(
                    label="⬇️ Download Invoice",
                    data=pdf_output.getvalue(),
                    file_name=f"invoice_{name}_{timestamp[:10]}.pdf",
                    mime="application/pdf"
                )
