# src/shared.py
from __future__ import annotations
import sys
import re
import calendar
from pathlib import Path
from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import cleaner, fetcher

# ──────────────────────────────────────────────────────────────
# Contract constants
# ──────────────────────────────────────────────────────────────
CONTRACT_TOTAL_RM    = 201_730.54
CONTRACT_START       = pd.Timestamp("2026-01-01")
CONTRACT_END_PLANNED = pd.Timestamp("2027-12-31")

MONTH_TABS: dict[str, str] = {
    "March 2026"   : "Summary (Mar26) ",
    "February 2026": "Summary (Feb26) ",
    "January 2026" : "Summary (Jan26) ",
}
MANPOWER_TABS: dict[str, str] = {
    "March 2026"   : "Manpower (Mar26)",
    "February 2026": "Manpower (Feb26)",
    "January 2026" : "Manpower (Jan26)",
}
ALL_MONTHS: dict[str, tuple[str, str]] = {
    "Jan 2026": ("Summary (Jan26) ", "Manpower (Jan26)"),
    "Feb 2026": ("Summary (Feb26) ", "Manpower (Feb26)"),
    "Mar 2026": ("Summary (Mar26) ", "Manpower (Mar26)"),
}
MONTH_END_DATES: dict[str, pd.Timestamp] = {
    "Jan 2026": pd.Timestamp("2026-01-31"),
    "Feb 2026": pd.Timestamp("2026-02-28"),
    "Mar 2026": pd.Timestamp("2026-03-31"),
}

# ──────────────────────────────────────────────────────────────
# Theme system
# ──────────────────────────────────────────────────────────────

DARK_VARS = """
    --bg-main:        #0B0D14;
    --bg-secondary:   #0F1120;
    --bg-card:        rgba(0,229,255,0.04);
    --bg-card-hover:  rgba(0,229,255,0.10);
    --border-card:    rgba(0,229,255,0.20);
    --border-hover:   rgba(0,229,255,0.60);
    --text-primary:   #D1D5E8;
    --text-secondary: #5A7FAA;
    --text-muted:     #2A3A55;
    --accent-cyan:    #00E5FF;
    --accent-lime:    #A8FF3E;
    --accent-amber:   #FFD166;
    --accent-coral:   #FF6B35;
    --accent-red:     #FF4560;
    --plot-bg:        rgba(15,17,26,0.55);
    --grid-color:     #1E2A3A;
    --section-border: rgba(0,229,255,0.10);
    --kpi-border:     rgba(0,229,255,0.18);
    --kpi-bg-green:   rgba(168,255,62,0.08);
    --kpi-border-green: rgba(168,255,62,0.25);
    --kpi-bg-amber:   rgba(255,209,102,0.08);
    --kpi-border-amber: rgba(255,209,102,0.25);
    --nav-glow:       rgba(0,229,255,0.15);
    --shadow:         rgba(0,229,255,0.08);
"""

LIGHT_VARS = """
    --bg-main:        #F0F4F8;
    --bg-secondary:   #FFFFFF;
    --bg-card:        rgba(0,100,200,0.04);
    --bg-card-hover:  rgba(0,100,200,0.10);
    --border-card:    rgba(0,100,200,0.20);
    --border-hover:   rgba(0,100,200,0.60);
    --text-primary:   #1A2035;
    --text-secondary: #4A6080;
    --text-muted:     #8090A8;
    --accent-cyan:    #0077CC;
    --accent-lime:    #2E7D32;
    --accent-amber:   #E65100;
    --accent-coral:   #C62828;
    --accent-red:     #B71C1C;
    --plot-bg:        rgba(240,244,248,0.80);
    --grid-color:     #D0D8E8;
    --section-border: rgba(0,100,200,0.12);
    --kpi-border:     rgba(0,100,200,0.20);
    --kpi-bg-green:   rgba(46,125,50,0.06);
    --kpi-border-green: rgba(46,125,50,0.30);
    --kpi-bg-amber:   rgba(230,81,0,0.06);
    --kpi-border-amber: rgba(230,81,0,0.30);
    --nav-glow:       rgba(0,100,200,0.12);
    --shadow:         rgba(0,100,200,0.06);
"""

BASE_CSS = """
<style>
@keyframes pulse-glow {
    0%   { box-shadow: 0 0 0px 0px var(--nav-glow); }
    50%  { box-shadow: 0 0 18px 4px var(--nav-glow); }
    100% { box-shadow: 0 0 0px 0px var(--nav-glow); }
}
@keyframes float {
    0%   { transform: translateY(0px);  }
    50%  { transform: translateY(-6px); }
    100% { transform: translateY(0px);  }
}
@keyframes spin-once {
    from { transform: rotate(0deg) scale(1);    }
    to   { transform: rotate(8deg) scale(1.15); }
}
@keyframes fade-in {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0);    }
}

:root { THEME_VARS }

html, body, [class*="css"] {
    font-family: 'Segoe UI', Arial, sans-serif !important;
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
    transition: background-color 0.3s, color 0.3s;
}
.block-container { padding: 2.5rem 2rem 2rem 2rem !important; }

/* ── Sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border-card) !important;
}

/* ── Section title ───────────────────────────────────────── */
.section-title {
    font-size: 0.68rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-secondary);
    border-bottom: 1px solid var(--section-border);
    padding-bottom: 0.35rem;
    margin: 1.2rem 0 0.8rem 0;
}

/* ── KPI cards ───────────────────────────────────────────── */
.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--kpi-border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    margin-bottom: 0.5rem;
    animation: fade-in 0.4s ease both;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--accent-cyan), transparent);
}
.kpi-card-green {
    background: var(--kpi-bg-green);
    border: 1px solid var(--kpi-border-green);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    margin-bottom: 0.5rem;
    animation: fade-in 0.4s ease both;
}
.kpi-card-green::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--accent-lime), transparent);
}
.kpi-card-amber {
    background: var(--kpi-bg-amber);
    border: 1px solid var(--kpi-border-amber);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    margin-bottom: 0.5rem;
    animation: fade-in 0.4s ease both;
}
.kpi-card-amber::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--accent-amber), transparent);
}
.kpi-label {
    font-size: 0.60rem;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: var(--text-secondary);
    margin-bottom: 0.3rem;
}
.kpi-value        { font-size: 1.75rem; font-weight: 700; color: var(--accent-cyan);  line-height: 1.1; }
.kpi-value-green  { font-size: 1.75rem; font-weight: 700; color: var(--accent-lime);  line-height: 1.1; }
.kpi-value-amber  { font-size: 1.75rem; font-weight: 700; color: var(--accent-amber); line-height: 1.1; }
.kpi-value-warn   { font-size: 1.75rem; font-weight: 700; color: var(--accent-coral); line-height: 1.1; }
.kpi-sub          { font-size: 0.67rem; color: var(--text-muted); margin-top: 0.2rem; }

/* ── Large nav buttons ───────────────────────────────────── */
.nav-btn-wrap {
    animation: fade-in 0.5s ease both;
}
.nav-btn {
    background: var(--bg-card);
    border: 1.5px solid var(--border-card);
    border-radius: 18px;
    padding: 2rem 1rem;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.25s, background 0.25s, transform 0.2s;
    animation: pulse-glow 3s ease-in-out infinite;
    display: block;
    width: 100%;
    margin-bottom: 0.5rem;
}
.nav-btn:hover {
    border-color: var(--border-hover);
    background: var(--bg-card-hover);
    transform: translateY(-3px);
}
.nav-btn:hover .nav-icon { animation: float 1.2s ease-in-out infinite; }
.nav-icon {
    font-size: 3.2rem;
    display: block;
    margin-bottom: 0.7rem;
    transition: transform 0.2s;
}
.nav-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--accent-cyan);
    margin-bottom: 0.3rem;
}
.nav-desc {
    font-size: 0.78rem;
    color: var(--text-secondary);
    line-height: 1.5;
}

/* ── Sub-nav (smaller buttons inside pages) ──────────────── */
.subnav-btn {
    background: var(--bg-card);
    border: 1.5px solid var(--border-card);
    border-radius: 14px;
    padding: 1.4rem 0.8rem;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s, transform 0.15s;
    display: block;
    width: 100%;
    margin-bottom: 0.4rem;
}
.subnav-btn:hover {
    border-color: var(--border-hover);
    background: var(--bg-card-hover);
    transform: translateY(-2px);
}
.subnav-btn.active {
    border-color: var(--accent-cyan) !important;
    background: rgba(0,229,255,0.10) !important;
    animation: pulse-glow 2.5s ease-in-out infinite;
}
.subnav-icon  { font-size: 2rem; display: block; margin-bottom: 0.4rem; }
.subnav-title { font-size: 0.9rem; font-weight: 700; color: var(--accent-cyan); }
.subnav-desc  { font-size: 0.70rem; color: var(--text-secondary); margin-top: 0.15rem; }

/* ── Chart container ─────────────────────────────────────── */
.stPlotlyChart { border-radius: 10px; overflow: hidden; }
hr { border-color: var(--section-border); }

/* ── Streamlit button overrides ──────────────────────────── */
.stButton button {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-card) !important;
}
.stButton button:hover {
    border-color: var(--border-hover) !important;
    color: var(--accent-cyan) !important;
}
</style>
"""


def _get_theme() -> str:
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"
    return st.session_state["theme"]


def inject_css() -> None:
    """Inject CSS with current theme variables."""
    theme = _get_theme()
    vars_block = DARK_VARS if theme == "dark" else LIGHT_VARS
    css = BASE_CSS.replace("THEME_VARS", vars_block)
    st.markdown(css, unsafe_allow_html=True)


def get_chart_theme() -> dict:
    """Return Plotly layout kwargs matching current theme."""
    theme = _get_theme()
    if theme == "dark":
        return dict(
            paper_bgcolor = "rgba(0,0,0,0)",
            plot_bgcolor  = "rgba(15,17,26,0.55)",
            font_color    = "#D1D5E8",
            gridcolor     = "#1E2A3A",
            zerolinecolor = "#2A3A4A",
        )
    else:
        return dict(
            paper_bgcolor = "rgba(240,244,248,0.80)",
            plot_bgcolor  = "rgba(255,255,255,0.90)",
            font_color    = "#1A2035",
            gridcolor     = "#D0D8E8",
            zerolinecolor = "#B0C0D8",
        )


# ──────────────────────────────────────────────────────────────
# UI helpers
# ──────────────────────────────────────────────────────────────

def section_title(text: str) -> None:
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def kpi_card(col, label: str, value: str, sub: str = "",
             cls: str = "kpi-value", card_cls: str = "kpi-card") -> None:
    col.markdown(f"""
    <div class="{card_cls}">
        <div class="kpi-label">{label}</div>
        <div class="{cls}">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def nav_button(icon: str, title: str, desc: str, key: str) -> bool:
    """
    Large animated navigation button on landing page.
    Returns True on click.
    """
    st.markdown(f"""
    <div class="nav-btn-wrap">
        <div class="nav-btn" id="nav_{key}">
            <span class="nav-icon">{icon}</span>
            <div class="nav-title">{title}</div>
            <div class="nav-desc">{desc}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    return st.button(f"Open {title}", key=f"navbtn_{key}", use_container_width=True)


def subnav_buttons(options: list[tuple[str, str, str]], state_key: str) -> str:
    """
    Row of smaller sub-navigation buttons inside a page.
    options: list of (icon, title, desc)
    state_key: session_state key to store selection
    Returns the currently selected title.
    """
    if state_key not in st.session_state:
        st.session_state[state_key] = options[0][1]

    cols = st.columns(len(options), gap="small")
    for i, (icon, title, desc) in enumerate(options):
        is_active = (st.session_state[state_key] == title)
        active_cls = " active" if is_active else ""
        cols[i].markdown(f"""
        <div class="subnav-btn{active_cls}">
            <span class="subnav-icon">{icon}</span>
            <div class="subnav-title">{title}</div>
            <div class="subnav-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if cols[i].button(f"{'▶ ' if is_active else ''}{title}", key=f"{state_key}_{i}",
                          use_container_width=True):
            st.session_state[state_key] = title
            st.rerun()

    return st.session_state[state_key]


# ──────────────────────────────────────────────────────────────
# Sidebar (shared across pages)
# ──────────────────────────────────────────────────────────────

def render_sidebar(show_activity_filter: bool = False) -> dict[str, Any]:
    with st.sidebar:
        st.markdown("## 🏗️ CCECC Dashboard")
        st.markdown("**WD5B — Zone W3 & W4**")
        st.markdown("---")

        if st.button("🏠  Home", use_container_width=True):
            st.switch_page("app.py")

        st.markdown("---")

        # Theme toggle
        theme = _get_theme()
        toggle_label = "☀️  Switch to Light Mode" if theme == "dark" else "🌙  Switch to Dark Mode"
        if st.button(toggle_label, use_container_width=True):
            st.session_state["theme"] = "light" if theme == "dark" else "dark"
            st.rerun()

        st.markdown("---")
        st.markdown("**Select Month**")
        selected_month_label = st.selectbox(
            "Month", options=list(MONTH_TABS.keys()), index=0, label_visibility="collapsed",
        )
        summary_tab  = MONTH_TABS[selected_month_label]
        manpower_tab = MANPOWER_TABS[selected_month_label]

        st.markdown("**Day Range**")
        _month_names = {
            "January":1,"February":2,"March":3,"April":4,
            "May":5,"June":6,"July":7,"August":8,
            "September":9,"October":10,"November":11,"December":12,
        }
        _m = re.search(r"(\w+) (\d{4})", selected_month_label)
        _mon, _year = (_month_names.get(_m.group(1), 3), int(_m.group(2))) if _m else (3, 2026)
        _days_in_month = calendar.monthrange(_year, _mon)[1]

        day_range = st.slider("Days", min_value=1, max_value=_days_in_month,
                              value=(1, _days_in_month), step=1, label_visibility="collapsed")
        filter_start = pd.Timestamp(date(_year, _mon, day_range[0]))
        filter_end   = pd.Timestamp(date(_year, _mon, day_range[1]))

        activity_filter = "Pipe"
        if show_activity_filter:
            activity_filter = st.selectbox(
                "Activity", options=["Pipe", "Road Cutting", "Service Pit"], index=0)

        st.markdown("---")
        if st.button("🔄  Refresh Data", use_container_width=True):
            fetcher.bust_cache()
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.caption(
            f"Contract: **{CONTRACT_TOTAL_RM:,.0f} rm**\n\n"
            f"Tab: **{summary_tab.strip()}**\n\nCache: 10 min"
        )

    return dict(
        selected_month_label=selected_month_label,
        summary_tab=summary_tab,
        manpower_tab=manpower_tab,
        filter_start=filter_start,
        filter_end=filter_end,
        activity_filter=activity_filter,
        day_range=day_range,
        _mon=_mon, _year=_year,
    )


# ──────────────────────────────────────────────────────────────
# Cached data loaders
# ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner="Loading summary...")
def load_summary(summary_tab: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = fetcher.fetch_sheet_by_name(summary_tab)
    return (
        cleaner.clean_summary_sheet(raw, sheet_name=summary_tab),
        cleaner.clean_vehicle_usage(raw, sheet_name=summary_tab),
    )


@st.cache_data(ttl=600, show_spinner="Loading manpower...")
def load_manpower(manpower_tab: str) -> pd.DataFrame:
    raw = fetcher.fetch_sheet_by_name(manpower_tab)
    return cleaner.clean_manpower_sheet(raw, sheet_name=manpower_tab)


@st.cache_data(ttl=600, show_spinner="Loading all months...")
def load_all_months() -> dict[str, dict]:
    result: dict[str, dict] = {}
    for label, (s_tab, m_tab) in ALL_MONTHS.items():
        raw_s = fetcher.fetch_sheet_by_name(s_tab)
        raw_m = fetcher.fetch_sheet_by_name(m_tab)
        s_df  = cleaner.clean_summary_sheet(raw_s, sheet_name=s_tab)
        m_df  = cleaner.clean_manpower_sheet(raw_m, sheet_name=m_tab)
        if not s_df.empty:
            d_start = s_df["Date"].min()
            d_end   = s_df["Date"].max()
            k       = cleaner.compute_kpis(s_df, d_start, d_end)
            avg_mp  = 0.0
            if not m_df.empty:
                day_df = m_df[m_df["Shift"] == "Day"]
                if not day_df.empty:
                    avg_mp = float(day_df.groupby("Date")["Count"].sum().mean())
            result[label] = {
                "pipe_rm"     : k.get("total_pipe_installed_rm", 0.0),
                "active_days" : k.get("active_days", 0),
                "avg_manpower": avg_mp,
                "excav_rm"    : k.get("total_excavation_rm", 0.0),
                "monthly_tgt" : k.get("monthly_target_rm", 0.0),
                "pits"        : k.get("total_service_pits", 0.0),
                "upto_feb"    : k.get("total_pipe_upto_feb", 0.0),
            }
    return result


def build_cumulative_timeline(all_months_data: dict) -> list[dict]:
    result, running = [], 0.0
    for label, d in all_months_data.items():
        running += d["pipe_rm"]
        result.append({
            "date": MONTH_END_DATES.get(label, pd.Timestamp.now()),
            "cumulative_rm": running,
            "label": label,
        })
    return result