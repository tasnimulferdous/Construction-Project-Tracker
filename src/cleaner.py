# src/cleaner.py
from __future__ import annotations
import logging
import re
from datetime import date
from typing import Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ── Summary sheet column indices (0-based) ───────────────────
_COL_DAY_START  = 9
_VEHICLE_DATA_START = 21
_VEHICLE_DATA_END   = 24


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _to_float(val: Any) -> float:
    if val in (None, "", " "):
        return np.nan
    try:
        s = str(val).strip()
        s = re.sub(r"\.{2,}", ".", s)
        return float(s)
    except ValueError:
        return np.nan


def _extract_month_year(sheet_name: str) -> tuple[int, int]:
    month_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4,
        "may": 5, "jun": 6, "jul": 7, "aug": 8,
        "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    match = re.search(r"\(([A-Za-z]{3})(\d{2})\)", sheet_name)
    if match:
        month = month_map.get(match.group(1).lower(), date.today().month)
        year  = 2000 + int(match.group(2))
        return month, year
    today = date.today()
    return today.month, today.year


def _day_to_date(day: int, month: int, year: int) -> pd.Timestamp | None:
    try:
        return pd.Timestamp(year=year, month=month, day=day)
    except ValueError:
        return None


def _is_numeric_or_pct(val: str) -> bool:
    v = val.strip().rstrip("%")
    try:
        float(v)
        return True
    except ValueError:
        return False


def _pad(row: list, length: int = 50) -> list:
    r = list(row)
    while len(r) < length:
        r.append("")
    return r


# ──────────────────────────────────────────────────────────────
# Summary sheet cleaner
# ──────────────────────────────────────────────────────────────

def clean_summary_sheet(
    raw: list[list[Any]],
    sheet_name: str = "Summary (Mar26) ",
) -> pd.DataFrame:
    """
    Parse the Summary sheet into a tidy long DataFrame.

    Layout:
      Rows 1-4 : Metadata
      Row  5   : Headers (index 4)
      Rows 6-18: Work activity data (indices 5-17)
                 Col A(0)=SN (unreliable - has totals/pct)
                 Col B(1)=Work Activities (forward-fill downward)
                 Col C(2)=SD (A/B/D)
                 Col D(3)=Pipe Dia (DN150/DN200/blank)
                 Col E(4)=Qty Upto Feb
                 Col F(5)=Qty Mar (monthly target)
                 Col G(6)=Sum
                 Col H(7)=Unit
                 Col I(8)=blank
                 Col J-AP (9-39)=Day 1-31
      Row 20   : blank
      Row 21+  : Vehicle Usage

    Returns: Activity | SD | Pipe_Dia | Unit | Day | Date |
             Daily_Qty | Qty_Upto_Feb | Qty_Mar
    """
    if not raw or len(raw) < 6:
        logger.warning("clean_summary_sheet: raw data too short")
        return pd.DataFrame()

    month, year = _extract_month_year(sheet_name)
    rows = [_pad(r, 50) for r in raw]

    DATA_START = 5
    DATA_END   = 18

    # Forward-fill SD zone (col C) independently — never reset
    last_sd = ""
    for i in range(DATA_START, min(DATA_END, len(rows))):
        sd_val = str(rows[i][2]).strip()
        if sd_val in ("A", "B", "D"):
            last_sd = sd_val
        rows[i][2] = last_sd

    # Track last explicit activity name from col B
    last_explicit_activity = ""

    records = []
    for i in range(DATA_START, min(DATA_END, len(rows))):
        row = rows[i]

        col_b    = str(row[1]).strip()
        sd       = str(row[2]).strip()
        pipe_dia = str(row[3]).strip()
        unit     = str(row[7]).strip()
        qty_upto = _to_float(row[4])
        qty_mar  = _to_float(row[5])

        # Update explicit activity name when col B has a real name
        if col_b and not _is_numeric_or_pct(col_b):
            last_explicit_activity = col_b

        # Determine effective activity using pipe_dia as the key signal:
        #   - Pipe dia present       → Pipe Installation
        #   - "Service" in last name → Service Pit Installation
        #   - Otherwise              → Road Cutting+Trench excavation
        if pipe_dia:
            activity = "Pipe Installation"
        elif last_explicit_activity and "Service" in last_explicit_activity:
            activity = "Service Pit Installation"
        else:
            activity = "Road Cutting+Trench excavation"

        if not sd or sd not in ("A", "B", "D"):
            continue
        if not qty_upto and not qty_mar:
            continue

        pipe_dia = pipe_dia if pipe_dia else "General"

        for day_offset in range(31):
            col_idx  = 9 + day_offset
            day_num  = day_offset + 1
            val      = _to_float(row[col_idx])
            date_val = _day_to_date(day_num, month, year)
            if date_val is None:
                continue

            records.append({
                "Activity"    : activity,
                "SD"          : sd,
                "Pipe_Dia"    : pipe_dia,
                "Unit"        : unit,
                "Day"         : day_num,
                "Date"        : date_val,
                "Daily_Qty"   : val,
                "Qty_Upto_Feb": qty_upto,
                "Qty_Mar"     : qty_mar,
            })

    if not records:
        logger.warning("clean_summary_sheet: no records parsed")
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df = df.dropna(subset=["Daily_Qty"]).reset_index(drop=True)
    logger.info("clean_summary_sheet: %d daily records", len(df))
    return df


# ──────────────────────────────────────────────────────────────
# Vehicle Usage cleaner
# ──────────────────────────────────────────────────────────────

def clean_vehicle_usage(
    raw: list[list[Any]],
    sheet_name: str = "Summary (Mar26) ",
) -> pd.DataFrame:
    if not raw or len(raw) <= _VEHICLE_DATA_END:
        return pd.DataFrame()

    month, year = _extract_month_year(sheet_name)
    rows = [_pad(r) for r in raw]
    records = []

    for i in range(_VEHICLE_DATA_START, _VEHICLE_DATA_END + 1):
        if i >= len(rows):
            break
        row     = rows[i]
        vehicle = str(row[1]).strip()
        if not vehicle:
            continue

        for day_offset in range(31):
            col_idx  = _COL_DAY_START + day_offset
            day_num  = day_offset + 1
            val      = _to_float(row[col_idx]) if col_idx < len(row) else np.nan
            date_val = _day_to_date(day_num, month, year)
            if date_val is None:
                continue
            records.append({
                "Vehicle": vehicle,
                "Day"    : day_num,
                "Date"   : date_val,
                "Hours"  : val,
            })

    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    return df.dropna(subset=["Hours"]).reset_index(drop=True)


# ──────────────────────────────────────────────────────────────
# Manpower sheet cleaner
# ──────────────────────────────────────────────────────────────

def clean_manpower_sheet(
    raw: list[list[Any]],
    sheet_name: str = "Manpower (Mar26)",
) -> pd.DataFrame:
    """
    Layout:
      Rows 1-8 : Logos, metadata, 3 header rows
      Row 9+   : Data — each date = Day row + Night row
      Col A(0) = Date "12-Mar-26" (only on Day row)
      Col B(1) = Shift "Day"/"Night"
      Col C-P (2-15) = Individual role counts
      Col Q-U (16-20) = Subtotals/Grand Total — SKIP
      Last row = "Total" — SKIP

    Returns: Date | Shift | Company | Role | Count
    """
    if not raw:
        return pd.DataFrame()

    ROLE_COLS = [
        (2,  "CCECC",                   "Management Personnel"),
        (3,  "CCECC",                   "Design Personnel"),
        (4,  "CCECC",                   "Site Personnel"),
        (5,  "CCECC Direct Team",       "Technician"),
        (6,  "CCECC Direct Team",       "Skilled Labour"),
        (7,  "CCECC Direct Team",       "Unskilled Labour"),
        (8,  "Rakib Enterprise (SD-A)", "Engineer"),
        (9,  "Rakib Enterprise (SD-A)", "Technician"),
        (10, "Rakib Enterprise (SD-A)", "Skilled Labour"),
        (11, "Rakib Enterprise (SD-A)", "Unskilled Labour"),
        (12, "Rayhan Traders (SD-D)",   "Engineer"),
        (13, "Rayhan Traders (SD-D)",   "Technician"),
        (14, "Rayhan Traders (SD-D)",   "Skilled Labour"),
        (15, "Rayhan Traders (SD-D)",   "Unskilled Labour"),
    ]

    DATA_START = 8
    rows       = [_pad(r, 22) for r in raw]
    records    = []
    last_date  = None

    for i in range(DATA_START, len(rows)):
        row   = rows[i]
        col_a = str(row[0]).strip()
        col_b = str(row[1]).strip()

        if col_a.lower() == "total" or col_b.lower() == "total":
            break
        if not col_a and not col_b:
            continue

        if col_a:
            try:
                last_date = pd.to_datetime(col_a, dayfirst=True, errors="coerce")
                if pd.isna(last_date):
                    last_date = pd.to_datetime(col_a, format="%d-%b-%y", errors="coerce")
            except Exception:
                last_date = None

        if last_date is None or pd.isna(last_date):
            continue

        shift = col_b if col_b in ("Day", "Night") else "Day"

        for col_idx, company, role in ROLE_COLS:
            val = _to_float(row[col_idx])
            if np.isnan(val):
                val = 0.0
            records.append({
                "Date"   : last_date,
                "Shift"  : shift,
                "Company": company,
                "Role"   : role,
                "Count"  : val,
            })

    if not records:
        logger.warning("clean_manpower_sheet: no records parsed")
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df = df[df["Count"] > 0].reset_index(drop=True)
    logger.info("clean_manpower_sheet: %d records", len(df))
    return df


# ──────────────────────────────────────────────────────────────
# KPI calculator
# ──────────────────────────────────────────────────────────────

def compute_kpis(
    summary_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
) -> dict[str, Any]:
    """
    Compute all KPI values from the summary DataFrame.

    Qty_Upto_Feb and Qty_Mar are stored on every daily row (repeated).
    We deduplicate by Activity+SD+Pipe_Dia before summing targets.
    """
    if summary_df.empty:
        return {k: 0 for k in [
            "total_pipe_installed_rm", "total_pipe_upto_feb",
            "total_excavation_rm", "total_service_pits",
            "active_days", "pct_of_monthly_target", "monthly_target_rm",
        ]}

    mask = (
        (summary_df["Date"] >= date_start)
        & (summary_df["Date"] <= date_end)
    )
    df = summary_df.loc[mask]

    def _sum(activity_kw: str, unit_kw: str = "") -> float:
        sub = df[df["Activity"].str.contains(activity_kw, case=False, na=False)]
        if unit_kw:
            sub = sub[sub["Unit"].str.contains(unit_kw, case=False, na=False)]
        return float(sub["Daily_Qty"].sum())

    # Deduplicate meta per Activity+SD+Pipe_Dia (values repeat on every day row)
    meta = summary_df.drop_duplicates(subset=["Activity", "SD", "Pipe_Dia"])

    pipe_meta  = meta[meta["Activity"].str.contains("Pipe",        case=False, na=False)]
    excav_meta = meta[meta["Activity"].str.contains("Road Cutting", case=False, na=False)]
    pit_meta   = meta[meta["Activity"].str.contains("Service Pit", case=False, na=False)]

    monthly_target = float(pipe_meta["Qty_Mar"].sum())      if not pipe_meta.empty  else 0.0
    pipe_upto_feb  = float(pipe_meta["Qty_Upto_Feb"].sum()) if not pipe_meta.empty  else 0.0

    pipe_installed = _sum("Pipe",         "rm")
    excav_actual   = _sum("Road Cutting", "rm")
    pits_actual    = _sum("Service Pit",  "Pcs")
    pct            = round(pipe_installed / monthly_target * 100, 1) if monthly_target else 0.0

    return {
        "total_pipe_installed_rm": pipe_installed,
        "total_pipe_upto_feb"    : pipe_upto_feb,
        "total_excavation_rm"    : excav_actual,
        "total_service_pits"     : pits_actual,
        "active_days"            : int(df["Date"].nunique()),
        "pct_of_monthly_target"  : pct,
        "monthly_target_rm"      : monthly_target,
    }