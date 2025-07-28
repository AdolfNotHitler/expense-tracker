import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Constants
CSV_FILE = "log.csv"

# ---------- Utility Functions ----------

def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    else:
        return pd.DataFrame(columns=[
            "DateTime", "Shop", "Item", "Qty", "NormalPrice",
            "PurchasePrice", "DiscountAmt", "DiscountPct",
            "TotalNormal", "TotalPurchase", "TotalDiscount"
        ])

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

def clear_inputs():
    st.session_state['shop'] = ""
    st.session_state['item'] = ""
    st.session_state['qty'] = 1
    st.session_state['normal_price'] = ""
    st.session_state['purchase_price'] = ""
    st.session_state['discount_pct'] = ""
    st.session_state['discount_amt'] = ""

def calculate_missing_fields(norm, purc, disc_pct, disc_amt):
    # Coerce to numeric or None
    norm = float(norm) if norm not in [None, "", 0] else None
    purc = float(purc) if purc not in [None, "", 0] else None
    disc_pct = float(disc_pct) if disc_pct not in [None, "", 0] else None
    disc_amt = float(disc_amt) if disc_amt not in [None, "", 0] else None

    # Logic fallback
    if norm is None and purc is not None and disc_pct is not None:
        norm = purc / (1 - disc_pct / 100)

    if disc_amt is None:
        if norm is not None and disc_pct is not None:
            disc_amt = norm * (disc_pct / 100)
        elif norm is not None and purc is not None:
            disc_amt = norm - purc
        elif purc is not None and disc_pct is not None:
            disc_amt = purc * (disc_pct / (100 - disc_pct))

    if purc is None and norm is not None and disc_amt is not None:
        purc = norm - disc_amt

    if disc_pct is None and norm and disc_amt:
        disc_pct = (disc_amt / norm) * 100

    return round_or_none(norm), round_or_none(purc), round_or_none(disc_pct), round_or_none(disc_amt)

def round_or_none(x):
    return round(x, 2) if x is not None else ""

def clear_last_entry():
    df = load_data()
    if not df.empty:
        df = df.iloc[:-1]  # Remove last row
        save_data(df)
        st.success("✅ Last log entry removed.")
    else:
        st.warning("⚠️ No entries to delete.")

# ---------- Streamlit App UI ----------

st.title("🧾 Expenditure Tracker")

# Load data
df = load_data()

# --- Input Fields ---
shop = st.text_input("Shop Name", key="shop")
item = st.text_input("Item Name", key="item")
qty = st.number_input("Quantity", min_value=1, value=1, step=1, key="qty")
normal_price = st.text_input("Normal Price", key="normal_price")
discount_pct = st.text_input("% Discount", key="discount_pct")
discount_amt = st.text_input("Discount Amount", key="discount_amt")
purchase_price = st.text_input("Purchase Price", key="purchase_price")

# --- Action Buttons ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("➕ Enter Log Entry"):
        # Apply logic fallback
        norm, purc, pct, amt = calculate_missing_fields(normal_price, purchase_price, discount_pct, discount_amt)

        # Update input display if user left it blank
        st.session_state['normal_price'] = norm
        st.session_state['purchase_price'] = purc
        st.session_state['discount_pct'] = pct
        st.session_state['discount_amt'] = amt

        # Totals
        total_norm = norm * qty if norm else 0
        total_purc = purc * qty if purc else 0
        total_disc = amt * qty if amt else 0

        # Log the data
        df = df.append({
            "DateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Shop": shop,
            "Item": item,
            "Qty": qty,
            "NormalPrice": norm,
            "PurchasePrice": purc,
            "DiscountAmt": amt,
            "DiscountPct": pct,
            "TotalNormal": total_norm,
            "TotalPurchase": total_purc,
            "TotalDiscount": total_disc
        }, ignore_index=True)

        save_data(df)
        st.success("✅ Entry logged successfully.")

with col2:
    if st.button("🧹 Clear Input Fields"):
        clear_inputs()
        st.success("✅ Input fields cleared.")

with col3:
    if st.button("❌ Clear Last Log Entry"):
        clear_last_entry()

# --- Display Log Table ---
st.subheader("📄 Logged Entries")
st.dataframe(df)

# --- Pivot Summary ---
st.subheader("📊 Summary Pivot (Daily Totals by Shop)")

if not df.empty:
    df["Date"] = pd.to_datetime(df["DateTime"]).dt.date
    pivot = df.pivot_table(
        index="Date",
        columns="Shop",
        values=["TotalNormal", "TotalPurchase", "TotalDiscount"],
        aggfunc="sum",
        fill_value=0
    )
    st.dataframe(pivot)
