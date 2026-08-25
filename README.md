# LabInvMngr
# MCLA Physics Lab Inventory Manager

This app is a live window into one Excel file. You never need to touch the code —
everything you see in the app comes directly from three tabs in that spreadsheet.
This guide explains what to type where, and exactly what shows up in the app as a result.

The workbook lives on OneDrive/SharePoint. The app re-reads it automatically about
once an hour, or immediately if someone clicks "🔄 Refresh data" in the sidebar.

---

## The three tabs, and what each one controls

### 1. Storage Room Directory
This is the master list of every physical item in storage rooms 111B and 109.
It drives the **Inventory** page, and is also what every other page checks
against to see what's actually available.

| Column | What to type | What happens in the app |
|---|---|---|
| **Name** | The item's name, e.g. `Motion Sensor` | Shown as the item's name everywhere in the app. **This must match exactly** (same spelling/capitalization) wherever this item is referenced in the Experiment Directory tab — see the linking note below. |
| **Category** | A grouping label, e.g. `Mechanics`, `Optics` | Becomes a filter dropdown on the Inventory page. |
| **Shelf** | Shelf location, e.g. `A3` | Shown as a column so someone can physically find the item. |
| **Quantity** | Total number owned | Shown as a column. |
| **Qty_Working** | Number currently working | Compared against Quantity to color-code the item's status (see below). **Leave this blank** if the item hasn't been counted/checked yet — don't put a `0` unless it's genuinely fully retired. |
| **Last_Checked** | A date | Shown as a short date on the Inventory page. |

**Do not fill in:**
- **Used_In_Experiments** — even if this column exists in the sheet, whatever you type there is ignored. The app rebuilds this automatically by scanning the Experiment Directory tab every time it loads.
- **Status** — don't add this column at all. The app calculates it automatically from Quantity vs. Qty_Working:

| If... | Status shown |
|---|---|
| Qty_Working is blank | 🔵 Not yet catalogued |
| Qty_Working = 0 | ⚪ Retired/Out of service |
| Qty_Working < Quantity | 🟡 Partial |
| Qty_Working = Quantity | 🟢 Fully working |
| Qty_Working > Quantity | 🔴 Flagged — likely a typo, worth double-checking |

**Bonus:** any *other* column you add to this tab (a Notes column, a Photo link, whatever) will automatically show up as an extra column on the Inventory page. No one needs to touch the app for that — it just appears.

---

### 2. Experiment Directory
This is the list of every experiment and demo, and what equipment each one needs.
It drives the **Check an Experiment/Demo** and **Experiment/Demo Library** pages.

**Important shape of this tab:** each row is one *item* needed for one *experiment* —
not one row per experiment. If "Pendulum Motion" needs 3 different items, that's 3 rows,
all with `Experiment_Name` set to `Pendulum Motion`.

| Column | What to type | What happens in the app |
|---|---|---|
| **Experiment_Name** | The experiment/demo's name | Shown as the heading in the Library, and as an option in the "Check an Experiment/Demo" dropdown. Repeat the exact same name on every row that belongs to this experiment. |
| **Topic/Category** | A grouping label, e.g. `Rotational`, `Optics` | Becomes the section heading on the Experiment/Demo Library page. |
| **Course_Tags** | Course code(s), comma-separated, e.g. `Phys 131, Phys 132` | Determines which course(s) this experiment appears under on the "Check" page's course dropdown. **Must be spelled and spaced exactly like the Course Code in the Department Overview tab** — `Phys 131` and `Phys131` are treated as different codes. |
| **Item_Name** | The item needed, e.g. `Motion Sensor` | The app looks this up against the Storage Room Directory's **Name** column. If it matches exactly, the app can check whether it's in stock. If it doesn't match (typo, different name), the item shows as **"🚫 Not in inventory"** even if the item actually exists on a shelf somewhere. |
| **Quantity/Station** | How many of this item needed per lab station | Multiplied by however many stations someone enters, to figure out Ready vs. Short. |
| **Links** | Full URL to the PDF write-up (OneDrive/SharePoint share link) | If filled in, a working "📄 PDF" button appears next to this experiment on both the Library page and the Check page. If left blank, the button still appears but is greyed out and says "Write-up not available." |

---

### 3. Department Overview
The simplest tab — just a list of courses. Drives the **Courses** page and the
course dropdown on **Check an Experiment/Demo**.

| Column | What to type | What happens in the app |
|---|---|---|
| **Course Code** | Short code, e.g. `Phys 131` | Must match the spelling/spacing used in Course_Tags on the Experiment Directory tab. |
| **Course Title** | Full course name | Shown alongside the code everywhere. |
| Any other column (Taught By, Semester, etc.) | Anything | Shown as-is on the Courses page. |

---

## Common tasks

**Adding a new item to inventory:**
Add a row to Storage Room Directory. Fill in Name, Category, Shelf, Quantity.
Leave Qty_Working blank until someone's actually counted it — it'll show as
"Not yet catalogued" until then, which is exactly the point.

**Marking something broken or retired:**
Find its row in Storage Room Directory, set Qty_Working to `0`. Status updates
automatically to "Retired/Out of service."

**Adding a new experiment/demo:**
Add one row to Experiment Directory *per item* it needs, all sharing the same
Experiment_Name. Double-check every Item_Name matches an existing Name in
Storage Room Directory exactly, or those items will show as not in inventory
even though they're really just a spelling mismatch.

**Adding a write-up for an existing experiment:**
Find any row for that experiment in Experiment Directory, paste the OneDrive
link into the Links column. Only needs to be on one row — all rows for the
same experiment share it.

**Adding a new course:**
Add a row to Department Overview. If you also want experiments tagged to it,
make sure Course_Tags on those experiment rows uses the identical code.

---

## Things that will cause confusion (not errors, just mismatches)

- **Spelling/capitalization mismatches** between Name (Storage Room Directory) and Item_Name (Experiment Directory) — the two must match exactly, or the app will think the item isn't in stock.
- **Spacing mismatches** in course codes (`Phys 131` vs `Phys131`) between Course_Tags and Course Code — same issue, the course filter just won't find it.
- **Renaming the tab names themselves** (Storage Room Directory / Experiment Directory / Department Overview) — the app looks for these exact three tab names. Renaming a tab will break that page until it's renamed back.
- **Renaming column headers** the app relies on (Name, Category, Shelf, Quantity, Qty_Working, Last_Checked, Experiment_Name, Topic/Category, Course_Tags, Item_Name, Quantity/Station, Links, Course Code, Course Title) — adding new columns is always safe; renaming these specific ones isn't.

Everything else — new columns, new rows, reordering rows, formatting cells — is safe to
change freely and won't break anything.
