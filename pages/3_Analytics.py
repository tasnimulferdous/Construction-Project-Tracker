# pages/3_Analytics.py
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.shared import (
    inject_css, render_sidebar, load_all_months,
    build_cumulative_timeline, kpi_card, section_title,
    subnav_buttons, base_layout, apply_axes, get_chart_theme, _LEGEND,
    CONTRACT_TOTAL_RM, CONTRACT_START, CONTRACT_END_PLANNED,
)
from src import cleaner, charts

st.set_page_config(page_title="Analytics — CCECC",
                   page_icon="📈", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()

ctx    = render_sidebar()
p      = __import__("src.shared", fromlist=["_p"])._p()
ct     = get_chart_theme()

with st.spinner("Loading analytics…"):
    all_months_data     = load_all_months()
    efficiency_df       = cleaner.compute_monthly_efficiency(all_months_data)
    cumulative_timeline = build_cumulative_timeline(all_months_data)

months_count    = len(all_months_data)
total_installed = sum(d["pipe_rm"] for d in all_months_data.values())
remaining_rm    = max(CONTRACT_TOTAL_RM - total_installed, 0)
avg_rate        = total_installed / months_count if months_count else 0
months_left     = round(remaining_rm / avg_rate, 1) if avg_rate else 0
pct_done        = round(total_installed / CONTRACT_TOTAL_RM * 100, 2)
months          = list(all_months_data.keys())

try:
    from dateutil.relativedelta import relativedelta
    proj_finish = pd.Timestamp.now() + relativedelta(
        months=int(months_left), days=int((months_left % 1)*30))
except ImportError:
    proj_finish = pd.NaT

months_to_end = (CONTRACT_END_PLANNED - pd.Timestamp.now()).days / 30
on_track      = months_left <= months_to_end

# ── Header ────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:1rem;animation:fade-in .5s ease both;">
    <p style="font-size:1.5rem;font-weight:800;color:{p['cyan']};margin:0;">📈 Analytics & Forecasting</p>
    <p style="font-size:.85rem;color:{p['text_s']};margin:.1rem 0;">
        Cross-month analysis &nbsp;|&nbsp; Trajectory &nbsp;|&nbsp; Efficiency &nbsp;|&nbsp; Resources
    </p>
</div>
""", unsafe_allow_html=True)

# ── Forecast KPIs ─────────────────────────────────────────────
section_title("Project Forecast Summary")
p1,p2,p3,p4,p5,p6 = st.columns(6)
kpi_card(p1,"Total Installed",  f"{total_installed:,.1f} rm",f"Across {months_count} months",
         cls="kpi-value-green",card_cls="kpi-card-green")
kpi_card(p2,"Remaining",        f"{remaining_rm:,.0f} rm",  f"{pct_done:.2f}% complete",
         cls="kpi-value-green",card_cls="kpi-card-green")
kpi_card(p3,"Avg Monthly Rate", f"{avg_rate:,.0f} rm/mo",   "Current pace",
         cls="kpi-value-amber",card_cls="kpi-card-amber")
kpi_card(p4,"Months Remaining", f"{months_left:.1f} mo",    "At current pace",
         cls="kpi-value-amber",card_cls="kpi-card-amber")
kpi_card(p5,"Projected Finish",
         proj_finish.strftime("%b %Y") if pd.notna(proj_finish) else "N/A",
         f"Planned: {CONTRACT_END_PLANNED.strftime('%b %Y')}",
         cls="kpi-value-amber",card_cls="kpi-card-amber")
kpi_card(p6,"On Track",
         "✅ YES" if on_track else "⚠️ DELAYED",
         f"Need {months_to_end:.0f} mo · Have {months_left:.1f} mo",
         cls="kpi-value-green" if on_track else "kpi-value-warn",
         card_cls="kpi-card-green" if on_track else "kpi-card")

st.markdown("<br>", unsafe_allow_html=True)
section_title("Select Analysis")

SUBNAV = [
    ("📈","Contract Progress",  "Trajectory · Planned vs Actual vs Projected"),
    ("⚡","Efficiency Analysis","rm/person/day · Trend · Change"),
    ("📅","Monthly Comparison", "Output · Manpower · Excavation by month"),
    ("🧮","Resource Calculator","Target rm → Days & Manpower required"),
]
selected = subnav_buttons(SUBNAV, "analytics_subnav")
st.markdown("<br>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# CONTRACT PROGRESS
# ──────────────────────────────────────────────────────────────
if selected == "Contract Progress":
    section_title("Contract Trajectory — Actual vs Planned vs Projected")

    actual_dates = [d["date"]          for d in cumulative_timeline]
    actual_vals  = [d["cumulative_rm"] for d in cumulative_timeline]

    fig_traj = go.Figure()
    # Planned
    fig_traj.add_trace(go.Scatter(
        x=[CONTRACT_START, CONTRACT_END_PLANNED],
        y=[0, CONTRACT_TOTAL_RM],
        name="Planned", mode="lines",
        line=dict(color=ct["gridcolor"], width=2, dash="dot")))
    # Projected
    if pd.notna(proj_finish) and avg_rate > 0 and actual_dates:
        proj_d, proj_v = [actual_dates[-1]], [actual_vals[-1]]
        cur, cv = proj_d[0], proj_v[0]
        while cur < proj_finish and cv < CONTRACT_TOTAL_RM:
            cur = cur + pd.DateOffset(months=1)
            cv  = min(cv + avg_rate, CONTRACT_TOTAL_RM)
            proj_d.append(cur); proj_v.append(cv)
        if len(proj_d) > 1:
            fig_traj.add_trace(go.Scatter(
                x=proj_d, y=proj_v,
                name=f"Projected (@{avg_rate:,.0f} rm/mo)", mode="lines",
                line=dict(color=p["amber"], width=2, dash="dash")))
    # Actual
    if actual_dates:
        fig_traj.add_trace(go.Scatter(
            x=actual_dates, y=actual_vals,
            name="Actual Cumulative", mode="lines+markers+text",
            line=dict(color=p["cyan"], width=3),
            marker=dict(size=10, color=p["cyan"], line=dict(width=2, color="#fff")),
            text=[f"{v:,.0f} rm" for v in actual_vals],
            textposition="top center", textfont=dict(size=11),
            fill="tozeroy", fillcolor=f"rgba(0,229,255,0.07)"))

    fig_traj.add_hline(y=CONTRACT_TOTAL_RM, line_dash="dot",
                       line_color=p["lime"], line_width=1.5,
                       annotation_text=f"Contract: {CONTRACT_TOTAL_RM:,.0f} rm",
                       annotation_position="right",
                       annotation_font=dict(color=p["lime"], size=11))
    if pd.notna(proj_finish):
        fig_traj.add_vline(x=proj_finish.timestamp()*1000,
                           line_dash="dash", line_color=p["amber"], line_width=1,
                           annotation_text=f"Est. Finish: {proj_finish.strftime('%b %Y')}",
                           annotation_position="top right",
                           annotation_font=dict(color=p["amber"], size=10))

    # ── FIX: pass legend separately, NOT inside base_layout ──
    fig_traj.update_layout(
        title_text="Contract Progress Trajectory",
        title_font=dict(size=14, color=ct["font_color"]),
        legend=_LEGEND,
        yaxis=dict(title="Cumulative Pipe (rm)", title_font=dict(size=11),
                   tickformat=",", gridcolor=ct["gridcolor"],
                   color=ct["font_color"]),
        xaxis=dict(title="", tickformat="%b %Y", gridcolor=ct["gridcolor"],
                   color=ct["font_color"]),
        **base_layout(height=440),
    )
    apply_axes(fig_traj, ct)
    st.plotly_chart(fig_traj, use_container_width=True)

    # Progress stacked bar — FIX: no legend kwarg duplication
    section_title("Cumulative Progress Bar")
    total_done = total_installed
    rem_bar    = max(CONTRACT_TOTAL_RM - total_done, 0)

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="Completed", x=[total_done], y=["Progress"],
        orientation="h", marker_color=p["cyan"], opacity=.9,
        text=f"{total_done:,.1f} rm  ({pct_done:.2f}%)",
        textposition="inside", textfont=dict(size=12, color="#000")))
    fig_bar.add_trace(go.Bar(
        name="Remaining", x=[rem_bar], y=["Progress"],
        orientation="h", marker_color="rgba(127,127,127,0.25)",
        text=f"{rem_bar:,.0f} rm remaining",
        textposition="inside", textfont=dict(size=11)))
    fig_bar.add_vline(x=CONTRACT_TOTAL_RM, line_dash="dot",
                      line_color=p["amber"], line_width=2,
                      annotation_text=f"Total: {CONTRACT_TOTAL_RM:,.0f} rm",
                      annotation_font=dict(color=p["amber"], size=11),
                      annotation_position="top right")
    # ── FIX: pass legend + barmode separately, use base_layout for the rest ──
    fig_bar.update_layout(
        barmode="stack",
        legend=dict(orientation="h", yanchor="bottom", y=1.1,
                    xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=11)),
        yaxis=dict(showticklabels=False),
        xaxis=dict(title="Running Metres (rm)", tickformat=",",
                   color=ct["font_color"], gridcolor=ct["gridcolor"]),
        **base_layout(height=130),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    section_title("Cumulative Data")
    with st.expander("View Trajectory Data", expanded=False):
        tdf = pd.DataFrame(cumulative_timeline)
        tdf["remaining_rm"]   = CONTRACT_TOTAL_RM - tdf["cumulative_rm"]
        tdf["completion_pct"] = (tdf["cumulative_rm"]/CONTRACT_TOTAL_RM*100).round(2)
        st.dataframe(tdf, use_container_width=True, hide_index=True)

# ──────────────────────────────────────────────────────────────
# EFFICIENCY ANALYSIS
# ──────────────────────────────────────────────────────────────
elif selected == "Efficiency Analysis":
    section_title("Efficiency: rm Installed per Person per Day")

    if not efficiency_df.empty:
        disp = efficiency_df[["Month","Pipe_rm","Active_Days","Avg_Manpower",
                               "RM_per_Person_Day","Efficiency_Change_Pct","Efficiency_Trend"]].copy()
        disp.columns = ["Month","Pipe (rm)","Active Days","Avg Manpower",
                         "rm/Person/Day","Efficiency Δ%","Trend"]
        disp["Pipe (rm)"]     = disp["Pipe (rm)"].round(1)
        disp["rm/Person/Day"] = disp["rm/Person/Day"].round(4)
        disp["Efficiency Δ%"] = disp["Efficiency Δ%"].round(1)
        st.dataframe(disp, use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)

    if not efficiency_df.empty:
        eff_clrs = []
        for _,row in efficiency_df.iterrows():
            t = row.get("Efficiency_Trend","—")
            eff_clrs.append(p["lime"] if t=="Improved" else p["red"] if t=="Declined" else p["amber"])

        fig_eff = make_subplots(rows=2, cols=2,
            subplot_titles=("Monthly Output & Avg Manpower",
                            "Efficiency: rm / Person / Day",
                            "Month-over-Month Change (%)",
                            "Pipe Installed by Month"),
            vertical_spacing=.16, horizontal_spacing=.10)

        mo = efficiency_df["Month"].tolist()
        CLRS4 = [p["cyan"],p["coral"],p["lime"],"#C77DFF",p["amber"]]
        bar_c = [CLRS4[i%len(CLRS4)] for i in range(len(efficiency_df))]

        # Panel 1
        fig_eff.add_trace(go.Bar(x=mo, y=efficiency_df["Pipe_rm"],
            name="Pipe (rm)", marker_color=bar_c, opacity=.82,
            text=efficiency_df["Pipe_rm"].round(0).astype(int).astype(str),
            textposition="outside", textfont=dict(size=9)), row=1, col=1)
        fig_eff.add_trace(go.Scatter(x=mo, y=efficiency_df["Avg_Manpower"],
            name="Avg Manpower", mode="lines+markers",
            line=dict(color=p["amber"],width=2),
            marker=dict(size=7,symbol="diamond")), row=1, col=1)
        fig_eff.update_yaxes(title_text="Pipe (rm)",title_font=dict(size=10),row=1,col=1)

        # Panel 2
        fig_eff.add_trace(go.Bar(x=mo, y=efficiency_df["RM_per_Person_Day"],
            name="rm/Person/Day", marker_color=eff_clrs, opacity=.85,
            text=efficiency_df["RM_per_Person_Day"].round(3).astype(str),
            textposition="outside",textfont=dict(size=9),showlegend=False), row=1, col=2)
        for _,row in efficiency_df.iterrows():
            chg = row.get("Efficiency_Change_Pct",0)
            if pd.notna(chg) and chg!=0:
                sign = "+" if chg>0 else ""
                fig_eff.add_annotation(x=row["Month"],y=row["RM_per_Person_Day"]*1.08,
                    text=f"{sign}{chg:.1f}%",showarrow=False,
                    font=dict(size=9,color=p["lime"] if chg>0 else p["red"]),row=1,col=2)
        fig_eff.update_yaxes(title_text="rm/Person/Day",title_font=dict(size=10),row=1,col=2)

        # Panel 3
        for col_k, dlbl, dcl in [("Pipe_Change_Pct","Pipe",p["cyan"]),
                                   ("Manpower_Change_Pct","Manpower",p["amber"]),
                                   ("Efficiency_Change_Pct","Efficiency",p["lime"])]:
            if col_k in efficiency_df.columns:
                fig_eff.add_trace(go.Bar(x=mo, y=efficiency_df[col_k].fillna(0),
                    name=dlbl, marker_color=dcl, opacity=.75), row=2, col=1)
        fig_eff.add_hline(y=0, line_color="rgba(127,127,127,0.25)", line_width=1, row=2, col=1)
        fig_eff.update_yaxes(title_text="Change (%)",title_font=dict(size=10),row=2,col=1)

        # Panel 4
        df_s = efficiency_df.sort_values("Pipe_rm", ascending=True)
        fig_eff.add_trace(go.Bar(y=df_s["Month"], x=df_s["Pipe_rm"],
            orientation="h", name="Pipe rm",
            marker_color=[p["cyan"] if i==len(df_s)-1 else "#C77DFF"
                          for i in range(len(df_s))],
            opacity=.85, text=df_s["Pipe_rm"].round(0).astype(int).astype(str),
            textposition="outside",textfont=dict(size=10),showlegend=False), row=2, col=2)
        fig_eff.update_xaxes(title_text="Pipe (rm)",title_font=dict(size=10),row=2,col=2)

        fig_eff.update_layout(
            barmode="group",
            legend=_LEGEND,
            **base_layout(height=640),
        )
        for ax in fig_eff.layout:
            if ax.startswith("xaxis") or ax.startswith("yaxis"):
                fig_eff.layout[ax].gridcolor     = ct["gridcolor"]
                fig_eff.layout[ax].zerolinecolor = ct["zerolinecolor"]
                if hasattr(fig_eff.layout[ax], "tickfont"):
                    fig_eff.layout[ax].tickfont = dict(size=10, color=ct["font_color"])
        fig_eff.update_annotations(font=dict(size=12, color=ct["font_color"]))
        st.plotly_chart(fig_eff, use_container_width=True)

    with st.expander("Full Efficiency Table", expanded=False):
        st.dataframe(efficiency_df, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", efficiency_df.to_csv(index=False).encode(),
                           "efficiency.csv","text/csv")

# ──────────────────────────────────────────────────────────────
# MONTHLY COMPARISON
# ──────────────────────────────────────────────────────────────
elif selected == "Monthly Comparison":
    section_title("Month-over-Month Comparison")

    if months:
        rows = []
        for i, lbl in enumerate(months):
            d    = all_months_data[lbl]
            prev = all_months_data[months[i-1]] if i>0 else None
            def _chg(c, pv): return round((c-pv)/pv*100,1) if pv and pv>0 else None
            rows.append({"Month":lbl,
                "Pipe (rm)":round(d["pipe_rm"],1),
                "Pipe Δ%":_chg(d["pipe_rm"], prev["pipe_rm"] if prev else None),
                "Avg Manpower":round(d["avg_manpower"],1),
                "Manpower Δ%":_chg(d["avg_manpower"], prev["avg_manpower"] if prev else None),
                "Excav (rm)":round(d["excav_rm"],1),
                "Excav Δ%":_chg(d["excav_rm"], prev["excav_rm"] if prev else None),
                "Active Days":d["active_days"],
                "Service Pits":int(d.get("pits",0)),
            })
        comp_df = pd.DataFrame(rows)
        st.dataframe(comp_df, use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # 3-panel comparison bars
        CLRS3 = [p["cyan"],p["coral"],p["lime"]]
        mets  = [("pipe_rm","Pipe (rm)"),("avg_manpower","Avg Manpower"),("excav_rm","Excav (rm)")]
        fig_c = make_subplots(rows=1, cols=3,
                              subplot_titles=[m[1] for m in mets],
                              horizontal_spacing=.10)
        for ci, (key, mlbl) in enumerate(mets, start=1):
            vals = [all_months_data[m][key] for m in months]
            fig_c.add_trace(go.Bar(x=months, y=vals, name=mlbl,
                marker_color=CLRS3[ci-1], opacity=.85,
                text=[f"{v:,.1f}" for v in vals],
                textposition="outside",textfont=dict(size=10),
                showlegend=False), row=1, col=ci)

        fig_c.update_layout(legend=_LEGEND, **base_layout(height=340))
        for ax in fig_c.layout:
            if ax.startswith("xaxis") or ax.startswith("yaxis"):
                fig_c.layout[ax].gridcolor     = ct["gridcolor"]
                fig_c.layout[ax].zerolinecolor = ct["zerolinecolor"]
                fig_c.layout[ax].tickfont      = dict(size=10, color=ct["font_color"])
        fig_c.update_annotations(font=dict(size=12, color=ct["font_color"]))
        st.plotly_chart(fig_c, use_container_width=True)

        # Δ% bars
        if len(months) > 1:
            section_title("Month-over-Month Change (%)")
            fig_d = go.Figure()
            for col_k, dlbl, dcl in [("Pipe Δ%","Pipe",p["cyan"]),
                                      ("Manpower Δ%","Manpower",p["amber"]),
                                      ("Excav Δ%","Excavation",p["coral"])]:
                if col_k in comp_df.columns:
                    fig_d.add_trace(go.Bar(x=comp_df["Month"],
                        y=comp_df[col_k].fillna(0),
                        name=dlbl, marker_color=dcl, opacity=.78))
            fig_d.add_hline(y=0, line_color="rgba(127,127,127,0.3)", line_width=1)
            fig_d.update_layout(barmode="group",legend=_LEGEND,**base_layout(height=300))
            fig_d.update_yaxes(title_text="Change (%)",title_font=dict(size=10))
            apply_axes(fig_d,ct)
            st.plotly_chart(fig_d, use_container_width=True)

        with st.expander("Full Comparison Table", expanded=False):
            st.dataframe(comp_df, use_container_width=True, hide_index=True)
            st.download_button("Download CSV", comp_df.to_csv(index=False).encode(),
                               "monthly_comparison.csv","text/csv")
    else:
        st.info("No monthly data available.")

# ──────────────────────────────────────────────────────────────
# RESOURCE CALCULATOR
# ──────────────────────────────────────────────────────────────
elif selected == "Resource Calculator":
    section_title("Resource Requirements Calculator")
    st.markdown(f"""
    <p style="color:{p['text_s']};font-size:.85rem;margin-bottom:1rem;">
        Enter a target installation quantity and available manpower to estimate
        how long the work will take — based on your current productivity rate.
    </p>
    """, unsafe_allow_html=True)

    avg_eff = float(efficiency_df["RM_per_Person_Day"].dropna().mean()) \
              if not efficiency_df.empty else 0
    last_mp = float(efficiency_df["Avg_Manpower"].iloc[-1]) \
              if not efficiency_df.empty else 0

    inp_col, res_col = st.columns([1,2], gap="large")
    with inp_col:
        st.markdown("**Inputs**")
        target_rm      = st.number_input("Target Pipe (rm)",
            min_value=1.0, max_value=float(CONTRACT_TOTAL_RM),
            value=min(1000.0, remaining_rm), step=100.0)
        mp_input       = st.number_input("Daily Manpower (persons)",
            min_value=1, max_value=500, value=max(int(last_mp),10), step=5)
        working_days_pm = st.slider("Working Days/Month", 15, 31, 22)
        st.markdown("---")
        st.markdown(f"""
        <div style="font-size:.78rem;color:{p['text_s']};line-height:1.8;">
            <b>Current Productivity</b><br>
            {avg_eff:.4f} rm / person / day<br>
            Based on {months_count} months of data
        </div>""", unsafe_allow_html=True)

    with res_col:
        if avg_eff > 0 and mp_input > 0:
            days_needed   = target_rm / (avg_eff * mp_input)
            months_needed = days_needed / working_days_pm
            daily_out     = avg_eff * mp_input
            mp_1mo        = target_rm / (avg_eff * working_days_pm)

            r1,r2,r3,r4 = st.columns(4)
            kpi_card(r1,"Days Required",   f"{days_needed:.0f} days",f"@ {mp_input} persons/day",
                     cls="kpi-value-amber",card_cls="kpi-card-amber")
            kpi_card(r2,"Months Required", f"{months_needed:.1f} mo",f"{working_days_pm} days/mo",
                     cls="kpi-value-amber",card_cls="kpi-card-amber")
            kpi_card(r3,"Daily Output",    f"{daily_out:.1f} rm/day",f"{avg_eff:.4f} rm/person/day",
                     cls="kpi-value-amber",card_cls="kpi-card-amber")
            kpi_card(r4,"MP for 1 Month",  f"{mp_1mo:.0f} persons",f"to do {target_rm:,.0f} rm",
                     cls="kpi-value-amber",card_cls="kpi-card-amber")

            st.markdown("<br>", unsafe_allow_html=True)

            # Sensitivity chart
            mp_r   = list(range(5, 301, 5))
            days_r = [target_rm/(avg_eff*m) if avg_eff>0 else 0 for m in mp_r]
            mo_r   = [d/working_days_pm for d in days_r]

            fig_s = make_subplots(specs=[[{"secondary_y":True}]])
            fig_s.add_trace(go.Scatter(x=mp_r, y=days_r, name="Days Required",
                mode="lines", line=dict(color=p["cyan"],width=2.5),
                fill="tozeroy",fillcolor="rgba(0,229,255,0.07)"), secondary_y=False)
            fig_s.add_trace(go.Scatter(x=mp_r, y=mo_r, name="Months Required",
                mode="lines", line=dict(color=p["amber"],width=2,dash="dash")),
                secondary_y=True)
            fig_s.add_trace(go.Scatter(x=[mp_input], y=[days_needed],
                name="Your Selection", mode="markers",
                marker=dict(size=14,color=p["lime"],symbol="star",
                            line=dict(width=2,color="#fff"))), secondary_y=False)
            fig_s.update_layout(
                title_text=f"Days vs Manpower for {target_rm:,.0f} rm",
                title_font=dict(size=13, color=ct["font_color"]),
                legend=_LEGEND,
                **base_layout(height=340),
            )
            fig_s.update_yaxes(title_text="Days Required",secondary_y=False,
                gridcolor=ct["gridcolor"],title_font=dict(size=10))
            fig_s.update_yaxes(title_text="Months Required",secondary_y=True,
                showgrid=False,title_font=dict(size=10))
            fig_s.update_xaxes(title_text="Daily Manpower",gridcolor=ct["gridcolor"])
            apply_axes(fig_s, ct)
            st.plotly_chart(fig_s, use_container_width=True)

            # What-if table
            section_title("What-If Scenarios")
            scen = [{"Daily Manpower":m,
                     "Days Required":round(target_rm/(avg_eff*m),0),
                     "Months Required":round(target_rm/(avg_eff*m)/working_days_pm,1),
                     "Daily Output (rm)":round(avg_eff*m,1)}
                    for m in [20,30,40,50,75,100,150,200]]
            st.dataframe(pd.DataFrame(scen), use_container_width=True, hide_index=True)
        else:
            st.warning("Not enough productivity data yet.")

st.markdown(f"""
<hr style='border-color:{p['sec_border']}'/>
<p style='text-align:center;color:{p['text_m']};font-size:.65rem;'>
    CCECC-HONESS-SMEDI JV &nbsp;|&nbsp; WD5B &nbsp;|&nbsp; Analytics & Forecasting
</p>
""", unsafe_allow_html=True)