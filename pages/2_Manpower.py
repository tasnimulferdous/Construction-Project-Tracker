# pages/2_Manpower.py
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.shared import (
    inject_css, render_sidebar, load_manpower,
    kpi_card, section_title, subnav_buttons,
    base_layout, apply_axes, get_chart_theme, _LEGEND,
)

st.set_page_config(page_title="Manpower — CCECC",
                   page_icon="👷", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()

ctx          = render_sidebar()
manpower_tab = ctx["manpower_tab"]
f_start      = ctx["filter_start"]
f_end        = ctx["filter_end"]
label        = ctx["selected_month_label"]
day_range    = ctx["day_range"]

manpower_df = load_manpower(manpower_tab)
df = (manpower_df[(manpower_df["Date"]>=f_start)&(manpower_df["Date"]<=f_end)].copy()
      if not manpower_df.empty else pd.DataFrame())

ct   = get_chart_theme()
CLRS = ["#00E5FF","#FF6B35","#A8FF3E","#C77DFF","#FFD166","#FF4560","#00BFA5","#FF4081"]
p    = __import__("src.shared", fromlist=["_p"])._p()

# ── Header ────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:1rem;animation:fade-in .5s ease both;">
    <p style="font-size:1.5rem;font-weight:800;color:{p['cyan']};margin:0;">👷 Manpower Statistics</p>
    <p style="font-size:.85rem;color:{p['text_s']};margin:.1rem 0;">
        {label} &nbsp;|&nbsp; Day {day_range[0]}–{day_range[1]} &nbsp;|&nbsp;
        {f_start.strftime('%d %b')} to {f_end.strftime('%d %b %Y')}
    </p>
</div>
""", unsafe_allow_html=True)

# ── Top KPIs ──────────────────────────────────────────────────
section_title("Manpower Overview")
if not df.empty:
    day_df   = df[df["Shift"]=="Day"]
    total_pd = int(day_df["Count"].sum())
    act_days = int(day_df["Date"].nunique())
    avg_d    = round(day_df.groupby("Date")["Count"].sum().mean(),0) if act_days else 0
    peak     = int(day_df.groupby("Date")["Count"].sum().max()) if act_days else 0
    latest_d = day_df["Date"].max()
    latest_c = int(day_df[day_df["Date"]==latest_d]["Count"].sum()) if pd.notna(latest_d) else 0
    k1,k2,k3,k4,k5 = st.columns(5)
    kpi_card(k1,"Total Person-Days", f"{total_pd:,}","All roles · Day shift")
    kpi_card(k2,"Active Days",       str(act_days),  "Days with manpower")
    kpi_card(k3,"Avg Daily",         f"{avg_d:.0f}", "persons/day (Day shift)")
    kpi_card(k4,"Peak Day",          str(peak),      "Highest single day")
    kpi_card(k5,"Latest Day",        str(latest_c),
             f"as of {latest_d.strftime('%d %b') if pd.notna(latest_d) else 'N/A'}")
else:
    st.info("No manpower data for selected period.")

st.markdown("<br>", unsafe_allow_html=True)
section_title("Select View")

SUBNAV = [
    ("📊","Overview Summary","Donut · Roles · Daily trend · Shift comparison"),
    ("🏢","CCECC Manpower", "CCECC + CCECC Direct Team breakdown"),
    ("🤝","Sub Contractors","Rakib Enterprise · Rayhan Traders"),
]
selected = subnav_buttons(SUBNAV, "manpower_subnav")
st.markdown("<br>", unsafe_allow_html=True)

# ── Shared chart builders ─────────────────────────────────────

def _donut(d: pd.DataFrame, title: str):
    by_co = d.groupby("Company")["Count"].sum().reset_index()
    by_co = by_co[by_co["Count"]>0].sort_values("Count",ascending=False)
    total = int(by_co["Count"].sum())
    fig = go.Figure(go.Pie(
        labels=by_co["Company"], values=by_co["Count"], hole=.54,
        marker=dict(colors=CLRS[:len(by_co)]),
        textinfo="percent+label", textfont=dict(size=10), showlegend=False))
    fig.add_annotation(text=f"<b>{total}</b><br>Total",
        x=.5,y=.5,showarrow=False,
        font=dict(size=15,color=ct["font_color"]),align="center")
    fig.update_layout(title_text=title,
        title_font=dict(size=13,color=ct["font_color"]),
        legend=_LEGEND, **base_layout(height=320))
    return fig

def _role_bar(d: pd.DataFrame, title: str):
    by_role = d.groupby(["Company","Role"])["Count"].sum().reset_index()
    by_role = by_role[by_role["Count"]>0]
    fig = go.Figure()
    for i,role in enumerate(by_role["Role"].unique()):
        rd = by_role[by_role["Role"]==role]
        fig.add_trace(go.Bar(x=rd["Company"],y=rd["Count"],name=role,
            marker_color=CLRS[i%len(CLRS)],opacity=.85,
            text=rd["Count"].astype(int).astype(str),
            textposition="inside",textfont=dict(size=9)))
    fig.update_layout(barmode="stack",title_text=title,
        title_font=dict(size=13,color=ct["font_color"]),
        legend=_LEGEND, **base_layout(height=320))
    fig.update_xaxes(tickangle=-15,tickfont=dict(size=9))
    fig.update_yaxes(title_text="Headcount",title_font=dict(size=10))
    apply_axes(fig,ct)
    return fig

def _trend(d: pd.DataFrame, title: str, color: str):
    daily = d.groupby("Date")["Count"].sum().reset_index().sort_values("Date")
    daily["R3"] = daily["Count"].rolling(3,min_periods=1).mean()
    hex_c = color.lstrip("#"); r,g,b = int(hex_c[:2],16),int(hex_c[2:4],16),int(hex_c[4:],16)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["Date"],y=daily["Count"],name="Daily Total",
        mode="lines+markers",line=dict(color=color,width=2.5),marker=dict(size=7),
        fill="tozeroy",fillcolor=f"rgba({r},{g},{b},0.08)"))
    fig.add_trace(go.Scatter(x=daily["Date"],y=daily["R3"],name="3-day avg",
        mode="lines",line=dict(color="#FFD166",width=1.8,dash="dash")))
    fig.update_layout(title_text=title,title_font=dict(size=13,color=ct["font_color"]),
        legend=_LEGEND, **base_layout(height=280))
    fig.update_yaxes(title_text="Headcount",title_font=dict(size=10))
    apply_axes(fig,ct)
    return fig

def _shift(d: pd.DataFrame):
    pivot = (d.groupby(["Date","Shift"])["Count"]
             .sum().unstack(fill_value=0).reset_index().sort_values("Date"))
    fig = go.Figure()
    for sh in [c for c in pivot.columns if c!="Date"]:
        fig.add_trace(go.Bar(x=pivot["Date"],y=pivot[sh],name=f"{sh} Shift",
            marker_color="#00E5FF" if sh=="Day" else "#C77DFF",opacity=.85))
    fig.update_layout(barmode="group",title_text="Day vs Night Shift",
        title_font=dict(size=13,color=ct["font_color"]),
        legend=_LEGEND, **base_layout(height=260))
    apply_axes(fig,ct)
    return fig

def _show_section(day_d: pd.DataFrame, all_d: pd.DataFrame, color: str, label_pfx: str):
    col_d, col_r = st.columns(2, gap="medium")
    with col_d:
        st.plotly_chart(_donut(day_d, f"{label_pfx} Headcount"), use_container_width=True)
    with col_r:
        st.plotly_chart(_role_bar(day_d, f"{label_pfx} Role Breakdown"), use_container_width=True)
    section_title(f"{label_pfx} Daily Trend")
    st.plotly_chart(_trend(day_d, f"{label_pfx} Daily Headcount (Day Shift)", color),
                    use_container_width=True)
    section_title("Shift Comparison")
    st.plotly_chart(_shift(all_d), use_container_width=True)

# ── OVERVIEW ─────────────────────────────────────────────────
if selected == "Overview Summary" and not df.empty:
    day_df = df[df["Shift"]=="Day"]
    section_title("Headcount by Company")
    _show_section(day_df, df, "#00E5FF", "Overall")
    section_title("Data")
    with st.expander("View Full Manpower Data", expanded=False):
        st.dataframe(df.sort_values(["Date","Shift","Company","Role"]),
                     use_container_width=True, hide_index=True)
        st.download_button("Download CSV", df.to_csv(index=False).encode(),
                           "manpower_overview.csv","text/csv")

# ── CCECC ────────────────────────────────────────────────────
elif selected == "CCECC Manpower":
    cc_df = df[df["Company"].str.contains("CCECC",case=False,na=False)] if not df.empty else pd.DataFrame()
    cc_day = cc_df[cc_df["Shift"]=="Day"] if not cc_df.empty else pd.DataFrame()
    if not cc_day.empty:
        total_c = int(cc_day["Count"].sum())
        avg_c   = round(cc_day.groupby("Date")["Count"].sum().mean(),0)
        peak_c  = int(cc_day.groupby("Date")["Count"].sum().max())
        cos     = cc_day["Company"].nunique()
        c1,c2,c3,c4 = st.columns(4)
        kpi_card(c1,"CCECC Person-Days",f"{total_c:,}","Day shift")
        kpi_card(c2,"CCECC Groups",     str(cos),       "Active groups")
        kpi_card(c3,"Avg Daily",        f"{avg_c:.0f}", "persons/day")
        kpi_card(c4,"Peak Day",         str(peak_c),    "Maximum headcount")
        section_title("CCECC Breakdown")
        _show_section(cc_day, cc_df, "#00E5FF", "CCECC")
        section_title("CCECC Data")
        with st.expander("View CCECC Data", expanded=False):
            st.dataframe(cc_day.sort_values(["Date","Company","Role"]),
                         use_container_width=True, hide_index=True)
            st.download_button("Download CSV", cc_day.to_csv(index=False).encode(),
                               "ccecc_manpower.csv","text/csv")
    else:
        st.info("No CCECC manpower data for selected period.")

# ── SUB CONTRACTORS ──────────────────────────────────────────
elif selected == "Sub Contractors":
    sub_df  = df[~df["Company"].str.contains("CCECC",case=False,na=False)] if not df.empty else pd.DataFrame()
    sub_day = sub_df[sub_df["Shift"]=="Day"] if not sub_df.empty else pd.DataFrame()
    if not sub_day.empty:
        total_s = int(sub_day["Count"].sum())
        avg_s   = round(sub_day.groupby("Date")["Count"].sum().mean(),0)
        peak_s  = int(sub_day.groupby("Date")["Count"].sum().max())
        cos_s   = sub_day["Company"].nunique()
        c1,c2,c3,c4 = st.columns(4)
        kpi_card(c1,"Sub-Con Person-Days",f"{total_s:,}","Day shift")
        kpi_card(c2,"Companies",          str(cos_s),    "Active companies")
        kpi_card(c3,"Avg Daily",          f"{avg_s:.0f}","persons/day")
        kpi_card(c4,"Peak Day",           str(peak_s),   "Maximum headcount")

        section_title("Sub-Contractor Breakdown")
        _show_section(sub_day, sub_df, "#FF6B35", "Sub-Contractor")

        # Per-company mini cards + bars
        section_title("Per-Company Detail")
        companies = sub_day["Company"].unique()
        comp_cols = st.columns(len(companies))
        for i, company in enumerate(companies):
            comp_d = sub_day[sub_day["Company"]==company]
            t = int(comp_d["Count"].sum())
            a = round(comp_d.groupby("Date")["Count"].sum().mean(),0)
            with comp_cols[i]:
                st.markdown(f"""
                <div style="background:{p['bg_card']};border:1px solid {p['border']};
                            border-radius:10px;padding:1rem;text-align:center;margin-bottom:.8rem;">
                    <div style="font-size:.60rem;text-transform:uppercase;
                                letter-spacing:.1em;color:{p['text_s']};margin-bottom:.2rem;">{company}</div>
                    <div style="font-size:1.6rem;font-weight:700;color:{p['cyan']};">{t:,}</div>
                    <div style="font-size:.67rem;color:{p['text_m']};">Avg {a:.0f}/day</div>
                </div>
                """, unsafe_allow_html=True)
                rd = comp_d.groupby("Role")["Count"].sum().sort_values().reset_index()
                fig_r = go.Figure(go.Bar(x=rd["Count"],y=rd["Role"],orientation="h",
                    marker_color="#00E5FF",opacity=.8,
                    text=rd["Count"].astype(int).astype(str),
                    textposition="outside",textfont=dict(size=9)))
                fig_r.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor=ct["plot_bgcolor"],font_color=ct["font_color"],
                    height=200,margin=dict(l=8,r=40,t=8,b=8),showlegend=False)
                fig_r.update_xaxes(gridcolor=ct["gridcolor"],tickfont=dict(size=9))
                fig_r.update_yaxes(gridcolor=ct["gridcolor"],tickfont=dict(size=9))
                st.plotly_chart(fig_r, use_container_width=True)

        section_title("Sub-Contractor Data")
        with st.expander("View Data", expanded=False):
            st.dataframe(sub_day.sort_values(["Date","Company","Role"]),
                         use_container_width=True, hide_index=True)
            st.download_button("Download CSV", sub_day.to_csv(index=False).encode(),
                               "subcontractor_manpower.csv","text/csv")
    else:
        st.info("No sub-contractor data for selected period.")

st.markdown(f"""
<hr style='border-color:{p['sec_border']}'/>
<p style='text-align:center;color:{p['text_m']};font-size:.65rem;'>
    CCECC-HONESS-SMEDI JV &nbsp;|&nbsp; WD5B &nbsp;|&nbsp; Manpower Statistics
</p>
""", unsafe_allow_html=True)