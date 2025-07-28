import streamlit as st
import pandas as pd
from datetime import datetime
import os

LOG_FILE = "log.csv"

# Initialize log file
if not os.path.exists(LOG_FILE):
    df = pd.DataFrame(columns=[
        "DateTime", "Shop", "Item", "Qty",
        "NormalPrice", "PurchasePrice",
        "DiscountAmt", "DiscountPct",
        "TotalNormal", "TotalPurchase", "TotalDiscount"
    ])
    df.to_csv(LOG_FILE, index=False)

# Load log
df_log = pd.read_csv(LOG_FILE)

# Get dynamic dropdown options
shop_options = sorted(df_log["Shop"].dropna().unique().tolist())
item_options = sorted(df_log["Item"].dropna().unique().tolist())

# --- Input Form ---
st.title("📒 Expenditure Logger")

with st.form("entry_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        shop = st.selectbox("Shop Name", options=[""] + shop_options, index=0)
        if shop == "":
            shop = st.text_input("Enter New Shop Name")
        item = st.selectbox("Item Name", options=[""] + item_options, index=0)
        if item == "":
            item = st.text_input("Enter New Item Name")
        qty = st.number_input("Quantity", min_value=1, value=1, step=1)

    with col2:
        normal_price = st.number_input("Normal Price", min_value=0.0, step=0.01, format="%.2f")
        discount_pct = st.number_input("% Discount", min_value=0.0, step=0.01, format="%.2f")
        discount_amt = st.number_input("Discount Amount", min_value=0.0, step=0.01, format="%.2f")
        purchase_price = st.number_input("Purchase Price", min_value=0.0, step=0.01, format="%.2f")

    submitted = st.form_submit_button("✅ Enter Log Entry")
    clear = st.form_submit_button("🧹 Clear Input Fields")
    clear_last = st.form_submit_button("❌ Clear Last Entry")

# --- Logic ---
def compute_fallbacks(norm, disc_amt, disc_pct, purc):
    # Calculate missing discount if needed
    if norm and purc and disc_amt == 0 and disc_pct == 0:
        disc_amt = round(norm - purc, 2)
        disc_pct = round((disc_amt / norm) * 100, 2) if norm != 0 else 0
    elif disc_pct == 0 and disc_amt > 0 and norm > 0:
        disc_pct = round((disc_amt / norm) * 100, 2)
    elif disc_amt == 0 and disc_pct > 0 and norm > 0:
        disc_amt = round(norm * (disc_pct / 100), 2)
    elif purc == 0 and norm > 0 and disc_amt > 0:
        purc = round(norm - disc_amt, 2)
    elif norm == 0 and purc > 0 and disc_pct > 0:
        norm = round(purc / (1 - disc_pct / 100), 2)
        disc_amt = round(norm - purc, 2)

    return norm, disc_amt, disc_pct, purc

# --- Submission Logic ---
if submitted:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    norm = normal_price
    purc = purchase_price
    disc_amt = discount_amt
    disc_pct = discount_pct

    norm, disc_amt, disc_pct, purc = compute_fallbacks(norm, disc_amt, disc_pct, purc)

    total_norm = round(norm * qty, 2)
    total_purc = round(purc * qty, 2)
    total_disc = round(disc_amt * qty, 2)

    new_row = pd.DataFrame([{
        "DateTime": now,
        "Shop": shop,
        "Item": item,
        "Qty": qty,
        "NormalPrice": norm,
        "PurchasePrice": purc,
        "DiscountAmt": disc_amt,
        "DiscountPct": disc_pct,
        "TotalNormal": total_norm,
        "TotalPurchase": total_purc,
        "TotalDiscount": total_disc
    }])

    df_log = pd.concat([df_log, new_row], ignore_index=True)
    df_log.to_csv(LOG_FILE, index=False)
    st.success("Log entry added successfully.")

# --- Clear Input ---
if clear:
    st.experimental_rerun()

# --- Clear Last Entry ---
if clear_last:
    if len(df_log) > 0:
        df_log = df_log[:-1]
        df_log.to_csv(LOG_FILE, index=False)
        st.success("Last log entry removed.")
        st.experimental_rerun()
    else:
        st.warning("Log is already empty.")

# --- Display Log ---
st.markdown("## 📋 Current Expenditure Log")
if df_log.empty:
    st.info("No entries yet.")
else:
    st.dataframe(df_log.tail(10), use_container_width=True)
