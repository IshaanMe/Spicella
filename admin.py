### admin.py — Admin Dashboard with PDF Invoice (Google Sheets Based)

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from fpdf import FPDF
from io import BytesIO
from collections import defaultdict

st.set_page_config(page_title="Admin Dashboard", layout="wide")

st.title("🔐 Admin Login")
password = st.text_input("Enter Admin Password", type="password")
if password != "admin123":
    st.warning("Enter valid admin password to view orders.")
    st.stop()

st.title("📊 Spice Order Dashboard")

# Pricing structure
PRICES = {
    "Turmeric": {"250g": 40, "500g": 75, "1kg": 140},
    "Chili": {"250g": 50, "500g": 90, "1kg": 170},
    "Coriander": {"250g": 35, "500g": 65, "1kg": 120},
    "Cumin": {"250g": 60, "500g": 110, "1kg": 200},
}

# Google Sheets Setup
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
CREDS = Credentials.from_service_account_file("creds.json", scopes=SCOPE)
client = gspread.authorize(CREDS)
sheet = client.open("Spice Orders").worksheet("Orders")
data = sheet.get_all_values()[1:]  # skip header

# Group by timestamp + phone
orders_dict = defaultdict(list)
for row in data:
    timestamp, name, phone, address, spice, size, qty, price, total = row[:9]
    key = f"{timestamp}_{phone}"
    orders_dict[key].append({
        "timestamp": timestamp,
        "name": name,
        "phone": phone,
        "address": address,
        "spice": spice,
        "size": size,
        "qty": int(qty),
        "price": int(price),
        "total_amount": int(total)
    })

# Optional: Status tracking in JSON
STATUS_FILE = "order_status.json"
if st.checkbox("🔄 Reset status cache file"):
    with open(STATUS_FILE, "w") as f:
        json.dump({}, f)

if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, "r") as f:
        status_data = json.load(f)
else:
    status_data = {}

# Compute summaries
all_orders = list(orders_dict.items())
total_orders = len(all_orders)
total_revenue = sum(sum(item["qty"] * item["price"] for item in group) for _, group in all_orders)
unique_customers = len(set(k.split("_")[1] for k in orders_dict))
today_str = date.today().strftime("%Y-%m-%d")
todays_orders = [k for k, group in orders_dict.items() if today_str in k]
todays_revenue = sum(sum(item["qty"] * item["price"] for item in orders_dict[k]) for k in todays_orders)
pending_orders = sum(1 for k in orders_dict if status_data.get(k, "Pending") == "Pending")
delivered_orders = total_orders - pending_orders

# Summary Metrics
cols = st.columns(3)
cols[0].metric("🛍️ Total Orders", total_orders)
cols[1].metric("👥 Total Customers", unique_customers)
cols[2].metric("💰 Total Revenue", f"₹{total_revenue}")
cols = st.columns(3)
cols[0].metric("📦 Pending Orders", pending_orders)
cols[1].metric("✅ Delivered Orders", delivered_orders)
cols[2].metric("📅 Today's Revenue", f"₹{todays_revenue}")

st.markdown("---")

# Filters
st.sidebar.header("🔎 Filter Orders")
status_filter = st.sidebar.selectbox("Filter by Status", ["All", "Pending", "Delivered"])
search_name = st.sidebar.text_input("Search by Name").lower()
search_phone = st.sidebar.text_input("Search by Phone")

# Show Orders
filtered_orders = []
for key, items in all_orders:
    if status_filter != "All" and status_data.get(key, "Pending") != status_filter:
        continue
    name = items[0]["name"].lower()
    phone = items[0]["phone"]
    if search_name and search_name not in name:
        continue
    if search_phone and search_phone not in phone:
        continue
    filtered_orders.append((key, items))

if not filtered_orders:
    st.info("No orders match current filters.")
else:
    for key, items in filtered_orders:
        timestamp = items[0]["timestamp"]
        name = items[0]["name"]
        phone = items[0]["phone"]
        address = items[0]["address"]
        total = sum(i["qty"] * i["price"] for i in items)

        with st.expander(f"🧾 {name} | ₹{total} | {timestamp[:16]}"):
            st.markdown(f"**📞 Phone:** {phone}")
            st.markdown(f"**📍 Address:** {address or '-'}")
            st.markdown(f"**🕒 Time:** {timestamp}")

            st.markdown("### 🛒 Order Items:")
            for item in items:
                st.markdown(f"- {item['spice']} ({item['size']}): {item['qty']} × ₹{item['price']} = ₹{item['qty']*item['price']}")

            new_status = st.radio("Update Status:", ["Pending", "Delivered"],
                                  index=0 if status_data.get(key, "Pending") == "Pending" else 1, key=key)
            status_data[key] = new_status

            if st.button("📄 Download Invoice (PDF)", key=f"pdf_{key}"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, "Spice Order Invoice", ln=True, align="C")
                pdf.set_font("Arial", size=12)
                pdf.ln(10)

                pdf.cell(100, 10, f"Name: {name}", ln=True)
                pdf.cell(100, 10, f"Phone: {phone}", ln=True)
                pdf.cell(100, 10, f"Address: {address}", ln=True)
                pdf.cell(100, 10, f"Date: {timestamp}", ln=True)
                pdf.ln(10)

                pdf.set_font("Arial", 'B', 12)
                pdf.cell(80, 10, "Spice", border=1)
                pdf.cell(40, 10, "Quantity", border=1)
                pdf.cell(40, 10, "Price", border=1, ln=True)
                pdf.set_font("Arial", size=12)

                for item in items:
                    label = f"{item['spice']} ({item['size']})"
                    pdf.cell(80, 10, label, border=1)
                    pdf.cell(40, 10, str(item['qty']), border=1)
                    pdf.cell(40, 10, f"₹{item['qty'] * item['price']}", border=1, ln=True)

                pdf.set_font("Arial", 'B', 12)
                pdf.cell(120, 10, "Total", border=1)
                pdf.cell(40, 10, f"₹{total}", border=1, ln=True)

                pdf_output = BytesIO()
                pdf.output(pdf_output)
                st.download_button(
                    label="⬇️ Download Invoice",
                    data=pdf_output.getvalue(),
                    file_name=f"invoice_{phone}_{timestamp[:10]}.pdf",
                    mime="application/pdf"
                )

with open(STATUS_FILE, "w") as f:
    json.dump(status_data, f, indent=4)

st.success(f"{len(filtered_orders)} order(s) displayed.")
