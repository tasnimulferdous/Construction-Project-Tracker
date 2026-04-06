# app.py — Landing Page
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

# Extra landing-page only styles
st.markdown("""
<style>
.block-container { padding: 3rem 3rem 2rem 3rem !important; }

.project-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: var(--accent-cyan);
    letter-spacing: 0.02em;
    margin: 0 0 0.3rem 0;
    animation: fade-in 0.6s ease both;
}
.project-sub {
    font-size: 0.95rem;
    color: var(--text-secondary);
    margin: 0 0 0.1rem 0;
    animation: fade-in 0.7s ease both;
}
.project-meta {
    font-size: 0.82rem;
    color: var(--text-muted);
    margin-bottom: 2rem;
    animation: fade-in 0.8s ease both;
}

/* Landing nav cards */
.land-card {
    background: var(--bg-card);
    border: 1.5px solid var(--border-card);
    border-radius: 20px;
    padding: 2.8rem 1.5rem 2.2rem 1.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    animation: pulse-glow 3.5s ease-in-out infinite, fade-in 0.6s ease both;
    transition: border-color 0.25s, background 0.25s, transform 0.2s, box-shadow 0.25s;
    margin-bottom: 0.5rem;
}
.land-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, var(--accent-cyan), transparent);
}
.land-card:hover {
    border-color: var(--border-hover);
    background: var(--bg-card-hover);
    transform: translateY(-5px);
    box-shadow: 0 12px 30px var(--shadow);
}
.land-icon {
    font-size: 4rem;
    display: block;
    margin-bottom: 0.9rem;
    transition: transform 0.3s ease;
}
.land-card:hover .land-icon {
    animation: float 1.4s ease-in-out infinite;
}
.land-title {
    font-size: 1.3rem;
    font-weight: 800;
    color: var(--accent-cyan);
    margin-bottom: 0.5rem;
    letter-spacing: 0.02em;
}
.land-desc {
    font-size: 0.82rem;
    color: var(--text-secondary);
    line-height: 1.7;
}
.land-badge {
    display: inline-block;
    margin-top: 0.8rem;
    padding: 0.2rem 0.8rem;
    border-radius: 999px;
    border: 1px solid var(--border-card);
    font-size: 0.68rem;
    color: var(--text-secondary);
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

/* hide the plain Streamlit button under each card */
div[data-testid="column"] > div > div > div > .stButton > button {
    opacity: 0;
    position: absolute;
    top: 0; left: 0;
    width: 100%;
    height: 100%;
    cursor: pointer;
    border-radius: 20px;
}
/* Theme toggle button in top-right */
.theme-row { display: flex; justify-content: flex-end; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ── Theme toggle ──────────────────────────────────────────────
top_l, top_r = st.columns([6, 1])
with top_r:
    theme = _get_theme()
    if st.button("☀️" if theme == "dark" else "🌙", help="Toggle light/dark mode",
                 use_container_width=True):
        st.session_state["theme"] = "light" if theme == "dark" else "dark"
        st.rerun()

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<p class="project-title">🏗️ CCECC-HONESS-SMEDI JV</p>
<p class="project-sub">
    Design Build Contract — Reconstruction / New Construction / Rehabilitation of Sanitation Network
</p>
<p class="project-meta">
    Package WD5B &nbsp;|&nbsp; Zone W3 &amp; W4 &nbsp;|&nbsp;
    Dhaka Water Supply and Sewerage Authority (DWASA) &nbsp;|&nbsp;
    Contract Scope: 201,730.54 rm
</p>
""", unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# ── Contract KPIs ─────────────────────────────────────────────
section_title("Contract Overview")

with st.spinner("Loading contract summary..."):
    all_months_data = load_all_months()

total_installed = sum(d["pipe_rm"] for d in all_months_data.values())
remaining_rm    = max(CONTRACT_TOTAL_RM - total_installed, 0)
pct_done        = round(total_installed / CONTRACT_TOTAL_RM * 100, 2)
months_count    = len(all_months_data)
avg_rate        = total_installed / months_count if months_count else 0
months_left     = round(remaining_rm / avg_rate, 1) if avg_rate else 0

c1, c2, c3, c4, c5 = st.columns(5)
kpi_card(c1, "Contract Total",
         f"{CONTRACT_TOTAL_RM:,.0f} rm", "Full scope",
         cls="kpi-value-green", card_cls="kpi-card-green")
kpi_card(c2, "Total Installed",
         f"{total_installed:,.1f} rm", f"Across {months_count} months",
         cls="kpi-value-green", card_cls="kpi-card-green")
kpi_card(c3, "Overall Completion",
         f"{pct_done:.2f}%", f"{remaining_rm:,.0f} rm remaining",
         cls="kpi-value-green", card_cls="kpi-card-green")
kpi_card(c4, "Avg Monthly Rate",
         f"{avg_rate:,.0f} rm/mo", "Current pace",
         cls="kpi-value-amber", card_cls="kpi-card-amber")
kpi_card(c5, "Est. Months Remaining",
         f"{months_left:.1f} mo",
         f"Planned end: {CONTRACT_END_PLANNED.strftime('%b %Y')}",
         cls="kpi-value-amber", card_cls="kpi-card-amber")

st.markdown("<br><br>", unsafe_allow_html=True)
section_title("Select a Module")
st.markdown("<br>", unsafe_allow_html=True)

# ── Navigation cards ──────────────────────────────────────────
n1, n2, n3 = st.columns(3, gap="large")

CARDS = [
    (n1, "📊", "Project Progress",
     "Monthly KPIs · Pipe Installation\nRoad Cutting · Service Pits\nTarget vs Actual charts",
     "Pipes · Excavation · Work Activity",
     "pages/1_Progress.py"),
    (n2, "👷", "Manpower",
     "Total headcount by company & role\nCCECC vs Subcontractors\nDaily trend analysis",
     "Overview · CCECC · Sub Contractors",
     "pages/2_Manpower.py"),
    (n3, "📈", "Analytics",
     "Contract trajectory & forecast\nEfficiency analysis month-on-month\nResource calculator",
     "Progress · Efficiency · Comparison · Calculator",
     "pages/3_Analytics.py"),
]

for col, icon, title, desc, badge, page in CARDS:
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

# ── Footer ────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<hr/>
<p style="text-align:center; color:var(--text-muted); font-size:0.66rem; letter-spacing:0.08em;">
    CCECC-HONESS-SMEDI JV &nbsp;|&nbsp; WD5B &nbsp;|&nbsp;
    DWASA SANITATION NETWORK W3 &amp; W4 &nbsp;|&nbsp;
    CONTRACT: 201,730.54 rm &nbsp;|&nbsp; DATA: GOOGLE SHEETS MASTER TRACKER
</p>
""", unsafe_allow_html=True)