import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(page_title="MCLA Physics Lab Inventory", layout="wide", page_icon="🔬")

# ================= GLOBAL STYLE =================
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid var(--primary-color);
        border-radius: 10px;
        padding: 12px 16px;
    }
</style>
""", unsafe_allow_html=True)

STATUS_TINTS = {
    "Fully working":              "background-color:#E3F3E1; color:#1F6D1B;",
    "✅ Ready":                    "background-color:#E3F3E1; color:#1F6D1B;",
    "Partial":                     "background-color:#FFF6D8; color:#8A6D00;",
    "Not yet catalogued":          "background-color:#E3F1FB; color:#045A8D;",
    "❓ Not catalogued":           "background-color:#E3F1FB; color:#045A8D;",
    "Retired/Out of service":      "background-color:#ECECEC; color:#555555;",
    "🚫 Not in inventory":         "background-color:#ECECEC; color:#555555;",
    "⚠️ Check: working > owned":  "background-color:#FBE3E3; color:#B00020;",
    "❌ Short":                    "background-color:#FBE3E3; color:#B00020;",
}

def style_status(val):
    return STATUS_TINTS.get(val, "")

@st.cache_data(ttl=3600)
def load_workbook():
    url = st.secrets["onedrive_url"]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return pd.read_excel(BytesIO(response.content), sheet_name=None)
    except Exception:
        st.error(
            "Couldn't load the inventory data. This sometimes happens right after the app "
            "wakes up from sleep — try refreshing the page in a few seconds."
        )
        st.stop()

if st.sidebar.button("🔄 Refresh data"):
    st.cache_data.clear()

xls = load_workbook()

directory = xls["Storage Room Directory"].copy()
directory["Name"] = directory["Name"].astype(str).str.strip()
directory["Shelf"] = directory["Shelf"].astype(str)

experiments = xls["Experiment Directory"].copy()
experiments["Item_Name"] = experiments["Item_Name"].astype(str).str.strip()
experiments["Experiment_Name"] = experiments["Experiment_Name"].astype(str).str.strip()

dept = xls["Department Overview"].copy()
dept.columns = dept.columns.str.strip().str.rstrip(":")
dept["Course Code"] = dept["Course Code"].astype(str).str.strip()
dept["Course Title"] = dept["Course Title"].astype(str).str.strip()
course_map = dict(zip(dept["Course Code"], dept["Course Title"]))

try:
    lookup = experiments.groupby("Item_Name")["Experiment_Name"].apply(
        lambda names: ", ".join(sorted(set(names.dropna())))
    )
    directory["Used_In_Experiments"] = directory["Name"].map(lookup).fillna("—")
except Exception:
    st.warning(
        "⚠️ The Experiment Directory looks like it's being edited right now (some rows are "
        "incomplete). Please finish filling out the row you're working on, then refresh this "
        "page in a minute."
    )
    directory["Used_In_Experiments"] = "—"

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

# ================= PAGE IDENTITY =================
# Internal keys drive all logic below. PAGE_LABELS is the ONLY thing you need to
# edit to rename a page again later — nothing else in the file references the text.
PAGE_KEYS = ["experiment_library","check_experiment", "build_demo", "inventory","courses" ]

PAGE_LABELS = {
    "courses": "Courses",
    "inventory": "Inventory",
    "check_experiment": "Check an Experiment/Demo",
    "build_demo": "Build a New Demo",
    "experiment_library": "Experiment/Demo Library",
}

PAGE_ICONS = {
    "courses": "🎓",
    "inventory": "📦",
    "check_experiment": "🔍",
    "build_demo": "🧪",
    "experiment_library": "📚",
}


# ================= SIDEBAR =================
st.sidebar.markdown("### 🔬 MCLA Physics Lab Inventory")
st.sidebar.caption("Storage rooms 111B & 109")
st.sidebar.divider()

if "nav_radio" not in st.session_state:
    st.session_state.nav_radio = PAGE_KEYS[0]

# Apply any redirect requested elsewhere (e.g. a "Check" button) BEFORE the radio
# below is created. Doing it here — rather than inside the button's branch further
# down the script — avoids Streamlit's error for setting a widget's own state after
# that widget has already rendered earlier in the same run.
if "pending_page" in st.session_state:
    st.session_state.nav_radio = st.session_state.pop("pending_page")

page = st.sidebar.radio(
    "View", PAGE_KEYS,
    format_func=lambda k: f"{PAGE_ICONS[k]}  {PAGE_LABELS[k]}",
    key="nav_radio",
)

# ================= INVENTORY =================
if page == "inventory":
    st.title(f"{PAGE_ICONS['inventory']} {PAGE_LABELS['inventory']}")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total items", len(directory))
    k2.metric("Fully working", int((directory["Status"] == "Fully working").sum()))
    k3.metric("Needs attention", int(directory["Status"].isin(
        ["Partial", "⚠️ Check: working > owned"]).sum()))
    k4.metric("Not yet catalogued", int((directory["Status"] == "Not yet catalogued").sum()))

    st.divider()

    col1, col2, col3 = st.columns(3)
    category_filter = col1.multiselect("📁 Category", sorted(directory["Category"].dropna().unique()))
    status_filter = col2.multiselect("🚦 Status", sorted(directory["Status"].unique()))
    search = col3.text_input("🔎 Search by name")

    filtered = directory.copy()
    if category_filter:
        filtered = filtered[filtered["Category"].isin(category_filter)]
    if status_filter:
        filtered = filtered[filtered["Status"].isin(status_filter)]
    if search:
        filtered = filtered[filtered["Name"].str.contains(search, case=False, na=False)]

    if filtered.empty:
        st.info("No items match these filters. Try clearing one of the filters above.")
    else:
        display_cols = ["Name"] + [c for c in filtered.columns if c != "Name"]
        st.dataframe(
            filtered[display_cols].style.map(style_status, subset=["Status"]),
            width="stretch",
            hide_index=True,
        )
        st.caption(f"Showing {len(filtered)} of {len(directory)} items")

# ================= CHECK AN EXPERIMENT =================
elif page == "check_experiment":
    st.title(f"{PAGE_ICONS['check_experiment']} {PAGE_LABELS['check_experiment']}")
    st.caption(
        "Pick a course and experiment, enter your station count, and see what's ready and what's short. "
        "Live from the storage room inventory Excel file. If a write-up is available for the experiment, "
        "use the 📄 PDF button to open it."
    )

    all_courses = sorted(set(
        c.strip() for tags in experiments["Course_Tags"].dropna()
        for c in str(tags).split(",")
    ))

    course_display = {code: f"{code} — {course_map.get(code, 'Unknown')}" for code in all_courses}
    display_to_code = {v: k for k, v in course_display.items()}

    if "jump_experiment" in st.session_state:
        st.session_state.browse_course_select = "All"

    selected_display = st.selectbox(
        "🎓 Course", ["All"] + list(course_display.values()), key="browse_course_select"
    )
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
        if "jump_experiment" in st.session_state:
            if st.session_state.jump_experiment in experiment_names:
                st.session_state.browse_experiment_select = st.session_state.jump_experiment
            del st.session_state["jump_experiment"]

        selected_experiment = st.selectbox("🧪 Experiment", experiment_names, key="browse_experiment_select")
        num_stations = st.number_input("👥 Number of stations", min_value=1, value=1, step=1)

        exp_rows = experiments[experiments["Experiment_Name"] == selected_experiment].copy()
        exp_rows["Total_Needed"] = exp_rows["Quantity/Station"] * num_stations
        exp_rows = exp_rows.drop(columns=["Category", "Shelf"], errors="ignore")

        merged = exp_rows.merge(
            directory[["Name", "Qty_Working", "Category", "Shelf", "Last_Checked"]],
            left_on="Item_Name", right_on="Name", how="left"
        )

        def item_status(row):
            if pd.isna(row["Name"]):
                return "🚫 Not in inventory"
            elif pd.isna(row["Qty_Working"]):
                return "❓ Not catalogued"
            elif row["Qty_Working"] >= row["Total_Needed"]:
                return "✅ Ready"
            else:
                return "❌ Short"

        merged["Status"] = merged.apply(item_status, axis=1)

        with st.container(border=True):
            st.subheader(selected_experiment)
            overall = "✅ Ready" if (merged["Status"] == "✅ Ready").all() else "❌ Short / Incomplete"
            st.metric("Overall Status", overall)

            exp_links = exp_rows["Links"].dropna().astype(str).str.strip()
            exp_links = exp_links[exp_links.str.lower() != "nan"]
            if not exp_links.empty:
                st.link_button("📄 PDF", exp_links.iloc[0])
            else:
                st.button("📄 PDF", key="pdf_disabled_check_page", disabled=True, help="Write-up not available")

            display_cols = merged[["Item_Name", "Quantity/Station", "Total_Needed", "Qty_Working",
                                    "Category", "Shelf", "Status"]]
            st.dataframe(display_cols.style.map(style_status, subset=["Status"]), width="stretch", hide_index=True)

# ================= COURSES =================
elif page == "courses":
    st.title(f"{PAGE_ICONS['courses']} {PAGE_LABELS['courses']}")
    st.caption(f"{len(dept)} courses currently tracked, with instructor and semester info.")

    search = st.text_input("🔎 Search by course code or title")
    filtered_dept = dept.copy()
    if search:
        filtered_dept = filtered_dept[
            filtered_dept["Course Code"].str.contains(search, case=False, na=False) |
            filtered_dept["Course Title"].str.contains(search, case=False, na=False)
        ]

    st.dataframe(filtered_dept, width="stretch", hide_index=True)

# ================= BUILD A NEW DEMO =================
elif page == "build_demo":
    st.title(f"{PAGE_ICONS['build_demo']} {PAGE_LABELS['build_demo']}")
    st.caption(
        "Build a list of items for a new demo idea. Select an existing item, or type "
        "a new one if it's not in our inventory yet — it'll still show up, flagged as unavailable."
    )

    if "demo_items" not in st.session_state:
        st.session_state.demo_items = []

    existing_names = sorted(directory["Name"].dropna().unique())
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    with col1:
        dropdown_pick = st.selectbox("Select existing item", ["—"] + existing_names, key="item_picker")
    with col2:
        typed_pick = st.text_input("...or type a new item", key="new_item_name")
    with col3:
        qty_needed = st.number_input("Qty needed", min_value=1, value=1, step=1, key="qty_picker")
    with col4:
        st.write("")
        st.write("")
        if st.button("➕ Add"):
            item_name = typed_pick.strip() if typed_pick.strip() else (dropdown_pick if dropdown_pick != "—" else "")
            if item_name:
                st.session_state.demo_items.append(
                    {"Item_Name": item_name, "Quantity_Needed": qty_needed}
                )

    if st.session_state.demo_items:
        with st.container(border=True):
            st.subheader("Items for this demo")

            check_df = pd.DataFrame(st.session_state.demo_items)
            merged = check_df.merge(
                directory[["Name", "Qty_Working", "Category", "Shelf"]],
                left_on="Item_Name", right_on="Name", how="left"
            )

            def check_status(row):
                if pd.isna(row["Qty_Working"]):
                    return "🚫 Not in inventory"
                elif row["Qty_Working"] >= row["Quantity_Needed"]:
                    return "✅ Ready"
                else:
                    return "❌ Short"

            merged["Status"] = merged.apply(check_status, axis=1)

            display_cols = merged[["Item_Name", "Quantity_Needed", "Qty_Working", "Category", "Shelf", "Status"]]
            st.dataframe(display_cols.style.map(style_status, subset=["Status"]), width="stretch", hide_index=True)

            overall = "✅ Ready" if (merged["Status"] == "✅ Ready").all() else "❌ Missing or short on items"
            st.metric("Overall Status", overall)

            remove_choice = st.selectbox(
                "Remove an item", ["—"] + [d["Item_Name"] for d in st.session_state.demo_items]
            )
            if remove_choice != "—" and st.button("✖ Remove selected"):
                st.session_state.demo_items = [
                    d for d in st.session_state.demo_items if d["Item_Name"] != remove_choice
                ]
                st.rerun()
    else:
        st.info("No items added yet — pick one above or type a new one, then hit ➕ Add.")

    st.divider()

    st.subheader("Ask an AI for suggestions")
    st.caption(
        "Type your own question first (e.g. \"do we have what we need for this demo?\" or "
        "\"suggest an experiment using only these items\"), then paste the inventory list below it."
    )

    with st.expander("Show inventory list to copy"):
        item_names_only = sorted(directory["Name"].dropna().unique())
        inventory_list_text = "\n".join(f"- {name}" for name in item_names_only)
        st.code(inventory_list_text, language=None)

# ================= EXPERIMENT LIBRARY =================
elif page == "experiment_library":
    st.title(f"{PAGE_ICONS['experiment_library']} {PAGE_LABELS['experiment_library']}")
    st.caption("Browse past experiments by topic. Use 🔍 Check for live inventory status, or 📄 PDF to open the write-up.")

    exp_summary = experiments.dropna(subset=["Experiment_Name"]).drop_duplicates(subset=["Experiment_Name"])
    categories = sorted(exp_summary["Topic/Category"].dropna().unique())

    for category in categories:
        st.subheader(category)
        cat_experiments = exp_summary[exp_summary["Topic/Category"] == category].sort_values("Experiment_Name")

        for _, row in cat_experiments.iterrows():
            name = row["Experiment_Name"]
            link = row.get("Links", None)
            has_link = pd.notna(link) and str(link).strip() and str(link).lower() != "nan"

            with st.container(border=True):
                col1, col2, col3 = st.columns([1, 1, 5])

                with col3:
                    if st.button("🔍 Check", key=f"check_{name}"):
                        st.session_state.jump_experiment = name
                        st.session_state.pending_page = "check_experiment"
                        st.rerun()

                with col2:
                    if has_link:
                        st.link_button("📄 PDF", link, key=f"pdf_{name}")
                    else:
                        st.button("📄 PDF", key=f"pdf_disabled_{name}", disabled=True, help="Write-up not available")

                with col1:
                    st.write(name)