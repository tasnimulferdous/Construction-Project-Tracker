# src/cleaner.py
# ============================================================
#  ETL engine for CCECC Master Tracker Google Sheets.
#
#  SUMMARY SHEET LAYOUT (e.g. "Summary (Mar26) "):
#    Rows 1-4  : Metadata
#    Row  5    : Headers: SN | Work Activities | SD | Pipe Dia |
#                Work Qty (Upto Feb) | Work Qty (Mar) | Sum | Unit |
#                [blank] | 1..31 (days) | Week1..Week5
#    Rows 6-18 : Work activity data
#    Rows 21-24: Vehicle Usage data
#
#  MANPOWER SHEET LAYOUT (e.g. "Manpower (Mar26)"):
#    Rows 1-4  : Logos and project metadata
#    Row  5    : "Manpower Engaged : Summary" title
#    Row  6    : Group headers (CCECC | CCECC Direct Team | Sub Contractor...)
#    Row  7    : Role sub-headers (Management Personnel | Design Personnel ...)
#    Row  8+   : Data rows — each DATE has TWO rows: Day shift + Night shift
#                Col A = Date (only filled on "Day" row, blank on "Night" row)
#                Col B = Shift ("Day" / "Night")
#                Col C = Management Personnel (15)
#                Col D = Design Personnel (4)
#                Col E = Site Personnel (10)
#                Col F = Technician (CCECC Direct)
#                Col G = Skilled Labour (CCECC Direct)
#                Col H = Unskilled Labour (CCECC Direct)
#                Col I = Engineer (Rakib SD-A)
#                Col J = Technician (Rakib SD-A)
#                Col K = Skilled Labour (Rakib SD-A)
#                Col L = Unskilled Labour (Rakib SD-A)
#                Col M = Engineer (Rayhan SD-D)
#                Col N = Technician (Rayhan SD-D)
#                Col O = Skilled Labour (Rayhan SD-D)
#                Col P = Unskilled Labour (Rayhan SD-D)
#                Col Q = CCECC Sub Total
#                Col R = CCECC Direct Team Sub Total
#                Col S = RakibEnterprise Sub Total
#                Col T = Rayhan Traders Sub Total
#                Col U = Total  ← DO NOT SUM THIS
#    Last row  : "Total" summary row — must be excluded
# ============================================================

from __future__ import annotations
import logging
import re
from datetime import date
from typing import Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ── Summary sheet column indices (0-based) ───────────────────
_COL_SN         = 0
_COL_ACTIVITY   = 1
_COL_SD         = 2
_COL_PIPE_DIA   = 3
_COL_QTY_UPTO   = 4
_COL_QTY_MAR    = 5
_COL_SUM        = 6
_COL_UNIT       = 7
_COL_DAY_START  = 9    # Column J = Day 1
_COL_DAY_END    = 39   # Column AP = Day 31
_COL_WEEK_START = 40
_COL_WEEK_END   = 44

_SUMMARY_DATA_START  = 5   # Row 6 (0-based index 5)
_SUMMARY_DATA_END    = 18  # Row 19 (exclusive)
_VEHICLE_DATA_START  = 21
_VEHICLE_DATA_END    = 24

# ── Manpower sheet column indices (0-based) ──────────────────
_MP_COL_DATE      = 0   # A — Date (only on Day row)
_MP_COL_SHIFT     = 1   # B — "Day" or "Night"
_MP_COL_MGMT      = 2   # C — Management Personnel
_MP_COL_DESIGN    = 3   # D — Design Personnel
_MP_COL_SITE      = 4   # E — Site Personnel
_MP_COL_TECH_D    = 5   # F — Technician (Direct)
_MP_COL_SKILL_D   = 6   # G — Skilled Labour (Direct)
_MP_COL_UNSKILL_D = 7   # H — Unskilled Labour (Direct)
_MP_COL_ENG_A     = 8   # I — Engineer (Rakib SD-A)
_MP_COL_TECH_A    = 9   # J — Technician (Rakib SD-A)
_MP_COL_SKILL_A   = 10  # K — Skilled Labour (Rakib SD-A)
_MP_COL_UNSKILL_A = 11  # L — Unskilled Labour (Rakib SD-A)
_MP_COL_ENG_D     = 12  # M — Engineer (Rayhan SD-D)
_MP_COL_TECH_D2   = 13  # N — Technician (Rayhan SD-D)
_MP_COL_SKILL_D2  = 14  # O — Skilled Labour (Rayhan SD-D)
_MP_COL_UNSKILL_D2= 15  # P — Unskilled Labour (Rayhan SD-D)
_MP_COL_TOTAL     = 20  # U — Grand Total (skip this)

# Role labels matching the columns above
_MP_ROLES = [
    ("CCECC", "Management Personnel"),       # C
    ("CCECC", "Design Personnel"),           # D
    ("CCECC", "Site Personnel"),             # E
    ("CCECC Direct", "Technician"),          # F
    ("CCECC Direct", "Skilled Labour"),      # G
    ("CCECC Direct", "Unskilled Labour"),    # H
    ("Rakib Enterprise (SD-A)", "Engineer"),         # I
    ("Rakib Enterprise (SD-A)", "Technician"),       # J
    ("Rakib Enterprise (SD-A)", "Skilled Labour"),   # K
    ("Rakib Enterprise (SD-A)", "Unskilled Labour"), # L
    ("Rayhan Traders (SD-D)", "Engineer"),           # M
    ("Rayhan Traders (SD-D)", "Technician"),         # N
    ("Rayhan Traders (SD-D)", "Skilled Labour"),     # O
    ("Rayhan Traders (SD-D)", "Unskilled Labour"),   # P
]
_MP_DATA_COL_INDICES = list(range(2, 16))  # C through P (indices 2-15)
_MP_DATA_START_ROW   = 7  # Row 8 (0-based index 7) — first data row


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
    if not raw or len(raw) <= _SUMMARY_DATA_START:
        logger.warning("clean_summary_sheet: raw data is empty or too short")
        return pd.DataFrame()

    month, year = _extract_month_year(sheet_name)
    rows = [_pad(r) for r in raw]

    last_activity = ""
    last_sn = ""
    for i in range(_SUMMARY_DATA_START, min(len(rows), _SUMMARY_DATA_END)):
        sn_val  = str(rows[i][_COL_SN]).strip()
        act_val = str(rows[i][_COL_ACTIVITY]).strip()
        if sn_val and sn_val not in ("", "0"):
            last_sn = sn_val
        if act_val:
            last_activity = act_val
        rows[i][_COL_SN]       = last_sn
        rows[i][_COL_ACTIVITY] = last_activity

    records = []
    for i in range(_SUMMARY_DATA_START, min(len(rows), _SUMMARY_DATA_END)):
        row       = rows[i]
        activity  = str(row[_COL_ACTIVITY]).strip()
        sd        = str(row[_COL_SD]).strip()
        pipe_dia  = str(row[_COL_PIPE_DIA]).strip()
        unit      = str(row[_COL_UNIT]).strip()
        qty_upto  = _to_float(row[_COL_QTY_UPTO])
        qty_mar   = _to_float(row[_COL_QTY_MAR])

        if not activity:
            continue

        for day_offset in range(31):
            col_idx  = _COL_DAY_START + day_offset
            day_num  = day_offset + 1
            val      = _to_float(row[col_idx]) if col_idx < len(row) else np.nan
            date_val = _day_to_date(day_num, month, year)
            if date_val is None:
                continue

            records.append({
                "Activity"    : activity,
                "SD"          : sd or "N/A",
                "Pipe_Dia"    : pipe_dia or "General",
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
    logger.info("clean_summary_sheet: %d records", len(df))
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
# Manpower sheet cleaner  (rewritten for actual structure)
# ──────────────────────────────────────────────────────────────

def clean_manpower_sheet(
    raw: list[list[Any]],
    sheet_name: str = "Manpower (Mar26)",
) -> pd.DataFrame:
    """
    Parse the Manpower sheet.

    Structure:
      Row 8+  : Date (col A, only on Day row) | Shift (col B: Day/Night)
                | role counts in cols C-P (indices 2-15)
      Last row: "Total" — excluded
      Col U (index 20) = grand total — never summed directly

    Returns
    -------
    pd.DataFrame: Date | Shift | Company | Role | Count
    """
    if not raw:
        return pd.DataFrame()

    month, year = _extract_month_year(sheet_name)
    rows = [_pad(r, 25) for r in raw]

    records = []
    last_date_str = ""

    for i in range(_MP_DATA_START_ROW, len(rows)):
        row = rows[i]

        # Skip the grand Total summary row at the bottom
        col_a = str(row[_MP_COL_DATE]).strip()
        col_b = str(row[_MP_COL_SHIFT]).strip()

        if col_a.lower() == "total" or col_b.lower() == "total":
            continue

        # Forward-fill the date from the Day row into the Night row
        if col_a:
            last_date_str = col_a
        if not last_date_str:
            continue

        shift = col_b if col_b in ("Day", "Night") else "Day"

        # Parse the date — it comes as "19-Mar-26" or similar
        try:
            parsed_date = pd.to_datetime(last_date_str, dayfirst=True, errors="coerce")
            if pd.isna(parsed_date):
                # Try explicit format
                parsed_date = pd.to_datetime(
                    last_date_str, format="%d-%b-%y", errors="coerce"
                )
            if pd.isna(parsed_date):
                continue
        except Exception:
            continue

        # Read each role column (C through P = indices 2-15)
        for col_offset, (company, role) in enumerate(_MP_ROLES):
            col_idx = _MP_DATA_COL_INDICES[col_offset]
            val     = _to_float(row[col_idx])
            if np.isnan(val):
                val = 0.0

            records.append({
                "Date"   : parsed_date,
                "Shift"  : shift,
                "Company": company,
                "Role"   : role,
                "Count"  : val,
            })

    if not records:
        logger.warning("clean_manpower_sheet: no records parsed")
        return pd.DataFrame()

    df = pd.DataFrame(records)
    # Drop rows where count is 0 to keep data lean
    df = df[df["Count"] > 0].reset_index(drop=True)
    logger.info("clean_manpower_sheet: %d role-day records", len(df))
    return df


# ──────────────────────────────────────────────────────────────
# KPI calculator
# ──────────────────────────────────────────────────────────────

def compute_kpis(
    summary_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
) -> dict[str, Any]:
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

    pipe_df        = summary_df[summary_df["Activity"].str.contains("Pipe", case=False, na=False)]
    monthly_target = float(pipe_df["Qty_Mar"].drop_duplicates().sum()) if not pipe_df.empty else 0
    pipe_installed = _sum("Pipe", "rm")
    pct            = round(pipe_installed / monthly_target * 100, 1) if monthly_target else 0.0

    return {
        "total_pipe_installed_rm": pipe_installed,
        "total_pipe_upto_feb"    : float(
            pipe_df["Qty_Upto_Feb"].drop_duplicates().sum()
        ),
        "total_excavation_rm"    : _sum("Excavation", "rm") or _sum("Road Cutting", "rm"),
        "total_service_pits"     : _sum("Service Pit", "Pcs"),
        "active_days"            : int(df["Date"].nunique()),
        "pct_of_monthly_target"  : pct,
        "monthly_target_rm"      : monthly_target,
    }