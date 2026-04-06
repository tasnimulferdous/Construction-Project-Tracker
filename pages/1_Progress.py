# pages/1_Progress.py — Project Progress
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.shared import (
    inject_css, render_sidebar, load_summary,
    kpi_card, section_title, subnav_buttons,
    CONTRACT_TOTAL_RM, get_chart_theme,
)
from src import cleaner, charts

st.set_page_config(
    page_title="Project Progress — CCECC",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

ctx          = render_sidebar()
summary_tab  = ctx["summary_tab"]
filter_start = ctx["filter_start"]
filter_end   = ctx["filter_end"]
label        = ctx["selected_month_label"]
day_range    = ctx["day_range"]

summary_df, vehicle_df = load_summary(summary_tab)
kpis = cleaner.compute_kpis(summary_df, filter_start, filter_end)

pipe_rm     = kpis.get("total_pipe_installed_rm", 0.0)
excav_rm    = kpis.get("total_excavation_rm",     0.0)
pits        = kpis.get("total_service_pits",       0.0)
active_days = kpis.get("active_days",              0)
pct_target  = kpis.get("pct_of_monthly_target",   0.0)
monthly_tgt = kpis.get("monthly_target_rm",        0.0)
upto_feb    = kpis.get("total_pipe_upto_feb",      0.0)

meta         = summary_df.drop_duplicates(subset=["Activity","SD","Pipe_Dia"]) if not summary_df.empty else pd.DataFrame()
road_meta    = meta[meta["Activity"].str.contains("Road",    case=False, na=False)] if not meta.empty else pd.DataFrame()
pit_meta     = meta[meta["Activity"].str.contains("Service", case=False, na=False)] if not meta.empty else pd.DataFrame()
road_target  = float(road_meta["Qty_Mar"].sum()) if not road_meta.empty else 0
pit_target   = float(pit_meta["Qty_Mar"].sum())  if not pit_meta.empty  else 0

# ── Page header ───────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:1rem; animation: fade-in 0.5s ease both;">
    <p style="font-size:1.5rem; font-weight:800; color:var(--accent-cyan); margin:0;">
        📊 Project Progress
    </p>
    <p style="font-size:0.85rem; color:var(--text-secondary); margin:0.1rem 0;">
        {label} &nbsp;|&nbsp; Day {day_range[0]}–{day_range[1]} &nbsp;|&nbsp;
        {filter_start.strftime('%d %b')} to {filter_end.strftime('%d %b %Y')}
    </p>
</div>
""", unsafe_allow_html=True)

# ── Monthly KPIs ──────────────────────────────────────────────
section_title("Monthly Performance Indicators")
pct_cls = ("kpi-value-green" if pct_target >= 90
           else "kpi-value-amber" if pct_target >= 60
           else "kpi-value-warn")
pct_card = ("kpi-card-green" if pct_target >= 90
            else "kpi-card-amber" if pct_target >= 60
            else "kpi-card")

k1,k2,k3,k4,k5,k6 = st.columns(6)
kpi_card(k1,"Pipe Installed",   f"{pipe_rm:,.1f} rm",  f"Target: {monthly_tgt:,.0f} rm")
kpi_card(k2,"vs Monthly Target",f"{pct_target:.1f}%",  f"Upto Feb: {upto_feb:,.0f} rm", cls=pct_cls, card_cls=pct_card)
kpi_card(k3,"Excavation",       f"{excav_rm:,.1f} rm", "Road cutting + trench")
kpi_card(k4,"Service Pits",     f"{int(pits)} Pcs",    "All SD zones")
kpi_card(k5,"Active Days",      str(active_days),       f"of {day_range[1]-day_range[0]+1} selected")
kpi_card(k6,"Monthly Target",   f"{monthly_tgt:,.0f} rm","Pipe installation")

st.markdown("<br>", unsafe_allow_html=True)

# ── Sub-navigation ────────────────────────────────────────────
section_title("Select Activity")

SUBNAV = [
    ("📏", "Pipe Installation",   "Target vs actual · SD zones · Cumulative"),
    ("🚧", "Road Cutting",        "Excavation progress · Daily quantities"),
    ("⚙️", "Work Activity",       "All activities vs monthly targets"),
]
selected = subnav_buttons(SUBNAV, "progress_subnav")

st.markdown("<br>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# Chart theme
# ──────────────────────────────────────────────────────────────

ct = get_chart_theme()

def _base_layout(**extra) -> dict:
    return dict(
        paper_bgcolor = ct["paper_bgcolor"],
        plot_bgcolor  = ct["plot_bgcolor"],
        font_color    = ct["font_color"],
        font_family   = "Segoe UI, Arial, sans-serif",
        hovermode     = "x unified",
        margin        = dict(l=16, r=16, t=50, b=16),
        legend        = dict(bgcolor="rgba(0,0,0,0)",
                             bordercolor="rgba(127,127,127,0.2)", borderwidth=1,
                             font=dict(size=11)),
        **extra,
    )

def _update_axes(fig):
    fig.update_xaxes(gridcolor=ct["gridcolor"], zerolinecolor=ct["zerolinecolor"],
                     showline=False, tickfont=dict(size=10))
    fig.update_yaxes(gridcolor=ct["gridcolor"], zerolinecolor=ct["zerolinecolor"],
                     showline=False, tickfont=dict(size=10))
    return fig

def _line_chart(activity_kw, monthly_target, title, color, unit_label="rm") -> go.Figure:
    mask = (
        summary_df["Activity"].str.contains(activity_kw, case=False, na=False)
        & (summary_df["Date"] >= filter_start)
        & (summary_df["Date"] <= filter_end)
    )
    sub = summary_df.loc[mask].copy()
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if not sub.empty:
        daily = sub.groupby("Date")["Daily_Qty"].sum().reset_index().sort_values("Date")
        daily["Cumulative"] = daily["Daily_Qty"].cumsum()

        if monthly_target > 0:
            pd_dates   = pd.date_range(filter_start, filter_end, freq="D")
            rate       = monthly_target / 31
            planned    = [(i+1)*rate for i in range(len(pd_dates))]
            fig.add_trace(go.Scatter(
                x=pd_dates, y=planned, name="Planned (linear)",
                mode="lines", line=dict(color=ct["gridcolor"], width=2, dash="dot"),
            ), secondary_y=False)

        fig.add_trace(go.Scatter(
            x=daily["Date"], y=daily["Cumulative"],
            name=f"Actual Cumulative ({unit_label})",
            mode="lines+markers",
            line=dict(color=color, width=3),
            marker=dict(size=7, color=color, line=dict(width=2, color="#fff")),
            fill="tozeroy",
            fillcolor=color.replace(")", ",0.08)").replace("rgb", "rgba") if "rgb" in color
                      else f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
        ), secondary_y=False)

        fig.add_trace(go.Bar(
            x=daily["Date"], y=daily["Daily_Qty"],
            name=f"Daily ({unit_label})",
            marker_color=color, opacity=0.30,
        ), secondary_y=True)

    fig.update_layout(title_text=title, title_font=dict(size=14, color=ct["font_color"]),
                      **_base_layout(), height=370)
    fig.update_yaxes(title_text=f"Cumulative ({unit_label})", secondary_y=False,
                     title_font=dict(size=10), gridcolor=ct["gridcolor"])
    fig.update_yaxes(title_text=f"Daily ({unit_label})",      secondary_y=True,
                     title_font=dict(size=10), showgrid=False)
    _update_axes(fig)
    return fig

# ──────────────────────────────────────────────────────────────
# PIPE INSTALLATION
# ──────────────────────────────────────────────────────────────

if selected == "Pipe Installation":
    section_title("Pipe Installation — Planned vs Actual")

    fig_pipe = _line_chart("Pipe", monthly_tgt,
                           "Pipe Installation — Cumulative Actual vs Planned",
                           "#00E5FF")
    st.plotly_chart(fig_pipe, use_container_width=True)

    # SD zone breakdown
    st.markdown("<br>", unsafe_allow_html=True)
    section_title("Daily Installation by SD Zone")

    mask_pipe = (
        summary_df["Activity"].str.contains("Pipe", case=False, na=False)
        & (summary_df["Date"] >= filter_start)
        & (summary_df["Date"] <= filter_end)
    )
    pipe_df = summary_df.loc[mask_pipe].copy()

    if not pipe_df.empty:
        pivot = (pipe_df.groupby(["Date","SD"])["Daily_Qty"]
                 .sum().unstack(fill_value=0).reset_index().sort_values("Date"))
        sd_cols = [c for c in pivot.columns if c != "Date"]
        pivot["Total"] = pivot[sd_cols].sum(axis=1)

        fig_sd = make_subplots(specs=[[{"secondary_y": True}]])
        colors = ["#00E5FF","#FF6B35","#A8FF3E","#C77DFF"]
        for i, sd in enumerate(sd_cols):
            fig_sd.add_trace(go.Bar(x=pivot["Date"], y=pivot[sd], name=f"SD-{sd}",
                                    marker_color=colors[i%len(colors)], opacity=0.82),
                             secondary_y=False)
        pivot["Cumulative"] = pivot["Total"].cumsum()
        fig_sd.add_trace(go.Scatter(x=pivot["Date"], y=pivot["Cumulative"],
                                    name="Cumulative", mode="lines+markers",
                                    line=dict(color="#FFD166", width=2.5),
                                    marker=dict(size=5)),
                         secondary_y=True)
        fig_sd.update_layout(barmode="stack", title_text="Daily Pipe by SD Zone",
                             title_font=dict(size=13, color=ct["font_color"]),
                             **_base_layout(), height=320)
        fig_sd.update_yaxes(title_text="Daily (rm)", secondary_y=False,
                            gridcolor=ct["gridcolor"])
        fig_sd.update_yaxes(title_text="Cumulative (rm)", secondary_y=True, showgrid=False)
        _update_axes(fig_sd)
        st.plotly_chart(fig_sd, use_container_width=True)

    section_title("Pipe Installation Data")
    with st.expander("View Data Table", expanded=True):
        if pipe_df.empty:
            st.info("No pipe installation data for selected period.")
        else:
            show_df = (pipe_df.groupby(["Date","SD","Pipe_Dia"])["Daily_Qty"]
                       .sum().reset_index().sort_values(["Date","SD","Pipe_Dia"]))
            show_df.columns = ["Date","SD Zone","Pipe Diameter","Daily Qty (rm)"]
            show_df["Daily Qty (rm)"] = show_df["Daily Qty (rm)"].round(2)
            st.dataframe(show_df, use_container_width=True, hide_index=True)
            csv = show_df.to_csv(index=False).encode()
            st.download_button("Download CSV", csv, "pipe_installation.csv", "text/csv")

# ──────────────────────────────────────────────────────────────
# ROAD CUTTING
# ──────────────────────────────────────────────────────────────

elif selected == "Road Cutting":
    section_title("Road Cutting + Trench Excavation — Planned vs Actual")

    fig_road = _line_chart("Road Cutting", road_target,
                           "Road Cutting + Trench Excavation — Cumulative",
                           "#FF6B35")
    st.plotly_chart(fig_road, use_container_width=True)

    section_title("Daily Excavation by SD Zone")

    mask_road = (
        summary_df["Activity"].str.contains("Road Cutting", case=False, na=False)
        & (summary_df["Date"] >= filter_start)
        & (summary_df["Date"] <= filter_end)
    )
    road_df = summary_df.loc[mask_road].copy()

    if not road_df.empty:
        pivot_r = (road_df.groupby(["Date","SD"])["Daily_Qty"]
                   .sum().unstack(fill_value=0).reset_index().sort_values("Date"))
        sd_cols_r = [c for c in pivot_r.columns if c != "Date"]
        pivot_r["Total"] = pivot_r[sd_cols_r].sum(axis=1)

        fig_rd = go.Figure()
        colors = ["#FF6B35","#FFD166","#C77DFF"]
        for i, sd in enumerate(sd_cols_r):
            fig_rd.add_trace(go.Bar(x=pivot_r["Date"], y=pivot_r[sd], name=f"SD-{sd}",
                                    marker_color=colors[i%len(colors)], opacity=0.82))
        fig_rd.add_trace(go.Scatter(x=pivot_r["Date"], y=pivot_r["Total"],
                                    name="Daily Total", mode="lines+markers+text",
                                    line=dict(color="#FF6B35", width=2),
                                    marker=dict(size=6),
                                    text=pivot_r["Total"].round(1).astype(str),
                                    textposition="top center",
                                    textfont=dict(size=9)))
        fig_rd.update_layout(barmode="stack", title_text="Daily Excavation by SD Zone",
                             title_font=dict(size=13, color=ct["font_color"]),
                             **_base_layout(), height=320)
        _update_axes(fig_rd)
        st.plotly_chart(fig_rd, use_container_width=True)

    section_title("Excavation Data")
    with st.expander("View Data Table", expanded=True):
        if road_df.empty:
            st.info("No excavation data for selected period.")
        else:
            show_r = (road_df.groupby(["Date","SD"])["Daily_Qty"]
                      .sum().reset_index().sort_values(["Date","SD"]))
            show_r.columns = ["Date","SD Zone","Daily Qty (rm)"]
            show_r["Daily Qty (rm)"] = show_r["Daily Qty (rm)"].round(2)
            st.dataframe(show_r, use_container_width=True, hide_index=True)
            csv = show_r.to_csv(index=False).encode()
            st.download_button("Download CSV", csv, "excavation.csv", "text/csv")

# ──────────────────────────────────────────────────────────────
# WORK ACTIVITY
# ──────────────────────────────────────────────────────────────

elif selected == "Work Activity":
    section_title("All Work Activities — Period Totals vs Monthly Targets")

    fig_act = charts.activity_breakdown_chart(summary_df, filter_start, filter_end)
    # Apply current theme to chart
    fig_act.update_layout(**_base_layout())
    _update_axes(fig_act)
    st.plotly_chart(fig_act, use_container_width=True)

    # Service pit chart
    st.markdown("<br>", unsafe_allow_html=True)
    section_title("Service Pit Installation")

    mask_pit = (
        summary_df["Activity"].str.contains("Service Pit", case=False, na=False)
        & (summary_df["Date"] >= filter_start)
        & (summary_df["Date"] <= filter_end)
    )
    pit_df = summary_df.loc[mask_pit].copy()

    if not pit_df.empty:
        pit_daily = pit_df.groupby("Date")["Daily_Qty"].sum().reset_index().sort_values("Date")
        fig_pit = go.Figure()
        fig_pit.add_trace(go.Bar(x=pit_daily["Date"], y=pit_daily["Daily_Qty"],
                                 name="Service Pits (Pcs)",
                                 marker_color="#A8FF3E", opacity=0.85,
                                 text=pit_daily["Daily_Qty"].astype(int).astype(str),
                                 textposition="outside",
                                 textfont=dict(size=11)))
        fig_pit.update_layout(title_text="Service Pit Installation — Daily",
                              title_font=dict(size=13, color=ct["font_color"]),
                              **_base_layout(), height=280)
        fig_pit.update_yaxes(title_text="Pieces (Pcs)", gridcolor=ct["gridcolor"])
        _update_axes(fig_pit)
        st.plotly_chart(fig_pit, use_container_width=True)

    section_title("All Activity Data")
    with st.expander("View Data Table", expanded=True):
        if summary_df.empty:
            st.info("No data loaded.")
        else:
            filtered = summary_df[
                (summary_df["Date"] >= filter_start)
                & (summary_df["Date"] <= filter_end)
            ].sort_values(["Activity","SD","Date"]).reset_index(drop=True)
            tab1, tab2, tab3 = st.tabs(["Pipe","Road Cutting","Service Pit"])
            for tab, kw in zip([tab1,tab2,tab3],["Pipe","Road Cutting","Service Pit"]):
                with tab:
                    sub = filtered[filtered["Activity"].str.contains(kw, case=False, na=False)]
                    st.dataframe(sub[["Date","Activity","SD","Pipe_Dia","Unit","Daily_Qty","Qty_Mar"]],
                                 use_container_width=True, hide_index=True)
                    if not sub.empty:
                        st.download_button(f"Download {kw} CSV",
                                           sub.to_csv(index=False).encode(),
                                           f"{kw.lower().replace(' ','_')}.csv", "text/csv",
                                           key=f"dl_{kw}")

st.markdown("""
<hr/>
<p style="text-align:center; color:var(--text-muted); font-size:0.65rem;">
    CCECC-HONESS-SMEDI JV &nbsp;|&nbsp; WD5B &nbsp;|&nbsp; Project Progress
</p>
""", unsafe_allow_html=True)