import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from fpdf import FPDF
from io import BytesIO
from datetime import datetime, date
import json

st.set_page_config(page_title="Admin Dashboard", layout="wide")
st.title("🔐 Admin Login")

# Auth check
password = st.text_input("Enter Admin Password", type="password")
if password != "admin123":
    st.warning("Enter valid admin password to view orders.")
    st.stop()

# Google Sheets auth
creds = Credentials.from_service_account_file("creds.json", scopes=["https://www.googleapis.com/auth/spreadsheets"])
client = gspread.authorize(creds)
sheet = client.open("Spice Orders").worksheet("Orders")
data = sheet.get_all_records()

# Status file (local JSON)
STATUS_FILE = "order_status.json"
if not data:
    st.info("No orders yet.")
    st.stop()

# Read/update status tracking
if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, "r") as f:
        status_data = json.load(f)
else:
    status_data = {}

# Process orders
orders = []
for row in data:
    order_id = row.get("OrderID")
    try:
        order = {
            "filename": order_id,
            "name": row.get("Name", "-"),
            "phone": row.get("Phone", "-"),
            "address": row.get("Address", "-"),
            "timestamp": row.get("Timestamp", ""),
            "total_amount": int(row.get("Total", 0)),
            "order": json.loads(row.get("OrderData", "{}")),
            "status": status_data.get(order_id, "Pending")
        }
        orders.append(order)
    except Exception as e:
        st.warning(f"❌ Skipped order {order_id}: {e}")

# Summary metrics
st.title("📊 Spice Order Dashboard")
total_orders = len(orders)
total_revenue = sum(o["total_amount"] for o in orders)
unique_customers = len(set(o["phone"] for o in orders))
pending_orders = sum(1 for o in orders if o["status"] == "Pending")
delivered_orders = total_orders - pending_orders
today = date.today().isoformat()
todays_orders = [o for o in orders if o["timestamp"].startswith(today)]
todays_revenue = sum(o["total_amount"] for o in todays_orders)

cols = st.columns(3)
cols[0].metric("🛍️ Total Orders", total_orders)
cols[1].metric("👥 Total Customers", unique_customers)
cols[2].metric("💰 Total Revenue", f"₹{total_revenue}")

cols = st.columns(3)
cols[0].metric("📦 Pending", pending_orders)
cols[1].metric("✅ Delivered", delivered_orders)
cols[2].metric("📅 Today's Revenue", f"₹{todays_revenue}")

# Filter section
st.sidebar.header("🔎 Filter Orders")
status_filter = st.sidebar.selectbox("Status", ["All", "Pending", "Delivered"])
search_name = st.sidebar.text_input("Search Name").lower()
search_phone = st.sidebar.text_input("Search Phone")

filtered_orders = []
for o in orders:
    if status_filter != "All" and o["status"] != status_filter:
        continue
    if search_name and search_name not in o["name"].lower():
        continue
    if search_phone and search_phone not in o["phone"]:
        continue
    filtered_orders.append(o)

if not filtered_orders:
    st.info("No orders match filters.")
else:
    st.subheader(f"📦 Orders ({len(filtered_orders)})")
    for order in filtered_orders:
        with st.expander(f"🧾 {order['name']} | ₹{order['total_amount']} | {order['timestamp']}"):
            st.markdown(f"**📞 Phone:** {order['phone']}")
            st.markdown(f"**📍 Address:** {order['address']}")
            st.markdown(f"**🕒 Time:** {order['timestamp']}")
            st.markdown("### 🛒 Order Items")
            for item, qty in order["order"].items():
                spice, size = item.split("_")
                st.markdown(f"- {spice} ({size}): {qty}")

            new_status = st.radio("Update Status", ["Pending", "Delivered"],
                                  index=0 if order["status"] == "Pending" else 1,
                                  key=order["filename"])
            status_data[order["filename"]] = new_status

            if st.button("📄 Download Invoice", key="inv_" + order["filename"]):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, "Spice Order Invoice", ln=True, align="C")
                pdf.ln(10)

                pdf.set_font("Arial", size=12)
                pdf.cell(100, 10, f"Name: {order['name']}", ln=True)
                pdf.cell(100, 10, f"Phone: {order['phone']}", ln=True)
                pdf.cell(100, 10, f"Address: {order['address']}", ln=True)
                pdf.cell(100, 10, f"Date: {order['timestamp']}", ln=True)
                pdf.ln(5)

                pdf.set_font("Arial", 'B', 12)
                pdf.cell(80, 10, "Spice", border=1)
                pdf.cell(40, 10, "Qty", border=1)
                pdf.cell(40, 10, "Price", border=1, ln=True)

                pdf.set_font("Arial", size=12)
                PRICES = {
                    "Turmeric": {"250g": 40, "500g": 75, "1kg": 140},
                    "Chili": {"250g": 50, "500g": 90, "1kg": 170},
                    "Coriander": {"250g": 35, "500g": 65, "1kg": 120},
                    "Cumin": {"250g": 60, "500g": 110, "1kg": 200},
                }

                for item, qty in order["order"].items():
                    spice, size = item.split("_")
                    price = PRICES[spice][size]
                    pdf.cell(80, 10, f"{spice} ({size})", border=1)
                    pdf.cell(40, 10, str(qty), border=1)
                    pdf.cell(40, 10, f"₹{qty * price}", border=1, ln=True)

                pdf.cell(120, 10, "Total", border=1)
                pdf.cell(40, 10, f"₹{order['total_amount']}", border=1, ln=True)

                pdf_output = BytesIO()
                pdf.output(pdf_output)
                st.download_button("⬇️ Download PDF", data=pdf_output.getvalue(),
                                   file_name=f"invoice_{order['phone']}.pdf", mime="application/pdf")

# Save updated statuses
with open(STATUS_FILE, "w") as f:
    json.dump(status_data, f, indent=4)
