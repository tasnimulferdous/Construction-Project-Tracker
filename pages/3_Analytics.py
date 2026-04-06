# pages/3_Analytics.py — Analytics & Forecasting
import sys
from pathlib import Path

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.shared import (
    inject_css, render_sidebar, load_all_months,
    build_cumulative_timeline, kpi_card, section_title,
    subnav_buttons, get_chart_theme,
    CONTRACT_TOTAL_RM, CONTRACT_START, CONTRACT_END_PLANNED,
)
from src import cleaner, charts

st.set_page_config(
    page_title="Analytics — CCECC",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

ctx          = render_sidebar()
filter_start = ctx["filter_start"]
filter_end   = ctx["filter_end"]
label        = ctx["selected_month_label"]

with st.spinner("Loading analytics data..."):
    all_months_data     = load_all_months()
    efficiency_df       = cleaner.compute_monthly_efficiency(all_months_data)
    cumulative_timeline = build_cumulative_timeline(all_months_data)

months_count    = len(all_months_data)
total_installed = sum(d["pipe_rm"] for d in all_months_data.values())
remaining_rm    = max(CONTRACT_TOTAL_RM - total_installed, 0)
avg_rate        = total_installed / months_count if months_count else 0
months_left     = round(remaining_rm / avg_rate, 1) if avg_rate else 0
pct_done        = round(total_installed / CONTRACT_TOTAL_RM * 100, 2)

try:
    from dateutil.relativedelta import relativedelta
    proj_finish = pd.Timestamp.now() + relativedelta(
        months=int(months_left), days=int((months_left % 1) * 30))
except ImportError:
    proj_finish = pd.NaT

months_to_end = (CONTRACT_END_PLANNED - pd.Timestamp.now()).days / 30
on_track      = months_left <= months_to_end

ct = get_chart_theme()

def _base_layout(**extra) -> dict:
    return dict(
        paper_bgcolor=ct["paper_bgcolor"], plot_bgcolor=ct["plot_bgcolor"],
        font_color=ct["font_color"], font_family="Segoe UI, Arial, sans-serif",
        hovermode="x unified", margin=dict(l=16,r=16,t=50,b=16),
        legend=dict(bgcolor="rgba(0,0,0,0)",
                    bordercolor="rgba(127,127,127,0.2)", borderwidth=1,
                    font=dict(size=11)),
        **extra,
    )

def _axes(fig):
    fig.update_xaxes(gridcolor=ct["gridcolor"], zerolinecolor=ct["zerolinecolor"],
                     showline=False, tickfont=dict(size=10))
    fig.update_yaxes(gridcolor=ct["gridcolor"], zerolinecolor=ct["zerolinecolor"],
                     showline=False, tickfont=dict(size=10))
    return fig

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:1rem; animation:fade-in 0.5s ease both;">
    <p style="font-size:1.5rem; font-weight:800; color:var(--accent-cyan); margin:0;">
        📈 Analytics & Forecasting
    </p>
    <p style="font-size:0.85rem; color:var(--text-secondary); margin:0.1rem 0;">
        Cross-month analysis &nbsp;|&nbsp; Trajectory &nbsp;|&nbsp; Efficiency &nbsp;|&nbsp; Resources
    </p>
</div>
""", unsafe_allow_html=True)

# ── Global forecast KPIs ──────────────────────────────────────
section_title("Project Forecast Summary")
p1,p2,p3,p4,p5,p6 = st.columns(6)
kpi_card(p1,"Total Installed",   f"{total_installed:,.1f} rm",
         f"Across {months_count} months", cls="kpi-value-green", card_cls="kpi-card-green")
kpi_card(p2,"Remaining",         f"{remaining_rm:,.0f} rm",
         f"{pct_done:.2f}% complete", cls="kpi-value-green", card_cls="kpi-card-green")
kpi_card(p3,"Avg Monthly Rate",  f"{avg_rate:,.0f} rm/mo",
         "Current pace", cls="kpi-value-amber", card_cls="kpi-card-amber")
kpi_card(p4,"Months Remaining",  f"{months_left:.1f} mo",
         "At current pace", cls="kpi-value-amber", card_cls="kpi-card-amber")
kpi_card(p5,"Projected Finish",
         proj_finish.strftime("%b %Y") if pd.notna(proj_finish) else "N/A",
         f"Planned: {CONTRACT_END_PLANNED.strftime('%b %Y')}",
         cls="kpi-value-amber", card_cls="kpi-card-amber")
kpi_card(p6,"On Track",
         "✅ YES" if on_track else "⚠️ DELAYED",
         f"Need {months_to_end:.0f} mo · Have {months_left:.1f} mo",
         cls="kpi-value-green" if on_track else "kpi-value-warn",
         card_cls="kpi-card-green" if on_track else "kpi-card")

st.markdown("<br>", unsafe_allow_html=True)

# ── Sub-navigation ────────────────────────────────────────────
section_title("Select Analysis")
SUBNAV = [
    ("📈", "Contract Progress",   "Trajectory · Planned vs Actual vs Projected"),
    ("⚡", "Efficiency Analysis", "rm/person/day · Trend · Month comparison"),
    ("📅", "Monthly Comparison",  "Output · Manpower · Excavation by month"),
    ("🧮", "Resource Calculator", "Target rm → Days & Manpower required"),
]
selected = subnav_buttons(SUBNAV, "analytics_subnav")
st.markdown("<br>", unsafe_allow_html=True)

months = list(all_months_data.keys())

# ──────────────────────────────────────────────────────────────
# CONTRACT PROGRESS
# ──────────────────────────────────────────────────────────────

if selected == "Contract Progress":
    section_title("Contract Trajectory — Actual vs Planned vs Projected")

    # Build trajectory chart with current theme
    actual_dates = [d["date"]          for d in cumulative_timeline]
    actual_vals  = [d["cumulative_rm"] for d in cumulative_timeline]

    planned_dates = [CONTRACT_START, CONTRACT_END_PLANNED]
    planned_vals  = [0, CONTRACT_TOTAL_RM]

    proj_dates = [actual_dates[-1]] if actual_dates else []
    proj_vals  = [actual_vals[-1]]  if actual_vals  else []
    if pd.notna(proj_finish) and avg_rate > 0 and proj_dates:
        cur, cur_val = proj_dates[0], proj_vals[0]
        while cur < proj_finish and cur_val < CONTRACT_TOTAL_RM:
            cur     = cur + pd.DateOffset(months=1)
            cur_val = min(cur_val + avg_rate, CONTRACT_TOTAL_RM)
            proj_dates.append(cur)
            proj_vals.append(cur_val)

    fig_traj = go.Figure()
    fig_traj.add_trace(go.Scatter(x=planned_dates, y=planned_vals,
                                  name="Planned", mode="lines",
                                  line=dict(color=ct["gridcolor"], width=2, dash="dot")))
    if len(proj_dates) > 1:
        fig_traj.add_trace(go.Scatter(x=proj_dates, y=proj_vals,
                                      name=f"Projected (@{avg_rate:,.0f} rm/mo)",
                                      mode="lines",
                                      line=dict(color="#FFD166", width=2, dash="dash")))
    if actual_dates:
        fig_traj.add_trace(go.Scatter(
            x=actual_dates, y=actual_vals,
            name="Actual Cumulative", mode="lines+markers+text",
            line=dict(color="#00E5FF", width=3),
            marker=dict(size=10, color="#00E5FF", line=dict(width=2, color="#fff")),
            text=[f"{v:,.0f} rm" for v in actual_vals],
            textposition="top center", textfont=dict(size=11),
            fill="tozeroy", fillcolor="rgba(0,229,255,0.07)",
        ))
    fig_traj.add_hline(y=CONTRACT_TOTAL_RM, line_dash="dot", line_color="#A8FF3E",
                       line_width=1.5,
                       annotation_text=f"Contract: {CONTRACT_TOTAL_RM:,.0f} rm",
                       annotation_position="right",
                       annotation_font=dict(color="#A8FF3E", size=11))
    if pd.notna(proj_finish):
        fig_traj.add_vline(x=proj_finish.timestamp()*1000,
                           line_dash="dash", line_color="#FFD166", line_width=1,
                           annotation_text=f"Est. Finish: {proj_finish.strftime('%b %Y')}",
                           annotation_position="top right",
                           annotation_font=dict(color="#FFD166", size=10))
    fig_traj.update_layout(
        title_text="Contract Progress Trajectory",
        title_font=dict(size=14, color=ct["font_color"]),
        **_base_layout(), height=440,
        yaxis=dict(title="Cumulative Pipe (rm)", title_font=dict(size=11),
                   tickformat=",", gridcolor=ct["gridcolor"]),
        xaxis=dict(title="", tickformat="%b %Y", gridcolor=ct["gridcolor"]),
    )
    _axes(fig_traj)
    st.plotly_chart(fig_traj, use_container_width=True)

    # Progress bar chart
    section_title("Cumulative Progress Bar")
    total_done = total_installed
    remaining  = max(CONTRACT_TOTAL_RM - total_done, 0)
    upto_feb   = sum(d.get("upto_feb", 0) for d in all_months_data.values()
                     if "feb" in d.get("label","").lower()) if False else \
                 list(all_months_data.values())[0].get("upto_feb",0) if all_months_data else 0
    this_month = list(all_months_data.values())[-1]["pipe_rm"] if all_months_data else 0

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(name="Completed", x=[total_done], y=["Progress"],
                             orientation="h", marker_color="#00E5FF", opacity=0.9,
                             text=f"{total_done:,.1f} rm ({pct_done:.2f}%)",
                             textposition="inside", textfont=dict(size=12, color="#000")))
    fig_bar.add_trace(go.Bar(name="Remaining", x=[remaining], y=["Progress"],
                             orientation="h",
                             marker_color="rgba(127,127,127,0.25)",
                             text=f"{remaining:,.0f} rm remaining",
                             textposition="inside", textfont=dict(size=11)))
    fig_bar.add_vline(x=CONTRACT_TOTAL_RM, line_dash="dot", line_color="#FFD166",
                      line_width=2,
                      annotation_text=f"Total: {CONTRACT_TOTAL_RM:,.0f} rm",
                      annotation_font=dict(color="#FFD166", size=11),
                      annotation_position="top right")
    fig_bar.update_layout(barmode="stack", **_base_layout(), height=130,
                          yaxis=dict(showticklabels=False),
                          xaxis=dict(title="Running Metres (rm)", tickformat=","),
                          showlegend=True,
                          legend=dict(orientation="h", yanchor="bottom", y=1.1,
                                      xanchor="left", x=0))
    st.plotly_chart(fig_bar, use_container_width=True)

    section_title("Cumulative Data")
    with st.expander("View Trajectory Data", expanded=False):
        traj_df = pd.DataFrame(cumulative_timeline)
        traj_df["remaining_rm"]   = CONTRACT_TOTAL_RM - traj_df["cumulative_rm"]
        traj_df["completion_pct"] = (traj_df["cumulative_rm"] / CONTRACT_TOTAL_RM * 100).round(2)
        st.dataframe(traj_df, use_container_width=True, hide_index=True)

# ──────────────────────────────────────────────────────────────
# EFFICIENCY ANALYSIS
# ──────────────────────────────────────────────────────────────

elif selected == "Efficiency Analysis":
    section_title("Efficiency: rm Installed per Person per Day")

    if not efficiency_df.empty:
        # Summary table
        disp = efficiency_df[[
            "Month","Pipe_rm","Active_Days","Avg_Manpower",
            "RM_per_Person_Day","Efficiency_Change_Pct","Efficiency_Trend"
        ]].copy()
        disp.columns = [
            "Month","Pipe (rm)","Active Days","Avg Manpower",
            "rm/Person/Day","Efficiency Δ%","Trend"
        ]
        disp["Pipe (rm)"]      = disp["Pipe (rm)"].round(1)
        disp["rm/Person/Day"]  = disp["rm/Person/Day"].round(4)
        disp["Efficiency Δ%"]  = disp["Efficiency Δ%"].round(1)
        st.dataframe(disp, use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # 4-panel efficiency chart
    fig_eff = charts.monthly_efficiency_chart(efficiency_df)
    fig_eff.update_layout(**_base_layout(), height=640)
    for ax in fig_eff.layout:
        if ax.startswith("xaxis") or ax.startswith("yaxis"):
            fig_eff.layout[ax].gridcolor     = ct["gridcolor"]
            fig_eff.layout[ax].zerolinecolor = ct["zerolinecolor"]
            fig_eff.layout[ax].color         = ct["font_color"]
    st.plotly_chart(fig_eff, use_container_width=True)

    section_title("Full Efficiency Data")
    with st.expander("View Full Table", expanded=False):
        st.dataframe(efficiency_df, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", efficiency_df.to_csv(index=False).encode(),
                           "efficiency_data.csv", "text/csv")

# ──────────────────────────────────────────────────────────────
# MONTHLY COMPARISON
# ──────────────────────────────────────────────────────────────

elif selected == "Monthly Comparison":
    section_title("Month-over-Month Comparison")

    if len(all_months_data) >= 1:
        comparison_rows = []
        for i, lbl in enumerate(months):
            d    = all_months_data[lbl]
            prev = all_months_data[months[i-1]] if i > 0 else None
            def _chg(curr, pv):
                return round((curr-pv)/pv*100, 1) if pv and pv > 0 else None
            comparison_rows.append({
                "Month"             : lbl,
                "Pipe Installed (rm)": round(d["pipe_rm"], 1),
                "Pipe Δ%"           : _chg(d["pipe_rm"],      prev["pipe_rm"]      if prev else None),
                "Avg Manpower"      : round(d["avg_manpower"], 1),
                "Manpower Δ%"       : _chg(d["avg_manpower"],  prev["avg_manpower"] if prev else None),
                "Excavation (rm)"   : round(d["excav_rm"], 1),
                "Excav Δ%"          : _chg(d["excav_rm"],      prev["excav_rm"]     if prev else None),
                "Active Days"       : d["active_days"],
                "Service Pits (Pcs)": int(d.get("pits", 0)),
            })
        comp_df = pd.DataFrame(comparison_rows)
        st.dataframe(comp_df, use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Visual comparison
        COLORS3 = ["#00E5FF","#FF6B35","#A8FF3E"]
        metrics = [
            ("pipe_rm",      "Pipe Installed (rm)"),
            ("avg_manpower", "Avg Daily Manpower"),
            ("excav_rm",     "Excavation (rm)"),
        ]
        fig_comp = make_subplots(rows=1, cols=3,
                                 subplot_titles=[m[1] for m in metrics],
                                 horizontal_spacing=0.10)
        for ci, (key, mlabel) in enumerate(metrics, start=1):
            vals = [all_months_data[m][key] for m in months]
            fig_comp.add_trace(go.Bar(
                x=months, y=vals, name=mlabel,
                marker_color=COLORS3[ci-1], opacity=0.85,
                text=[f"{v:,.1f}" for v in vals],
                textposition="outside", textfont=dict(size=10),
                showlegend=False,
            ), row=1, col=ci)

        fig_comp.update_layout(**_base_layout(), height=340)
        for ax in fig_comp.layout:
            if ax.startswith("xaxis") or ax.startswith("yaxis"):
                fig_comp.layout[ax].gridcolor     = ct["gridcolor"]
                fig_comp.layout[ax].zerolinecolor = ct["zerolinecolor"]
                fig_comp.layout[ax].tickfont      = dict(size=10, color=ct["font_color"])
        fig_comp.update_annotations(font=dict(size=12, color=ct["font_color"]))
        st.plotly_chart(fig_comp, use_container_width=True)

        # Δ% chart
        if len(months) > 1:
            section_title("Month-over-Month Change (%)")
            fig_delta = go.Figure()
            DELTA_KEYS = [
                ("Pipe Δ%",     "Pipe Output",  "#00E5FF"),
                ("Manpower Δ%", "Manpower",     "#FFD166"),
                ("Excav Δ%",    "Excavation",   "#FF6B35"),
            ]
            for col_name, dlabel, dcolor in DELTA_KEYS:
                if col_name in comp_df.columns:
                    fig_delta.add_trace(go.Bar(
                        x=comp_df["Month"], y=comp_df[col_name].fillna(0),
                        name=dlabel, marker_color=dcolor, opacity=0.78,
                    ))
            fig_delta.add_hline(y=0, line_color="rgba(127,127,127,0.3)", line_width=1)
            fig_delta.update_layout(barmode="group", **_base_layout(), height=300)
            fig_delta.update_yaxes(title_text="Change (%)", title_font=dict(size=10))
            _axes(fig_delta)
            st.plotly_chart(fig_delta, use_container_width=True)

        section_title("Comparison Data")
        with st.expander("View Full Comparison Table", expanded=False):
            st.dataframe(comp_df, use_container_width=True, hide_index=True)
            st.download_button("Download CSV", comp_df.to_csv(index=False).encode(),
                               "monthly_comparison.csv", "text/csv")
    else:
        st.info("Need at least one month of data.")

# ──────────────────────────────────────────────────────────────
# RESOURCE CALCULATOR
# ──────────────────────────────────────────────────────────────

elif selected == "Resource Calculator":
    section_title("Resource Requirements Calculator")

    st.markdown("""
    <p style="color:var(--text-secondary); font-size:0.85rem; margin-bottom:1rem;">
        Enter a target installation quantity and available manpower to estimate
        how long the work will take — based on your current productivity rate.
    </p>
    """, unsafe_allow_html=True)

    avg_eff = float(efficiency_df["RM_per_Person_Day"].dropna().mean()) \
              if not efficiency_df.empty else 0
    last_mp = float(efficiency_df["Avg_Manpower"].iloc[-1]) \
              if not efficiency_df.empty else 0

    inp_col, res_col = st.columns([1, 2], gap="large")

    with inp_col:
        st.markdown("**Inputs**")
        target_rm = st.number_input(
            "Target Pipe to Install (rm)",
            min_value=1.0, max_value=float(CONTRACT_TOTAL_RM),
            value=min(1000.0, remaining_rm), step=100.0)
        manpower_input = st.number_input(
            "Available Daily Manpower (persons)",
            min_value=1, max_value=500,
            value=max(int(last_mp), 10), step=5)
        working_days_pm = st.slider(
            "Working Days per Month", min_value=15, max_value=31, value=22)

        st.markdown("---")
        st.markdown(f"""
        <div style="font-size:0.78rem; color:var(--text-secondary); line-height:1.8;">
            <b>Current Productivity</b><br>
            {avg_eff:.4f} rm / person / day<br>
            Based on {months_count} months of data
        </div>
        """, unsafe_allow_html=True)

    with res_col:
        if avg_eff > 0 and manpower_input > 0:
            days_needed      = target_rm / (avg_eff * manpower_input)
            months_needed    = days_needed / working_days_pm
            daily_output     = avg_eff * manpower_input
            mp_for_one_month = target_rm / (avg_eff * working_days_pm) if avg_eff > 0 else 0

            r1,r2,r3,r4 = st.columns(4)
            kpi_card(r1,"Days Required",
                     f"{days_needed:.0f} days",
                     f"@ {manpower_input} persons/day",
                     cls="kpi-value-amber", card_cls="kpi-card-amber")
            kpi_card(r2,"Months Required",
                     f"{months_needed:.1f} mo",
                     f"{working_days_pm} working days/mo",
                     cls="kpi-value-amber", card_cls="kpi-card-amber")
            kpi_card(r3,"Daily Output",
                     f"{daily_output:.1f} rm/day",
                     f"{avg_eff:.4f} rm/person/day",
                     cls="kpi-value-amber", card_cls="kpi-card-amber")
            kpi_card(r4,"Manpower for 1 Month",
                     f"{mp_for_one_month:.0f} persons",
                     f"to do {target_rm:,.0f} rm in 1 month",
                     cls="kpi-value-amber", card_cls="kpi-card-amber")

            st.markdown("<br>", unsafe_allow_html=True)

            # Sensitivity curve
            mp_range    = list(range(5, 301, 5))
            days_range  = [target_rm/(avg_eff*mp) if avg_eff > 0 else 0 for mp in mp_range]
            month_range = [d/working_days_pm for d in days_range]

            fig_sens = make_subplots(specs=[[{"secondary_y": True}]])
            fig_sens.add_trace(go.Scatter(
                x=mp_range, y=days_range,
                name="Days Required", mode="lines",
                line=dict(color="#00E5FF", width=2.5),
                fill="tozeroy", fillcolor="rgba(0,229,255,0.07)",
            ), secondary_y=False)
            fig_sens.add_trace(go.Scatter(
                x=mp_range, y=month_range,
                name="Months Required", mode="lines",
                line=dict(color="#FFD166", width=2, dash="dash"),
            ), secondary_y=True)
            # Mark selection
            fig_sens.add_trace(go.Scatter(
                x=[manpower_input], y=[days_needed],
                name="Your Selection", mode="markers",
                marker=dict(size=14, color="#A8FF3E", symbol="star",
                            line=dict(width=2, color="#fff")),
            ), secondary_y=False)
            fig_sens.update_layout(
                title_text=f"Days vs Manpower for {target_rm:,.0f} rm",
                title_font=dict(size=13, color=ct["font_color"]),
                **_base_layout(), height=340)
            fig_sens.update_yaxes(title_text="Days Required", secondary_y=False,
                                  title_font=dict(size=10), gridcolor=ct["gridcolor"])
            fig_sens.update_yaxes(title_text="Months Required", secondary_y=True,
                                  title_font=dict(size=10), showgrid=False)
            fig_sens.update_xaxes(title_text="Daily Manpower (persons)",
                                  gridcolor=ct["gridcolor"])
            _axes(fig_sens)
            st.plotly_chart(fig_sens, use_container_width=True)

            # What-if table
            section_title("What-If Scenarios")
            scenarios = []
            for mp in [20, 30, 40, 50, 75, 100, 150, 200]:
                d = target_rm/(avg_eff*mp) if avg_eff > 0 else 0
                m = d/working_days_pm
                scenarios.append({
                    "Daily Manpower": mp,
                    "Days Required" : round(d,0),
                    "Months Required": round(m,1),
                    "Daily Output (rm)": round(avg_eff*mp,1),
                })
            st.dataframe(pd.DataFrame(scenarios), use_container_width=True, hide_index=True)
        else:
            st.warning("Not enough productivity data. Need at least one month with manpower records.")

st.markdown("""
<hr/>
<p style="text-align:center; color:var(--text-muted); font-size:0.65rem;">
    CCECC-HONESS-SMEDI JV &nbsp;|&nbsp; WD5B &nbsp;|&nbsp; Analytics & Forecasting
</p>
""", unsafe_allow_html=True)