### main.py — Customer Order App

import streamlit as st
import json
import os
from datetime import datetime

# Spice prices
PRICES = {
    "Turmeric": {"250g": 40, "500g": 75, "1kg": 140},
    "Chili": {"250g": 50, "500g": 90, "1kg": 170},
    "Coriander": {"250g": 35, "500g": 65, "1kg": 120},
    "Cumin": {"250g": 60, "500g": 110, "1kg": 200},
}

SPICES = list(PRICES.keys())
SIZES = ["250g", "500g", "1kg"]

st.set_page_config(page_title="Spice Order App", layout="wide")
st.title("🌶️ Spice Order App")

# Customer info
st.subheader("Customer Details")
name = st.text_input("Name")
phone = st.text_input("Phone Number")
address = st.text_area("Address (Optional)")

st.subheader("Select Your Spices")
order = {}
total_amount = 0
total_quantity = 0

# Helper functions
if "quantities" not in st.session_state:
    st.session_state.quantities = {f"{spice}_{size}": 0 for spice in SPICES for size in SIZES}

def increment(key):
    st.session_state.quantities[key] += 1

def decrement(key):
    st.session_state.quantities[key] = max(0, st.session_state.quantities[key] - 1)

# Inline CSS styling
st.markdown("""
<style>
    .row-box {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin-top: 4px;
    }
    .gm-label {
        font-size: 18px;
        font-weight: bold;
        padding: 2px 6px;
        min-width: 100px;
    }
    .btn-red > button {
        background-color: #ffcccc !important;
        color: #800000 !important;
        font-size: 14px !important;
        padding: 4px 8px !important;
        border-radius: 8px !important;
    }
    .btn-green > button {
        background-color: #ccffcc !important;
        color: #006600 !important;
        font-size: 14px !important;
        padding: 4px 8px !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# Spice selection
for spice in SPICES:
    st.markdown(f"<h4 style='font-size: 26px;'>{spice}</h4>", unsafe_allow_html=True)
    cols = st.columns(len(SIZES))
    for i, size in enumerate(SIZES):
        key = f"{spice}_{size}"
        with cols[i]:
            st.markdown(
                f"<div class='row-box'><div class='gm-label'>{size} (₹{PRICES[spice][size]})</div>",
                unsafe_allow_html=True)

            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                with st.container():
                    st.markdown("<div class='btn-red'>", unsafe_allow_html=True)
                    st.button("➖", key=f"decr_{key}", on_click=decrement, args=(key,), help="Decrease quantity")
                    st.markdown("</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div style='text-align:center;font-size:16px;padding-top:8px;'>{st.session_state.quantities[key]}</div>", unsafe_allow_html=True)
            with col3:
                with st.container():
                    st.markdown("<div class='btn-green'>", unsafe_allow_html=True)
                    st.button("➕", key=f"incr_{key}", on_click=increment, args=(key,), help="Increase quantity")
                    st.markdown("</div></div>", unsafe_allow_html=True)

        order[key] = st.session_state.quantities[key]
        total_amount += st.session_state.quantities[key] * PRICES[spice][size]
        total_quantity += st.session_state.quantities[key]

# Cart icon and summary
st.markdown("<hr>", unsafe_allow_html=True)
cart_col1, cart_col2 = st.columns([1, 5])
with cart_col1:
    st.markdown(f"<h3>🛒</h3>", unsafe_allow_html=True)
with cart_col2:
    st.markdown(f"<h5>{total_quantity} items | Total: ₹{total_amount}</h5>", unsafe_allow_html=True)

# Summary
st.subheader("Order Summary")
summary = {k: v for k, v in order.items() if v > 0}
if summary:
    for item, qty in summary.items():
        spice, size = item.split("_")
        price = PRICES[spice][size]
        st.write(f"{spice} - {size}: {qty} × ₹{price} = ₹{qty * price}")
    st.markdown(f"### 🧾 Total: ₹{total_amount}")
else:
    st.write("No spices selected.")

if st.button("Submit Order"):
    if not name or not phone:
        st.error("Name and phone number are required.")
    else:
        order_data = {
            "name": name,
            "phone": phone,
            "address": address,
            "order": summary,
            "total_amount": total_amount,
            "timestamp": datetime.now().isoformat()
        }
        os.makedirs("orders", exist_ok=True)
        filename = f"orders/{phone}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(order_data, f, indent=4)
        st.success("Order submitted successfully!")
