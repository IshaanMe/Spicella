### admin.py — Admin Dashboard (Google Sheets)

import streamlit as st
import pandas as pd
from datetime import datetime, date
from fpdf import FPDF
from io import BytesIO
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Admin Dashboard", layout="wide")

st.title("🔐 Admin Login")
password = st.text_input("Enter Admin Password", type="password")
if password != "admin123":
    st.warning("Enter valid admin password to view orders.")
    st.stop()

st.title("📊 Spice Order Dashboard")

# --- Google Sheets Setup ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("creds.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open("Spice Orders").worksheet("Orders")

# --- Prices ---
PRICES = {
    "Turmeric": {"250g": 40, "500g": 75, "1kg": 140},
    "Chili": {"250g": 50, "500g": 90, "1kg": 170},
    "Coriander": {"250g": 35, "500g": 65, "1kg": 120},
    "Cumin": {"250g": 60, "500g": 110, "1kg": 200},
}

# --- Load Orders ---
data = sheet.get_all_records()
if not data:
    st.info("No orders found in Google Sheet.")
    st.stop()

orders_df = pd.DataFrame(data)
orders_df["Timestamp"] = pd.to_datetime(orders_df["Timestamp"], errors='coerce')

# --- Summary ---
st.subheader("📈 Dashboard Summary")
total_orders = len(orders_df)
total_revenue = orders_df["Total"].sum()
unique_customers = orders_df["Phone"].nunique()
today = pd.to_datetime(date.today())
todays_orders = orders_df[orders_df["Timestamp"].dt.date == today.date()]
todays_revenue = todays_orders["Total"].sum()

cols = st.columns(3)
cols[0].metric("🛍️ Total Orders", total_orders)
cols[1].metric("👥 Total Customers", unique_customers)
cols[2].metric("💰 Total Revenue", f"₹{total_revenue}")

cols = st.columns(2)
cols[0].metric("📅 Today's Orders", len(todays_orders))
cols[1].metric("📅 Today's Revenue", f"₹{todays_revenue}")

st.markdown("---")

# --- Filter ---
st.sidebar.header("🔎 Filter Orders")
name_filter = st.sidebar.text_input("Search by Name").lower()
phone_filter = st.sidebar.text_input("Search by Phone")

filtered = orders_df.copy()
if name_filter:
    filtered = filtered[filtered["Name"].str.lower().str.contains(name_filter)]
if phone_filter:
    filtered = filtered[filtered["Phone"].astype(str).str.contains(phone_filter)]

if filtered.empty:
    st.info("No matching orders.")
    st.stop()

st.subheader(f"📦 Orders ({len(filtered)})")

for idx, row in filtered.iterrows():
    with st.expander(f"🧾 {row['Name']} | ₹{row['Total']} | {row['Timestamp'].strftime('%Y-%m-%d %H:%M')}"):
        st.markdown(f"**📞 Phone:** {row['Phone']}")
        st.markdown(f"**📍 Address:** {row['Address']}")

        st.markdown("### 🛒 Items:")
        items = eval(row["Order"]) if isinstance(row["Order"], str) else row["Order"]
        for item, qty in items.items():
            spice, size = item.split("_")
            st.markdown(f"- {spice} ({size}): {qty}")

        if st.button("📄 Download Invoice", key=f"invoice_{idx}"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, "Spice Order Invoice", ln=True, align="C")
            pdf.ln(10)

            pdf.set_font("Arial", size=12)
            pdf.cell(100, 10, f"Name: {row['Name']}", ln=True)
            pdf.cell(100, 10, f"Phone: {row['Phone']}", ln=True)
            pdf.cell(100, 10, f"Address: {row['Address']}", ln=True)
            pdf.cell(100, 10, f"Date: {row['Timestamp'].strftime('%Y-%m-%d %H:%M')}", ln=True)
            pdf.ln(10)

            pdf.set_font("Arial", 'B', 12)
            pdf.cell(80, 10, "Spice", border=1)
            pdf.cell(40, 10, "Quantity", border=1)
            pdf.cell(40, 10, "Price", border=1, ln=True)

            pdf.set_font("Arial", size=12)
            for item, qty in items.items():
                spice, size = item.split("_")
                price = PRICES.get(spice, {}).get(size, 0)
                pdf.cell(80, 10, f"{spice} ({size})", border=1)
                pdf.cell(40, 10, str(qty), border=1)
                pdf.cell(40, 10, f"₹{qty * price}", border=1, ln=True)

            pdf.set_font("Arial", 'B', 12)
            pdf.cell(120, 10, "Total", border=1)
            pdf.cell(40, 10, f"₹{row['Total']}", border=1, ln=True)

            pdf_output = BytesIO()
            pdf.output(pdf_output)

            st.download_button(
                label="⬇️ Download Invoice",
                data=pdf_output.getvalue(),
                file_name=f"invoice_{row['Phone']}_{row['Timestamp'].date()}.pdf",
                mime="application/pdf"
            )

st.success(f"Displayed {len(filtered)} orders.")
