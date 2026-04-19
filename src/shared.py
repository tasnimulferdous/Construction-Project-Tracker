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

# ── Contract constants ────────────────────────────────────────
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

# ── Sidebar kill — call this FIRST on every page ─────────────
HIDE_SIDEBAR = """
<style>
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
section[data-testid="stSidebarContent"],
button[data-testid="baseButton-header"],
button[kind="header"] {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
}
.main .block-container {
    padding-left: 2.4rem !important;
    padding-right: 2.4rem !important;
}
</style>
"""

# ── Professional white palette ────────────────────────────────
PAL = dict(
    # Backgrounds
    bg          = "#FFFFFF",
    bg2         = "#F4F7FE",
    bg3         = "#EEF2FB",
    bg_card     = "#FFFFFF",
    bg_card_h   = "#F0F5FF",
    # Borders
    border      = "#D0DAF0",
    border_h    = "#1A56DB",
    border_s    = "#E4EAF8",
    # Text
    text        = "#0D1117",
    text2       = "#374151",
    text3       = "#6B7280",
    text4       = "#9CA3AF",
    # Accents
    blue        = "#1A56DB",
    blue_l      = "#3B82F6",
    blue_ll     = "#DBEAFE",
    green       = "#059669",
    green_l     = "#D1FAE5",
    amber       = "#D97706",
    amber_l     = "#FEF3C7",
    red         = "#DC2626",
    red_l       = "#FEE2E2",
    purple      = "#7C3AED",
    purple_l    = "#EDE9FE",
    teal        = "#0891B2",
    teal_l      = "#CFFAFE",
    orange      = "#EA580C",
    orange_l    = "#FFEDD5",
    # Charts
    plot_bg     = "#FFFFFF",
    grid        = "#E5EAF5",
    zero        = "#C8D0E8",
    # Shadows
    shadow_sm   = "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)",
    shadow_md   = "0 4px 12px rgba(0,0,0,0.10), 0 2px 4px rgba(0,0,0,0.06)",
    shadow_lg   = "0 10px 28px rgba(0,0,0,0.12), 0 4px 8px rgba(0,0,0,0.06)",
)

CHART_COLORS = ["#1A56DB","#059669","#D97706","#7C3AED","#0891B2","#EA580C","#DC2626"]


def inject_css() -> None:
    p = PAL
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

@keyframes fadeUp {{
    from {{ opacity:0; transform:translateY(12px); }}
    to   {{ opacity:1; transform:translateY(0); }}
}}
@keyframes pulse-blue {{
    0%,100% {{ box-shadow: 0 0 0 0 rgba(26,86,219,0.15); }}
    50%      {{ box-shadow: 0 0 0 8px rgba(26,86,219,0.0); }}
}}
@keyframes float {{
    0%,100% {{ transform: translateY(0px) scale(1); }}
    50%      {{ transform: translateY(-6px) scale(1.04); }}
}}

/* ── Base ──────────────────────────────────────── */
html, body, .stApp, .main {{
    background: {p['bg']} !important;
    color: {p['text']} !important;
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important;
}}
.block-container {{
    background: {p['bg']} !important;
    padding: 1.8rem 2.4rem 2rem 2.4rem !important;
    max-width: 1400px !important;
}}

/* ── Hide sidebar completely ────────────────────── */
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
button[kind="header"] {{
    display: none !important;
}}

/* ── All text defaults ──────────────────────────── */
p, span, div, li, td, th, label {{
    color: {p['text2']} !important;
    font-family: 'Inter','Segoe UI',Arial,sans-serif !important;
}}
h1,h2,h3,h4,h5,h6 {{
    color: {p['text']} !important;
    font-family: 'Inter','Segoe UI',Arial,sans-serif !important;
}}

/* ── Streamlit buttons (default) ─────────────────── */
.stButton > button {{
    background: {p['bg2']} !important;
    color: {p['text2']} !important;
    border: 1.5px solid {p['border']} !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: .875rem !important;
    transition: all .18s ease !important;
    box-shadow: {p['shadow_sm']} !important;
}}
.stButton > button:hover {{
    background: {p['blue_ll']} !important;
    color: {p['blue']} !important;
    border-color: {p['blue']} !important;
    box-shadow: {p['shadow_md']} !important;
}}

/* ── Selectbox / inputs ──────────────────────────── */
.stSelectbox > div > div,
[data-baseweb="select"] > div {{
    background: {p['bg']} !important;
    border-color: {p['border']} !important;
    border-radius: 8px !important;
    color: {p['text']} !important;
    box-shadow: {p['shadow_sm']} !important;
}}
[data-baseweb="select"] span {{ color: {p['text']} !important; }}
[data-baseweb="popover"] li {{ background:{p['bg']} !important; color:{p['text']} !important; }}
[data-baseweb="popover"] li:hover {{ background:{p['bg2']} !important; }}
.stNumberInput input, .stTextInput input {{
    background: {p['bg']} !important;
    color: {p['text']} !important;
    border-color: {p['border']} !important;
    border-radius: 8px !important;
}}
.stSlider [data-baseweb="slider"] {{ background: {p['border']} !important; }}

/* ── Labels ─────────────────────────────────────── */
.stSelectbox label, .stSlider label,
.stNumberInput label, .stTextInput label,
.stDateInput label, .stRadio label {{
    color: {p['text3']} !important;
    font-weight: 500 !important;
    font-size: .8125rem !important;
}}

/* ── Tabs ────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    background: {p['bg2']} !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid {p['border_s']} !important;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: {p['text3']} !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: .875rem !important;
    border: none !important;
}}
.stTabs [aria-selected="true"] {{
    background: {p['bg']} !important;
    color: {p['blue']} !important;
    font-weight: 600 !important;
    box-shadow: {p['shadow_sm']} !important;
}}

/* ── Expander ────────────────────────────────────── */
.streamlit-expanderHeader {{
    background: {p['bg2']} !important;
    color: {p['text2']} !important;
    border: 1px solid {p['border_s']} !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}}
.streamlit-expanderContent {{
    background: {p['bg']} !important;
    border: 1px solid {p['border_s']} !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}}

/* ── DataFrames ──────────────────────────────────── */
[data-testid="stDataFrame"] {{ border-radius: 10px !important; overflow:hidden !important; }}

/* ── Alerts ──────────────────────────────────────── */
.stAlert {{ border-radius: 10px !important; border: 1px solid {p['border_s']} !important; }}
.stInfo   {{ background: {p['blue_ll']} !important; color: {p['blue']} !important; }}
.stSuccess {{ background: {p['green_l']} !important; }}
.stWarning {{ background: {p['amber_l']} !important; }}

/* ── Chart ───────────────────────────────────────── */
.stPlotlyChart {{ border-radius: 12px !important; overflow:hidden !important;
    box-shadow: {p['shadow_sm']} !important; border: 1px solid {p['border_s']} !important; }}

/* ── Section title ───────────────────────────────── */
.section-title {{
    font-size: .6875rem; font-weight: 700; letter-spacing: .10em;
    text-transform: uppercase; color: {p['text3']};
    border-bottom: 2px solid {p['border_s']};
    padding-bottom: .4rem; margin: 1.4rem 0 .9rem 0;
    font-family: 'Inter','Segoe UI',Arial,sans-serif;
}}

/* ── KPI cards ────────────────────────────────────── */
.kpi-card {{
    background: {p['bg_card']}; border: 1px solid {p['border_s']};
    border-radius: 12px; padding: 1.1rem 1.3rem;
    text-align: center; position: relative; overflow: hidden;
    box-shadow: {p['shadow_sm']}; margin-bottom: .6rem;
    animation: fadeUp .35s ease both;
    transition: box-shadow .2s, transform .2s;
}}
.kpi-card:hover {{ box-shadow: {p['shadow_md']}; transform: translateY(-2px); }}
.kpi-card::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg, {p['blue']}, {p['blue_l']});
}}
.kpi-green {{
    background: linear-gradient(135deg,{p['green_l']},#fff);
    border: 1px solid #A7F3D0;
    border-radius:12px; padding:1.1rem 1.3rem;
    text-align:center; position:relative; overflow:hidden;
    box-shadow:{p['shadow_sm']}; margin-bottom:.6rem;
    animation: fadeUp .35s ease both;
}}
.kpi-green::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg,{p['green']},{p['teal']});
}}
.kpi-amber {{
    background: linear-gradient(135deg,{p['amber_l']},#fff);
    border: 1px solid #FDE68A;
    border-radius:12px; padding:1.1rem 1.3rem;
    text-align:center; position:relative; overflow:hidden;
    box-shadow:{p['shadow_sm']}; margin-bottom:.6rem;
    animation: fadeUp .35s ease both;
}}
.kpi-amber::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg,{p['amber']},{p['orange']});
}}
.kpi-label {{
    font-size: .6875rem; font-weight:600; letter-spacing:.08em;
    text-transform:uppercase; color:{p['text3']}; margin-bottom:.35rem;
}}
.kpi-val        {{ font-size:1.75rem; font-weight:800; color:{p['blue']};  line-height:1.1; }}
.kpi-val-green  {{ font-size:1.75rem; font-weight:800; color:{p['green']}; line-height:1.1; }}
.kpi-val-amber  {{ font-size:1.75rem; font-weight:800; color:{p['amber']}; line-height:1.1; }}
.kpi-val-red    {{ font-size:1.75rem; font-weight:800; color:{p['red']};   line-height:1.1; }}
.kpi-sub        {{ font-size:.75rem; color:{p['text4']}; margin-top:.25rem; font-weight:400; }}

/* ── Activity icon buttons ────────────────────────── */
.act-btn {{
    background: {p['bg_card']}; border: 2px solid {p['border_s']};
    border-radius: 16px; padding: 1.8rem 1rem 1.4rem 1rem;
    text-align: center; cursor: pointer; position: relative;
    box-shadow: {p['shadow_sm']};
    transition: all .22s ease;
    animation: fadeUp .4s ease both;
}}
.act-btn:hover {{
    border-color: {p['blue']}; background: {p['bg_card_h']};
    box-shadow: {p['shadow_md']};
    transform: translateY(-4px);
}}
.act-btn:hover .act-icon {{ animation: float 1.2s ease-in-out infinite; }}
.act-btn.selected {{
    border-color: {p['blue']} !important;
    background: linear-gradient(135deg,{p['blue_ll']},{p['bg']}) !important;
    box-shadow: 0 0 0 3px rgba(26,86,219,0.15), {p['shadow_md']} !important;
}}
.act-btn.selected::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:4px;
    background: linear-gradient(90deg,{p['blue']},{p['blue_l']});
    border-radius: 14px 14px 0 0;
}}
.act-icon  {{ font-size:2.8rem; display:block; margin-bottom:.6rem; }}
.act-title {{ font-size:.9375rem; font-weight:700; color:{p['text']}; margin-bottom:.2rem; }}
.act-sub   {{ font-size:.75rem; color:{p['text3']}; }}

/* ── Filter bar ──────────────────────────────────── */
.filter-bar {{
    background: {p['bg2']}; border: 1px solid {p['border_s']};
    border-radius: 12px; padding: 1rem 1.4rem;
    margin-bottom: 1.2rem; box-shadow: {p['shadow_sm']};
    display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;
}}

/* ── Page header bar ────────────────────────────── */
.page-header {{
    background: linear-gradient(135deg,{p['blue']},{p['blue_l']});
    border-radius: 14px; padding: 1.4rem 2rem;
    margin-bottom: 1.4rem; color: #fff;
    box-shadow: {p['shadow_md']};
}}
.page-header h2 {{
    color: #fff !important; font-size:1.375rem; font-weight:800; margin:0;
}}
.page-header p {{
    color: rgba(255,255,255,.82) !important; font-size:.875rem; margin:.2rem 0 0 0;
}}

/* ── Nav cards on landing ────────────────────────── */
.nav-card {{
    background: {p['bg_card']}; border: 2px solid {p['border_s']};
    border-radius: 20px; padding: 2.4rem 1.4rem 2rem 1.4rem;
    text-align: center; cursor: pointer; position: relative; overflow: hidden;
    box-shadow: {p['shadow_md']};
    transition: all .25s ease;
    animation: fadeUp .5s ease both, pulse-blue 4s ease-in-out infinite;
}}
.nav-card::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:4px;
    background: linear-gradient(90deg,{p['blue']},{p['blue_l']},{p['teal']});
}}
.nav-card:hover {{
    border-color: {p['blue']}; transform: translateY(-6px);
    box-shadow: {p['shadow_lg']};
    background: linear-gradient(135deg,{p['blue_ll']},{p['bg']});
}}
.nav-card:hover .nav-icon {{ animation: float 1.4s ease-in-out infinite; }}
.nav-icon  {{ font-size:3.8rem; display:block; margin-bottom:.9rem; }}
.nav-title {{ font-size:1.2rem; font-weight:800; color:{p['blue']}; margin-bottom:.4rem; }}
.nav-desc  {{ font-size:.8125rem; color:{p['text3']}; line-height:1.7; }}
.nav-badge {{
    display:inline-block; margin-top:.8rem; padding:.25rem 1rem;
    background:{p['blue_ll']}; border-radius:999px;
    font-size:.6875rem; color:{p['blue']}; font-weight:600;
    letter-spacing:.04em; text-transform:uppercase;
}}

/* ── Invisible Streamlit button over nav/act cards ── */
div[data-testid="column"] > div > div > div > .stButton > button {{
    opacity: 0 !important;
    position: absolute !important;
    top: 0 !important; left: 0 !important;
    width: 100% !important; height: 100% !important;
    cursor: pointer !important;
    z-index: 99 !important;
    border-radius: 20px !important;
}}

/* ── Misc ────────────────────────────────────────── */
hr {{ border: none; border-top: 1px solid {p['border_s']}; margin: 1rem 0; }}
.stSpinner > div {{ color: {p['blue']} !important; }}
</style>
""", unsafe_allow_html=True)


def get_chart_theme() -> dict:
    return dict(
        paper_bgcolor = "#FFFFFF",
        plot_bgcolor  = "#FFFFFF",
        font_color    = PAL["text2"],
        font_family   = "Inter, Segoe UI, Arial, sans-serif",
        gridcolor     = PAL["grid"],
        zerolinecolor = PAL["zero"],
        colors        = CHART_COLORS,
    )


_LEGEND = dict(
    bgcolor="rgba(255,255,255,0.95)",
    bordercolor=PAL["border_s"],
    borderwidth=1,
    font=dict(size=11, color=PAL["text2"]),
)


def base_layout(height: int = 360, **extra) -> dict:
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
                     showline=False, tickfont=dict(size=10, color=ct["font_color"]),
                     linecolor=ct["gridcolor"])
    fig.update_yaxes(gridcolor=ct["gridcolor"], zerolinecolor=ct["zerolinecolor"],
                     showline=False, tickfont=dict(size=10, color=ct["font_color"]),
                     linecolor=ct["gridcolor"])


# ── UI helpers ─────────────────────────────────────────────────

def section_title(text: str) -> None:
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def kpi_card(col, label: str, value: str, sub: str = "",
             val_cls: str = "kpi-val", card_cls: str = "kpi-card") -> None:
    col.markdown(f"""
    <div class="{card_cls}">
        <div class="kpi-label">{label}</div>
        <div class="{val_cls}">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def page_header(icon: str, title: str, subtitle: str) -> None:
    st.markdown(f"""
    <div class="page-header">
        <h2>{icon} &nbsp;{title}</h2>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def activity_icon_buttons(options: list[tuple[str,str,str,str]], state_key: str) -> str:
    """
    Render large, beautiful, fully-clickable icon cards.
    
    options: list of (icon, title, subtitle, accent_hex_color)
    state_key: unique session state key for this button group
    Returns: currently selected title string

    Approach: render HTML cards + use st.columns of st.button with
    deliberate CSS that makes ONLY the button text invisible while the
    button fills its entire column cell. The card HTML is rendered above
    using st.markdown, sized exactly to the column width and height.
    The st.button then sits in the same column rendered immediately after
    with negative margin-top to pull it back up over the card.
    
    The ONLY reliable Streamlit trick: the st.button label is a single
    space " " so nothing renders, the button height matches the card
    height, opacity stays 1 but background+border are transparent, so
    it looks invisible but clicks work.
    """
    if state_key not in st.session_state:
        st.session_state[state_key] = options[0][1]

    current = st.session_state[state_key]
    p       = PAL
    n       = len(options)
    CARD_H  = 210  # px — card height, must match button height below

    # ── Per-card CSS (active state highlight) ─────────────────
    active_css = ""
    for i, (icon, title, sub, accent) in enumerate(options):
        if title == current:
            r = int(accent.lstrip("#")[0:2], 16)
            g = int(accent.lstrip("#")[2:4], 16)
            b = int(accent.lstrip("#")[4:6], 16)
            active_css += f"""
            .ibc-{state_key}-{i} {{
                border: 2.5px solid {accent} !important;
                background: linear-gradient(155deg,
                    rgba({r},{g},{b},0.09), #FFFFFF 65%) !important;
                box-shadow: 0 0 0 4px rgba({r},{g},{b},0.14),
                            0 10px 28px rgba({r},{g},{b},0.20) !important;
            }}
            .ibc-{state_key}-{i} .ibc-title {{ color: {accent} !important; }}
            .ibc-{state_key}-{i} .ibc-strip {{
                background: linear-gradient(90deg, {accent},
                    rgba({r},{g},{b},0.6)) !important;
                height: 5px !important;
            }}
            """

    # ── Shared CSS injected once ───────────────────────────────
    st.markdown(f"""
<style>
@keyframes ib-float-{state_key} {{
    0%,100% {{ transform: translateY(0px)   scale(1);    }}
    50%      {{ transform: translateY(-9px) scale(1.05); }}
}}
@keyframes ib-pulse-{state_key} {{
    0%,100% {{ box-shadow: 0 4px 16px rgba(26,86,219,0.10); }}
    50%      {{ box-shadow: 0 8px 32px rgba(26,86,219,0.28); }}
}}

/* Base card */
.ibc-{state_key} {{
    position: relative;
    background: #FFFFFF;
    border: 2px solid {p['border_s']};
    border-radius: 20px;
    text-align: center;
    overflow: hidden;
    cursor: pointer;
    height: {CARD_H}px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    transition: all 0.22s cubic-bezier(0.34,1.56,0.64,1);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0 12px;
    user-select: none;
}}
.ibc-{state_key}:hover {{
    border-color: {p['blue']} !important;
    background: linear-gradient(155deg, {p['blue_ll']}, #FFFFFF 65%) !important;
    box-shadow: 0 12px 32px rgba(26,86,219,0.20),
                0 2px 8px rgba(0,0,0,0.08) !important;
    transform: translateY(-6px) scale(1.02) !important;
}}
.ibc-{state_key}:hover .ibc-icon {{
    animation: ib-float-{state_key} 1.3s ease-in-out infinite;
}}
.ibc-{state_key}.ibc-active-{state_key} {{
    animation: ib-pulse-{state_key} 2.8s ease-in-out infinite;
}}

/* Colour strip at top */
.ibc-strip {{
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    border-radius: 18px 18px 0 0;
    background: linear-gradient(90deg, {p['blue']}, {p['teal']});
    transition: height 0.2s ease;
}}
.ibc-{state_key}:hover .ibc-strip {{ height: 5px; }}

/* Icon */
.ibc-icon {{
    font-size: 3.8rem;
    line-height: 1;
    margin-bottom: 12px;
    display: block;
    transition: transform 0.22s ease;
}}

/* Title */
.ibc-title {{
    font-size: 1.0625rem;
    font-weight: 700;
    color: {p['text']};
    font-family: 'Inter','Segoe UI',Arial,sans-serif;
    margin-bottom: 5px;
    letter-spacing: -0.01em;
    line-height: 1.2;
}}

/* Subtitle */
.ibc-sub {{
    font-size: 0.75rem;
    color: {p['text3']};
    line-height: 1.55;
    font-family: 'Inter','Segoe UI',Arial,sans-serif;
}}

/* ── The invisible Streamlit button sits IN the same column,
   pulled up over the card via margin-top negative equal to
   card height + any gap Streamlit adds (~8px).
   We make it fully transparent but keep pointer-events. ── */
.ibw-{state_key} {{
    margin-top: -{CARD_H + 8}px;
    position: relative;
    z-index: 30;
}}
.ibw-{state_key} .stButton > button {{
    width:   100% !important;
    height:  {CARD_H}px !important;
    opacity: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    cursor: pointer !important;
    border-radius: 20px !important;
    padding: 0 !important;
    margin: 0 !important;
}}

/* Active per-card overrides */
{active_css}
</style>
""", unsafe_allow_html=True)

    # ── Render cards row ───────────────────────────────────────
    cols = st.columns(n, gap="medium")
    for i, (icon, title, sub, accent) in enumerate(options):
        is_active = (title == current)
        active_cls = f" ibc-active-{state_key}" if is_active else ""
        with cols[i]:
            # 1) Visual card (HTML)
            st.markdown(f"""
<div class="ibc-{state_key} ibc-{state_key}-{i}{active_cls}">
    <div class="ibc-strip"></div>
    <span class="ibc-icon">{icon}</span>
    <div class="ibc-title">{title}</div>
    <div class="ibc-sub">{sub.replace(chr(10), "<br>")}</div>
</div>
""", unsafe_allow_html=True)
            # 2) Invisible button in a wrapper div pulled up over card
            st.markdown(f'<div class="ibw-{state_key}">', unsafe_allow_html=True)
            if st.button(" ", key=f"{state_key}_b{i}", use_container_width=True):
                st.session_state[state_key] = title
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    return current


def top_filter_bar(month_options: list[str], state_prefix: str) -> dict:
    """
    Horizontal top filter bar: Month | Day range | returns dict of filters.
    """
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])

    with c1:
        selected_month = st.selectbox(
            "Month", month_options, key=f"{state_prefix}_month",
            label_visibility="visible")
    with c2:
        _mn = {"January":1,"February":2,"March":3,"April":4,
               "May":5,"June":6,"July":7,"August":8,
               "September":9,"October":10,"November":11,"December":12}
        _m = re.search(r"(\w+) (\d{4})", selected_month)
        _mon, _year = (_mn.get(_m.group(1),3), int(_m.group(2))) if _m else (3,2026)
        _days = calendar.monthrange(_year, _mon)[1]
        day_range = st.slider(
            "Day Range", 1, _days, (1, _days),
            key=f"{state_prefix}_days")
    with c3:
        if st.button("🏠 Home", key=f"{state_prefix}_home", use_container_width=True):
            st.switch_page("app.py")
    with c4:
        if st.button("🔄 Refresh", key=f"{state_prefix}_refresh", use_container_width=True):
            st.cache_data.clear()
            fetcher.bust_cache()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    f_start = pd.Timestamp(date(_year, _mon, day_range[0]))
    f_end   = pd.Timestamp(date(_year, _mon, day_range[1]))

    return dict(
        selected_month=selected_month,
        summary_tab=MONTH_TABS.get(selected_month, "Summary (Mar26) "),
        manpower_tab=MANPOWER_TABS.get(selected_month, "Manpower (Mar26)"),
        filter_start=f_start, filter_end=f_end,
        day_range=day_range, _mon=_mon, _year=_year,
    )


# ── Cached data loaders ─────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner="Loading data…")
def load_summary(summary_tab: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = fetcher.fetch_sheet_by_name(summary_tab)
    return (
        cleaner.clean_summary_sheet(raw, sheet_name=summary_tab),
        cleaner.clean_vehicle_usage(raw, sheet_name=summary_tab),
    )




@st.cache_data(ttl=1800, show_spinner="Loading manpower…")
def load_manpower(manpower_tab: str) -> pd.DataFrame:
    raw = fetcher.fetch_sheet_by_name(manpower_tab)
    return cleaner.clean_manpower_sheet(raw, sheet_name=manpower_tab)



@st.cache_data(ttl=1800, show_spinner="Loading all months…")
def load_all_months() -> dict[str, dict]:
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


# ── Cross-month merged loaders ────────────────────────────────

@st.cache_data(ttl=1800, show_spinner="Loading all summary data…")
def load_merged_summary() -> pd.DataFrame:
    """
    Fetch and merge ALL available monthly summary sheets into one DataFrame.
    Enables cross-month date filtering (e.g. Feb 15 → Mar 7).
    """
    frames = []
    for label, (s_tab, _) in ALL_MONTHS.items():
        raw  = fetcher.fetch_sheet_by_name(s_tab)
        s_df = cleaner.clean_summary_sheet(raw, sheet_name=s_tab)
        if not s_df.empty:
            frames.append(s_df)
    if not frames:
        return pd.DataFrame()
    merged = pd.concat(frames, ignore_index=True)
    # Drop duplicate date+activity+SD+Pipe_Dia rows (safety)
    merged = merged.drop_duplicates(
        subset=["Date","Activity","SD","Pipe_Dia"]).reset_index(drop=True)
    return merged.sort_values("Date")


@st.cache_data(ttl=1800, show_spinner="Loading all manpower data…")
def load_merged_manpower() -> pd.DataFrame:
    """
    Fetch and merge ALL available monthly manpower sheets into one DataFrame.
    """
    frames = []
    for label, (_, m_tab) in ALL_MONTHS.items():
        raw  = fetcher.fetch_sheet_by_name(m_tab)
        m_df = cleaner.clean_manpower_sheet(raw, sheet_name=m_tab)
        if not m_df.empty:
            frames.append(m_df)
    if not frames:
        return pd.DataFrame()
    merged = pd.concat(frames, ignore_index=True)
    merged = merged.drop_duplicates(
        subset=["Date","Shift","Company","Role"]).reset_index(drop=True)
    return merged.sort_values("Date")