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
            "Discount%", "DiscountAmount",
            "TotalNormal", "TotalPurchase", "TotalDiscount"
        ])
        df.to_csv(LOG_FILE, index=False)

# Load log
def load_log():
    if os.path.exists(LOG_FILE):
        return pd.read_csv(LOG_FILE)
    return pd.DataFrame(columns=[
        "DateTime", "Shop", "Item", "Qty",
        "NormalPrice", "PurchasePrice",
        "Discount%", "DiscountAmount",
        "TotalNormal", "TotalPurchase", "TotalDiscount"
    ])

# Save entry to log
def save_entry(entry):
    df = load_log()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(LOG_FILE, index=False)

# Calculation logic
def calculate_missing_fields(norm, purc, disc_pct, disc_amt):
    norm = float(norm) if norm else None
    purc = float(purc) if purc else None
    disc_pct = float(disc_pct) if disc_pct else None
    disc_amt = float(disc_amt) if disc_amt else None

    # 1. Compute Normal Price from Purchase Price + Discount%
    if norm is None and purc is not None and disc_pct is not None:
        norm = purc / (1 - disc_pct / 100) if disc_pct < 100 else None

    # 2. Compute Normal Price from Purchase Price + Discount Amount
    if norm is None and purc is not None and disc_amt is not None:
        norm = purc + disc_amt

    # 3. Compute Purchase Price from Normal Price + Discount%
    if purc is None and norm is not None and disc_pct is not None:
        purc = norm * (1 - disc_pct / 100)

    # 4. Compute Purchase Price from Normal Price + Discount Amount
    if purc is None and norm is not None and disc_amt is not None:
        purc = norm - disc_amt

    # 5. Compute Discount Amount if missing
    if disc_amt is None and norm is not None and purc is not None:
        disc_amt = norm - purc

    # 6. Compute Discount % if missing
    if disc_pct is None and norm is not None and purc is not None and norm != 0:
        disc_pct = (disc_amt / norm) * 100 if disc_amt is not None else 0

    # 7. If still missing, set defaults
    if norm is None and purc is not None:
        norm = purc
    if purc is None and norm is not None:
        purc = norm
    if disc_amt is None:
        disc_amt = 0
    if disc_pct is None:
        disc_pct = 0

    return round(norm, 2), round(purc, 2), round(disc_pct, 2), round(disc_amt, 2)

# Streamlit App
st.title("Expenditure Logger with Auto-Calculation")

init_log()

with st.form("log_form"):
    shop = st.text_input("Shop Name")
    item = st.text_input("Item Name")
    qty = st.number_input("Quantity", min_value=1, value=1)

    st.subheader("Price Details")

    norm_price_input = st.text_input("Normal Price")
    purc_price_input = st.text_input("Purchase Price")
    disc_pct_input = st.text_input("Discount %")
    disc_amt_input = st.text_input("Discount Amount")

    # Real-time calculation
    calculated_norm, calculated_purc, calculated_pct, calculated_amt = calculate_missing_fields(
        norm_price_input, purc_price_input, disc_pct_input, disc_amt_input
    )

    # Display auto-filled values
    st.markdown("### Auto-filled Calculations")
    st.write(f"**Normal Price:** {calculated_norm}")
    st.write(f"**Purchase Price:** {calculated_purc}")
    st.write(f"**Discount %:** {calculated_pct}")
    st.write(f"**Discount Amount:** {calculated_amt}")

    submitted = st.form_submit_button("Submit Entry")

    if submitted:
        total_normal = calculated_norm * qty
        total_purchase = calculated_purc * qty
        total_discount = calculated_amt * qty

        entry = {
            "DateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Shop": shop,
            "Item": item,
            "Qty": qty,
            "NormalPrice": calculated_norm,
            "PurchasePrice": calculated_purc,
            "Discount%": calculated_pct,
            "DiscountAmount": calculated_amt,
            "TotalNormal": total_normal,
            "TotalPurchase": total_purchase,
            "TotalDiscount": total_discount
        }

        save_entry(entry)
        st.success("Entry submitted successfully!")

# Display log
st.subheader("Expenditure Log")
df = load_log()
st.dataframe(df)
