import streamlit as st
import pandas as pd
import os
from datetime import datetime

LOG_FILE = "log.csv"

# -----------------------
# Initialize log
# -----------------------
def init_log():
    if not os.path.exists(LOG_FILE):
        df = pd.DataFrame(columns=[
            "DateTime", "Shop", "Item", "Qty",
            "NormalPrice", "PurchasePrice",
            "DiscountAmt", "DiscountPct",
            "TotalNormal", "TotalPurchase", "TotalDiscount"
        ])
        df.to_csv(LOG_FILE, index=False)

# -----------------------
# Load log
# -----------------------
def load_log():
    return pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=[
        "DateTime", "Shop", "Item", "Qty",
        "NormalPrice", "PurchasePrice",
        "DiscountAmt", "DiscountPct",
        "TotalNormal", "TotalPurchase", "TotalDiscount"
    ])

# -----------------------
# Save log
# -----------------------
def save_log(df):
    df.to_csv(LOG_FILE, index=False)

# -----------------------
# Helper: Round or None
# -----------------------
def round_or_none(val):
    try:
        return round(val, 2)
    except:
        return None

# -----------------------
# Backfill/Calculate missing fields
# -----------------------
def calculate_missing_fields(norm, purc, disc_pct, disc_amt):
    norm = float(norm) if norm not in [None, "", 0] else None
    purc = float(purc) if purc not in [None, "", 0] else None
    disc_pct = float(disc_pct) if disc_pct not in [None, "", 0] else None
    disc_amt = float(disc_amt) if disc_amt not in [None, "", 0] else None

    # Fallback logic
    if norm is None and purc is not None and disc_pct is not None:
        norm = purc / (1 - disc_pct / 100)

    if disc_amt is None:
        if norm is not None and disc_pct is not None:
            disc_amt = norm * disc_pct / 100
        elif norm is not None and purc is not None:
            disc_amt = norm - purc
        elif purc is not None and disc_pct is not None:
            disc_amt = purc * disc_pct / (100 - disc_pct)

    if purc is None and norm is not None and disc_amt is not None:
        purc = norm - disc_amt

    if disc_pct is None and norm and disc_amt:
        try:
            disc_pct = (disc_amt / norm) * 100
        except ZeroDivisionError:
            disc_pct = 0

    return round_or_none(norm), round_or_none(purc), round_or_none(disc_pct), round_or_none(disc_amt)

# -----------------------
# Initialize session state
# -----------------------
init_log()
log_df = load_log()

input_fields = {
    "shop": "",
    "new_shop": "",
    "item": "",
    "new_item": "",
    "qty": 1,
    "normal_price": 0.0,
    "purchase_price": 0.0,
    "discount_amt": 0.0,
    "discount_pct": 0.0
}

for key, default in input_fields.items():
    if key not in st.session_state:
        st.session_state[key] = default

# -----------------------
# Main App UI
# -----------------------
st.title("📋 Expenditure Tracker")

shops = sorted(log_df["Shop"].dropna().unique().tolist())
items = sorted(log_df["Item"].dropna().unique().tolist())

with st.form("entry_form"):
    st.subheader("📝 Enter New Expenditure")

    shop = st.selectbox("Shop", options=[""] + shops, index=0, key="shop")
    if shop == "":
        shop = st.text_input("Enter new shop", key="new_shop")

    item = st.selectbox("Item", options=[""] + items, index=0, key="item")
    if item == "":
        item = st.text_input("Enter new item", key="new_item")

    qty = st.number_input("Quantity", min_value=1, step=1, key="qty")
    norm_price = st.number_input("Normal Price", min_value=0.0, format="%.2f", key="normal_price")
    disc_pct = st.number_input("Discount %", min_value=0.0, max_value=100.0, format="%.2f", key="discount_pct")
    disc_amt = st.number_input("Discount Amount", min_value=0.0, format="%.2f", key="discount_amt")
    purc_price = st.number_input("Purchase Price", min_value=0.0, format="%.2f", key="purchase_price")

    submitted = st.form_submit_button("✅ Enter Log Entry")

# -----------------------
# Enter Log Entry
# -----------------------
if submitted:
    norm, purc, pct, amt = calculate_missing_fields(norm_price, purc_price, disc_pct, disc_amt)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_entry = {
        "DateTime": now,
        "Shop": shop,
        "Item": item,
        "Qty": qty,
        "NormalPrice": norm,
        "PurchasePrice": purc,
        "DiscountAmt": amt,
        "DiscountPct": pct,
        "TotalNormal": norm * qty if norm is not None else 0,
        "TotalPurchase": purc * qty if purc is not None else 0,
        "TotalDiscount": amt * qty if amt is not None else 0
    }

    log_df = pd.concat([log_df, pd.DataFrame([new_entry])], ignore_index=True)
    save_log(log_df)
    st.success("✔️ Entry logged successfully.")

# -----------------------
# Clear Input Fields
# -----------------------
if st.button("🧹 Clear Input Fields"):
    for key in input_fields.keys():
        st.session_state[key] = input_fields[key]
    st.experimental_rerun()

# -----------------------
# Clear Last Entry
# -----------------------
if st.button("❌ Clear Last Entry"):
    if not log_df.empty:
        log_df = log_df.iloc[:-1]
        save_log(log_df)
        st.success("Last entry removed.")
        st.experimental_rerun()
    else:
        st.warning("Log is already empty.")

# -----------------------
# Display Log
# -----------------------
st.subheader("📒 Log")
st.dataframe(log_df, use_container_width=True)

# -----------------------
# Pivot Summary
# -----------------------
if not log_df.empty:
    st.subheader("📊 Summary")

    log_df["Date"] = pd.to_datetime(log_df["DateTime"]).dt.date
    pivot = log_df.groupby(["Date", "Shop"]).agg({
        "TotalNormal": "sum",
        "TotalPurchase": "sum",
        "TotalDiscount": "sum"
    }).reset_index()

    pivot_table = pivot.pivot_table(index=["Date", "Shop"], columns="Shop",
                                     values=["TotalNormal", "TotalPurchase", "TotalDiscount"],
                                     aggfunc="sum", fill_value=0)

    st.dataframe(pivot_table, use_container_width=True)
