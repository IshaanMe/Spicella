import streamlit as st
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Pricing structure
PRICES = {
    "Turmeric": {"250g": 40, "500g": 75, "1kg": 140},
    "Chili": {"250g": 50, "500g": 90, "1kg": 170},
    "Coriander": {"250g": 35, "500g": 65, "1kg": 120},
    "Cumin": {"250g": 60, "500g": 110, "1kg": 200},
}
SPICES = list(PRICES.keys())
SIZES = ["250g", "500g", "1kg"]

# Google Sheets setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("creds.json", SCOPE)
client = gspread.authorize(CREDS)
sheet = client.open("Spice Orders").worksheet("Orders")  # <-- match exact sheet name

# Streamlit UI
st.set_page_config(page_title="Spice Order App", layout="wide")
st.title("🌶️ Spice Order App")

# Customer info
st.subheader("Customer Details")
name = st.text_input("Name")
phone = st.text_input("Phone Number")
address = st.text_area("Address (Optional)")

# Order input
st.subheader("Select Your Spices")
if "quantities" not in st.session_state:
    st.session_state.quantities = {f"{spice}_{size}": 0 for spice in SPICES for size in SIZES}

def increment(k): st.session_state.quantities[k] += 1
def decrement(k): st.session_state.quantities[k] = max(0, st.session_state.quantities[k] - 1)

total_amount = 0
total_quantity = 0
order = {}

for spice in SPICES:
    st.markdown(f"### {spice}")
    cols = st.columns(3)
    for i, size in enumerate(SIZES):
        key = f"{spice}_{size}"
        with cols[i]:
            st.markdown(f"**{size} (₹{PRICES[spice][size]})**")
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                st.button("➖", key=f"dec_{key}", on_click=decrement, args=(key,))
            with c2:
                st.write(st.session_state.quantities[key])
            with c3:
                st.button("➕", key=f"inc_{key}", on_click=increment, args=(key,))
        if st.session_state.quantities[key] > 0:
            order[key] = st.session_state.quantities[key]
            total_amount += st.session_state.quantities[key] * PRICES[spice][size]
            total_quantity += st.session_state.quantities[key]

# Cart summary
st.markdown("---")
st.markdown(f"🛒 **Total Items:** {total_quantity} | **Total Amount:** ₹{total_amount}")

# Final Submission
if st.button("Submit Order"):
    if not name or not phone:
        st.error("Please enter name and phone number.")
    elif total_quantity == 0:
        st.error("No spices selected.")
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for key, qty in order.items():
            spice, size = key.split("_")
            price = PRICES[spice][size]
            row = [timestamp, name, phone, address, spice, size, qty, price, total_amount]
            sheet.append_row(row)

        st.success("✅ Order submitted successfully!")
        st.session_state.quantities = {k: 0 for k in st.session_state.quantities}
