### admin.py — Admin Dashboard with PDF Invoice

import streamlit as st
import json
import os
from datetime import datetime, date
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="Admin Dashboard", layout="wide")

st.title("🔐 Admin Login")
password = st.text_input("Enter Admin Password", type="password")
if password != "admin123":
    st.warning("Enter valid admin password to view orders.")
    st.stop()

st.title("📊 Spice Order Dashboard")

ORDER_FOLDER = "orders"
STATUS_FILE = "order_status.json"

PRICES = {
    "Turmeric": {"250g": 40, "500g": 75, "1kg": 140},
    "Chili": {"250g": 50, "500g": 90, "1kg": 170},
    "Coriander": {"250g": 35, "500g": 65, "1kg": 120},
    "Cumin": {"250g": 60, "500g": 110, "1kg": 200},
}

if not os.path.exists(ORDER_FOLDER):
    os.makedirs(ORDER_FOLDER)

order_files = sorted(os.listdir(ORDER_FOLDER), reverse=True)
st.write("📂 Found order files:", order_files)  # Debug print
orders = []
for filename in order_files:
    if filename.endswith(".json"):
        with open(os.path.join(ORDER_FOLDER, filename), "r") as f:
            data = json.load(f)
            data["filename"] = filename
            orders.append(data)

if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, "r") as f:
        status_data = json.load(f)
else:
    status_data = {}

for order in orders:
    order_id = order["filename"]
    order["status"] = status_data.get(order_id, "Pending")

# Dashboard Summary
st.subheader("📈 Dashboard Summary")
total_orders = len(orders)
total_revenue = sum(o["total_amount"] for o in orders)
unique_customers = len(set(o["phone"] for o in orders))
pending_orders = sum(1 for o in orders if o["status"] == "Pending")
delivered_orders = total_orders - pending_orders
today = date.today()
todays_orders = [o for o in orders if datetime.fromisoformat(o["timestamp"]).date() == today]
todays_revenue = sum(o["total_amount"] for o in todays_orders)

cols = st.columns(3)
cols[0].metric("🛍️ Total Orders", total_orders)
cols[1].metric("👥 Total Customers", unique_customers)
cols[2].metric("💰 Total Revenue", f"₹{total_revenue}")

cols = st.columns(3)
cols[0].metric("📦 Pending Orders", pending_orders)
cols[1].metric("✅ Delivered Orders", delivered_orders)
cols[2].metric("📅 Today's Revenue", f"₹{todays_revenue}")

st.markdown("---")

st.sidebar.header("🔎 Filter Orders")
status_filter = st.sidebar.selectbox("Filter by Status", ["All", "Pending", "Delivered"])
search_name = st.sidebar.text_input("Search by Customer Name").lower()
search_phone = st.sidebar.text_input("Search by Phone")

filtered_orders = []
for order in orders:
    if status_filter != "All" and order["status"] != status_filter:
        continue
    if search_name and search_name not in order["name"].lower():
        continue
    if search_phone and search_phone not in order["phone"]:
        continue
    filtered_orders.append(order)

if not filtered_orders:
    st.info("No orders match current filters.")
else:
    st.subheader(f"📦 Orders ({len(filtered_orders)})")
    for order in filtered_orders:
        order_id = order["filename"]
        with st.expander(f"🧾 {order['name']} | ₹{order['total_amount']} | {order['timestamp'][:16]}"):
            st.markdown(f"**📞 Phone:** {order['phone']}")
            st.markdown(f"**📍 Address:** {order.get('address', '-')}")
            st.markdown(f"**🕒 Time:** {order['timestamp']}")

            st.markdown("### 🛒 Order Items:")
            for item, qty in order["order"].items():
                spice, size = item.split("_")
                st.markdown(f"- {spice} ({size}): {qty}")

            new_status = st.radio("Update Status:", ["Pending", "Delivered"],
                                   index=0 if order["status"] == "Pending" else 1, key=order_id)
            status_data[order_id] = new_status

            if st.button("📄 Download Invoice (PDF)", key=f"invoice_{order_id}"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)

                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, "Spice Order Invoice", ln=True, align="C")
                pdf.ln(10)

                pdf.set_font("Arial", size=12)
                pdf.cell(100, 10, f"Name: {order['name']}", ln=True)
                pdf.cell(100, 10, f"Phone: {order['phone']}", ln=True)
                pdf.cell(100, 10, f"Address: {order.get('address', 'N/A')}", ln=True)
                pdf.cell(100, 10, f"Date: {order['timestamp'][:16]}", ln=True)
                pdf.ln(10)

                pdf.set_font("Arial", 'B', 12)
                pdf.cell(80, 10, "Spice", border=1)
                pdf.cell(40, 10, "Quantity", border=1)
                pdf.cell(40, 10, "Price", border=1, ln=True)

                pdf.set_font("Arial", size=12)
                for item, qty in order["order"].items():
                    spice, size = item.split("_")
                    price = PRICES[spice][size]
                    line = f"{spice} ({size})"
                    pdf.cell(80, 10, line, border=1)
                    pdf.cell(40, 10, str(qty), border=1)
                    pdf.cell(40, 10, f"₹{qty * price}", border=1, ln=True)

                pdf.set_font("Arial", 'B', 12)
                pdf.cell(120, 10, "Total", border=1)
                pdf.cell(40, 10, f"₹{order['total_amount']}", border=1, ln=True)

                pdf_output = BytesIO()
                pdf.output(pdf_output)
                st.download_button(
                    label="⬇️ Download Invoice",
                    data=pdf_output.getvalue(),
                    file_name=f"invoice_{order['phone']}_{order['timestamp'][:10]}.pdf",
                    mime="application/pdf"
                )

with open(STATUS_FILE, "w") as f:
    json.dump(status_data, f, indent=4)

st.success(f"{len(filtered_orders)} order(s) displayed.")
