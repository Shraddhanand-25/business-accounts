import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px

st.set_page_config(page_title="Business Accounts", layout="wide")
st.title("🧾 Shivanand Cloth Stores")

# Database connection
conn = sqlite3.connect('business_accounts.db', check_same_thread=False)
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, email TEXT, address TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, email TEXT, address TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS invoices (id INTEGER PRIMARY KEY, date TEXT, customer TEXT, amount REAL, status TEXT, notes TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS payables (id INTEGER PRIMARY KEY, date TEXT, supplier TEXT, amount REAL, due_date TEXT, status TEXT, notes TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS loans_credits (id INTEGER PRIMARY KEY, type TEXT, party TEXT, amount REAL, date TEXT, notes TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, date TEXT, type TEXT, party TEXT, amount REAL, ref_id INTEGER, notes TEXT)''')
conn.commit()

# Sidebar Navigation
page = st.sidebar.selectbox("Menu", 
    ["Dashboard", "Customers", "Suppliers", "Create Invoice", "Payables", "Loans & Credits", "Record Payment", "Reports"])

# ===================== DASHBOARD =====================
if page == "Dashboard":
    st.header("Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    
    total_invoices = pd.read_sql("SELECT SUM(amount) as sum FROM invoices WHERE status='Unpaid'", conn).iloc[0]['sum'] or 0
    total_payables = pd.read_sql("SELECT SUM(amount) as sum FROM payables WHERE status='Unpaid'", conn).iloc[0]['sum'] or 0
    
    col1.metric("Total Receivable", f"₹{total_invoices:,.2f}")
    col2.metric("Total Payable", f"₹{total_payables:,.2f}")
    col3.metric("Invoices", len(pd.read_sql("SELECT * FROM invoices", conn)))
    col4.metric("Payables Due", len(pd.read_sql("SELECT * FROM payables WHERE due_date <= date('now')", conn)))
    
    st.subheader("Recent Transactions")
    recent = pd.read_sql("SELECT * FROM (SELECT 'Invoice' as type, date, customer as party, amount, status FROM invoices UNION SELECT 'Payable' as type, date, supplier as party, amount, status FROM payables) ORDER BY date DESC LIMIT 10", conn)
    st.dataframe(recent)

# ===================== CUSTOMERS =====================
elif page == "Customers":
    st.header("Customers")
    name = st.text_input("Name")
    phone = st.text_input("Phone")
    email = st.text_input("Email")
    address = st.text_area("Address")
    if st.button("Add Customer"):
        c.execute("INSERT INTO customers (name,phone,email,address) VALUES (?,?,?,?)", (name,phone,email,address))
        conn.commit()
        st.success("Customer added!")
    
    st.subheader("All Customers")
    df = pd.read_sql("SELECT * FROM customers", conn)
    st.dataframe(df)

# ===================== SUPPLIERS =====================
elif page == "Suppliers":
    st.header("Suppliers")
    name = st.text_input("Supplier Name")
    phone = st.text_input("Phone")
    email = st.text_input("Email")
    address = st.text_area("Address")
    if st.button("Add Supplier"):
        c.execute("INSERT INTO suppliers (name,phone,email,address) VALUES (?,?,?,?)", (name,phone,email,address))
        conn.commit()
        st.success("Supplier added!")
    
    st.subheader("All Suppliers")
    df = pd.read_sql("SELECT * FROM suppliers", conn)
    st.dataframe(df)

# ===================== CREATE INVOICE =====================
elif page == "Create Invoice":
    st.header("Create New Invoice / Bill")
    date_today = date.today().isoformat()
    customers = pd.read_sql("SELECT name FROM customers", conn)['name'].tolist()
    
    inv_date = st.date_input("Date", value=date.today())
    customer = st.selectbox("Customer", customers if customers else ["Add customer first"])
    amount = st.number_input("Amount (₹)", min_value=0.0, value=1000.0)
    notes = st.text_area("Notes / Items")
    
    if st.button("Create Invoice"):
        c.execute("INSERT INTO invoices (date, customer, amount, status, notes) VALUES (?,?,?,?,?)", 
                 (inv_date, customer, amount, "Unpaid", notes))
        conn.commit()
        st.success(f"Invoice created for {customer} - ₹{amount}")

# ===================== PAYABLES =====================
elif page == "Payables":
    st.header("Bills to Pay (Payables)")
    suppliers = pd.read_sql("SELECT name FROM suppliers", conn)['name'].tolist()
    
    p_date = st.date_input("Bill Date", value=date.today())
    supplier = st.selectbox("Supplier", suppliers if suppliers else ["Add supplier first"])
    amount = st.number_input("Amount (₹)", min_value=0.0)
    due_date = st.date_input("Due Date")
    notes = st.text_area("Notes")
    
    if st.button("Add Payable"):
        c.execute("INSERT INTO payables (date, supplier, amount, due_date, status, notes) VALUES (?,?,?,?,?,?)", 
                 (p_date, supplier, amount, due_date, "Unpaid", notes))
        conn.commit()
        st.success("Payable added!")

    st.subheader("All Payables")
    df = pd.read_sql("SELECT * FROM payables ORDER BY due_date", conn)
    st.dataframe(df)

# ===================== LOANS & CREDITS =====================
elif page == "Loans & Credits":
    st.header("Loans & Credits")
    type_ = st.selectbox("Type", ["Loan Taken", "Loan Given", "Credit Received", "Credit Given"])
    party = st.text_input("Party Name")
    amount = st.number_input("Amount (₹)", min_value=0.0)
    l_date = st.date_input("Date", value=date.today())
    notes = st.text_area("Notes")
    
    if st.button("Save"):
        c.execute("INSERT INTO loans_credits (type, party, amount, date, notes) VALUES (?,?,?,?,?)", 
                 (type_, party, amount, l_date, notes))
        conn.commit()
        st.success("Saved!")

# ===================== RECORD PAYMENT =====================
elif page == "Record Payment":
    st.header("Record Payment")
    p_type = st.selectbox("Payment For", ["Invoice", "Payable", "Loan/Credit"])
    date_p = st.date_input("Payment Date", value=date.today())
    party = st.text_input("Party")
    amount = st.number_input("Amount Paid (₹)", min_value=0.0)
    notes = st.text_area("Notes")
    
    if st.button("Record Payment"):
        c.execute("INSERT INTO payments (date, type, party, amount, notes) VALUES (?,?,?,?,?)", 
                 (date_p, p_type, party, amount, notes))
        st.success("Payment recorded!")

# ===================== REPORTS =====================
elif page == "Reports":
    st.header("Reports")
    tab1, tab2, tab3 = st.tabs(["Invoices", "Payables", "Export Data"])
    
    with tab1:
        df_inv = pd.read_sql("SELECT * FROM invoices", conn)
        st.dataframe(df_inv)
        if st.button("Export Invoices CSV"):
            df_inv.to_csv("invoices.csv", index=False)
            st.success("Exported!")
    
    with tab2:
        df_pay = pd.read_sql("SELECT * FROM payables", conn)
        st.dataframe(df_pay)
    
    with tab3:
        st.write("All data exported as CSV files in the folder.")

st.sidebar.info("Data is saved in business_accounts.db file")

# Run with: streamlit run app.py