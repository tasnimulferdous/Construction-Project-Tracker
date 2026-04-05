# app.py
import sys
import re
import calendar
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src import charts, cleaner, fetcher

# ──────────────────────────────────────────────────────────────
# CONTRACT CONSTANT
# ──────────────────────────────────────────────────────────────
CONTRACT_TOTAL_RM = 201_730.54   # Total pipe to install across full contract

# ──────────────────────────────────────────────────────────────
# 1. PAGE CONFIG
# ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CCECC Project Tracker - Dhaka",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# 2. CSS
# ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Segoe UI', Arial, sans-serif;
    background-color: #0B0D14;
    color: #D1D5E8;
}
.block-container { padding: 4rem 2rem 2rem 2rem !important; }

.kpi-card {
    background: linear-gradient(135deg, rgba(0,229,255,0.06), rgba(0,0,0,0));
    border: 1px solid rgba(0,229,255,0.18);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    margin-bottom: 0.5rem;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00E5FF, transparent);
}
.kpi-card-contract {
    background: linear-gradient(135deg, rgba(168,255,62,0.08), rgba(0,0,0,0));
    border: 1px solid rgba(168,255,62,0.25);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    margin-bottom: 0.5rem;
}
.kpi-card-contract::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #A8FF3E, transparent);
}
.kpi-label {
    font-size: 0.62rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #5A7FAA;
    margin-bottom: 0.3rem;
}
.kpi-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #00E5FF;
    line-height: 1.1;
}
.kpi-value-contract {
    font-size: 1.8rem;
    font-weight: 700;
    color: #A8FF3E;
    line-height: 1.1;
}
.kpi-sub  { font-size: 0.68rem; color: #4B5A78; margin-top: 0.2rem; }
.kpi-warn  { color: #FF6B35; }
.kpi-good  { color: #A8FF3E; }
.kpi-amber { color: #FFD166; }

.section-title {
    font-size: 0.7rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #3D5A80;
    border-bottom: 1px solid rgba(0,229,255,0.1);
    padding-bottom: 0.35rem;
    margin: 1.2rem 0 0.8rem 0;
}
[data-testid="stSidebar"] {
    background-color: #0F1120;
    border-right: 1px solid rgba(255,255,255,0.05);
}
.stPlotlyChart { border-radius: 10px; overflow: hidden; }
hr { border-color: rgba(255,255,255,0.06); }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# 3. SIDEBAR
# ──────────────────────────────────────────────────────────────

MONTH_TABS = {
    "March 2026"   : "Summary (Mar26) ",
    "February 2026": "Summary (Feb26) ",
    "January 2026" : "Summary (Jan26) ",
}
MANPOWER_TABS = {
    "March 2026"   : "Manpower (Mar26)",
    "February 2026": "Manpower (Feb26)",
    "January 2026" : "Manpower (Jan26)",
}

with st.sidebar:
    st.markdown("## CCECC Dashboard")
    st.markdown("**WD5B — Zone W3 & W4**")
    st.markdown("---")

    selected_month_label = st.selectbox(
        "Select Month",
        options=list(MONTH_TABS.keys()),
        index=0,
    )
    summary_tab  = MONTH_TABS[selected_month_label]
    manpower_tab = MANPOWER_TABS[selected_month_label]

    st.markdown("---")
    st.markdown("**Day Range Filter**")

    _month_names = {
        "January":1, "February":2, "March":3,    "April":4,
        "May":5,     "June":6,     "July":7,      "August":8,
        "September":9,"October":10,"November":11, "December":12,
    }
    _m = re.search(r"(\w+) (\d{4})", selected_month_label)
    if _m:
        _mon  = _month_names.get(_m.group(1), 3)
        _year = int(_m.group(2))
    else:
        _mon, _year = 3, 2026

    _days_in_month = calendar.monthrange(_year, _mon)[1]

    day_range = st.slider(
        "Days of month",
        min_value=1,
        max_value=_days_in_month,
        value=(1, _days_in_month),
        step=1,
    )
    filter_start = pd.Timestamp(date(_year, _mon, day_range[0]))
    filter_end   = pd.Timestamp(date(_year, _mon, day_range[1]))

    st.markdown("---")
    st.markdown("**Activity Filter**")
    activity_filter = st.selectbox(
        "Burn-Rate / Daily Progress Activity",
        options=["Pipe", "Road Cutting", "Service Pit"],
        index=0,
    )

    st.markdown("---")
    if st.button("Refresh Data Now", use_container_width=True):
        fetcher.bust_cache()
        st.rerun()

    with st.expander("Sheet Tabs Available", expanded=False):
        all_tabs = fetcher.list_worksheets()
        for t in all_tabs:
            st.caption(f"- {t}")

    st.markdown("---")
    st.caption(
        f"Contract Total: **{CONTRACT_TOTAL_RM:,.2f} rm**\n\n"
        f"Viewing: **{summary_tab.strip()}**\n\n"
        f"Cache TTL: 10 min"
    )

# ──────────────────────────────────────────────────────────────
# 4. FETCH AND CLEAN
# ──────────────────────────────────────────────────────────────

with st.spinner(f"Loading {summary_tab.strip()}..."):
    raw_summary  = fetcher.fetch_sheet_by_name(summary_tab)
    raw_manpower = fetcher.fetch_sheet_by_name(manpower_tab)

summary_df  = cleaner.clean_summary_sheet(raw_summary,  sheet_name=summary_tab)
vehicle_df  = cleaner.clean_vehicle_usage(raw_summary,  sheet_name=summary_tab)
manpower_df = cleaner.clean_manpower_sheet(raw_manpower, sheet_name=manpower_tab)
kpis        = cleaner.compute_kpis(summary_df, filter_start, filter_end)

# ──────────────────────────────────────────────────────────────
# 5. HEADER
# ──────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="margin-bottom:1.2rem;">
    <p style="font-size:1.6rem; font-weight:700; color:#00E5FF; margin:0; padding:0;">
        CCECC-HONESS-SMEDI JV
    </p>
    <p style="font-size:0.85rem; color:#3D5A80; margin:0.15rem 0 0.3rem 0;">
        WD5B &nbsp;|&nbsp; Zone W3 &amp; W4 &nbsp;|&nbsp;
        DWASA Sanitation Network &nbsp;|&nbsp; Package WD5B
    </p>
    <p style="font-size:0.92rem; color:#5A7FAA; margin:0;">
        {selected_month_label} &nbsp;|&nbsp;
        Day {day_range[0]} to {day_range[1]} &nbsp;|&nbsp;
        {filter_start.strftime('%d %b')} to {filter_end.strftime('%d %b %Y')}
    </p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# 6. KPI CARDS — Row 1: Monthly KPIs
# ──────────────────────────────────────────────────────────────

pipe_rm       = kpis.get("total_pipe_installed_rm", 0.0)
pipe_upto_feb = kpis.get("total_pipe_upto_feb",     0.0)
excav_rm      = kpis.get("total_excavation_rm",      0.0)
pits          = kpis.get("total_service_pits",        0.0)
active_days   = kpis.get("active_days",               0)
pct_target    = kpis.get("pct_of_monthly_target",     0.0)
monthly_tgt   = kpis.get("monthly_target_rm",         0.0)

# Contract-level totals
total_installed_all = pipe_upto_feb + pipe_rm
pct_contract        = round(total_installed_all / CONTRACT_TOTAL_RM * 100, 2) if CONTRACT_TOTAL_RM else 0
contract_remaining  = CONTRACT_TOTAL_RM - total_installed_all


def _card(col, label, value, sub="", cls="kpi-value"):
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="{cls}">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def _card_contract(col, label, value, sub=""):
    col.markdown(f"""
    <div class="kpi-card-contract">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value-contract">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


st.markdown('<div class="section-title">Contract Overview</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
_card_contract(c1, "Contract Total",
               f"{CONTRACT_TOTAL_RM:,.0f} rm",
               "Full scope — all months")
_card_contract(c2, "Total Installed",
               f"{total_installed_all:,.1f} rm",
               f"Upto Feb: {pipe_upto_feb:,.0f} + This month: {pipe_rm:,.0f}")
_card_contract(c3, "Contract Completion",
               f"{pct_contract:.2f}%",
               f"{contract_remaining:,.0f} rm remaining")
_card_contract(c4, "Contract Remaining",
               f"{contract_remaining:,.0f} rm",
               f"of {CONTRACT_TOTAL_RM:,.0f} rm total")

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 2: Monthly KPIs ───────────────────────────────────────
st.markdown('<div class="section-title">Monthly Performance Indicators</div>', unsafe_allow_html=True)

pct_cls = "kpi-value kpi-good" if pct_target >= 90 else "kpi-value kpi-amber" if pct_target >= 60 else "kpi-value kpi-warn"

k1, k2, k3, k4, k5, k6 = st.columns(6)

_card(k1, "Pipe Installed",
      f"{pipe_rm:,.1f} rm",
      f"Monthly target: {monthly_tgt:,.0f} rm")

_card(k2, "vs Monthly Target",
      f"{pct_target:.1f}%",
      f"Upto Feb: {pipe_upto_feb:,.0f} rm",
      cls=pct_cls)

_card(k3, "Excavation",
      f"{excav_rm:,.1f} rm",
      "Road cutting + trench")

_card(k4, "Service Pits",
      f"{int(pits)} Pcs",
      "All SD zones")

_card(k5, "Active Days",
      str(active_days),
      f"of {day_range[1] - day_range[0] + 1} selected")

# Manpower KPI
if not manpower_df.empty:
    latest_mp_date = manpower_df.loc[
        manpower_df["Date"] <= filter_end, "Date"
    ].max()
    if pd.notna(latest_mp_date):
        day_mask  = (manpower_df["Date"] == latest_mp_date)
        if "Shift" in manpower_df.columns:
            day_mask = day_mask & (manpower_df["Shift"] == "Day")
        latest_mp = manpower_df.loc[day_mask, "Count"].sum()
        _card(k6, "Total Manpower",
              f"{int(latest_mp)}",
              f"Day shift as of {latest_mp_date.strftime('%d %b')}")
    else:
        _card(k6, "Total Manpower", "--", "no date found")
else:
    _card(k6, "Total Manpower", "--", "no data")

st.markdown("<br>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# 7. CONTRACT PROGRESS BAR
# ──────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">Contract Progress — Total Pipe Installation</div>',
            unsafe_allow_html=True)

fig_contract = charts.contract_progress_chart(
    pipe_upto_feb   = pipe_upto_feb,
    pipe_this_month = pipe_rm,
    contract_total  = CONTRACT_TOTAL_RM,
)
st.plotly_chart(fig_contract, use_container_width=True)

# ──────────────────────────────────────────────────────────────
# 8. BURN RATE + GAUGE
# ──────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">Monthly Burn Rate Analysis</div>', unsafe_allow_html=True)

col_burn, col_gauge = st.columns([3, 1], gap="medium")

with col_burn:
    fig_burn = charts.burn_rate_chart(
        summary_df, filter_start, filter_end,
        activity_filter=activity_filter,
    )
    st.plotly_chart(fig_burn, use_container_width=True)

with col_gauge:
    fig_gauge = charts.completion_gauge(
        achieved=pipe_rm,
        target=monthly_tgt,
        label="Pipe Install vs Monthly Target",
    )
    st.plotly_chart(fig_gauge, use_container_width=True)
    if monthly_tgt > 0:
        remaining = monthly_tgt - pipe_rm
        st.markdown(
            f"<p style='text-align:center;color:#3D5A80;font-size:0.72rem;margin-top:-0.5rem;'>"
            f"<strong style='color:#A0A8C0;'>{remaining:,.1f} rm</strong> remaining this month"
            f"</p>",
            unsafe_allow_html=True,
        )

# ──────────────────────────────────────────────────────────────
# 9. DAILY PROGRESS BAR CHART  (NEW)
# ──────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">Daily Progress</div>', unsafe_allow_html=True)

fig_daily_prog = charts.daily_progress_bar_chart(
    summary_df, filter_start, filter_end,
    activity_filter=activity_filter,
)
st.plotly_chart(fig_daily_prog, use_container_width=True)

# ──────────────────────────────────────────────────────────────
# 10. DAILY PIPE BY SD ZONE
# ──────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">Pipe Installation by SD Zone</div>', unsafe_allow_html=True)

fig_sd = charts.daily_pipe_installation_chart(summary_df, filter_start, filter_end)
st.plotly_chart(fig_sd, use_container_width=True)

# ──────────────────────────────────────────────────────────────
# 11. ACTIVITY BREAKDOWN + VEHICLE USAGE
# ──────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">Work Breakdown & Equipment</div>', unsafe_allow_html=True)

col_act, col_veh = st.columns([3, 2], gap="medium")

with col_act:
    fig_act = charts.activity_breakdown_chart(summary_df, filter_start, filter_end)
    st.plotly_chart(fig_act, use_container_width=True)

with col_veh:
    fig_veh = charts.vehicle_utilisation_chart(vehicle_df, filter_start, filter_end)
    st.plotly_chart(fig_veh, use_container_width=True)

# ──────────────────────────────────────────────────────────────
# 12. MANPOWER SUMMARY CHART  (NEW)
# ──────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">Manpower Statistics</div>', unsafe_allow_html=True)

fig_mp_summary = charts.manpower_summary_chart(manpower_df, filter_start, filter_end)
st.plotly_chart(fig_mp_summary, use_container_width=True)

# ──────────────────────────────────────────────────────────────
# 13. DATA EXPLORER
# ──────────────────────────────────────────────────────────────

with st.expander("Raw Data Explorer", expanded=False):
    tab1, tab2, tab3 = st.tabs(["Work Activities", "Vehicle Usage", "Manpower"])

    with tab1:
        if summary_df.empty:
            st.info("No summary data loaded.")
        else:
            st.dataframe(
                summary_df[
                    (summary_df["Date"] >= filter_start)
                    & (summary_df["Date"] <= filter_end)
                ].sort_values(["Date", "Activity"]),
                use_container_width=True, hide_index=True,
            )
    with tab2:
        if vehicle_df.empty:
            st.info("No vehicle data loaded.")
        else:
            st.dataframe(
                vehicle_df[
                    (vehicle_df["Date"] >= filter_start)
                    & (vehicle_df["Date"] <= filter_end)
                ].sort_values("Date"),
                use_container_width=True, hide_index=True,
            )
    with tab3:
        if manpower_df.empty:
            st.info("No manpower data loaded.")
        else:
            st.dataframe(
                manpower_df[
                    (manpower_df["Date"] >= filter_start)
                    & (manpower_df["Date"] <= filter_end)
                ].sort_values("Date"),
                use_container_width=True, hide_index=True,
            )

# ──────────────────────────────────────────────────────────────
# 14. FOOTER
# ──────────────────────────────────────────────────────────────

st.markdown("""
<hr/>
<p style="text-align:center; color:#1E2A40; font-size:0.68rem; letter-spacing:0.08em;">
    CCECC-HONESS-SMEDI JV &nbsp;|&nbsp; WD5B &nbsp;|&nbsp;
    DWASA SANITATION NETWORK W3 &amp; W4 &nbsp;|&nbsp;
    CONTRACT: 201,730.54 rm &nbsp;|&nbsp; AUTO-REFRESH: 10 MIN
</p>
""", unsafe_allow_html=True)