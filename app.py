import streamlit as st
import pandas as pd

st.set_page_config(page_title="Physics Lab Inventory", layout="wide")

st.title("Physics Lab Inventory — Maintenance View (MVP)")

uploaded_file = "test_directory.xlsx"  # local test copy, same folder as app.py

@st.cache_data
def load_data(path):
    df = pd.read_excel(path, sheet_name="Storage Room Directory")
    df["Shelf"] = df["Shelf"].astype(str)
    return df

directory = load_data(uploaded_file)


# --- Derived status, no separate Retired column needed ---
def compute_status(row):
    if pd.isna(row["Qty_Working"]):
        return "⚠️ Not yet catalogued"
    elif row["Qty_Working"] == 0:
        return "Retired/Out of service"
    elif row["Qty_Working"] < row["Quantity"]:
        return "Partial"
    elif row["Qty_Working"] > row["Quantity"]:
        return "⚠️ Check: working > owned"
    else:
        return "Fully working"

directory["Status"] = directory.apply(compute_status, axis=1)

# --- Filters ---
col1, col2, col3 = st.columns(3)
category_filter = col1.multiselect("Category", sorted(directory["Category"].dropna().unique()))
status_filter = col2.multiselect("Status", sorted(directory["Status"].unique()))
search = col3.text_input("Search by name")

filtered = directory.copy()
if category_filter:
    filtered = filtered[filtered["Category"].isin(category_filter)]
if status_filter:
    filtered = filtered[filtered["Status"].isin(status_filter)]
if search:
    filtered = filtered[filtered["Name"].str.contains(search, case=False, na=False)]

st.dataframe(filtered, width='stretch')

st.caption(f"Showing {len(filtered)} of {len(directory)} items")