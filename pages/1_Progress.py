# pages/1_Progress.py
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
    base_layout, apply_axes, get_chart_theme, _LEGEND,
)
from src import cleaner, charts

st.set_page_config(page_title="Project Progress — CCECC",
                   page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()

ctx         = render_sidebar()
summary_tab = ctx["summary_tab"]
f_start     = ctx["filter_start"]
f_end       = ctx["filter_end"]
label       = ctx["selected_month_label"]
day_range   = ctx["day_range"]

summary_df, _ = load_summary(summary_tab)
kpis = cleaner.compute_kpis(summary_df, f_start, f_end)

pipe_rm     = kpis.get("total_pipe_installed_rm", 0.0)
excav_rm    = kpis.get("total_excavation_rm",     0.0)
pits        = kpis.get("total_service_pits",       0.0)
active_days = kpis.get("active_days",              0)
pct_target  = kpis.get("pct_of_monthly_target",   0.0)
monthly_tgt = kpis.get("monthly_target_rm",        0.0)
upto_feb    = kpis.get("total_pipe_upto_feb",      0.0)

meta       = summary_df.drop_duplicates(subset=["Activity","SD","Pipe_Dia"]) \
             if not summary_df.empty else pd.DataFrame()
road_tgt   = float(meta[meta["Activity"].str.contains("Road",    case=False, na=False)]["Qty_Mar"].sum()) \
             if not meta.empty else 0
pit_tgt    = float(meta[meta["Activity"].str.contains("Service", case=False, na=False)]["Qty_Mar"].sum()) \
             if not meta.empty else 0

ct = get_chart_theme()

# ── Header ────────────────────────────────────────────────────
p = __import__("src.shared", fromlist=["_p"])._p()
st.markdown(f"""
<div style="margin-bottom:1rem;animation:fade-in .5s ease both;">
    <p style="font-size:1.5rem;font-weight:800;color:{p['cyan']};margin:0;">📊 Project Progress</p>
    <p style="font-size:.85rem;color:{p['text_s']};margin:.1rem 0;">
        {label} &nbsp;|&nbsp; Day {day_range[0]}–{day_range[1]} &nbsp;|&nbsp;
        {f_start.strftime('%d %b')} to {f_end.strftime('%d %b %Y')}
    </p>
</div>
""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────
section_title("Monthly Performance Indicators")
pc = ("kpi-value-green","kpi-card-green") if pct_target>=90 \
     else ("kpi-value-amber","kpi-card-amber") if pct_target>=60 \
     else ("kpi-value-warn","kpi-card")

k1,k2,k3,k4,k5,k6 = st.columns(6)
kpi_card(k1,"Pipe Installed",   f"{pipe_rm:,.1f} rm",f"Target: {monthly_tgt:,.0f} rm")
kpi_card(k2,"vs Monthly Target",f"{pct_target:.1f}%",f"Upto Feb: {upto_feb:,.0f} rm",cls=pc[0],card_cls=pc[1])
kpi_card(k3,"Excavation",       f"{excav_rm:,.1f} rm","Road cutting + trench")
kpi_card(k4,"Service Pits",     f"{int(pits)} Pcs","All SD zones")
kpi_card(k5,"Active Days",      str(active_days),f"of {day_range[1]-day_range[0]+1} selected")
kpi_card(k6,"Monthly Target",   f"{monthly_tgt:,.0f} rm","Pipe installation")

st.markdown("<br>", unsafe_allow_html=True)
section_title("Select Activity")

SUBNAV = [
    ("📏","Pipe Installation", "Target vs actual · SD zones · Cumulative"),
    ("🚧","Road Cutting",      "Excavation progress · Daily quantities"),
    ("⚙️","Work Activity",     "All activities vs monthly targets"),
]
selected = subnav_buttons(SUBNAV, "progress_subnav")
st.markdown("<br>", unsafe_allow_html=True)

# ── Chart builder ─────────────────────────────────────────────
def _line_chart(activity_kw, monthly_target, title, color, unit="rm"):
    mask = (summary_df["Activity"].str.contains(activity_kw, case=False, na=False)
            & (summary_df["Date"] >= f_start) & (summary_df["Date"] <= f_end))
    sub  = summary_df.loc[mask].copy()
    fig  = make_subplots(specs=[[{"secondary_y": True}]])

    if not sub.empty:
        daily = sub.groupby("Date")["Daily_Qty"].sum().reset_index().sort_values("Date")
        daily["Cumulative"] = daily["Daily_Qty"].cumsum()

        if monthly_target > 0:
            pd_d   = pd.date_range(f_start, f_end, freq="D")
            rate   = monthly_target / 31
            fig.add_trace(go.Scatter(
                x=pd_d, y=[(i+1)*rate for i in range(len(pd_d))],
                name="Planned", mode="lines",
                line=dict(color=ct["gridcolor"], width=2, dash="dot"),
            ), secondary_y=False)

        hex_c = color.lstrip("#")
        r,g,b = int(hex_c[:2],16), int(hex_c[2:4],16), int(hex_c[4:],16)
        fig.add_trace(go.Scatter(
            x=daily["Date"], y=daily["Cumulative"],
            name=f"Actual Cumulative ({unit})", mode="lines+markers",
            line=dict(color=color, width=3),
            marker=dict(size=7, color=color, line=dict(width=2, color="#fff")),
            fill="tozeroy", fillcolor=f"rgba({r},{g},{b},0.08)",
        ), secondary_y=False)
        fig.add_trace(go.Bar(
            x=daily["Date"], y=daily["Daily_Qty"],
            name=f"Daily ({unit})", marker_color=color, opacity=0.28,
        ), secondary_y=True)

    fig.update_layout(title_text=title,
                      title_font=dict(size=14, color=ct["font_color"]),
                      legend=_LEGEND,
                      **base_layout(height=370))
    fig.update_yaxes(title_text=f"Cumulative ({unit})", secondary_y=False,
                     title_font=dict(size=10), gridcolor=ct["gridcolor"])
    fig.update_yaxes(title_text=f"Daily ({unit})", secondary_y=True,
                     title_font=dict(size=10), showgrid=False)
    apply_axes(fig, ct)
    return fig

# ── PIPE ─────────────────────────────────────────────────────
if selected == "Pipe Installation":
    section_title("Pipe Installation — Planned vs Actual")
    st.plotly_chart(_line_chart("Pipe", monthly_tgt,
        "Pipe Installation — Cumulative Actual vs Planned", "#00E5FF"),
        use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    section_title("Daily Installation by SD Zone")

    mask_p = (summary_df["Activity"].str.contains("Pipe", case=False, na=False)
              & (summary_df["Date"]>=f_start) & (summary_df["Date"]<=f_end))
    pipe_df = summary_df.loc[mask_p].copy()

    if not pipe_df.empty:
        piv = (pipe_df.groupby(["Date","SD"])["Daily_Qty"]
               .sum().unstack(fill_value=0).reset_index().sort_values("Date"))
        sd_cols = [c for c in piv.columns if c != "Date"]
        piv["Total"]      = piv[sd_cols].sum(axis=1)
        piv["Cumulative"] = piv["Total"].cumsum()

        fig_sd = make_subplots(specs=[[{"secondary_y":True}]])
        clrs = ["#00E5FF","#FF6B35","#A8FF3E","#C77DFF"]
        for i,sd in enumerate(sd_cols):
            fig_sd.add_trace(go.Bar(x=piv["Date"],y=piv[sd],name=f"SD-{sd}",
                marker_color=clrs[i%len(clrs)],opacity=.82), secondary_y=False)
        fig_sd.add_trace(go.Scatter(x=piv["Date"],y=piv["Cumulative"],name="Cumulative",
            mode="lines+markers",line=dict(color="#FFD166",width=2.5),
            marker=dict(size=5)), secondary_y=True)
        fig_sd.update_layout(barmode="stack",title_text="Daily Pipe by SD Zone",
            title_font=dict(size=13,color=ct["font_color"]),
            legend=_LEGEND, **base_layout(height=320))
        fig_sd.update_yaxes(title_text="Daily (rm)",secondary_y=False,
            gridcolor=ct["gridcolor"])
        fig_sd.update_yaxes(title_text="Cumulative (rm)",secondary_y=True,showgrid=False)
        apply_axes(fig_sd, ct)
        st.plotly_chart(fig_sd, use_container_width=True)

    section_title("Pipe Installation Data")
    with st.expander("View Data Table", expanded=True):
        if pipe_df.empty:
            st.info("No pipe data.")
        else:
            show = (pipe_df.groupby(["Date","SD","Pipe_Dia"])["Daily_Qty"]
                    .sum().reset_index().sort_values(["Date","SD","Pipe_Dia"]))
            show.columns = ["Date","SD Zone","Pipe Diameter","Daily Qty (rm)"]
            show["Daily Qty (rm)"] = show["Daily Qty (rm)"].round(2)
            st.dataframe(show, use_container_width=True, hide_index=True)
            st.download_button("Download CSV", show.to_csv(index=False).encode(),
                               "pipe_installation.csv","text/csv")

# ── ROAD CUTTING ─────────────────────────────────────────────
elif selected == "Road Cutting":
    section_title("Road Cutting + Trench Excavation — Planned vs Actual")
    st.plotly_chart(_line_chart("Road Cutting", road_tgt,
        "Road Cutting + Trench Excavation — Cumulative", "#FF6B35"),
        use_container_width=True)

    section_title("Daily Excavation by SD Zone")
    mask_r = (summary_df["Activity"].str.contains("Road Cutting", case=False, na=False)
              & (summary_df["Date"]>=f_start) & (summary_df["Date"]<=f_end))
    road_df = summary_df.loc[mask_r].copy()

    if not road_df.empty:
        piv_r = (road_df.groupby(["Date","SD"])["Daily_Qty"]
                 .sum().unstack(fill_value=0).reset_index().sort_values("Date"))
        sd_r  = [c for c in piv_r.columns if c != "Date"]
        piv_r["Total"] = piv_r[sd_r].sum(axis=1)

        fig_rd = go.Figure()
        for i,sd in enumerate(sd_r):
            fig_rd.add_trace(go.Bar(x=piv_r["Date"],y=piv_r[sd],name=f"SD-{sd}",
                marker_color=["#FF6B35","#FFD166","#C77DFF"][i%3],opacity=.82))
        fig_rd.add_trace(go.Scatter(x=piv_r["Date"],y=piv_r["Total"],name="Daily Total",
            mode="lines+markers+text",line=dict(color="#FF6B35",width=2),
            marker=dict(size=6),
            text=piv_r["Total"].round(1).astype(str),
            textposition="top center",textfont=dict(size=9)))
        fig_rd.update_layout(barmode="stack",title_text="Daily Excavation by SD Zone",
            title_font=dict(size=13,color=ct["font_color"]),
            legend=_LEGEND, **base_layout(height=320))
        apply_axes(fig_rd, ct)
        st.plotly_chart(fig_rd, use_container_width=True)

    section_title("Excavation Data")
    with st.expander("View Data Table", expanded=True):
        if road_df.empty:
            st.info("No excavation data.")
        else:
            show_r = (road_df.groupby(["Date","SD"])["Daily_Qty"]
                      .sum().reset_index().sort_values(["Date","SD"]))
            show_r.columns = ["Date","SD Zone","Daily Qty (rm)"]
            show_r["Daily Qty (rm)"] = show_r["Daily Qty (rm)"].round(2)
            st.dataframe(show_r, use_container_width=True, hide_index=True)
            st.download_button("Download CSV", show_r.to_csv(index=False).encode(),
                               "excavation.csv","text/csv")

# ── WORK ACTIVITY ─────────────────────────────────────────────
elif selected == "Work Activity":
    section_title("All Work Activities — Period Totals vs Monthly Targets")

    if not summary_df.empty:
        mask_a = (summary_df["Date"]>=f_start)&(summary_df["Date"]<=f_end)
        agg = (summary_df.loc[mask_a]
               .groupby(["Activity","SD","Pipe_Dia"])
               .agg(Achieved=("Daily_Qty","sum"),Target=("Qty_Mar","first"))
               .reset_index())
        agg["Label"] = (agg["Activity"]+" SD-"+agg["SD"]+" "+agg["Pipe_Dia"]).str.strip()
        agg = agg.sort_values("Achieved",ascending=True)

        fig_act = go.Figure()
        fig_act.add_trace(go.Bar(y=agg["Label"],x=agg["Achieved"],name="Achieved",
            orientation="h",marker_color=ct["accent"],opacity=.85,
            text=agg["Achieved"].round(1).astype(str),
            textposition="outside",textfont=dict(size=9)))
        fig_act.add_trace(go.Scatter(y=agg["Label"],x=agg["Target"],
            name="Monthly Target",mode="markers",
            marker=dict(symbol="line-ns",size=14,color="#FFD166",
                        line=dict(width=2,color="#FFD166"))))
        fig_act.update_layout(barmode="overlay",
            title_text="Work Activity vs Monthly Target",
            title_font=dict(size=13,color=ct["font_color"]),
            legend=_LEGEND,
            **base_layout(height=max(300, len(agg)*36)))
        fig_act.update_xaxes(title_text="Quantity (rm / Pcs)",gridcolor=ct["gridcolor"])
        apply_axes(fig_act, ct)
        st.plotly_chart(fig_act, use_container_width=True)

    # Service pit chart
    st.markdown("<br>", unsafe_allow_html=True)
    section_title("Service Pit Installation")
    mask_pit = (summary_df["Activity"].str.contains("Service Pit",case=False,na=False)
                &(summary_df["Date"]>=f_start)&(summary_df["Date"]<=f_end))
    pit_df = summary_df.loc[mask_pit].copy()

    if not pit_df.empty:
        pit_d = pit_df.groupby("Date")["Daily_Qty"].sum().reset_index().sort_values("Date")
        fig_p = go.Figure(go.Bar(
            x=pit_d["Date"],y=pit_d["Daily_Qty"],name="Service Pits (Pcs)",
            marker_color="#A8FF3E",opacity=.85,
            text=pit_d["Daily_Qty"].astype(int).astype(str),
            textposition="outside",textfont=dict(size=11)))
        fig_p.update_layout(title_text="Service Pit Installation — Daily",
            title_font=dict(size=13,color=ct["font_color"]),
            legend=_LEGEND, **base_layout(height=280))
        fig_p.update_yaxes(title_text="Pieces (Pcs)",gridcolor=ct["gridcolor"])
        apply_axes(fig_p, ct)
        st.plotly_chart(fig_p, use_container_width=True)

    section_title("All Activity Data")
    with st.expander("View Data Table", expanded=True):
        if summary_df.empty:
            st.info("No data.")
        else:
            filtered = summary_df[
                (summary_df["Date"]>=f_start)&(summary_df["Date"]<=f_end)
            ].sort_values(["Activity","SD","Date"]).reset_index(drop=True)
            t1,t2,t3 = st.tabs(["Pipe","Road Cutting","Service Pit"])
            for tab,kw in zip([t1,t2,t3],["Pipe","Road Cutting","Service Pit"]):
                with tab:
                    sub = filtered[filtered["Activity"].str.contains(kw,case=False,na=False)]
                    cols_show = [c for c in ["Date","Activity","SD","Pipe_Dia","Unit",
                                             "Daily_Qty","Qty_Mar"] if c in sub.columns]
                    st.dataframe(sub[cols_show], use_container_width=True, hide_index=True)
                    if not sub.empty:
                        st.download_button(f"Download {kw} CSV",
                            sub.to_csv(index=False).encode(),
                            f"{kw.lower().replace(' ','_')}.csv","text/csv",
                            key=f"dl_{kw}")

p2 = __import__("src.shared", fromlist=["_p"])._p()
st.markdown(f"""
<hr style='border-color:{p2['sec_border']}'/>
<p style='text-align:center;color:{p2['text_m']};font-size:.65rem;'>
    CCECC-HONESS-SMEDI JV &nbsp;|&nbsp; WD5B &nbsp;|&nbsp; Project Progress
</p>
""", unsafe_allow_html=True)