### main.py — Customer Order App

import streamlit as st
import json
import os
from datetime import datetime

# Spice prices
total_price = 0
PRICES = {
    "Turmeric": {"250g": 40, "500g": 75, "1kg": 140},
    "Chili": {"250g": 50, "500g": 90, "1kg": 170},
    "Coriander": {"250g": 35, "500g": 65, "1kg": 120},
    "Cumin": {"250g": 60, "500g": 110, "1kg": 200},
}

SPICES = list(PRICES.keys())
SIZES = ["250g", "500g", "1kg"]

st.title("🌶️ Spice Order App")

# Customer info
st.subheader("Customer Details")
name = st.text_input("Name")
phone = st.text_input("Phone Number")
address = st.text_area("Address (Optional)")

st.subheader("Select Your Spices")
order = {}
total_amount = 0

for spice in SPICES:
    st.markdown(f"**{spice}**")
    cols = st.columns(len(SIZES))
    for i, size in enumerate(SIZES):
        key = f"{spice}_{size}"
        if key not in st.session_state:
            st.session_state[key] = 0
        with cols[i]:
            st.button("-", key=f"decr_{key}", on_click=lambda k=key: st.session_state.update({k: max(0, st.session_state[k]-1)}))
            st.write(f"{size} (₹{PRICES[spice][size]}): {st.session_state[key]}")
            st.button("+", key=f"incr_{key}", on_click=lambda k=key: st.session_state.update({k: st.session_state[k]+1}))
        order[key] = st.session_state[key]
        total_amount += st.session_state[key] * PRICES[spice][size]

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
