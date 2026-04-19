# app.py — Landing Page
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.shared import (
    CONTRACT_TOTAL_RM, CONTRACT_END_PLANNED,
    inject_css, load_all_months, kpi_card, PAL,
)

st.set_page_config(
    page_title="CCECC Project Tracker",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()

p = PAL

# ── Extra landing-only CSS: make st.button look like nav cards ─
st.markdown(f"""
<style>
/* Target each nav button by its key-derived data-testid */
div[data-testid="stHorizontalBlock"] .stButton > button {{
    width: 100% !important;
    min-height: 260px !important;
    background: #FFFFFF !important;
    border: 2px solid {p['border_s']} !important;
    border-radius: 20px !important;
    color: {p['text']} !important;
    font-family: 'Inter','Segoe UI',Arial,sans-serif !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    white-space: pre-line !important;
    line-height: 1.8 !important;
    padding: 2rem 1.5rem !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
    transition: all 0.22s ease !important;
    cursor: pointer !important;
    position: relative !important;
    overflow: hidden !important;
}}
div[data-testid="stHorizontalBlock"] .stButton > button::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, {p['blue']}, {p['blue_l']}, {p['teal']});
    border-radius: 18px 18px 0 0;
}}
div[data-testid="stHorizontalBlock"] .stButton > button:hover {{
    border-color: {p['blue']} !important;
    background: linear-gradient(160deg, {p['blue_ll']}, #FFFFFF) !important;
    box-shadow: 0 10px 28px rgba(26,86,219,0.18) !important;
    transform: translateY(-5px) !important;
    color: {p['blue']} !important;
}}
</style>
""", unsafe_allow_html=True)

# ── Compact header ─────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            margin-bottom:.8rem;">
    <div>
        <p style="font-size:3rem;font-weight:800;color:{p['text']};margin:0;
                  font-family:'Inter','Segoe UI',Arial,sans-serif;
                  letter-spacing:-.01em;">
            🏗️&nbsp; CCECC-HONESS-SMEDI JV
        </p>
        <p style="font-size:.8125rem;color:{p['text3']};margin:.1rem 0 0 0;">
            Design Build Contract &nbsp;·&nbsp; Sanitation Network Zone W3 &amp; W4
            &nbsp;·&nbsp; Package WD5B &nbsp;·&nbsp; DWASA
        </p>
    </div>
    <span style="background:{p['blue_ll']};color:{p['blue']};
                 font-size:.75rem;font-weight:700;letter-spacing:.07em;
                 text-transform:uppercase;padding:.3rem 1rem;
                 border-radius:999px;white-space:nowrap;">
        LIVE DASHBOARD
    </span>
</div>
<hr style="border:none;border-top:2px solid {p['border_s']};margin:.2rem 0 .9rem 0;">
""", unsafe_allow_html=True)

# ── Contract KPIs ─────────────────────────────────────────────
with st.spinner("Loading contract data…"):
    all_months_data = load_all_months()

total_installed = sum(d["pipe_rm"] for d in all_months_data.values())
remaining_rm    = max(CONTRACT_TOTAL_RM - total_installed, 0)
pct_done        = round(total_installed / CONTRACT_TOTAL_RM * 100, 2)
months_count    = len(all_months_data)
avg_rate        = total_installed / months_count if months_count else 0
months_left     = round(remaining_rm / avg_rate, 1) if avg_rate else 0

c1, c2, c3, c4, c5 = st.columns(5)
kpi_card(c1, "Contract Scope",      f"{CONTRACT_TOTAL_RM:,.0f} rm",
         "Total pipe to install",    val_cls="kpi-val-green",  card_cls="kpi-green")
kpi_card(c2, "Total Installed",      f"{total_installed:,.1f} rm",
         f"Across {months_count} months", val_cls="kpi-val-green", card_cls="kpi-green")
kpi_card(c3, "Overall Completion",   f"{pct_done:.2f}%",
         f"{remaining_rm:,.0f} rm remaining", val_cls="kpi-val-green", card_cls="kpi-green")
kpi_card(c4, "Avg Monthly Rate",     f"{avg_rate:,.0f} rm/mo",
         "At current pace",          val_cls="kpi-val-amber",  card_cls="kpi-amber")
kpi_card(c5, "Est. Months Left",     f"{months_left:.1f} mo",
         f"Planned: {CONTRACT_END_PLANNED.strftime('%b %Y')}",
         val_cls="kpi-val-amber",    card_cls="kpi-amber")

# ── Section label ─────────────────────────────────────────────
st.markdown(f"""
<p style="font-size:.6875rem;font-weight:700;letter-spacing:.12em;
          text-transform:uppercase;color:{p['text3']};
          border-bottom:2px solid {p['border_s']};
          padding-bottom:.4rem;margin:1.1rem 0 1rem 0;">
    Select Module
</p>
""", unsafe_allow_html=True)

# ── Navigation — pure Streamlit buttons styled as cards ────────
CARDS = [
    ("pages/1_Progress.py", "nav_progress",
     "📊\n\nProject Progress\n\nPipe · Road Cutting · Service Pits · Manhole\nTarget vs Actual · SD zone breakdown"),
    ("pages/2_Manpower.py", "nav_manpower",
     "👷\n\nManpower\n\nHeadcount by company & role\nCCECC · Sub-contractors · Daily trends"),
    ("pages/3_Analytics.py", "nav_analytics",
     "📈\n\nAnalytics\n\nContract trajectory & forecast\nEfficiency · Comparison · Resource calculator"),
]

nav_cols = st.columns(3, gap="large")
for col, (page, key, label) in zip(nav_cols, CARDS):
    with col:
        if st.button(label, key=key, use_container_width=True):
            st.switch_page(page)

# ── Footer ────────────────────────────────────────────────────
st.markdown(f"""
<hr style="border:none;border-top:1px solid {p['border_s']};margin:1.4rem 0 .4rem 0;">
<p style="text-align:center;color:{p['text4']};font-size:.6875rem;letter-spacing:.05em;">
    CCECC-HONESS-SMEDI JV &nbsp;·&nbsp; WD5B &nbsp;·&nbsp;
    DWASA Sanitation Network W3 &amp; W4 &nbsp;·&nbsp;
    Contract: {CONTRACT_TOTAL_RM:,.0f} rm &nbsp;·&nbsp; Data: Google Sheets Master Tracker
</p>
""", unsafe_allow_html=True)