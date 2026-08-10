import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(page_title="MCLA Physics Lab Inventory", layout="wide")

@st.cache_data(ttl=600)
def load_workbook():
    url = st.secrets["onedrive_url"]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return pd.read_excel(BytesIO(response.content), sheet_name=None)

if st.sidebar.button("🔄 Refresh data"):
    st.cache_data.clear()

xls = load_workbook()

directory = xls["Storage Room Directory"].copy()
directory["Name"] = directory["Name"].astype(str).str.strip()
directory["Shelf"] = directory["Shelf"].astype(str)

experiments = xls["Experiment Directory"].copy()
experiments["Item_Name"] = experiments["Item_Name"].astype(str).str.strip()
experiments["Experiment_Name"] = experiments["Experiment_Name"].astype(str).str.strip()

# --- Department Overview, loaded once, used by multiple pages ---
dept = xls["Department Overview"].copy()
dept.columns = dept.columns.str.strip().str.rstrip(":")
dept["Course Code"] = dept["Course Code"].astype(str).str.strip()
dept["Course Title"] = dept["Course Title"].astype(str).str.strip()
course_map = dict(zip(dept["Course Code"], dept["Course Title"]))

# --- Auto-derive Used_In_Experiments from Experiment Directory ---
lookup = experiments.groupby("Item_Name")["Experiment_Name"].apply(
    lambda names: ", ".join(sorted(set(names)))
)
directory["Used_In_Experiments"] = directory["Name"].map(lookup).fillna("—")

# --- Derived status for Maintenance View ---
def compute_status(row):
    if pd.isna(row["Qty_Working"]):
        return "Not yet catalogued"
    elif row["Qty_Working"] == 0:
        return "Retired/Out of service"
    elif row["Qty_Working"] < row["Quantity"]:
        return "Partial"
    elif row["Qty_Working"] > row["Quantity"]:
        return "⚠️ Check: working > owned"
    else:
        return "Fully working"

directory["Status"] = directory.apply(compute_status, axis=1)

# ================= PAGE NAVIGATION =================
page = st.sidebar.radio("View", ["Course Overview", "Maintenance View", "Browse by Experiment"])

# ================= MAINTENANCE VIEW =================
if page == "Maintenance View":
    st.title("Physics Lab Inventory — Maintenance View")

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

    st.dataframe(filtered, width="stretch")
    st.caption(f"Showing {len(filtered)} of {len(directory)} items")

# ================= BROWSE BY EXPERIMENT =================
elif page == "Browse by Experiment":
    st.title("Browse by Experiment")
    st.caption(
        "Pick a course and experiment, enter your station count, and see what's ready and what's short. "
        "Live from the storage room inventory Excel file."
    )

    all_courses = sorted(set(
        c.strip() for tags in experiments["Course_Tags"].dropna()
        for c in str(tags).split(",")
    ))

    course_display = {code: f"{code} — {course_map.get(code, 'Unknown')}" for code in all_courses}
    display_to_code = {v: k for k, v in course_display.items()}

    selected_display = st.selectbox("Course", ["All"] + list(course_display.values()))
    selected_course = "All" if selected_display == "All" else display_to_code[selected_display]

    if selected_course == "All":
        course_experiments = experiments
    else:
        course_experiments = experiments[
            experiments["Course_Tags"].str.contains(selected_course, na=False)
        ]

    experiment_names = sorted(course_experiments["Experiment_Name"].dropna().unique())
    if not experiment_names:
        st.info("No experiments found for this course yet.")
    else:
        selected_experiment = st.selectbox("Experiment", experiment_names)

        num_stations = st.number_input("Number of stations", min_value=1, value=1, step=1)

        exp_rows = experiments[experiments["Experiment_Name"] == selected_experiment].copy()
        exp_rows["Total_Needed"] = exp_rows["Quantity/Station"] * num_stations
        exp_rows = exp_rows.drop(columns=["Category", "Shelf"], errors="ignore")

        merged = exp_rows.merge(
            directory[["Name", "Qty_Working", "Category", "Shelf", "Last_Checked"]],
            left_on="Item_Name", right_on="Name", how="left"
        )

        def item_status(row):
            if pd.isna(row["Qty_Working"]):
                return "❓ Not catalogued"
            elif row["Qty_Working"] >= row["Total_Needed"]:
                return "✅ Ready"
            else:
                return "❌ Short"

        merged["Status"] = merged.apply(item_status, axis=1)

        st.subheader(selected_experiment)
        overall = "✅ Ready" if (merged["Status"] == "✅ Ready").all() else "❌ Short / Incomplete"
        st.metric("Overall Status", overall)

        st.dataframe(
            merged[["Item_Name", "Quantity/Station", "Total_Needed", "Qty_Working", "Category", "Shelf", "Status"]],
            width="stretch"
        )

# ================= COURSE OVERVIEW =================
elif page == "Course Overview":
    st.title("Course Overview")
    st.caption("All courses currently tracked, with instructor and semester info.")

    search = st.text_input("Search by course code or title")
    filtered_dept = dept.copy()
    if search:
        filtered_dept = filtered_dept[
            filtered_dept["Course Code"].str.contains(search, case=False, na=False) |
            filtered_dept["Course Title"].str.contains(search, case=False, na=False)
        ]

    st.dataframe(filtered_dept, width="stretch")