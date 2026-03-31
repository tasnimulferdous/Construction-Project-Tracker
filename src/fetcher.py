# src/fetcher.py
# ============================================================
#  Google Sheets API connection for CCECC Master Tracker.
#  Actual tab names discovered from the live sheet:
#    Summary (Mar26), Manpower (Mar26),
#    Summary (Feb26), Weather (Feb2026),
#    Manpower (Feb26), SD-A Mat+Eqp (Feb26), SD-D Mat+Eqp (Feb26),
#    Summary (Jan26), Weather (Jan26), Manpower (Jan26),
#    SD-A Mat+Eqp (Jan26), SD-D Mat+Eqp (Jan26)
# ============================================================

from __future__ import annotations
import logging
from typing import Any

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound

logger = logging.getLogger(__name__)

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]
_CACHE_TTL = 600   # 10 minutes


def _get_client() -> gspread.Client:
    try:
        creds_info: dict[str, Any] = dict(st.secrets["gcp_service_account"])
    except KeyError as exc:
        raise RuntimeError(
            "Missing [gcp_service_account] in .streamlit/secrets.toml"
        ) from exc
    creds = Credentials.from_service_account_info(creds_info, scopes=_SCOPES)
    return gspread.authorize(creds)


def _spreadsheet_id() -> str:
    return "1WH-_LaJCWXsol9cSEh6lA-lTXq3fZBDsmLLcjmH-DMk"


@st.cache_data(ttl=_CACHE_TTL, show_spinner="Fetching data from Google Sheets...")
def fetch_sheet_by_name(worksheet_name: str) -> list[list[Any]]:
    """
    Fetch all values from a worksheet by its exact tab name.
    Returns raw list-of-lists with pad_values=True so all rows
    have the same column count.
    """
    try:
        client      = _get_client()
        spreadsheet = client.open_by_key(_spreadsheet_id())
        worksheet   = spreadsheet.worksheet(worksheet_name)
        raw         = worksheet.get_all_values(pad_values=True)
        logger.info("Fetched '%s': %d rows x %d cols",
                    worksheet_name, len(raw), len(raw[0]) if raw else 0)
        return raw

    except SpreadsheetNotFound:
        st.error("Spreadsheet not found. Make sure the service account has access.")
    except WorksheetNotFound:
        st.error(f"Tab '{worksheet_name}' does not exist in the spreadsheet.")
    except APIError as exc:
        st.error(f"Google Sheets API error: {exc}")
    except Exception as exc:
        st.error(f"Unexpected error: {exc}")
        logger.exception("fetch_sheet_by_name failed for '%s'", worksheet_name)
    return []


@st.cache_data(ttl=_CACHE_TTL, show_spinner="Loading worksheet list...")
def list_worksheets() -> list[str]:
    """Return all tab names in the spreadsheet."""
    try:
        client      = _get_client()
        spreadsheet = client.open_by_key(_spreadsheet_id())
        return [ws.title for ws in spreadsheet.worksheets()]
    except Exception as exc:
        st.error(f"Could not list worksheets: {exc}")
        return []


def bust_cache() -> None:
    fetch_sheet_by_name.clear()
    list_worksheets.clear()
    st.toast("Cache cleared. Data will reload from Google Sheets.", icon="✅")
    