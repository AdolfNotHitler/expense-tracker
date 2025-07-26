import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Log file
LOG_FILE = "log.csv"

# Load or create initial log DataFrame
if os.path.exists(LOG_FILE):
    df_log = pd.read_csv(LOG_FILE)
else:
    df_log = pd.DataFrame(columns=[
        "DateTime", "Shop", "Item", "Qty", "NormalPrice",
        "PurchasePrice", "DiscountAmt", "DiscountPct",
        "TotalNormal", "TotalPurchase", "TotalDiscount"
    ])
    df_log.to_csv(LOG_FILE, index=False)

st.title("📊 Expenditure Tracker")

# Dropdown sources
shops = sorted(df_log["Shop"].dropna().unique().tolist())
items = sorted(df_log["Item"].dropna().unique().tolist())

# Input fields
shop = st.selectbox("🛒 Shop Name", options=shops + ["<New Entry>"])
if shop == "<New Entry>":
    shop = st.text_input("Enter new shop name")

item = st.selectbox("📦 Item Name", options=items + ["<New Entry>"])
if item == "<New Entry>":
    item = st.text_input("Enter new item name")

qty = st.number_input("🔢 Quantity", min_value=1, step=1, value=1)
normal_price = st.number_input("💰 Normal Price (unit)", min_value=0.0, step=0.01, format="%.2f")
discount_pct = st.number_input("📉 % Discount", min_value=0.0, step=0.01, format="%.2f")
discount_amt = st.number_input("💵 Discount Amount (unit)", min_value=0.0, step=0.01, format="%.2f")
purchase_price = st.number_input("🛍️ Purchase Price (unit)", min_value=0.0, step=0.01, format="%.2f")

if st.button("✅ Enter"):
    # Compute missing values
    if normal_price == 0 and purchase_price > 0 and discount_pct > 0:
        normal_price = round(purchase_price / (1 - discount_pct / 100), 2)

    if discount_amt == 0 and normal_price > 0 and discount_pct > 0:
        discount_amt = round(normal_price * (discount_pct / 100), 2)

    if purchase_price == 0 and normal_price > 0:
        purchase_price = round(normal_price - discount_amt, 2)

    if discount_pct == 0 and normal_price > 0:
        discount_pct = round((discount_amt / normal_price) * 100, 2) if normal_price else 0

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_normal = round(normal_price * qty, 2)
    total_purchase = round(purchase_price * qty, 2)
    total_discount = round(discount_amt * qty, 2)

    new_row = {
        "DateTime": timestamp,
        "Shop": shop,
        "Item": item,
        "Qty": qty,
        "NormalPrice": normal_price,
        "PurchasePrice": purchase_price,
        "DiscountAmt": discount_amt,
        "DiscountPct": discount_pct,
        "TotalNormal": total_normal,
        "TotalPurchase": total_purchase,
        "TotalDiscount": total_discount,
    }

    df_log = pd.concat([df_log, pd.DataFrame([new_row])], ignore_index=True)
    df_log.to_csv(LOG_FILE, index=False)
    st.success("✅ Entry logged successfully!")

if st.button("🧹 Clear Last Entry"):
    if len(df_log) > 0:
        df_log = df_log.iloc[:-1]
        df_log.to_csv(LOG_FILE, index=False)
        st.success("🗑️ Last entry removed.")
    else:
        st.warning("⚠️ No entries to remove.")

st.markdown("---")
st.subheader("📘 Log History")
st.dataframe(df_log.sort_values("DateTime", ascending=False), use_container_width=True)

# Pivot table summary
st.markdown("---")
st.subheader("📊 Totals Summary")

if not df_log.empty:
    df_log["Date"] = pd.to_datetime(df_log["DateTime"]).dt.date
    pivot = pd.pivot_table(
        df_log,
        index="Date",
        columns="Shop",
        values=["TotalNormal", "TotalPurchase", "TotalDiscount"],
        aggfunc="sum",
        fill_value=0
    )
    st.dataframe(pivot, use_container_width=True)
else:
    st.info("No data yet.")
