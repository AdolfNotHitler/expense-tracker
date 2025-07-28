import streamlit as st
import pandas as pd
import os
from datetime import datetime

LOG_FILE = "log.csv"

# Initialize log if not exists
def init_log():
    if not os.path.exists(LOG_FILE):
        df = pd.DataFrame(columns=[
            "DateTime", "Shop", "Item", "Qty", "NormalPrice", "PurchasePrice",
            "DiscountAmt", "DiscountPct", "TotalNormal", "TotalPurchase", "TotalDiscount"
        ])
        df.to_csv(LOG_FILE, index=False)

# Load log file
def load_log():
    return pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=[
        "DateTime", "Shop", "Item", "Qty", "NormalPrice", "PurchasePrice",
        "DiscountAmt", "DiscountPct", "TotalNormal", "TotalPurchase", "TotalDiscount"
    ])

# Save log file
def save_log(df):
    df.to_csv(LOG_FILE, index=False)

# Round helper
def round_or_none(val):
    try:
        return round(val, 2)
    except:
        return None

# Calculate missing fields
def calculate_missing_fields(norm, purc, disc_pct, disc_amt):
    norm = float(norm) if norm not in [None, "", 0] else None
    purc = float(purc) if purc not in [None, "", 0] else None
    disc_pct = float(disc_pct) if disc_pct not in [None, "", 0] else None
    disc_amt = float(disc_amt) if disc_amt not in [None, "", 0] else None

    if norm is None and purc is not None and disc_pct is not None:
        try:
            norm = purc / (1 - disc_pct / 100)
        except ZeroDivisionError:
            norm = purc

    if disc_amt is None:
        if norm is not None and disc_pct is not None:
            disc_amt = norm * (disc_pct / 100)
        elif norm is not None and purc is not None:
            disc_amt = norm - purc
        elif purc is not None and disc_pct is not None:
            try:
                disc_amt = purc * (disc_pct / (100 - disc_pct))
            except ZeroDivisionError:
                disc_amt = 0

    if purc is None and norm is not None and disc_amt is not None:
        purc = norm - disc_amt

    if disc_pct is None and norm and disc_amt:
        try:
            disc_pct = (disc_amt / norm) * 100
        except ZeroDivisionError:
            disc_pct = 0

    return round_or_none(norm), round_or_none(purc), round_or_none(disc_pct), round_or_none(disc_amt)

# Initialize
init_log()
log_df = load_log()

# Setup session state
for field in ["shop", "new_shop", "item", "new_item", "qty", "normal_price", "purchase_price", "discount_amt", "discount_pct"]:
    if field not in st.session_state:
        st.session_state[field] = "" if field.startswith("new") or field in ["shop", "item"] else 0

shops = sorted(log_df["Shop"].dropna().unique().tolist())
items = sorted(log_df["Item"].dropna().unique().tolist())

st.title("📋 Expenditure Tracker")

with st.form("entry_form"):
    st.subheader("New Entry")
    shop = st.selectbox("Shop Name", options=[""] + shops, index=0, key="shop")
    if shop == "":
        new_shop = st.text_input("Enter new shop name", key="new_shop")
        shop = new_shop

    item = st.selectbox("Item Name", options=[""] + items, index=0, key="item")
    if item == "":
        new_item = st.text_input("Enter new item name", key="new_item")
        item = new_item

    qty = st.number_input("Quantity", min_value=1, step=1, key="qty")
    normal_price = st.number_input("Normal Price", min_value=0.0, step=0.01, format="%.2f", key="normal_price")
    discount_pct = st.number_input("Discount %", min_value=0.0, max_value=100.0, step=0.01, format="%.2f", key="discount_pct")
    discount_amt = st.number_input("Discount Amount", min_value=0.0, step=0.01, format="%.2f", key="discount_amt")
    purchase_price = st.number_input("Purchase Price", min_value=0.0, step=0.01, format="%.2f", key="purchase_price")

    submitted = st.form_submit_button("Enter Log Entry")

    if submitted:
        norm, purc, pct, amt = calculate_missing_fields(
            norm=normal_price,
            purc=purchase_price,
            disc_pct=discount_pct,
            disc_amt=discount_amt
        )

        # Inline warnings
        warnings = []
        if norm is not None and purc is not None and purc > norm:
            warnings.append(f"⚠️ Purchase price ({purc}) is higher than normal price ({norm})")
        if norm is not None and norm <= 0:
            warnings.append("⚠️ Normal price is zero or negative")
        if purc is not None and purc <= 0:
            warnings.append("⚠️ Purchase price is zero or negative")
        if qty <= 0:
            warnings.append("⚠️ Quantity must be greater than zero")

        for msg in warnings:
            st.warning(msg)

        if any("⚠️" in w for w in warnings):
            st.stop()

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
        st.success("✅ Entry logged successfully.")

# Clear Input Button
def clear_inputs():
    for field in ["shop", "new_shop", "item", "new_item", "qty", "normal_price", "purchase_price", "discount_amt", "discount_pct"]:
        st.session_state[field] = "" if field.startswith("new") or field in ["shop", "item"] else 0

if st.button("🧹 Clear Input"):
    clear_inputs()
    st.experimental_rerun()

# Clear Last Entry Button
if st.button("❌ Clear Last Entry"):
    if not log_df.empty:
        log_df = log_df[:-1]
        save_log(log_df)
        st.success("Last entry removed.")
        st.experimental_rerun()
    else:
        st.warning("No entries to delete.")

# Display log
st.subheader("📒 Log")
st.dataframe(log_df, use_container_width=True)

# Pivot summary
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
    fill_value=0)
    st.dataframe(pivot_table, use_container_width=True)
