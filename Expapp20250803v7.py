import streamlit as st
import pandas as pd
from datetime import datetime
import os

LOG_FILE = "log.csv"

# Initialize log file
def init_log():
    if not os.path.exists(LOG_FILE):
        df = pd.DataFrame(columns=[
            "DateTime", "Shop", "Item", "Qty",
            "NormalPrice", "PurchasePrice",
            "DiscountAmt", "DiscountPct",
            "TotalNormal", "TotalPurchase", "TotalDiscount"
        ])
        df.to_csv(LOG_FILE, index=False)

# Load log file
def load_log():
    return pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=[
        "DateTime", "Shop", "Item", "Qty",
        "NormalPrice", "PurchasePrice",
        "DiscountAmt", "DiscountPct",
        "TotalNormal", "TotalPurchase", "TotalDiscount"
    ])

# Save log file
def save_log(df):
    df.to_csv(LOG_FILE, index=False)

# Convert input to float or None
def to_float(val):
    try:
        val = float(val)
        return val if val > 0 else None
    except (TypeError, ValueError):
        return None

# Round helper
def round_or_none(val):
    return round(val, 2) if val is not None else None

# Calculate missing fields with complete fallback logic
def calculate_missing_fields(norm, purc, disc_pct, disc_amt):
    norm = to_float(norm)
    purc = to_float(purc)
    disc_pct = to_float(disc_pct)
    disc_amt = to_float(disc_amt)

    # Calculate purchase price if normal price and discount amount are provided
    if purc is None and norm is not None and disc_amt is not None:
        purc = norm - disc_amt

    # Calculate purchase price if normal price and discount % are provided
    if purc is None and norm is not None and disc_pct is not None:
        purc = norm * (1 - disc_pct / 100)

    # Calculate normal price if purchase price and discount amount are provided
    if norm is None and purc is not None and disc_amt is not None:
        norm = purc + disc_amt

    # Calculate normal price if purchase price and discount % are provided
    if norm is None and purc is not None and disc_pct is not None:
        norm = purc / (1 - disc_pct / 100) if disc_pct < 100 else None

    # Calculate discount amount
    if disc_amt is None:
        if norm is not None and purc is not None:
            disc_amt = norm - purc
        elif norm is not None and disc_pct is not None:
            disc_amt = norm * (disc_pct / 100)

    # Calculate discount percentage
    if disc_pct is None and norm is not None and disc_amt is not None:
        disc_pct = (disc_amt / norm) * 100 if norm > 0 else 0

    return round_or_none(norm), round_or_none(purc), round_or_none(disc_pct), round_or_none(disc_amt)

# Initialize session state
def init_session_state():
    defaults = {
        "shop_input": "",
        "item_input": "",
        "qty": 1,
        "normal_price": 0.0,
        "discount_pct": 0.0,
        "discount_amt": 0.0,
        "purchase_price": 0.0
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

# Initialize app
init_log()
init_session_state()
log_df = load_log()

st.title("📋 Expenditure Tracker")

# Load dropdown values
shops = sorted(log_df["Shop"].dropna().unique().tolist())
items = sorted(log_df["Item"].dropna().unique().tolist())

# Entry Form
with st.form("entry_form", clear_on_submit=True):
    st.subheader("New Entry")

    # Shop Name field with dynamic dropdown
    shop_selection = st.selectbox("Shop Name (type to search or add new)",
                                  options=[""] + shops,
                                  index=0,
                                  key="shop_select")
    shop_input = st.text_input("Shop Name", value=st.session_state.shop_input, key="shop_input")
    st.session_state.shop_input = shop_input if shop_input else shop_selection

    # Item Name field with dynamic dropdown
    item_selection = st.selectbox("Item Name (type to search or add new)",
                                  options=[""] + items,
                                  index=0,
                                  key="item_select")
    item_input = st.text_input("Item Name", value=st.session_state.item_input, key="item_input")
    st.session_state.item_input = item_input if item_input else item_selection

    qty = st.number_input("Quantity", min_value=1, step=1, value=st.session_state.qty)
    normal_price = st.number_input("Normal Price", min_value=0.0, step=0.01, format="%.2f", value=st.session_state.normal_price)
    discount_pct = st.number_input("Discount %", min_value=0.0, max_value=100.0, step=0.01, format="%.2f", value=st.session_state.discount_pct)
    discount_amt = st.number_input("Discount Amount", min_value=0.0, step=0.01, format="%.2f", value=st.session_state.discount_amt)
    purchase_price = st.number_input("Purchase Price", min_value=0.0, step=0.01, format="%.2f", value=st.session_state.purchase_price)

    submitted = st.form_submit_button("✅ Enter Log Entry")

# Submit Logic
if submitted:
    shop_name = st.session_state.shop_input.strip()
    item_name = st.session_state.item_input.strip()

    # Validate inputs
    if not shop_name or not item_name:
        st.error("Shop and Item names are required.")
    else:
        norm, purc, pct, amt = calculate_missing_fields(
            normal_price, purchase_price, discount_pct, discount_amt
        )

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = {
            "DateTime": now,
            "Shop": shop_name,
            "Item": item_name,
            "Qty": qty,
            "NormalPrice": norm,
            "PurchasePrice": purc,
            "DiscountAmt": amt,
            "DiscountPct": pct,
            "TotalNormal": round_or_none(norm * qty) if norm is not None else 0,
            "TotalPurchase": round_or_none(purc * qty) if purc is not None else 0,
            "TotalDiscount": round_or_none(amt * qty) if amt is not None else 0
        }

        log_df = pd.concat([log_df, pd.DataFrame([new_entry])], ignore_index=True)
        save_log(log_df)
        st.success("✅ Entry logged successfully.")
        
        # Reset session state after successful submission
        init_session_state()
        st.rerun()

# Clear Buttons
col1, col2 = st.columns(2)
with col1:
    with st.form("clear_inputs_form"):
        if st.form_submit_button("🧹 Clear Input Fields"):
            init_session_state()
            st.rerun()

with col2:
    with st.form("clear_last_form"):
        if st.form_submit_button("❌ Clear Last Entry"):
            if not log_df.empty:
                log_df = log_df.iloc[:-1]
                save_log(log_df)
                st.success("❌ Last entry removed.")
                st.rerun()
            else:
                st.warning("No entries to delete.")

# Display Log
st.subheader("📒 Log")
st.dataframe(log_df, use_container_width=True)

# Summary
if not log_df.empty:
    st.subheader("📊 Summary (Daily Totals)")
    log_df["Date"] = pd.to_datetime(log_df["DateTime"]).dt.date
    pivot = log_df.groupby(["Date", "Shop"]).agg({
        "TotalNormal": "sum",
        "TotalPurchase": "sum",
        "TotalDiscount": "sum"
    }).reset_index()

    pivot_table = pivot.pivot_table(
        index=["Date", "Shop"],
        values=["TotalNormal", "TotalPurchase", "TotalDiscount"],
        aggfunc="sum",
        fill_value=0
    )
    st.dataframe(pivot_table, use_container_width=True)