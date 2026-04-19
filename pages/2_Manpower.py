# pages/2_Manpower.py
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.shared import HIDE_SIDEBAR
st.markdown(HIDE_SIDEBAR, unsafe_allow_html=True)

from src.shared import (
    inject_css, load_merged_manpower, kpi_card, section_title,
    page_header, base_layout, apply_axes, get_chart_theme,
    _LEGEND, PAL, CHART_COLORS, activity_icon_buttons,
)

st.set_page_config(
    page_title="Manpower — CCECC",
    page_icon="👷", layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()
st.markdown(HIDE_SIDEBAR, unsafe_allow_html=True)

p  = PAL
ct = get_chart_theme()

# ── Top bar ────────────────────────────────────────────────────
hc1, hc2 = st.columns([8,1])
with hc1:
    page_header("👷","Manpower Statistics",
                "Cross-month headcount — filter any date range across all available months")
with hc2:
    st.markdown("<br>",unsafe_allow_html=True)
    if st.button("🏠 Home", key="mp_home", use_container_width=True):
        st.switch_page("app.py")

# ── Load ALL months merged ─────────────────────────────────────
with st.spinner("Loading all manpower data…"):
    all_mp = load_merged_manpower()

if all_mp.empty:
    st.error("No manpower data loaded.")
    st.stop()

DATA_MIN = all_mp["Date"].min().date()
DATA_MAX = all_mp["Date"].max().date()

# ── Icon buttons ───────────────────────────────────────────────


if "mp_act" not in st.session_state:
    st.session_state["mp_act"] = "Overview Summary"

ACTIVITIES = [
    ("📊","Overview Summary", "Total headcount\nDonut · Daily trend · Shifts", "mp-ovw",  "ov"),
    ("🏢","CCECC Manpower",   "CCECC + CCECC Direct Team",                     "mp-ccecc","cc"),
    ("🤝","Sub Contractors",  "Rakib Enterprise · Rayhan Traders",              "mp-sub",  "sc"),
]

section_title("Select View")
ACTIVITIES = [
    ("📊","Overview Summary", "Total headcount · Donut\nDaily trend · Shift comparison", "#1A56DB"),
    ("🏢","CCECC Manpower",   "CCECC + CCECC Direct Team\nManagement · Site · Tech",     "#059669"),
    ("🤝","Sub Contractors",  "Rakib Enterprise · Rayhan Traders\nRole breakdown",        "#7C3AED"),
]
activity_icon_buttons(ACTIVITIES, "mp_act")

selected = st.session_state["mp_act"]

# ── Cross-month date filter ────────────────────────────────────
st.markdown(f"""
<div style="background:{p['bg2']};border:1px solid {p['border_s']};
            border-radius:14px;padding:1rem 1.5rem .8rem 1.5rem;margin-bottom:1.2rem;">
<p style="font-size:.6875rem;font-weight:700;text-transform:uppercase;
          letter-spacing:.1em;color:{p['text3']};margin:0 0 .75rem 0;">
    ⚙ Filter Options
</p>
""", unsafe_allow_html=True)
dc1, dc2, dc3 = st.columns([3, 2, 1])
with dc1:
    date_range = st.date_input(
        "Date range",
        value=(DATA_MIN, DATA_MAX),
        min_value=DATA_MIN, max_value=DATA_MAX,
        key="mp_dr",
        help=f"Range: {DATA_MIN.strftime('%d %b %Y')} – {DATA_MAX.strftime('%d %b %Y')}")
with dc2:
    shift_sel = st.selectbox("Shift", ["Day Shift Only","Night Shift Only","Both Shifts"],
                             key="mp_shift")
with dc3:
    if st.button("🔄 Refresh", key="mp_refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

if isinstance(date_range,(list,tuple)) and len(date_range)==2:
    f_start = pd.Timestamp(date_range[0]); f_end = pd.Timestamp(date_range[1])
else:
    s = date_range[0] if isinstance(date_range,(list,tuple)) else date_range
    f_start = f_end = pd.Timestamp(s)

# Filter by date
df_date = all_mp[(all_mp["Date"]>=f_start)&(all_mp["Date"]<=f_end)].copy()
# Filter by shift
if shift_sel == "Day Shift Only":
    df = df_date[df_date["Shift"]=="Day"]
elif shift_sel == "Night Shift Only":
    df = df_date[df_date["Shift"]=="Night"]
else:
    df = df_date

date_label = f"{f_start.strftime('%d %b %Y')} → {f_end.strftime('%d %b %Y')}"

# ── Shared chart builders ──────────────────────────────────────
CLRS = CHART_COLORS

def _top_kpis(d: pd.DataFrame, prefix: str = ""):
    day_df = d[d["Shift"]=="Day"] if "Shift" in d.columns and not d.empty else d
    total  = int(day_df["Count"].sum()) if not day_df.empty else 0
    days   = int(day_df["Date"].nunique()) if not day_df.empty else 0
    avg_d  = round(day_df.groupby("Date")["Count"].sum().mean(),0) if days else 0
    peak   = int(day_df.groupby("Date")["Count"].sum().max()) if days else 0
    ld     = day_df["Date"].max() if not day_df.empty else pd.NaT
    lc     = int(day_df[day_df["Date"]==ld]["Count"].sum()) if pd.notna(ld) else 0
    k1,k2,k3,k4,k5 = st.columns(5)
    kpi_card(k1,f"{prefix}Person-Days",f"{total:,}","Day shift")
    kpi_card(k2,"Active Days",         str(days),   "Days with manpower")
    kpi_card(k3,"Avg Daily",           f"{avg_d:.0f}","persons/day")
    kpi_card(k4,"Peak Day",            str(peak),    "Highest day count")
    kpi_card(k5,"Latest Day",          str(lc),
             f"as of {ld.strftime('%d %b') if pd.notna(ld) else 'N/A'}")

def _donut(d,title):
    by_co = d.groupby("Company")["Count"].sum().reset_index()
    by_co = by_co[by_co["Count"]>0].sort_values("Count",ascending=False)
    total = int(by_co["Count"].sum())
    fig = go.Figure(go.Pie(
        labels=by_co["Company"],values=by_co["Count"],hole=.54,
        marker=dict(colors=CLRS[:len(by_co)]),
        textinfo="percent+label",textfont=dict(size=11,color=p["text"]),showlegend=False))
    fig.add_annotation(text=f"<b>{total}</b><br>Total",x=.5,y=.5,showarrow=False,
        font=dict(size=16,color=p["text"]),align="center")
    fig.update_layout(title_text=title,title_font=dict(size=13,color=ct["font_color"]),
        **base_layout(height=320))
    return fig

def _role_bar(d,title):
    by_role = d.groupby(["Company","Role"])["Count"].sum().reset_index()
    by_role = by_role[by_role["Count"]>0]
    fig = go.Figure()
    for i,role in enumerate(by_role["Role"].unique()):
        rd = by_role[by_role["Role"]==role]
        fig.add_trace(go.Bar(x=rd["Company"],y=rd["Count"],name=role,
            marker_color=CLRS[i%len(CLRS)],opacity=.85,
            text=rd["Count"].astype(int).astype(str),
            textposition="inside",textfont=dict(size=9,color="#fff")))
    fig.update_layout(barmode="stack",title_text=title,
        title_font=dict(size=13,color=ct["font_color"]),
        legend=_LEGEND,**base_layout(height=320))
    fig.update_xaxes(tickangle=-15)
    fig.update_yaxes(title_text="Headcount",title_font=dict(size=10))
    apply_axes(fig,ct); return fig

def _trend(d,title,color):
    day_d = d[d["Shift"]=="Day"] if not d.empty else d
    daily = day_d.groupby("Date")["Count"].sum().reset_index().sort_values("Date")
    daily["R3"] = daily["Count"].rolling(3,min_periods=1).mean()
    r,g,b = tuple(int(color.lstrip("#")[j:j+2],16) for j in (0,2,4))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["Date"],y=daily["Count"],name="Daily Total",
        mode="lines+markers",line=dict(color=color,width=2.5),marker=dict(size=7),
        fill="tozeroy",fillcolor=f"rgba({r},{g},{b},0.08)"))
    fig.add_trace(go.Scatter(x=daily["Date"],y=daily["R3"],name="3-day avg",
        mode="lines",line=dict(color=p["text4"],width=1.8,dash="dash")))
    fig.update_layout(title_text=title,title_font=dict(size=13,color=ct["font_color"]),
        legend=_LEGEND,**base_layout(height=280))
    fig.update_yaxes(title_text="Headcount",title_font=dict(size=10))
    apply_axes(fig,ct); return fig

def _shift_chart(d):
    pivot = (d.groupby(["Date","Shift"])["Count"]
             .sum().unstack(fill_value=0).reset_index().sort_values("Date"))
    fig = go.Figure()
    for sh in [c for c in pivot.columns if c!="Date"]:
        fig.add_trace(go.Bar(x=pivot["Date"],y=pivot[sh],name=f"{sh} Shift",
            marker_color=p["blue"] if sh=="Day" else p["purple"],opacity=.85))
    fig.update_layout(barmode="group",title_text="Day vs Night Shift",
        title_font=dict(size=13,color=ct["font_color"]),
        legend=_LEGEND,**base_layout(height=260))
    apply_axes(fig,ct); return fig

def _full_section(day_d,all_d,color,pfx):
    if day_d.empty:
        st.info(f"No {pfx} data for {date_label}."); return
    section_title(f"{pfx} Headcount")
    c1,c2 = st.columns(2,gap="medium")
    with c1: st.plotly_chart(_donut(day_d,f"{pfx} by Company"),use_container_width=True)
    with c2: st.plotly_chart(_role_bar(day_d,f"{pfx} Role Breakdown"),use_container_width=True)
    section_title("Daily Trend (Day Shift)")
    st.plotly_chart(_trend(all_d,f"{pfx} Daily Headcount",color),use_container_width=True)
    if "Day" in all_d["Shift"].unique() and "Night" in all_d["Shift"].unique():
        section_title("Shift Comparison")
        st.plotly_chart(_shift_chart(all_d),use_container_width=True)
    section_title("Data Table")
    with st.expander("View data",expanded=False):
        show = day_d.sort_values(["Date","Company","Role"])
        st.dataframe(show,use_container_width=True,hide_index=True)
        st.download_button("⬇ Download CSV",show.to_csv(index=False).encode(),
            f"{pfx.lower().replace(' ','_')}_manpower.csv","text/csv")

# ── Sections ───────────────────────────────────────────────────
section_title(f"Showing: {date_label}")

if selected == "Overview Summary":
    _top_kpis(df)
    st.markdown("<br>",unsafe_allow_html=True)
    day_df = df[df["Shift"]=="Day"] if not df.empty else pd.DataFrame()
    _full_section(day_df, df_date, p["blue"], "Overall")

elif selected == "CCECC Manpower":
    cc_all = df_date[df_date["Company"].str.contains("CCECC",case=False,na=False)]
    cc_day = cc_all[cc_all["Shift"]=="Day"]
    section_title("CCECC Manpower")
    _top_kpis(cc_all,"CCECC ")
    st.markdown("<br>",unsafe_allow_html=True)
    _full_section(cc_day, cc_all, p["green"], "CCECC")

elif selected == "Sub Contractors":
    sub_all = df_date[~df_date["Company"].str.contains("CCECC",case=False,na=False)]
    sub_day = sub_all[sub_all["Shift"]=="Day"]
    section_title("Sub-Contractor Manpower")
    _top_kpis(sub_all,"Sub-Con ")
    st.markdown("<br>",unsafe_allow_html=True)
    _full_section(sub_day, sub_all, p["purple"], "Sub-Contractor")
    if not sub_day.empty:
        section_title("Per-Company Detail")
        companies = sub_day["Company"].unique()
        comp_cols = st.columns(len(companies))
        for i,company in enumerate(companies):
            comp_d = sub_day[sub_day["Company"]==company]
            t = int(comp_d["Count"].sum())
            a = round(comp_d.groupby("Date")["Count"].sum().mean(),0)
            with comp_cols[i]:
                st.markdown(f"""
                <div class="kpi-card" style="margin-bottom:1rem;">
                    <div class="kpi-label">{company}</div>
                    <div class="kpi-val">{t:,}</div>
                    <div class="kpi-sub">Avg {a:.0f}/day</div>
                </div>""",unsafe_allow_html=True)
                rd = comp_d.groupby("Role")["Count"].sum().sort_values().reset_index()
                fig_r = go.Figure(go.Bar(x=rd["Count"],y=rd["Role"],orientation="h",
                    marker_color=p["blue"],opacity=.85,
                    text=rd["Count"].astype(int).astype(str),
                    textposition="outside",textfont=dict(size=9,color=p["text3"])))
                fig_r.update_layout(paper_bgcolor="#FFFFFF",plot_bgcolor="#FFFFFF",
                    font_color=ct["font_color"],height=200,
                    margin=dict(l=8,r=48,t=8,b=8),showlegend=False)
                fig_r.update_xaxes(gridcolor=ct["gridcolor"],tickfont=dict(size=9))
                fig_r.update_yaxes(gridcolor=ct["gridcolor"],tickfont=dict(size=9))
                st.plotly_chart(fig_r,use_container_width=True)

st.markdown(f"""
<hr style="border:none;border-top:1px solid {p['border_s']};margin:2rem 0 .5rem 0;">
<p style="text-align:center;color:{p['text4']};font-size:.6875rem;">
    CCECC-HONESS-SMEDI JV &nbsp;·&nbsp; WD5B &nbsp;·&nbsp; Manpower Statistics
</p>""",unsafe_allow_html=True)