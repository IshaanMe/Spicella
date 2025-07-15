

# 🛒 Spice Order App

This Streamlit-based app allows customers to place spice orders and enables the admin to view, filter, and download invoices for each order.

---

## 📦 Features

### Customer App (`main.py`)
- Customer must enter name and phone
- Optional address field
- Select spice quantities with `+/-` buttons like Zepto
- Auto-calculates price
- Saves order as a `.json` file

### Admin Dashboard (`admin.py`)
- Password-protected view
- Dashboard metrics: Total Orders, Customers, Revenue
- View, filter, and update order status
- Generate and download invoice as PDF

---

## 💻 How to Run

1. **Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/spice-order-app.git
cd spice-order-app
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the customer app**
```bash
streamlit run main.py
```

4. **Run the admin dashboard**
```bash
streamlit run admin.py
```

---

## 📂 Folder Structure

```
spice-order-app/
├── main.py              # Customer-facing app
├── admin.py             # Admin dashboard with PDF invoices
├── orders/              # Automatically created to store JSON orders
├── order_status.json    # Auto-updated with order status
├── requirements.txt     # Required Python packages
└── README.md            # Project description
```

---

## 🔐 Default Admin Password
`admin123` (you can change it in `admin.py`)

---

## ✅ To Deploy on Streamlit Cloud
- Push this repo to GitHub
- Go to https://streamlit.io/cloud
- Click "New App" and link your repo
- Choose `main.py` or `admin.py` to deploy separately

---

## 🧩 Next Ideas
- Google Sheets integration
- Customer invoice email/WhatsApp
- Mobile PWA-like interface

Feel free to contribute or modify!
