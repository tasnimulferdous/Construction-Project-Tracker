# src/shared.py
from __future__ import annotations
import sys, re, calendar
from pathlib import Path
from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import cleaner, fetcher

# ── Constants ─────────────────────────────────────────────────
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

# ── Theme ─────────────────────────────────────────────────────

def _get_theme() -> str:
    return st.session_state.get("theme", "dark")


# Dark palette
_DARK = dict(
    bg_main        = "#0B0D14",
    bg_side        = "#0F1120",
    bg_card        = "rgba(0,229,255,0.04)",
    bg_card_h      = "rgba(0,229,255,0.11)",
    border         = "rgba(0,229,255,0.20)",
    border_h       = "rgba(0,229,255,0.65)",
    text_p         = "#D1D5E8",
    text_s         = "#5A7FAA",
    text_m         = "#2A3A55",
    cyan           = "#00E5FF",
    lime           = "#A8FF3E",
    amber          = "#FFD166",
    coral          = "#FF6B35",
    red            = "#FF4560",
    violet         = "#C77DFF",
    plot_bg        = "rgba(15,17,26,0.55)",
    grid           = "#1E2A3A",
    zero           = "#2A3A4A",
    sec_border     = "rgba(0,229,255,0.10)",
    kpi_border     = "rgba(0,229,255,0.20)",
    kpi_bg_g       = "rgba(168,255,62,0.07)",
    kpi_bd_g       = "rgba(168,255,62,0.28)",
    kpi_bg_a       = "rgba(255,209,102,0.07)",
    kpi_bd_a       = "rgba(255,209,102,0.28)",
    nav_glow       = "rgba(0,229,255,0.14)",
    shadow         = "rgba(0,0,0,0.40)",
    input_bg       = "#0F1120",
    input_border   = "rgba(0,229,255,0.25)",
    table_header   = "#0F1120",
    table_row_alt  = "rgba(0,229,255,0.03)",
)

# Light palette
_LIGHT = dict(
    bg_main        = "#FFFFFF",
    bg_side        = "#FFFFFF",
    bg_card        = "rgba(0,100,200,0.04)",
    bg_card_h      = "rgba(0,100,200,0.10)",
    border         = "rgba(0,100,200,0.22)",
    border_h       = "rgba(0,100,200,0.65)",
    text_p         = "#111827",
    text_s         = "#4B6080",
    text_m         = "#8090A8",
    cyan           = "#0066CC",
    lime           = "#2E7D32",
    amber          = "#B45309",
    coral          = "#C2410C",
    red            = "#B91C1C",
    violet         = "#7B2FBE",
    plot_bg        = "rgba(255,255,255,0.92)",
    grid           = "#D8E0EE",
    zero           = "#B0C0D8",
    sec_border     = "rgba(0,100,200,0.12)",
    kpi_border     = "rgba(0,100,200,0.22)",
    kpi_bg_g       = "rgba(46,125,50,0.06)",
    kpi_bd_g       = "rgba(46,125,50,0.32)",
    kpi_bg_a       = "rgba(180,83,9,0.06)",
    kpi_bd_a       = "rgba(180,83,9,0.32)",
    nav_glow       = "rgba(0,100,200,0.10)",
    shadow         = "rgba(0,0,0,0.10)",
    input_bg       = "#FFFFFF",
    input_border   = "rgba(0,100,200,0.30)",
    table_header   = "#E8EEF8",
    table_row_alt  = "rgba(0,100,200,0.03)",
)


def _p() -> dict:
    return _DARK if _get_theme() == "dark" else _LIGHT


def inject_css() -> None:
    p    = _p()
    dark = (_get_theme() == "dark")

    # Button colours depend on theme
    btn_bg      = "rgba(0,229,255,0.05)"   if dark else "#FFFFFF"
    btn_text    = "#D1D5E8"                 if dark else "#0D1117"
    btn_border  = "rgba(0,229,255,0.22)"   if dark else "rgba(0,80,160,0.30)"
    btn_bg_h    = "rgba(0,229,255,0.14)"   if dark else "#EEF4FF"
    btn_text_h  = "#00E5FF"                if dark else "#003E99"
    btn_bd_h    = "rgba(0,229,255,0.70)"   if dark else "rgba(0,80,160,0.70)"

    # Input colours
    inp_bg      = "#0F1120"  if dark else "#FFFFFF"
    inp_text    = "#D1D5E8"  if dark else "#0D1117"
    inp_border  = "rgba(0,229,255,0.30)"   if dark else "rgba(0,80,160,0.35)"

    # Sidebar label colour
    sidebar_text = "#A0B0C8" if dark else "#1A2A40"

    st.markdown(f"""
<style>
/* ── Animations ──────────────────────────────── */
@keyframes pulse-glow {{
    0%,100% {{ box-shadow: 0 0 0px 0px {p['nav_glow']}; }}
    50%      {{ box-shadow: 0 0 20px 6px {p['nav_glow']}; }}
}}
@keyframes float {{
    0%,100% {{ transform: translateY(0px); }}
    50%      {{ transform: translateY(-7px); }}
}}
@keyframes fade-in {{
    from {{ opacity:0; transform:translateY(10px); }}
    to   {{ opacity:1; transform:translateY(0);    }}
}}

/* ── Global background & text ─────────────────── */
html, body, .stApp {{
    background-color: {p['bg_main']} !important;
    color: {p['text_p']} !important;
    font-family: 'Segoe UI', Arial, sans-serif !important;
}}
.block-container {{
    background-color: {p['bg_main']} !important;
    padding: 2.5rem 2rem 2rem 2rem !important;
}}

/* All plain text */
p, span, div, label, li, td, th,
.stMarkdown, .stMarkdown p, .stMarkdown li,
.stText, .stCaption, .stCaption p,
[class*="css"] {{
    color: {p['text_p']} !important;
}}

/* ── Sidebar ──────────────────────────────────── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child {{
    background-color: {p['bg_side']} !important;
    border-right: 1px solid {p['border']} !important;
}}
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div {{
    color: {sidebar_text} !important;
}}

/* ── Streamlit buttons ────────────────────────── */
.stButton > button,
.stButton > button:focus,
.stButton > button:active {{
    background-color: {btn_bg} !important;
    color: {btn_text} !important;
    border: 1.5px solid {btn_border} !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all .2s !important;
}}
.stButton > button:hover {{
    background-color: {btn_bg_h} !important;
    color: {btn_text_h} !important;
    border-color: {btn_bd_h} !important;
}}

/* ── Selectbox ────────────────────────────────── */
.stSelectbox > div > div {{
    background-color: {inp_bg} !important;
    color: {inp_text} !important;
    border-color: {inp_border} !important;
}}
.stSelectbox label {{ color: {p['text_s']} !important; }}
[data-baseweb="select"] span,
[data-baseweb="select"] div {{
    color: {inp_text} !important;
    background-color: {inp_bg} !important;
}}
[data-baseweb="popover"] li,
[data-baseweb="menu"] li {{
    background-color: {inp_bg} !important;
    color: {inp_text} !important;
}}

/* ── Slider ───────────────────────────────────── */
.stSlider label {{ color: {p['text_s']} !important; }}
.stSlider [data-baseweb="slider"] div {{
    background-color: {p['border']} !important;
}}

/* ── Number input ─────────────────────────────── */
.stNumberInput > div > div > input {{
    background-color: {inp_bg} !important;
    color: {inp_text} !important;
    border-color: {inp_border} !important;
}}
.stNumberInput label {{ color: {p['text_s']} !important; }}

/* ── Expander ─────────────────────────────────── */
.streamlit-expanderHeader {{
    background-color: {p['bg_card']} !important;
    color: {p['text_p']} !important;
    border: 1px solid {p['border']} !important;
    border-radius: 8px !important;
}}
.streamlit-expanderContent {{
    background-color: {p['bg_side']} !important;
    border: 1px solid {p['border']} !important;
}}

/* ── DataFrames ───────────────────────────────── */
[data-testid="stDataFrame"],
.stDataFrame, iframe {{
    background-color: {p['bg_side']} !important;
    color: {p['text_p']} !important;
}}

/* ── Tabs ─────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    background-color: {p['bg_card']} !important;
}}
.stTabs [data-baseweb="tab"] {{
    color: {p['text_s']} !important;
}}
.stTabs [aria-selected="true"] {{
    color: {p['cyan']} !important;
    border-bottom-color: {p['cyan']} !important;
}}

/* ── Info / warning boxes ─────────────────────── */
.stAlert, .stInfo, .stWarning, .stSuccess, .stError {{
    background-color: {p['bg_card']} !important;
    color: {p['text_p']} !important;
    border: 1px solid {p['border']} !important;
}}

/* ── Spinner ──────────────────────────────────── */
.stSpinner > div {{ color: {p['cyan']} !important; }}

/* ── Section title ────────────────────────────── */
.section-title {{
    font-size: .68rem; letter-spacing: .14em; text-transform: uppercase;
    color: {p['text_s']};
    border-bottom: 1px solid {p['sec_border']};
    padding-bottom: .35rem; margin: 1.2rem 0 .8rem 0;
}}

/* ── KPI cards ────────────────────────────────── */
.kpi-card {{
    background: {p['bg_card']};
    border: 1px solid {p['kpi_border']};
    border-radius: 10px; padding: 1rem 1.1rem;
    text-align: center; position: relative;
    overflow: hidden; margin-bottom: .5rem;
    animation: fade-in .4s ease both;
}}
.kpi-card::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background: linear-gradient(90deg, {p['cyan']}, transparent);
}}
.kpi-card-green {{
    background: {p['kpi_bg_g']};
    border: 1px solid {p['kpi_bd_g']};
    border-radius:10px; padding:1rem 1.1rem;
    text-align:center; position:relative; overflow:hidden;
    margin-bottom:.5rem; animation: fade-in .4s ease both;
}}
.kpi-card-green::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background: linear-gradient(90deg, {p['lime']}, transparent);
}}
.kpi-card-amber {{
    background: {p['kpi_bg_a']};
    border: 1px solid {p['kpi_bd_a']};
    border-radius:10px; padding:1rem 1.1rem;
    text-align:center; position:relative; overflow:hidden;
    margin-bottom:.5rem; animation: fade-in .4s ease both;
}}
.kpi-card-amber::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background: linear-gradient(90deg, {p['amber']}, transparent);
}}
.kpi-label {{
    font-size:.60rem; letter-spacing:.10em; text-transform:uppercase;
    color:{p['text_s']}; margin-bottom:.3rem;
}}
.kpi-value       {{ font-size:1.75rem; font-weight:700; color:{p['cyan']};   line-height:1.1; }}
.kpi-value-green {{ font-size:1.75rem; font-weight:700; color:{p['lime']};   line-height:1.1; }}
.kpi-value-amber {{ font-size:1.75rem; font-weight:700; color:{p['amber']};  line-height:1.1; }}
.kpi-value-warn  {{ font-size:1.75rem; font-weight:700; color:{p['coral']};  line-height:1.1; }}
.kpi-sub         {{ font-size:.67rem; color:{p['text_m']}; margin-top:.2rem; }}

/* ── Landing nav cards ────────────────────────── */
.land-card {{
    background: {p['bg_card']}; border: 1.5px solid {p['border']};
    border-radius: 20px; padding: 2.8rem 1.5rem 2.2rem 1.5rem;
    text-align: center; position: relative; overflow: hidden;
    animation: pulse-glow 3.5s ease-in-out infinite, fade-in .6s ease both;
    transition: border-color .25s, background .25s, transform .2s, box-shadow .25s;
    margin-bottom: .5rem;
}}
.land-card::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg, {p['cyan']}, transparent);
}}
.land-card:hover {{
    border-color: {p['border_h']};
    background: {p['bg_card_h']};
    transform: translateY(-5px);
    box-shadow: 0 14px 35px {p['shadow']};
}}
.land-card:hover .land-icon {{ animation: float 1.4s ease-in-out infinite; }}
.land-icon  {{ font-size:4rem; display:block; margin-bottom:.9rem; transition:transform .3s; }}
.land-title {{ font-size:1.3rem; font-weight:800; color:{p['cyan']}; margin-bottom:.5rem; }}
.land-desc  {{ font-size:.82rem; color:{p['text_s']}; line-height:1.7; }}
.land-badge {{
    display:inline-block; margin-top:.8rem; padding:.2rem .8rem;
    border-radius:999px; border:1px solid {p['border']};
    font-size:.68rem; color:{p['text_s']};
    letter-spacing:.06em; text-transform:uppercase;
}}

/* ── Sub-nav buttons ──────────────────────────── */
.subnav-btn {{
    background:{p['bg_card']}; border:1.5px solid {p['border']};
    border-radius:14px; padding:1.4rem .8rem;
    text-align:center; cursor:pointer;
    transition: border-color .2s, background .2s, transform .15s;
    display:block; width:100%; margin-bottom:.4rem;
}}
.subnav-btn:hover {{
    border-color:{p['border_h']}; background:{p['bg_card_h']};
    transform:translateY(-2px);
}}
.subnav-btn.active {{
    border-color:{p['cyan']} !important;
    background:{p['bg_card_h']} !important;
    animation: pulse-glow 2.5s ease-in-out infinite;
}}
.subnav-icon  {{ font-size:2rem; display:block; margin-bottom:.4rem; }}
.subnav-title {{ font-size:.9rem; font-weight:700; color:{p['cyan']}; }}
.subnav-desc  {{ font-size:.70rem; color:{p['text_s']}; margin-top:.15rem; }}

/* ── Hide Streamlit button under nav cards ────── */
div[data-testid="column"] > div > div > div > .stButton > button {{
    opacity: 0 !important;
    position: absolute !important;
    top: 0 !important; left: 0 !important;
    width: 100% !important; height: 100% !important;
    cursor: pointer !important;
    border-radius: 20px !important;
    z-index: 10 !important;
}}

/* ── Misc ─────────────────────────────────────── */
.stPlotlyChart {{ border-radius:10px; overflow:hidden; }}
hr {{ border-color:{p['sec_border']}; }}
</style>
""", unsafe_allow_html=True)


def get_chart_theme() -> dict:
    """Plotly layout colours for current theme."""
    p = _p()
    return dict(
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = p["plot_bg"],
        font_color    = p["text_p"],
        font_family   = "Segoe UI, Arial, sans-serif",
        gridcolor     = p["grid"],
        zerolinecolor = p["zero"],
        accent        = p["cyan"],
    )


# ── UI helpers ────────────────────────────────────────────────

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


def subnav_buttons(options: list[tuple[str, str, str]], state_key: str) -> str:
    if state_key not in st.session_state:
        st.session_state[state_key] = options[0][1]

    cols = st.columns(len(options), gap="small")
    for i, (icon, title, desc) in enumerate(options):
        active = st.session_state[state_key] == title
        cols[i].markdown(f"""
        <div class="subnav-btn{'  active' if active else ''}">
            <span class="subnav-icon">{icon}</span>
            <div class="subnav-title">{title}</div>
            <div class="subnav-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        label = f"▶ {title}" if active else title
        if cols[i].button(label, key=f"{state_key}_{i}", use_container_width=True):
            st.session_state[state_key] = title
            st.rerun()

    return st.session_state[state_key]


# ── Shared Plotly layout (NO legend key — add per chart) ──────

def base_layout(height: int = 360, **extra) -> dict:
    """
    Return shared Plotly layout kwargs.
    Does NOT include 'legend' — pass that per-chart to avoid
    'multiple values for keyword argument legend' errors.
    """
    ct = get_chart_theme()
    return dict(
        paper_bgcolor = ct["paper_bgcolor"],
        plot_bgcolor  = ct["plot_bgcolor"],
        font_color    = ct["font_color"],
        font_family   = ct["font_family"],
        hovermode     = "x unified",
        height        = height,
        margin        = dict(l=16, r=16, t=50, b=16),
        **extra,
    )


def apply_axes(fig, ct: dict | None = None) -> None:
    if ct is None:
        ct = get_chart_theme()
    fig.update_xaxes(gridcolor=ct["gridcolor"], zerolinecolor=ct["zerolinecolor"],
                     showline=False, tickfont=dict(size=10, color=ct["font_color"]))
    fig.update_yaxes(gridcolor=ct["gridcolor"], zerolinecolor=ct["zerolinecolor"],
                     showline=False, tickfont=dict(size=10, color=ct["font_color"]))


_LEGEND = dict(bgcolor="rgba(0,0,0,0)",
               bordercolor="rgba(127,127,127,0.18)",
               borderwidth=1, font=dict(size=11))


# ── Sidebar ───────────────────────────────────────────────────

def render_sidebar(show_activity_filter: bool = False) -> dict[str, Any]:
    with st.sidebar:
        st.markdown("## 🏗️ CCECC")
        st.markdown("**WD5B — Zone W3 & W4**")
        st.markdown("---")

        if st.button("🏠  Home", use_container_width=True):
            st.switch_page("app.py")

        # Theme toggle
        theme = _get_theme()
        lbl   = "☀️  Light Mode" if theme == "dark" else "🌙  Dark Mode"
        if st.button(lbl, use_container_width=True, key="theme_toggle"):
            st.session_state["theme"] = "light" if theme == "dark" else "dark"
            st.rerun()

        st.markdown("---")
        selected_month_label = st.selectbox(
            "Month", options=list(MONTH_TABS.keys()), index=0)
        summary_tab  = MONTH_TABS[selected_month_label]
        manpower_tab = MANPOWER_TABS[selected_month_label]

        _mn = {
            "January":1,"February":2,"March":3,"April":4,
            "May":5,"June":6,"July":7,"August":8,
            "September":9,"October":10,"November":11,"December":12,
        }
        _m = re.search(r"(\w+) (\d{4})", selected_month_label)
        _mon, _year = (_mn.get(_m.group(1), 3), int(_m.group(2))) if _m else (3, 2026)
        _days = calendar.monthrange(_year, _mon)[1]

        day_range = st.slider("Day range", 1, _days, (1, _days), label_visibility="collapsed")
        filter_start = pd.Timestamp(date(_year, _mon, day_range[0]))
        filter_end   = pd.Timestamp(date(_year, _mon, day_range[1]))

        activity_filter = "Pipe"
        if show_activity_filter:
            activity_filter = st.selectbox(
                "Activity", ["Pipe","Road Cutting","Service Pit"])

        st.markdown("---")
        if st.button("🔄  Refresh", use_container_width=True):
            st.cache_data.clear()
            fetcher.bust_cache()
            st.rerun()

        st.caption(f"Contract: **{CONTRACT_TOTAL_RM:,.0f} rm**\n\n"
                   f"Tab: **{summary_tab.strip()}**")

    return dict(
        selected_month_label=selected_month_label,
        summary_tab=summary_tab, manpower_tab=manpower_tab,
        filter_start=filter_start, filter_end=filter_end,
        activity_filter=activity_filter,
        day_range=day_range, _mon=_mon, _year=_year,
    )


# ── Cached data loaders ───────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner="Loading summary…")
def load_summary(summary_tab: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load + clean ONE summary tab. TTL = 30 min."""
    raw = fetcher.fetch_sheet_by_name(summary_tab)
    return (
        cleaner.clean_summary_sheet(raw, sheet_name=summary_tab),
        cleaner.clean_vehicle_usage(raw, sheet_name=summary_tab),
    )


@st.cache_data(ttl=1800, show_spinner="Loading manpower…")
def load_manpower(manpower_tab: str) -> pd.DataFrame:
    """Load + clean ONE manpower tab. TTL = 30 min."""
    raw = fetcher.fetch_sheet_by_name(manpower_tab)
    return cleaner.clean_manpower_sheet(raw, sheet_name=manpower_tab)


@st.cache_data(ttl=1800, show_spinner="Loading all months…")
def load_all_months() -> dict[str, dict]:
    """
    Load KPI summaries for ALL months.
    Called only from Analytics page — NOT from Progress/Manpower.
    TTL = 30 min.
    """
    result: dict[str, dict] = {}
    for label, (s_tab, m_tab) in ALL_MONTHS.items():
        raw_s = fetcher.fetch_sheet_by_name(s_tab)
        s_df  = cleaner.clean_summary_sheet(raw_s, sheet_name=s_tab)
        if s_df.empty:
            continue
        k = cleaner.compute_kpis(s_df, s_df["Date"].min(), s_df["Date"].max())

        raw_m = fetcher.fetch_sheet_by_name(m_tab)
        m_df  = cleaner.clean_manpower_sheet(raw_m, sheet_name=m_tab)
        avg_mp = 0.0
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