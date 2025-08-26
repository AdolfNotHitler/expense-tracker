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

# Utility conversions
def to_float(val):
    try:
        val = float(val)
        return val if val > 0 else None
    except:
        return None

def round_or_none(val):
    return round(val, 2) if val is not None else None

# Fallback field calculations
def calculate_missing_fields(norm, purc, disc_pct, disc_amt):
    # Convert 0 or empty to None
    norm = to_float(norm)
    purc = to_float(purc)
    disc_pct = to_float(disc_pct)
    disc_amt = to_float(disc_amt)

    # Fallback logic
    if purc is None and norm is not None and disc_amt is not None:
        purc = norm - disc_amt
    if purc is None and norm is not None and disc_pct is not None:
        purc = norm * (1 - disc_pct / 100)
    if norm is None and purc is not None and disc_amt is not None:
        norm = purc + disc_amt
    if norm is None and purc is not None and disc_pct is not None and disc_pct < 100:
        norm = purc / (1 - disc_pct / 100)

    # Calculate discount amount if missing
    if disc_amt is None:
        if norm is not None and purc is not None:
            disc_amt = norm - purc
        elif norm is not None and disc_pct is not None:
            disc_amt = norm * (disc_pct / 100)

    # Calculate discount % if missing
    if disc_pct is None and norm is not None and disc_amt is not None and norm > 0:
        disc_pct = (disc_amt / norm) * 100

    return round_or_none(norm), round_or_none(purc), round_or_none(disc_pct), round_or_none(disc_amt)

# Label for dropdown selection
def get_index_label(row):
    return f"{row['DateTime']} - {row['Shop']} - {row['Item']} (x{row['Qty']})"

# App Start
init_log()
log_df = load_log()
shops = sorted(log_df["Shop"].dropna().unique().tolist())
items = sorted(log_df["Item"].dropna().unique().tolist())

st.title("📋 Expenditure Tracker")

# --- Edit Log Section ---
st.subheader("✏️ Edit Log Entries")
if not log_df.empty:
    log_df["label"] = log_df.apply(get_index_label, axis=1)
    selected = st.selectbox("Select entry to edit", [""] + log_df["label"].tolist())

    if selected:
        idx = log_df[log_df["label"] == selected].index[0]
        selected_row = log_df.loc[idx]

        with st.form("edit_entry"):
            st.write("Edit the selected entry:")
            shop_name = st.text_input("Shop", selected_row["Shop"])
            item_name = st.text_input("Item", selected_row["Item"])
            qty = st.number_input("Quantity", min_value=1, step=1, value=int(selected_row["Qty"]))
            norm = st.number_input("Normal Price", min_value=0.0, step=0.01, value=float(selected_row["NormalPrice"] or 0))
            purc = st.number_input("Purchase Price", min_value=0.0, step=0.01, value=float(selected_row["PurchasePrice"] or 0))
            disc_amt = st.number_input("Discount Amount", min_value=0.0, step=0.01, value=float(selected_row["DiscountAmt"] or 0))
            disc_pct = st.number_input("Discount %", min_value=0.0, max_value=100.0, step=0.01, value=float(selected_row["DiscountPct"] or 0))

            update_btn = st.form_submit_button("💾 Save Changes")
            if update_btn:
                norm, purc, disc_pct, disc_amt = calculate_missing_fields(norm, purc, disc_pct, disc_amt)

                # Validation: At least one price required
                if norm is None and purc is None:
                    st.error("You must enter at least Normal Price or Purchase Price.")
                else:
                    log_df.loc[idx] = {
                        "DateTime": selected_row["DateTime"],
                        "Shop": shop_name,
                        "Item": item_name,
                        "Qty": qty,
                        "NormalPrice": norm,
                        "PurchasePrice": purc,
                        "DiscountAmt": disc_amt,
                        "DiscountPct": disc_pct,
                        "TotalNormal": round_or_none((norm or 0) * qty),
                        "TotalPurchase": round_or_none((purc or 0) * qty),
                        "TotalDiscount": round_or_none((disc_amt or 0) * qty)
                    }
                    save_log(log_df.drop(columns=["label"], errors="ignore"))
                    st.success("✅ Entry updated.")
                    st.rerun()
else:
    st.info("Log is empty. No entries to edit.")

# --- New Entry Section ---
st.subheader("🆕 New Entry")
with st.form("new_entry_form"):
    col1, col2 = st.columns(2)

    with col1:
        shop_select = st.selectbox("Select Existing Shop", [""] + shops)
    with col2:
        shop = st.text_input("Shop Name (new or existing)", value=shop_select or "")

    with col1:
        item_select = st.selectbox("Select Existing Item", [""] + items)
    with col2:
        item = st.text_input("Item Name (new or existing)", value=item_select or "")

    qty = st.number_input("Quantity", min_value=1, step=1, value=1)
    normal_price = st.number_input("Normal Price", min_value=0.0, step=0.01)
    purchase_price = st.number_input("Purchase Price", min_value=0.0, step=0.01)
    discount_amt = st.number_input("Discount Amount", min_value=0.0, step=0.01)
    discount_pct = st.number_input("Discount %", min_value=0.0, max_value=100.0, step=0.01)

    submit = st.form_submit_button("✅ Enter Log Entry")

    if submit:
        if not shop.strip() or not item.strip():
            st.error("Shop and Item name must not be blank.")
        else:
            norm, purc, pct, amt = calculate_missing_fields(normal_price, purchase_price, discount_pct, discount_amt)

            # Validation: At least one price required
            if norm is None and purc is None:
                st.error("You must enter at least Normal Price or Purchase Price.")
            else:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_entry = {
                    "DateTime": now,
                    "Shop": shop.strip(),
                    "Item": item.strip(),
                    "Qty": qty,
                    "NormalPrice": norm,
                    "PurchasePrice": purc,
                    "DiscountAmt": amt,
                    "DiscountPct": pct,
                    "TotalNormal": round_or_none((norm or 0) * qty),
                    "TotalPurchase": round_or_none((purc or 0) * qty),
                    "TotalDiscount": round_or_none((amt or 0) * qty)
                }
                log_df = pd.concat([log_df, pd.DataFrame([new_entry])], ignore_index=True)
                save_log(log_df.drop(columns=["label"], errors="ignore"))
                st.success("✅ Entry logged.")
                st.rerun()

# --- Clear Last Entry ---
st.subheader("🗑️ Log Actions")
if st.button("❌ Clear Last Entry"):
    if not log_df.empty:
        log_df = log_df.iloc[:-1]
        save_log(log_df.drop(columns=["label"], errors="ignore"))
        st.success("✅ Last entry removed.")
        st.rerun()
    else:
        st.warning("⚠️ Log is already empty.")

# --- Display Log ---
st.subheader("📒 Full Log")
if not log_df.empty:
    st.dataframe(log_df.drop(columns=["label"], errors="ignore"), use_container_width=True)
else:
    st.info("No entries yet.")

# --- Summary ---
if not log_df.empty:
    st.subheader("📊 Summary (Daily Totals)")
    log_df["Date"] = pd.to_datetime(log_df["DateTime"]).dt.date
    pivot = log_df.groupby(["Date", "Shop"]).agg({
        "TotalNormal": "sum",
        "TotalPurchase": "sum",
        "TotalDiscount": "sum"
    }).reset_index()
    st.dataframe(pivot, use_container_width=True)
