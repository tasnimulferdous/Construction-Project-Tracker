# pages/2_Manpower.py — Manpower Statistics
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.shared import (
    inject_css, render_sidebar, load_manpower,
    kpi_card, section_title, subnav_buttons, get_chart_theme,
)

st.set_page_config(
    page_title="Manpower — CCECC",
    page_icon="👷",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

ctx          = render_sidebar()
manpower_tab = ctx["manpower_tab"]
filter_start = ctx["filter_start"]
filter_end   = ctx["filter_end"]
label        = ctx["selected_month_label"]
day_range    = ctx["day_range"]

manpower_df = load_manpower(manpower_tab)
df = manpower_df[
    (manpower_df["Date"] >= filter_start)
    & (manpower_df["Date"] <= filter_end)
].copy() if not manpower_df.empty else pd.DataFrame()

ct = get_chart_theme()
COLORS = ["#00E5FF","#FF6B35","#A8FF3E","#C77DFF","#FFD166","#FF4560","#00BFA5","#FF4081"]

def _base_layout(**extra) -> dict:
    return dict(
        paper_bgcolor=ct["paper_bgcolor"], plot_bgcolor=ct["plot_bgcolor"],
        font_color=ct["font_color"], font_family="Segoe UI, Arial, sans-serif",
        hovermode="x unified",
        margin=dict(l=16, r=16, t=50, b=16),
        legend=dict(bgcolor="rgba(0,0,0,0)",
                    bordercolor="rgba(127,127,127,0.2)",
                    borderwidth=1, font=dict(size=11)),
        **extra,
    )

def _axes(fig):
    fig.update_xaxes(gridcolor=ct["gridcolor"], zerolinecolor=ct["zerolinecolor"],
                     showline=False, tickfont=dict(size=10))
    fig.update_yaxes(gridcolor=ct["gridcolor"], zerolinecolor=ct["zerolinecolor"],
                     showline=False, tickfont=dict(size=10))
    return fig

# ── Header ────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:1rem; animation:fade-in 0.5s ease both;">
    <p style="font-size:1.5rem; font-weight:800; color:var(--accent-cyan); margin:0;">
        👷 Manpower Statistics
    </p>
    <p style="font-size:0.85rem; color:var(--text-secondary); margin:0.1rem 0;">
        {label} &nbsp;|&nbsp; Day {day_range[0]}–{day_range[1]} &nbsp;|&nbsp;
        {filter_start.strftime('%d %b')} to {filter_end.strftime('%d %b %Y')}
    </p>
</div>
""", unsafe_allow_html=True)

# ── Top KPIs ──────────────────────────────────────────────────
section_title("Manpower Overview")
if not df.empty:
    day_df = df[df["Shift"] == "Day"]
    total_pd  = int(day_df["Count"].sum())
    act_days  = int(day_df["Date"].nunique())
    avg_daily = round(day_df.groupby("Date")["Count"].sum().mean(), 0) if act_days else 0
    peak      = int(day_df.groupby("Date")["Count"].sum().max()) if act_days else 0
    latest_dt = day_df["Date"].max()
    latest_c  = int(day_df[day_df["Date"]==latest_dt]["Count"].sum()) if pd.notna(latest_dt) else 0

    k1,k2,k3,k4,k5 = st.columns(5)
    kpi_card(k1,"Total Person-Days", f"{total_pd:,}",    "All roles · Day shift")
    kpi_card(k2,"Active Days",       str(act_days),       "Days with manpower")
    kpi_card(k3,"Avg Daily Headcount",f"{avg_daily:.0f}", "Day shift avg")
    kpi_card(k4,"Peak Day",          str(peak),           "Highest single day")
    kpi_card(k5,"Latest Day",        str(latest_c),
             f"as of {latest_dt.strftime('%d %b') if pd.notna(latest_dt) else 'N/A'}")
else:
    st.info("No manpower data for selected period.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Sub-navigation ────────────────────────────────────────────
section_title("Select View")
SUBNAV = [
    ("📊", "Overview Summary",  "Donut · Roles · Daily trend"),
    ("🏢", "CCECC Manpower",    "CCECC + CCECC Direct Team"),
    ("🤝", "Sub Contractors",   "Rakib Enterprise · Rayhan Traders"),
]
selected = subnav_buttons(SUBNAV, "manpower_subnav")
st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Shared chart builders
# ─────────────────────────────────────────────────────────────

def _donut(company_df: pd.DataFrame, title: str) -> go.Figure:
    by_co = company_df.groupby("Company")["Count"].sum().reset_index()
    by_co = by_co[by_co["Count"] > 0].sort_values("Count", ascending=False)
    total = int(by_co["Count"].sum())
    fig = go.Figure(go.Pie(
        labels=by_co["Company"], values=by_co["Count"],
        hole=0.54, marker=dict(colors=COLORS[:len(by_co)]),
        textinfo="percent+label", textfont=dict(size=10),
        showlegend=False,
    ))
    fig.add_annotation(text=f"<b>{total}</b><br>Total",
                       x=0.5, y=0.5, showarrow=False,
                       font=dict(size=15, color=ct["font_color"]), align="center")
    fig.update_layout(title_text=title,
                      title_font=dict(size=13, color=ct["font_color"]),
                      **_base_layout(), height=320)
    return fig


def _role_bar(company_df: pd.DataFrame, title: str) -> go.Figure:
    by_role = (company_df.groupby(["Company","Role"])["Count"]
               .sum().reset_index())
    by_role = by_role[by_role["Count"] > 0]
    roles   = by_role["Role"].unique()
    fig = go.Figure()
    for i, role in enumerate(roles):
        rd = by_role[by_role["Role"]==role]
        fig.add_trace(go.Bar(x=rd["Company"], y=rd["Count"], name=role,
                             marker_color=COLORS[i%len(COLORS)], opacity=0.85,
                             text=rd["Count"].astype(int).astype(str),
                             textposition="inside", textfont=dict(size=9)))
    fig.update_layout(barmode="stack", title_text=title,
                      title_font=dict(size=13, color=ct["font_color"]),
                      **_base_layout(), height=320)
    fig.update_xaxes(tickangle=-15, tickfont=dict(size=9))
    fig.update_yaxes(title_text="Headcount", title_font=dict(size=10))
    _axes(fig)
    return fig


def _daily_trend(company_df: pd.DataFrame, title: str, color: str) -> go.Figure:
    daily = company_df.groupby("Date")["Count"].sum().reset_index().sort_values("Date")
    daily["Rolling3"] = daily["Count"].rolling(3, min_periods=1).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["Date"], y=daily["Count"],
                             name="Daily Total", mode="lines+markers",
                             line=dict(color=color, width=2.5),
                             marker=dict(size=7),
                             fill="tozeroy",
                             fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)"))
    fig.add_trace(go.Scatter(x=daily["Date"], y=daily["Rolling3"],
                             name="3-day avg", mode="lines",
                             line=dict(color="#FFD166", width=1.8, dash="dash")))
    fig.update_layout(title_text=title,
                      title_font=dict(size=13, color=ct["font_color"]),
                      **_base_layout(), height=280)
    fig.update_yaxes(title_text="Headcount", title_font=dict(size=10))
    _axes(fig)
    return fig


def _shift_compare(company_df: pd.DataFrame) -> go.Figure:
    pivot = (company_df.groupby(["Date","Shift"])["Count"]
             .sum().unstack(fill_value=0).reset_index().sort_values("Date"))
    fig = go.Figure()
    for i, sh in enumerate([c for c in pivot.columns if c != "Date"]):
        clr = "#00E5FF" if sh == "Day" else "#C77DFF"
        fig.add_trace(go.Bar(x=pivot["Date"], y=pivot[sh], name=f"{sh} Shift",
                             marker_color=clr, opacity=0.85))
    fig.update_layout(barmode="group", title_text="Day vs Night Shift",
                      title_font=dict(size=13, color=ct["font_color"]),
                      **_base_layout(), height=260)
    _axes(fig)
    return fig


# ──────────────────────────────────────────────────────────────
# OVERVIEW SUMMARY
# ──────────────────────────────────────────────────────────────

if selected == "Overview Summary" and not df.empty:
    day_df = df[df["Shift"] == "Day"]

    section_title("Headcount by Company")
    col_d, col_r = st.columns(2, gap="medium")
    with col_d:
        st.plotly_chart(_donut(day_df, "Headcount by Company"), use_container_width=True)
    with col_r:
        st.plotly_chart(_role_bar(day_df, "Role Breakdown by Company"), use_container_width=True)

    section_title("Daily Headcount Trend")
    st.plotly_chart(_daily_trend(day_df, "Daily Total Manpower (Day Shift)", "#00E5FF"),
                    use_container_width=True)

    section_title("Shift Comparison")
    st.plotly_chart(_shift_compare(df), use_container_width=True)

    section_title("Data")
    with st.expander("View Full Manpower Data", expanded=False):
        st.dataframe(df.sort_values(["Date","Shift","Company","Role"]),
                     use_container_width=True, hide_index=True)
        st.download_button("Download CSV", df.to_csv(index=False).encode(),
                           "manpower_overview.csv", "text/csv")

# ──────────────────────────────────────────────────────────────
# CCECC MANPOWER
# ──────────────────────────────────────────────────────────────

elif selected == "CCECC Manpower":
    ccecc_filter = df[df["Company"].str.contains("CCECC", case=False, na=False)] if not df.empty else pd.DataFrame()
    day_ccecc    = ccecc_filter[ccecc_filter["Shift"] == "Day"] if not ccecc_filter.empty else pd.DataFrame()

    if not day_ccecc.empty:
        total_ccecc = int(day_ccecc["Count"].sum())
        avg_ccecc   = round(day_ccecc.groupby("Date")["Count"].sum().mean(), 0)
        peak_ccecc  = int(day_ccecc.groupby("Date")["Count"].sum().max())
        companies   = day_ccecc["Company"].unique()

        c1,c2,c3,c4 = st.columns(4)
        kpi_card(c1,"CCECC Total Person-Days", f"{total_ccecc:,}",  "Day shift")
        kpi_card(c2,"CCECC Companies",         str(len(companies)), "Active groups")
        kpi_card(c3,"Avg Daily",               f"{avg_ccecc:.0f}",  "persons/day")
        kpi_card(c4,"Peak Day",                str(peak_ccecc),     "Maximum headcount")

        section_title("CCECC Headcount Breakdown")
        col_d2, col_r2 = st.columns(2, gap="medium")
        with col_d2:
            st.plotly_chart(_donut(day_ccecc, "CCECC Companies"), use_container_width=True)
        with col_r2:
            st.plotly_chart(_role_bar(day_ccecc, "CCECC Role Breakdown"), use_container_width=True)

        section_title("CCECC Daily Trend")
        st.plotly_chart(_daily_trend(day_ccecc, "CCECC Daily Headcount (Day Shift)", "#00E5FF"),
                        use_container_width=True)

        section_title("CCECC Shift Comparison")
        st.plotly_chart(_shift_compare(ccecc_filter), use_container_width=True)

        section_title("CCECC Data")
        with st.expander("View CCECC Manpower Data", expanded=False):
            show = day_ccecc.sort_values(["Date","Company","Role"])
            st.dataframe(show, use_container_width=True, hide_index=True)
            st.download_button("Download CSV", show.to_csv(index=False).encode(),
                               "ccecc_manpower.csv", "text/csv")
    else:
        st.info("No CCECC manpower data for selected period.")

# ──────────────────────────────────────────────────────────────
# SUB CONTRACTORS
# ──────────────────────────────────────────────────────────────

elif selected == "Sub Contractors":
    sub_filter = df[~df["Company"].str.contains("CCECC", case=False, na=False)] if not df.empty else pd.DataFrame()
    day_sub    = sub_filter[sub_filter["Shift"] == "Day"] if not sub_filter.empty else pd.DataFrame()

    if not day_sub.empty:
        total_sub = int(day_sub["Count"].sum())
        avg_sub   = round(day_sub.groupby("Date")["Count"].sum().mean(), 0)
        peak_sub  = int(day_sub.groupby("Date")["Count"].sum().max())
        companies = day_sub["Company"].unique()

        c1,c2,c3,c4 = st.columns(4)
        kpi_card(c1,"Sub-Con Total Person-Days", f"{total_sub:,}",  "Day shift")
        kpi_card(c2,"Sub-Contractors",           str(len(companies)),"Active companies")
        kpi_card(c3,"Avg Daily",                 f"{avg_sub:.0f}",  "persons/day")
        kpi_card(c4,"Peak Day",                  str(peak_sub),     "Maximum headcount")

        section_title("Sub-Contractor Breakdown")
        col_d3, col_r3 = st.columns(2, gap="medium")
        with col_d3:
            st.plotly_chart(_donut(day_sub, "Sub-Contractor Companies"), use_container_width=True)
        with col_r3:
            st.plotly_chart(_role_bar(day_sub, "Sub-Contractor Role Breakdown"), use_container_width=True)

        # Per-company detail
        section_title("Per-Company Detail")
        sub_companies = day_sub["Company"].unique()
        comp_cols = st.columns(len(sub_companies))
        for i, company in enumerate(sub_companies):
            comp_data = day_sub[day_sub["Company"]==company]
            total_c   = int(comp_data["Count"].sum())
            avg_c     = round(comp_data.groupby("Date")["Count"].sum().mean(), 0)
            with comp_cols[i]:
                st.markdown(f"""
                <div style="background:var(--bg-card); border:1px solid var(--border-card);
                            border-radius:10px; padding:1rem; text-align:center; margin-bottom:0.8rem;">
                    <div style="font-size:0.60rem; text-transform:uppercase; letter-spacing:0.1em;
                                color:var(--text-secondary); margin-bottom:0.2rem;">{company}</div>
                    <div style="font-size:1.6rem; font-weight:700; color:var(--accent-cyan);">{total_c:,}</div>
                    <div style="font-size:0.67rem; color:var(--text-muted);">Avg {avg_c:.0f}/day</div>
                </div>
                """, unsafe_allow_html=True)
                role_data = comp_data.groupby("Role")["Count"].sum().sort_values(ascending=True).reset_index()
                fig_r = go.Figure(go.Bar(
                    x=role_data["Count"], y=role_data["Role"],
                    orientation="h", marker_color="#00E5FF", opacity=0.8,
                    text=role_data["Count"].astype(int).astype(str),
                    textposition="outside", textfont=dict(size=9),
                ))
                fig_r.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                    plot_bgcolor=ct["plot_bgcolor"],
                                    font_color=ct["font_color"],
                                    height=200,
                                    margin=dict(l=8,r=40,t=8,b=8))
                fig_r.update_xaxes(gridcolor=ct["gridcolor"], tickfont=dict(size=9))
                fig_r.update_yaxes(gridcolor=ct["gridcolor"], tickfont=dict(size=9))
                st.plotly_chart(fig_r, use_container_width=True)

        section_title("Daily Sub-Contractor Trend")
        st.plotly_chart(_daily_trend(day_sub, "Sub-Contractor Daily Headcount (Day Shift)", "#FF6B35"),
                        use_container_width=True)

        section_title("Sub-Contractor Shift Comparison")
        st.plotly_chart(_shift_compare(sub_filter), use_container_width=True)

        section_title("Sub-Contractor Data")
        with st.expander("View Sub-Contractor Data", expanded=False):
            show = day_sub.sort_values(["Date","Company","Role"])
            st.dataframe(show, use_container_width=True, hide_index=True)
            st.download_button("Download CSV", show.to_csv(index=False).encode(),
                               "subcontractor_manpower.csv", "text/csv")
    else:
        st.info("No sub-contractor data for selected period.")

st.markdown("""
<hr/>
<p style="text-align:center; color:var(--text-muted); font-size:0.65rem;">
    CCECC-HONESS-SMEDI JV &nbsp;|&nbsp; WD5B &nbsp;|&nbsp; Manpower Statistics
</p>
""", unsafe_allow_html=True)