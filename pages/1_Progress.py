# pages/1_Progress.py
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.shared import HIDE_SIDEBAR
st.markdown(HIDE_SIDEBAR, unsafe_allow_html=True)

from src.shared import (
    inject_css, load_merged_summary, kpi_card, section_title,
    page_header, base_layout, apply_axes, get_chart_theme,
    _LEGEND, PAL, CHART_COLORS, activity_icon_buttons,
)
from src import cleaner

st.set_page_config(
    page_title="Project Progress — CCECC",
    page_icon="📊", layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()
st.markdown(HIDE_SIDEBAR, unsafe_allow_html=True)

p  = PAL
ct = get_chart_theme()

# ══════════════════════════════════════════════════════════════
# ICON BUTTON CSS + RENDERER
# The card is pure HTML, the invisible st.button sits on top
# via negative margin so the whole card area is clickable.
# ══════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════
# PAGE LAYOUT
# ══════════════════════════════════════════════════════════════
hc1, hc2 = st.columns([8, 1])
with hc1:
    page_header("📊", "Project Progress",
                "Cross-month analysis — filter any date range across Jan, Feb, Mar 2026")
with hc2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🏠 Home", key="prog_home", use_container_width=True):
        st.switch_page("app.py")

# ══════════════════════════════════════════════════════════════
# LOAD ALL MONTHS MERGED (cross-month capable)
# ══════════════════════════════════════════════════════════════
with st.spinner("Loading data from all months…"):
    all_df = load_merged_summary()

if all_df.empty:
    st.error("No data loaded. Check Google Sheets connection and service account permissions.")
    st.stop()

DATA_MIN = all_df["Date"].min().date()
DATA_MAX = all_df["Date"].max().date()

# ══════════════════════════════════════════════════════════════
# ACTIVITY ICONS
# ══════════════════════════════════════════════════════════════
section_title("Select Activity")

ACTIVITIES = [
    ("🚧", "Road Cutting",      "Trench excavation\nSD-A · SD-B · SD-D",               "#EA580C"),
    ("📏", "Pipe Installation", "DN150 & DN200\nSD zones · cross-month range",          "#1A56DB"),
    ("⚙️",  "Service Pit",      "Pit installation\nSD-A · SD-D",                        "#059669"),
    ("🏗️", "Manhole",           "Manhole construction\nupdated automatically",           "#7C3AED"),
]
selected = activity_icon_buttons(ACTIVITIES, "prog_act")

# ══════════════════════════════════════════════════════════════
# FILTER BAR — cross-month date range
# ══════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="background:{p['bg2']};border:1px solid {p['border_s']};
            border-radius:14px;padding:1.1rem 1.5rem .8rem 1.5rem;margin:6px 0 1.2rem 0;">
<p style="font-size:.6875rem;font-weight:700;text-transform:uppercase;
          letter-spacing:.1em;color:{p['text3']};margin:0 0 .75rem 0;">
    ⚙ Filter Options
</p>
""", unsafe_allow_html=True)

# Row 1: date range + time grouping
r1c1, r1c2, r1c3 = st.columns([3, 2, 2])

with r1c1:
    date_range = st.date_input(
        "Date range",
        value=(DATA_MIN, DATA_MAX),
        min_value=DATA_MIN,
        max_value=DATA_MAX,
        key="prog_dr",
        help=f"Any range from {DATA_MIN.strftime('%d %b %Y')} to {DATA_MAX.strftime('%d %b %Y')}"
    )

with r1c2:
    time_group = st.selectbox(
        "Group by", ["Daily", "Weekly", "Monthly"],
        key="prog_tg")

with r1c3:
    if st.button("🔄 Refresh data", key="prog_refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Row 2: SD + Pipe Dia (only relevant for Pipe; SD only for Road/Pit)
if selected == "Pipe Installation":
    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        sd_raw  = sorted(all_df["SD"].dropna().unique().tolist())
        sd_opts = ["All SD Zones"] + [f"SD-{s}" for s in sd_raw]
        sd_sel  = st.selectbox("SD Zone (sub-division)", sd_opts, key="prog_sd")
    with r2c2:
        dia_raw  = sorted([d for d in all_df["Pipe_Dia"].dropna().unique()
                           if d not in ("General", "")])
        dia_opts = ["All Diameters"] + dia_raw
        dia_sel  = st.selectbox("Pipe Diameter", dia_opts, key="prog_dia")
    with r2c3:
        view_mode = st.radio("Chart view", ["Cumulative", "Period quantities"],
                             horizontal=True, key="prog_vm")
elif selected in ("Road Cutting", "Service Pit"):
    sd_raw  = sorted(all_df["SD"].dropna().unique().tolist())
    sd_opts = ["All SD Zones"] + [f"SD-{s}" for s in sd_raw]
    sd_sel  = st.selectbox("SD Zone", sd_opts, key="prog_sd2")
    dia_sel = "All Diameters"
    view_mode = "Cumulative"
else:
    sd_sel    = "All SD Zones"
    dia_sel   = "All Diameters"
    view_mode = "Cumulative"

st.markdown("</div>", unsafe_allow_html=True)

# Parse date range safely
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    f_start = pd.Timestamp(date_range[0])
    f_end   = pd.Timestamp(date_range[1])
else:
    # user clicked only one date — use it as both start and end
    single = date_range[0] if isinstance(date_range, (list,tuple)) else date_range
    f_start = f_end = pd.Timestamp(single)

date_label = (f"{f_start.strftime('%d %b %Y')} → {f_end.strftime('%d %b %Y')} "
              f"· {time_group}")

# ══════════════════════════════════════════════════════════════
# SHARED HELPERS
# ══════════════════════════════════════════════════════════════

def _base_filter(activity_kw: str) -> pd.DataFrame:
    """Filter all_df by activity keyword + selected date range."""
    return all_df[
        all_df["Activity"].str.contains(activity_kw, case=False, na=False)
        & (all_df["Date"] >= f_start)
        & (all_df["Date"] <= f_end)
    ].copy()


def _apply_sd_dia(df: pd.DataFrame) -> pd.DataFrame:
    """Apply SD zone and pipe diameter filters."""
    if sd_sel not in ("All SD Zones",) and not df.empty:
        df = df[df["SD"] == sd_sel.replace("SD-", "")]
    if dia_sel not in ("All Diameters",) and not df.empty:
        df = df[df["Pipe_Dia"] == dia_sel]
    return df


def _add_period(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if time_group == "Weekly":
        df["Period"] = df["Date"].dt.to_period("W").apply(lambda x: x.start_time)
    elif time_group == "Monthly":
        df["Period"] = df["Date"].dt.to_period("M").apply(lambda x: x.start_time)
    else:
        df["Period"] = df["Date"]
    return df


def _kpi_row(df: pd.DataFrame, activity_kw: str, unit: str = "rm"):
    total = df["Daily_Qty"].sum() if not df.empty else 0.0
    days  = int(df["Date"].nunique()) if not df.empty else 0
    avg_d = total / days if days else 0.0
    peak  = float(df.groupby("Date")["Daily_Qty"].sum().max()) if not df.empty else 0.0
    # Target from full (unfiltered) dataset
    meta  = all_df.drop_duplicates(["Activity","SD","Pipe_Dia"])
    tgt_m = meta[meta["Activity"].str.contains(activity_kw, case=False, na=False)]
    tgt   = float(tgt_m["Qty_Mar"].sum()) if not tgt_m.empty else 0.0
    pct   = round(total / tgt * 100, 1) if tgt else 0.0
    pv, pc = (("kpi-val-green","kpi-green") if pct>=90 else
              ("kpi-val-amber","kpi-amber") if pct>=60 else
              ("kpi-val-red",  "kpi-card"))
    k1,k2,k3,k4,k5 = st.columns(5)
    kpi_card(k1,"Total Installed",  f"{total:,.1f} {unit}", f"Monthly target: {tgt:,.0f} {unit}")
    kpi_card(k2,"vs Target",        f"{pct:.1f}%",          "vs all-months target",val_cls=pv,card_cls=pc)
    kpi_card(k3,"Active Days",      str(days),               "Days with recorded work")
    kpi_card(k4,"Daily Average",    f"{avg_d:.1f} {unit}",  "Per active day")
    kpi_card(k5,"Peak Day",         f"{peak:.1f} {unit}",   "Single day max")


def _combo_chart(df_p: pd.DataFrame, target: float,
                 title: str, color: str, unit: str = "rm") -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if not df_p.empty:
        agg = (df_p.groupby("Period")["Daily_Qty"]
               .sum().reset_index().sort_values("Period"))
        agg["Cumulative"] = agg["Daily_Qty"].cumsum()
        if target > 0:
            fig.add_trace(go.Scatter(
                x=[agg["Period"].iloc[0], agg["Period"].iloc[-1]],
                y=[0, target], name="Target (monthly)",
                mode="lines",
                line=dict(color=p["text4"], width=1.8, dash="dot")),
                secondary_y=False)
        r,g,b = tuple(int(color.lstrip("#")[j:j+2], 16) for j in (0, 2, 4))
        fig.add_trace(go.Scatter(
            x=agg["Period"], y=agg["Cumulative"],
            name=f"Cumulative ({unit})", mode="lines+markers",
            line=dict(color=color, width=2.8),
            marker=dict(size=8, color=color, line=dict(width=2, color="#fff")),
            fill="tozeroy", fillcolor=f"rgba({r},{g},{b},0.08)"),
            secondary_y=False)
        fig.add_trace(go.Bar(
            x=agg["Period"], y=agg["Daily_Qty"],
            name=f"Per period ({unit})",
            marker_color=color, opacity=0.22),
            secondary_y=True)
    fig.update_layout(
        title_text=title,
        title_font=dict(size=14, color=ct["font_color"],
                        family="Inter,Segoe UI,Arial"),
        legend=_LEGEND, **base_layout(height=420))
    fig.update_yaxes(title_text=f"Cumulative ({unit})", secondary_y=False,
                     title_font=dict(size=10), gridcolor=ct["gridcolor"])
    fig.update_yaxes(title_text=f"Per period ({unit})", secondary_y=True,
                     title_font=dict(size=10), showgrid=False)
    apply_axes(fig, ct)
    return fig


# ══════════════════════════════════════════════════════════════
# ROAD CUTTING
# ══════════════════════════════════════════════════════════════
if selected == "Road Cutting":
    df_r  = _base_filter("Road Cutting")
    df_rs = df_r[df_r["SD"] == sd_sel.replace("SD-","")].copy() \
            if sd_sel != "All SD Zones" else df_r.copy()
    df_rp = _add_period(df_rs)

    meta_r = all_df.drop_duplicates(["Activity","SD","Pipe_Dia"])
    tgt_r  = float(meta_r[meta_r["Activity"].str.contains(
                  "Road", case=False, na=False)]["Qty_Mar"].sum())

    section_title(f"🚧 Road Cutting — {date_label}")
    _kpi_row(df_rs, "Road Cutting")
    st.markdown("<br>", unsafe_allow_html=True)

    st.plotly_chart(_combo_chart(df_rp, tgt_r,
        f"Road Cutting — Cumulative ({sd_sel})", "#EA580C"),
        use_container_width=True)

    if sd_sel == "All SD Zones" and not df_rp.empty:
        section_title("Breakdown by SD Zone")
        piv = (_add_period(df_r)
               .groupby(["Period","SD"])["Daily_Qty"]
               .sum().unstack(fill_value=0).reset_index().sort_values("Period"))
        sd_c = [c for c in piv.columns if c != "Period"]
        fig_sd = go.Figure()
        clrs   = ["#EA580C","#D97706","#7C3AED"]
        for i,sd in enumerate(sd_c):
            fig_sd.add_trace(go.Bar(x=piv["Period"],y=piv[sd],
                name=f"SD-{sd}",marker_color=clrs[i%3],opacity=.85))
        fig_sd.update_layout(barmode="stack",legend=_LEGEND,**base_layout(height=280))
        apply_axes(fig_sd, ct)
        st.plotly_chart(fig_sd, use_container_width=True)

    section_title("Data Table")
    with st.expander("Road cutting data", expanded=True):
        if df_rs.empty:
            st.info("No data for selected filters.")
        else:
            show = (df_rs.groupby(["Date","SD"])["Daily_Qty"]
                    .sum().reset_index().sort_values(["Date","SD"]))
            show.columns = ["Date","SD Zone","Daily Qty (rm)"]
            show["Daily Qty (rm)"] = show["Daily Qty (rm)"].round(2)
            st.dataframe(show, use_container_width=True, hide_index=True)
            st.download_button("⬇ Download CSV",
                show.to_csv(index=False).encode(),
                "road_cutting.csv","text/csv")


# ══════════════════════════════════════════════════════════════
# PIPE INSTALLATION
# ══════════════════════════════════════════════════════════════
elif selected == "Pipe Installation":
    df_p  = _base_filter("Pipe")
    df_pf = _apply_sd_dia(df_p)
    df_pp = _add_period(df_pf)

    # Scale target to match filters
    meta_p = all_df.drop_duplicates(["Activity","SD","Pipe_Dia"])
    tgt_p  = meta_p[meta_p["Activity"].str.contains("Pipe", case=False, na=False)]
    if sd_sel != "All SD Zones":
        tgt_p = tgt_p[tgt_p["SD"] == sd_sel.replace("SD-","")]
    if dia_sel != "All Diameters":
        tgt_p = tgt_p[tgt_p["Pipe_Dia"] == dia_sel]
    target_rm = float(tgt_p["Qty_Mar"].sum()) if not tgt_p.empty else 0.0

    section_title(f"📏 Pipe Installation — {date_label}")
    _kpi_row(df_pf, "Pipe")
    st.markdown("<br>", unsafe_allow_html=True)

    filter_desc = f"{sd_sel} · {dia_sel}"

    if view_mode == "Cumulative":
        st.plotly_chart(_combo_chart(df_pp, target_rm,
            f"Pipe Installation — Cumulative ({filter_desc})", "#1A56DB"),
            use_container_width=True)
    else:
        if not df_pp.empty:
            agg = (df_pp.groupby("Period")["Daily_Qty"]
                   .sum().reset_index().sort_values("Period"))
            fig_pv = go.Figure(go.Bar(
                x=agg["Period"], y=agg["Daily_Qty"],
                name="Installed (rm)", marker_color="#1A56DB", opacity=.85,
                text=agg["Daily_Qty"].round(1).astype(str),
                textposition="outside",
                textfont=dict(size=9, color=p["text3"])))
            if target_rm > 0:
                fig_pv.add_hline(y=target_rm, line_dash="dot",
                    line_color=p["green"], line_width=1.5,
                    annotation_text=f"Monthly target: {target_rm:,.0f} rm",
                    annotation_font=dict(color=p["green"], size=10))
            fig_pv.update_layout(legend=_LEGEND, **base_layout(height=400))
            fig_pv.update_yaxes(title_text="Quantity (rm)",
                                 gridcolor=ct["gridcolor"])
            apply_axes(fig_pv, ct)
            st.plotly_chart(fig_pv, use_container_width=True)
        else:
            st.info("No data for selected filters.")

    # Breakdown charts when broad filters selected
    if sd_sel == "All SD Zones" or dia_sel == "All Diameters":
        section_title("Breakdown Charts")
        bc1, bc2 = st.columns(2, gap="medium")
        full_pipe = _add_period(_base_filter("Pipe"))

        if sd_sel == "All SD Zones" and not full_pipe.empty:
            with bc1:
                piv_sd = (full_pipe.groupby(["Period","SD"])["Daily_Qty"]
                          .sum().unstack(fill_value=0).reset_index()
                          .sort_values("Period"))
                sd_c = [c for c in piv_sd.columns if c != "Period"]
                fig_s = go.Figure()
                for i, sd in enumerate(sd_c):
                    fig_s.add_trace(go.Bar(
                        x=piv_sd["Period"], y=piv_sd[sd],
                        name=f"SD-{sd}",
                        marker_color=CHART_COLORS[i % len(CHART_COLORS)],
                        opacity=.85))
                fig_s.update_layout(barmode="stack",
                    title_text="Pipe by SD Zone",
                    title_font=dict(size=13, color=ct["font_color"]),
                    legend=_LEGEND, **base_layout(height=300))
                apply_axes(fig_s, ct)
                st.plotly_chart(fig_s, use_container_width=True)

        if dia_sel == "All Diameters" and not full_pipe.empty:
            col = bc2 if sd_sel == "All SD Zones" else bc1
            with col:
                piv_d = (full_pipe.groupby(["Period","Pipe_Dia"])["Daily_Qty"]
                         .sum().unstack(fill_value=0).reset_index()
                         .sort_values("Period"))
                dia_c = [c for c in piv_d.columns if c != "Period"]
                fig_d2 = go.Figure()
                dia_clrs = {"DN150":"#1A56DB","DN200":"#059669","General":"#D97706"}
                for dia in dia_c:
                    fig_d2.add_trace(go.Bar(
                        x=piv_d["Period"], y=piv_d[dia], name=dia,
                        marker_color=dia_clrs.get(dia, "#7C3AED"),
                        opacity=.85))
                fig_d2.update_layout(barmode="stack",
                    title_text="Pipe by Diameter",
                    title_font=dict(size=13, color=ct["font_color"]),
                    legend=_LEGEND, **base_layout(height=300))
                apply_axes(fig_d2, ct)
                st.plotly_chart(fig_d2, use_container_width=True)

    section_title("Data Table")
    with st.expander("Pipe installation data", expanded=True):
        if df_pf.empty:
            st.info("No data for selected filters.")
        else:
            t1, t2, t3 = st.tabs(["All Diameters","DN150","DN200"])
            for tab, dfl in zip([t1,t2,t3], ["All","DN150","DN200"]):
                with tab:
                    sub = df_pf if dfl == "All" \
                          else df_pf[df_pf["Pipe_Dia"] == dfl]
                    if sub.empty:
                        st.info("No data.")
                    else:
                        show = sub[["Date","SD","Pipe_Dia","Daily_Qty"]].copy()
                        show.columns = ["Date","SD Zone","Pipe Diameter","Daily Qty (rm)"]
                        show["Daily Qty (rm)"] = show["Daily Qty (rm)"].round(2)
                        st.dataframe(
                            show.sort_values(["Date","SD Zone"]),
                            use_container_width=True, hide_index=True)
                        st.download_button(
                            f"⬇ Download {dfl}",
                            show.to_csv(index=False).encode(),
                            f"pipe_{dfl.lower()}.csv","text/csv",
                            key=f"dl_pipe_{dfl}")


# ══════════════════════════════════════════════════════════════
# SERVICE PIT
# ══════════════════════════════════════════════════════════════
elif selected == "Service Pit":
    df_s  = _base_filter("Service Pit")
    df_ss = df_s[df_s["SD"] == sd_sel.replace("SD-","")].copy() \
            if sd_sel != "All SD Zones" else df_s.copy()
    df_sp = _add_period(df_ss)

    meta_s = all_df.drop_duplicates(["Activity","SD","Pipe_Dia"])
    tgt_s  = float(meta_s[meta_s["Activity"].str.contains(
                  "Service Pit", case=False, na=False)]["Qty_Mar"].sum())

    section_title(f"⚙️ Service Pit Installation — {date_label}")
    _kpi_row(df_ss, "Service Pit", "Pcs")
    st.markdown("<br>", unsafe_allow_html=True)

    st.plotly_chart(_combo_chart(df_sp, tgt_s,
        f"Service Pit — Cumulative ({sd_sel})", "#059669", "Pcs"),
        use_container_width=True)

    if sd_sel == "All SD Zones" and not df_sp.empty:
        section_title("By SD Zone")
        agg_s = (_add_period(df_s)
                 .groupby(["Period","SD"])["Daily_Qty"]
                 .sum().reset_index().sort_values("Period"))
        fig_sp = go.Figure()
        sp_clrs = ["#059669","#0891B2","#7C3AED"]
        for i,(sd_z,grp) in enumerate(agg_s.groupby("SD")):
            fig_sp.add_trace(go.Bar(
                x=grp["Period"], y=grp["Daily_Qty"],
                name=f"SD-{sd_z}",
                marker_color=sp_clrs[i%3], opacity=.85,
                text=grp["Daily_Qty"].astype(int).astype(str),
                textposition="outside", textfont=dict(size=10)))
        fig_sp.update_layout(barmode="group", legend=_LEGEND,
                             **base_layout(height=280))
        fig_sp.update_yaxes(title_text="Pieces (Pcs)")
        apply_axes(fig_sp, ct)
        st.plotly_chart(fig_sp, use_container_width=True)

    section_title("Data Table")
    with st.expander("Service pit data", expanded=True):
        if df_ss.empty:
            st.info("No data for selected filters.")
        else:
            show_s = df_ss[["Date","SD","Daily_Qty"]].copy()
            show_s.columns = ["Date","SD Zone","Pcs Installed"]
            st.dataframe(show_s.sort_values("Date"),
                         use_container_width=True, hide_index=True)
            st.download_button("⬇ Download CSV",
                show_s.to_csv(index=False).encode(),
                "service_pit.csv","text/csv")


# ══════════════════════════════════════════════════════════════
# MANHOLE
# ══════════════════════════════════════════════════════════════
elif selected == "Manhole":
    df_m = _base_filter("Manhole")
    section_title("🏗️ Manhole Construction")
    if df_m.empty:
        st.markdown(f"""
        <div style="background:{p['bg2']};border:2px dashed {p['border']};
                    border-radius:16px;padding:4rem 2rem;text-align:center;
                    margin:1rem 0;">
            <p style="font-size:3.5rem;margin:0 0 1rem 0;">🏗️</p>
            <p style="font-size:1.2rem;font-weight:800;color:{p['text']};
                      margin:0 0 .5rem 0;
                      font-family:'Inter','Segoe UI',Arial,sans-serif;">
                No Manhole Data Yet
            </p>
            <p style="font-size:.875rem;color:{p['text3']};
                      max-width:440px;margin:0 auto;line-height:1.7;">
                Manhole construction records will appear here automatically
                once entries are added to the Master Tracker Google Sheet.
                The dashboard refreshes every 30 minutes.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        df_mp = _add_period(df_m)
        _kpi_row(df_m, "Manhole", "Nos")
        st.plotly_chart(_combo_chart(df_mp, 0,
            "Manhole Construction Progress","#7C3AED","Nos"),
            use_container_width=True)
        with st.expander("Manhole data", expanded=True):
            show_m = df_m[["Date","SD","Daily_Qty"]].copy()
            show_m.columns = ["Date","SD Zone","Nos Constructed"]
            st.dataframe(show_m.sort_values("Date"),
                         use_container_width=True, hide_index=True)

st.markdown(f"""
<hr style="border:none;border-top:1px solid {p['border_s']};margin:2rem 0 .5rem 0;">
<p style="text-align:center;color:{p['text4']};font-size:.6875rem;">
    CCECC-HONESS-SMEDI JV &nbsp;·&nbsp; WD5B &nbsp;·&nbsp; Project Progress
</p>""", unsafe_allow_html=True)