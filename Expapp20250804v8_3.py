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

# Load log
def load_log():
    return pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=[
        "DateTime", "Shop", "Item", "Qty",
        "NormalPrice", "PurchasePrice",
        "DiscountAmt", "DiscountPct",
        "TotalNormal", "TotalPurchase", "TotalDiscount"
    ])

# Save log
def save_log(df):
    df.to_csv(LOG_FILE, index=False)

# To float or None
def to_float(val):
    try:
        val = float(val)
        return val if val > 0 else None
    except:
        return None

# Round helper
def round_or_none(val):
    return round(val, 2) if val is not None else None

# Complete fallback logic
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

# Init session
def init_session_state():
    defaults = {
        "temp_shop_input": "",
        "temp_item_input": "",
        "edit_index": None,
        "qty": 1,
        "normal_price": 0.0,
        "discount_pct": 0.0,
        "discount_amt": 0.0,
        "purchase_price": 0.0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

# Reset session
def reset_session_state():
    keys_to_clear = [
        "temp_shop_input", "temp_item_input", "edit_index",
        "qty", "normal_price", "discount_pct",
        "discount_amt", "purchase_price"
    ]
    for key in keys_to_clear:
        st.session_state[key] = "" if "input" in key else 0 if "price" in key or "amt" in key or "pct" in key else 1

# App start
init_log()
init_session_state()
log_df = load_log()

st.title("📋 Expenditure Tracker")

shops = sorted(log_df["Shop"].dropna().unique().tolist())
items = sorted(log_df["Item"].dropna().unique().tolist())

# --- Entry Form ---
with st.form("entry_form", clear_on_submit=True):
    st.subheader("New Entry / Edit Entry")

    # --- Dynamic Shop Name Input ---
    shop_select = st.selectbox("🔽 Select Existing Shop", [""] + shops)
    if shop_select and shop_select != st.session_state.temp_shop_input:
        st.session_state.temp_shop_input = shop_select
    shop_input = st.text_input("🏪 Shop Name (type or select)", value=st.session_state.temp_shop_input)

    # --- Dynamic Item Name Input ---
    item_select = st.selectbox("🔽 Select Existing Item", [""] + items)
    if item_select and item_select != st.session_state.temp_item_input:
        st.session_state.temp_item_input = item_select
    item_input = st.text_input("📦 Item Name (type or select)", value=st.session_state.temp_item_input)

    qty = st.number_input("Quantity", min_value=1, value=st.session_state.qty, step=1, key="qty")
    normal_price = st.number_input("Normal Price", min_value=0.0, value=st.session_state.normal_price, step=0.01, format="%.2f", key="normal_price")
    discount_pct = st.number_input("Discount %", min_value=0.0, max_value=100.0, value=st.session_state.discount_pct, step=0.01, format="%.2f", key="discount_pct")
    discount_amt = st.number_input("Discount Amount", min_value=0.0, value=st.session_state.discount_amt, step=0.01, format="%.2f", key="discount_amt")
    purchase_price = st.number_input("Purchase Price", min_value=0.0, value=st.session_state.purchase_price, step=0.01, format="%.2f", key="purchase_price")

    submit_label = "✅ Update Log Entry" if st.session_state.edit_index is not None else "✅ Enter Log Entry"
    submitted = st.form_submit_button(submit_label)

# --- Submission Logic ---
if submitted:
    shop = shop_input.strip()
    item = item_input.strip()

    if not shop or not item:
        st.error("Shop and Item names are required.")
    else:
        norm, purc, pct, amt = calculate_missing_fields(normal_price, purchase_price, discount_pct, discount_amt)

        entry = {
            "DateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Shop": shop,
            "Item": item,
            "Qty": qty,
            "NormalPrice": norm,
            "PurchasePrice": purc,
            "DiscountAmt": amt,
            "DiscountPct": pct,
            "TotalNormal": round_or_none(norm * qty) if norm else 0,
            "TotalPurchase": round_or_none(purc * qty) if purc else 0,
            "TotalDiscount": round_or_none(amt * qty) if amt else 0
        }

        if st.session_state.edit_index is not None:
            log_df.iloc[st.session_state.edit_index] = entry
            st.success("✏️ Log entry updated.")
        else:
            log_df = pd.concat([log_df, pd.DataFrame([entry])], ignore_index=True)
            st.success("✅ Entry added to log.")

        save_log(log_df)
        reset_session_state()
        st.rerun()

# --- Edit Existing Entry ---
st.subheader("🛠 Edit Log Entry")
if not log_df.empty:
    edit_row = st.selectbox("Select an entry to edit", log_df.index[::-1], format_func=lambda i: f"{log_df.loc[i, 'DateTime']} – {log_df.loc[i, 'Shop']} – {log_df.loc[i, 'Item']}")
    if st.button("✏️ Load for Editing"):
        row = log_df.loc[edit_row]
        st.session_state.temp_shop_input = row["Shop"]
        st.session_state.temp_item_input = row["Item"]
        st.session_state.qty = int(row["Qty"])
        st.session_state.normal_price = float(row["NormalPrice"])
        st.session_state.discount_pct = float(row["DiscountPct"])
        st.session_state.discount_amt = float(row["DiscountAmt"])
        st.session_state.purchase_price = float(row["PurchasePrice"])
        st.session_state.edit_index = edit_row
        st.rerun()

# --- Delete Last Entry ---
if st.button("❌ Clear Last Entry"):
    if not log_df.empty:
        log_df = log_df.iloc[:-1]
        save_log(log_df)
        st.success("🗑 Last entry removed.")
        st.rerun()
    else:
        st.warning("No entries to remove.")

# --- Display Log ---
st.subheader("📒 Log")
st.dataframe(log_df, use_container_width=True)

# --- Summary Table ---
if not log_df.empty:
    st.subheader("📊 Summary by Date & Shop")
    log_df["Date"] = pd.to_datetime(log_df["DateTime"]).dt.date
    pivot = log_df.groupby(["Date", "Shop"]).agg({
        "TotalNormal": "sum",
        "TotalPurchase": "sum",
        "TotalDiscount": "sum"
    }).reset_index()

    pivot_table = pivot.pivot_table(index=["Date", "Shop"], values=["TotalNormal", "TotalPurchase", "TotalDiscount"], aggfunc="sum", fill_value=0)
    st.dataframe(pivot_table, use_container_width=True)
