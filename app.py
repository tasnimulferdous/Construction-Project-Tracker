# app.py
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.shared import (
    CONTRACT_TOTAL_RM, CONTRACT_END_PLANNED,
    inject_css, load_all_months, kpi_card, section_title, _get_theme,
)

st.set_page_config(
    page_title="CCECC Project Tracker",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()

st.markdown("""
<style>
.block-container { padding: 3rem 3rem 2rem 3rem !important; }
.project-title {
    font-size: 2.4rem; font-weight: 800; color: var(--accent-cyan, #00E5FF);
    letter-spacing: .02em; margin: 0 0 .3rem 0; animation: fade-in .6s ease both;
}
</style>
""", unsafe_allow_html=True)

# ── Theme toggle row ──────────────────────────────────────────
tl, tr = st.columns([8, 1])
with tr:
    theme = _get_theme()
    if st.button("☀️" if theme == "dark" else "🌙",
                 help="Toggle light/dark mode", use_container_width=True):
        st.session_state["theme"] = "light" if theme == "dark" else "dark"
        st.rerun()

# ── Header ────────────────────────────────────────────────────
p = __import__("src.shared", fromlist=["_p"])._p()

st.markdown(f"""
<p style="font-size:2.4rem;font-weight:800;color:{p['cyan']};margin:0 0 .3rem 0;
          animation:fade-in .6s ease both;">🏗️ CCECC-HONESS-SMEDI JV</p>
<p style="font-size:.95rem;color:{p['text_s']};margin:0 0 .1rem 0;">
    Design Build Contract — Reconstruction / New Construction / Rehabilitation of Sanitation Network
</p>
<p style="font-size:.82rem;color:{p['text_m']};margin-bottom:1.8rem;">
    Package WD5B &nbsp;|&nbsp; Zone W3 &amp; W4 &nbsp;|&nbsp;
    Dhaka Water Supply and Sewerage Authority (DWASA) &nbsp;|&nbsp;
    Contract Scope: 201,730.54 rm
</p>
""", unsafe_allow_html=True)

st.markdown(f"<hr style='border-color:{p['sec_border']}'>", unsafe_allow_html=True)

# ── Contract KPIs ─────────────────────────────────────────────
section_title("Contract Overview")

with st.spinner("Loading contract summary…"):
    all_months_data = load_all_months()

total_installed = sum(d["pipe_rm"] for d in all_months_data.values())
remaining_rm    = max(CONTRACT_TOTAL_RM - total_installed, 0)
pct_done        = round(total_installed / CONTRACT_TOTAL_RM * 100, 2)
months_count    = len(all_months_data)
avg_rate        = total_installed / months_count if months_count else 0
months_left     = round(remaining_rm / avg_rate, 1) if avg_rate else 0

c1,c2,c3,c4,c5 = st.columns(5)
kpi_card(c1,"Contract Total",      f"{CONTRACT_TOTAL_RM:,.0f} rm","Full scope",
         cls="kpi-value-green", card_cls="kpi-card-green")
kpi_card(c2,"Total Installed",     f"{total_installed:,.1f} rm",f"Across {months_count} months",
         cls="kpi-value-green", card_cls="kpi-card-green")
kpi_card(c3,"Overall Completion",  f"{pct_done:.2f}%",f"{remaining_rm:,.0f} rm remaining",
         cls="kpi-value-green", card_cls="kpi-card-green")
kpi_card(c4,"Avg Monthly Rate",    f"{avg_rate:,.0f} rm/mo","Current pace",
         cls="kpi-value-amber", card_cls="kpi-card-amber")
kpi_card(c5,"Est. Months Remaining",f"{months_left:.1f} mo",
         f"Planned end: {CONTRACT_END_PLANNED.strftime('%b %Y')}",
         cls="kpi-value-amber", card_cls="kpi-card-amber")

st.markdown("<br><br>", unsafe_allow_html=True)
section_title("Select a Module")
st.markdown("<br>", unsafe_allow_html=True)

# ── Navigation cards ──────────────────────────────────────────
CARDS = [
    ("📊","Project Progress",
     "Monthly KPIs · Pipe Installation\nRoad Cutting · Service Pits\nTarget vs Actual charts",
     "Pipes · Excavation · Work Activity","pages/1_Progress.py"),
    ("👷","Manpower",
     "Total headcount by company & role\nCCECC vs Subcontractors\nDaily trend analysis",
     "Overview · CCECC · Sub Contractors","pages/2_Manpower.py"),
    ("📈","Analytics",
     "Contract trajectory & forecast\nEfficiency analysis month-on-month\nResource calculator",
     "Progress · Efficiency · Comparison · Calculator","pages/3_Analytics.py"),
]

cols = st.columns(3, gap="large")
for col, (icon, title, desc, badge, page) in zip(cols, CARDS):
    with col:
        st.markdown(f"""
        <div class="land-card">
            <span class="land-icon">{icon}</span>
            <div class="land-title">{title}</div>
            <div class="land-desc">{desc}</div>
            <span class="land-badge">{badge}</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Open {title}", key=f"land_{title}", use_container_width=True):
            st.switch_page(page)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<hr style='border-color:{p['sec_border']}'/>
<p style="text-align:center;color:{p['text_m']};font-size:.66rem;letter-spacing:.08em;">
    CCECC-HONESS-SMEDI JV &nbsp;|&nbsp; WD5B &nbsp;|&nbsp;
    DWASA SANITATION NETWORK W3 &amp; W4 &nbsp;|&nbsp;
    CONTRACT: 201,730.54 rm &nbsp;|&nbsp; DATA: GOOGLE SHEETS MASTER TRACKER
</p>
""", unsafe_allow_html=True)