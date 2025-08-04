import streamlit as st
import pandas as pd
from datetime import datetime
import os

LOG_FILE = "log.csv"

# Helper functions
def init_log():
    if not os.path.exists(LOG_FILE):
        df = pd.DataFrame(columns=[
            "DateTime", "Shop", "Item", "Qty",
            "NormalPrice", "PurchasePrice",
            "DiscountAmt", "DiscountPct",
            "TotalNormal", "TotalPurchase", "TotalDiscount"
        ])
        df.to_csv(LOG_FILE, index=False)

def load_log():
    return pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=[
        "DateTime", "Shop", "Item", "Qty",
        "NormalPrice", "PurchasePrice",
        "DiscountAmt", "DiscountPct",
        "TotalNormal", "TotalPurchase", "TotalDiscount"
    ])

def save_log(df):
    df.to_csv(LOG_FILE, index=False)

def to_float(val):
    try:
        val = float(val)
        return val if val > 0 else None
    except (TypeError, ValueError):
        return None

def round_or_none(val):
    return round(val, 2) if val is not None else None

def calculate_missing_fields(norm, purc, disc_pct, disc_amt):
    norm = to_float(norm)
    purc = to_float(purc)
    disc_pct = to_float(disc_pct)
    disc_amt = to_float(disc_amt)

    if purc is None and norm is not None and disc_amt is not None:
        purc = norm - disc_amt
    if purc is None and norm is not None and disc_pct is not None:
        purc = norm * (1 - disc_pct / 100)
    if norm is None and purc is not None and disc_amt is not None:
        norm = purc + disc_amt
    if norm is None and purc is not None and disc_pct is not None:
        norm = purc / (1 - disc_pct / 100) if disc_pct < 100 else None
    if disc_amt is None:
        if norm is not None and purc is not None:
            disc_amt = norm - purc
        elif norm is not None and disc_pct is not None:
            disc_amt = norm * (disc_pct / 100)
    if disc_pct is None and norm is not None and disc_amt is not None:
        disc_pct = (disc_amt / norm) * 100 if norm > 0 else 0

    return round_or_none(norm), round_or_none(purc), round_or_none(disc_pct), round_or_none(disc_amt)

# Load data
init_log()
log_df = load_log()

# Title
st.title("📋 Expenditure Tracker")

# Dropdown data
shops = sorted(log_df["Shop"].dropna().unique().tolist())
items = sorted(log_df["Item"].dropna().unique().tolist())

# Track previous entry for backfill
if "last_entry" not in st.session_state:
    st.session_state.last_entry = {}

# Input form
with st.form("entry_form"):
    st.subheader("New Entry")

    shop_select = st.selectbox("Select Existing Shop", [""] + shops, index=0)
    shop_input = st.text_input("Shop Name (new or existing)", value=shop_select or "")
    item_select = st.selectbox("Select Existing Item", [""] + items, index=0)
    item_input = st.text_input("Item Name (new or existing)", value=item_select or "")
    
    qty = st.number_input("Quantity", min_value=1, step=1, value=1)
    normal_price = st.number_input("Normal Price", min_value=0.0, step=0.01, format="%.2f")
    discount_pct = st.number_input("Discount %", min_value=0.0, max_value=100.0, step=0.01, format="%.2f")
    discount_amt = st.number_input("Discount Amount", min_value=0.0, step=0.01, format="%.2f")
    purchase_price = st.number_input("Purchase Price", min_value=0.0, step=0.01, format="%.2f")

    submitted = st.form_submit_button("✅ Enter Log Entry")

# On submission
if submitted:
    if not shop_input.strip() or not item_input.strip():
        st.error("Shop and Item names are required.")
    else:
        norm, purc, pct, amt = calculate_missing_fields(normal_price, purchase_price, discount_pct, discount_amt)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = {
            "DateTime": now,
            "Shop": shop_input.strip(),
            "Item": item_input.strip(),
            "Qty": qty,
            "NormalPrice": norm,
            "PurchasePrice": purc,
            "DiscountAmt": amt,
            "DiscountPct": pct,
            "TotalNormal": round_or_none(norm * qty) if norm else 0,
            "TotalPurchase": round_or_none(purc * qty) if purc else 0,
            "TotalDiscount": round_or_none(amt * qty) if amt else 0
        }

        log_df = pd.concat([log_df, pd.DataFrame([new_entry])], ignore_index=True)
        save_log(log_df)

        st.session_state.last_entry = new_entry
        st.success("✅ Entry logged successfully.")
        st.rerun()

# Buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("🧹 Clear Input Fields"):
        st.experimental_set_query_params()  # Reset all fields by reloading page
        st.rerun()

with col2:
    if st.button("❌ Clear Last Entry"):
        if not log_df.empty:
            log_df = log_df.iloc[:-1]
            save_log(log_df)
            st.success("❌ Last entry removed.")
            st.rerun()
        else:
            st.warning("No entries to remove.")

# Log display
st.subheader("📒 Log")
st.dataframe(log_df, use_container_width=True)

# Summary table
if not log_df.empty:
    st.subheader("📊 Summary (Daily Totals)")
    log_df["Date"] = pd.to_datetime(log_df["DateTime"]).dt.date
    pivot = log_df.groupby(["Date", "Shop"]).agg({
        "TotalNormal": "sum",
        "TotalPurchase": "sum",
        "TotalDiscount": "sum"
    }).reset_index()
    summary = pivot.pivot_table(index=["Date", "Shop"], values=["TotalNormal", "TotalPurchase", "TotalDiscount"], aggfunc="sum")
    st.dataframe(summary, use_container_width=True)
