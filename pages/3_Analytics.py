# pages/3_Analytics.py
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
    inject_css, load_all_months, build_cumulative_timeline,
    kpi_card, section_title, page_header,
    base_layout, apply_axes, get_chart_theme,
    _LEGEND, PAL, CHART_COLORS, activity_icon_buttons,
    CONTRACT_TOTAL_RM, CONTRACT_START, CONTRACT_END_PLANNED,
)
from src import cleaner

st.set_page_config(
    page_title="Analytics — CCECC",
    page_icon="📈", layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()
st.markdown(HIDE_SIDEBAR, unsafe_allow_html=True)

p  = PAL
ct = get_chart_theme()

hc1,hc2 = st.columns([8,1])
with hc1:
    page_header("📈","Analytics & Forecasting",
                "Contract trajectory · Efficiency · Month comparison · Resource calculator")
with hc2:
    st.markdown("<br>",unsafe_allow_html=True)
    if st.button("🏠 Home",key="ana_home",use_container_width=True):
        st.switch_page("app.py")

with st.spinner("Loading analytics…"):
    amd  = load_all_months()
    eff  = cleaner.compute_monthly_efficiency(amd)
    tl   = build_cumulative_timeline(amd)

months_count    = len(amd)
total_installed = sum(d["pipe_rm"] for d in amd.values())
remaining_rm    = max(CONTRACT_TOTAL_RM-total_installed,0)
avg_rate        = total_installed/months_count if months_count else 0
months_left     = round(remaining_rm/avg_rate,1) if avg_rate else 0
pct_done        = round(total_installed/CONTRACT_TOTAL_RM*100,2)
months          = list(amd.keys())

try:
    from dateutil.relativedelta import relativedelta
    proj_finish = pd.Timestamp.now()+relativedelta(
        months=int(months_left),days=int((months_left%1)*30))
except Exception:
    proj_finish = pd.NaT

months_to_end = (CONTRACT_END_PLANNED-pd.Timestamp.now()).days/30
on_track      = months_left<=months_to_end

# ── Global KPIs ─────────────────────────────────────────────
section_title("Project Forecast Summary")
g1,g2,g3,g4,g5,g6 = st.columns(6)
kpi_card(g1,"Installed",    f"{total_installed:,.1f} rm",f"{months_count} months",
         val_cls="kpi-val-green",card_cls="kpi-green")
kpi_card(g2,"Remaining",    f"{remaining_rm:,.0f} rm",  f"{pct_done:.2f}% done",
         val_cls="kpi-val-green",card_cls="kpi-green")
kpi_card(g3,"Monthly Rate", f"{avg_rate:,.0f} rm/mo",   "Current pace",
         val_cls="kpi-val-amber",card_cls="kpi-amber")
kpi_card(g4,"Months Left",  f"{months_left:.1f} mo",    "At current pace",
         val_cls="kpi-val-amber",card_cls="kpi-amber")
kpi_card(g5,"Proj. Finish",
         proj_finish.strftime("%b %Y") if pd.notna(proj_finish) else "N/A",
         f"Planned: {CONTRACT_END_PLANNED.strftime('%b %Y')}",
         val_cls="kpi-val-amber",card_cls="kpi-amber")
kpi_card(g6,"On Track",
         "✅ YES" if on_track else "⚠️ DELAYED",
         f"Need {months_to_end:.0f} mo, have {months_left:.1f} mo",
         val_cls="kpi-val-green" if on_track else "kpi-val-red",
         card_cls="kpi-green" if on_track else "kpi-card")

st.markdown("<br>",unsafe_allow_html=True)
section_title("Select Analysis")

# ── Icon buttons ─────────────────────────────────────────────
if "ana_act" not in st.session_state:
    st.session_state["ana_act"] = "Contract Progress"

ANA_ACTS = [
    ("📈","Contract Progress",   "Planned vs Actual vs Projected\nCompletion timeline","ana-c1","cp"),
    ("⚡","Efficiency Analysis", "rm/person/day\nMonth trend & change %",              "ana-c2","ea"),
    ("📅","Monthly Comparison",  "Output · Manpower · Excavation\nMonth-over-month",  "ana-c3","mc"),
    ("🧮","Resource Calculator", "Target rm → Days & Manpower\nWhat-if scenarios",    "ana-c4","rc"),
]

ACTIVITIES_ANA = [
    ("📈","Contract Progress",   "Planned vs Actual vs Projected\nCompletion timeline",  "#1A56DB"),
    ("⚡","Efficiency Analysis", "rm / person / day\nMonth trend & Δ%",                  "#059669"),
    ("📅","Monthly Comparison",  "Output · Manpower · Excavation\nMonth-over-month",     "#D97706"),
    ("🧮","Resource Calculator", "Target rm → Days & Manpower\nWhat-if scenarios",       "#7C3AED"),
]
activity_icon_buttons(ACTIVITIES_ANA, "ana_act")


selected = st.session_state["ana_act"]

def _axes_all(fig):
    for ax in fig.layout:
        if ax.startswith("xaxis") or ax.startswith("yaxis"):
            try:
                fig.layout[ax].gridcolor=ct["gridcolor"]
                fig.layout[ax].zerolinecolor=ct["zerolinecolor"]
                fig.layout[ax].tickfont=dict(size=10,color=ct["font_color"])
            except Exception: pass

# ══════════════════════════════════════════════════════════════
if selected == "Contract Progress":
    section_title("Contract Trajectory — Actual vs Planned vs Projected")
    actual_dates=[d["date"] for d in tl]
    actual_vals =[d["cumulative_rm"] for d in tl]
    fig_t=go.Figure()
    fig_t.add_trace(go.Scatter(x=[CONTRACT_START,CONTRACT_END_PLANNED],y=[0,CONTRACT_TOTAL_RM],
        name="Planned",mode="lines",line=dict(color=p["text4"],width=2,dash="dot")))
    if pd.notna(proj_finish) and avg_rate>0 and actual_dates:
        pd_,pv_=[actual_dates[-1]],[actual_vals[-1]]
        c,cv=pd_[0],pv_[0]
        while c<proj_finish and cv<CONTRACT_TOTAL_RM:
            c=c+pd.DateOffset(months=1); cv=min(cv+avg_rate,CONTRACT_TOTAL_RM)
            pd_.append(c); pv_.append(cv)
        if len(pd_)>1:
            fig_t.add_trace(go.Scatter(x=pd_,y=pv_,
                name=f"Projected (@{avg_rate:,.0f} rm/mo)",mode="lines",
                line=dict(color=p["amber"],width=2,dash="dash")))
    if actual_dates:
        fig_t.add_trace(go.Scatter(x=actual_dates,y=actual_vals,
            name="Actual Cumulative",mode="lines+markers+text",
            line=dict(color=p["blue"],width=3),
            marker=dict(size=11,color=p["blue"],line=dict(width=2,color="#fff")),
            text=[f"{v:,.0f} rm" for v in actual_vals],
            textposition="top center",textfont=dict(size=11,color=p["blue"]),
            fill="tozeroy",fillcolor="rgba(26,86,219,0.07)"))
    fig_t.add_hline(y=CONTRACT_TOTAL_RM,line_dash="dot",line_color=p["green"],line_width=1.5,
        annotation_text=f"Contract: {CONTRACT_TOTAL_RM:,.0f} rm",
        annotation_position="right",annotation_font=dict(color=p["green"],size=11))
    if pd.notna(proj_finish):
        fig_t.add_vline(x=proj_finish.timestamp()*1000,
            line_dash="dash",line_color=p["amber"],line_width=1,
            annotation_text=f"Est. Finish: {proj_finish.strftime('%b %Y')}",
            annotation_position="top right",annotation_font=dict(color=p["amber"],size=10))
    fig_t.update_layout(title_text="Contract Progress Trajectory",
        title_font=dict(size=14,color=ct["font_color"]),legend=_LEGEND,
        yaxis=dict(title="Cumulative Pipe (rm)",title_font=dict(size=10),
                   tickformat=",",gridcolor=ct["gridcolor"]),
        xaxis=dict(title="",tickformat="%b %Y",gridcolor=ct["gridcolor"]),
        **base_layout(height=440))
    apply_axes(fig_t,ct)
    st.plotly_chart(fig_t,use_container_width=True)

    section_title("Cumulative Progress Bar")
    fig_b=go.Figure()
    fig_b.add_trace(go.Bar(name="Installed",x=[total_installed],y=["Progress"],
        orientation="h",marker_color=p["blue"],opacity=.9,
        text=f"{total_installed:,.1f} rm  ({pct_done:.2f}%)",
        textposition="inside",textfont=dict(size=12,color="#fff")))
    fig_b.add_trace(go.Bar(name="Remaining",x=[remaining_rm],y=["Progress"],
        orientation="h",marker_color=p["border"],
        text=f"{remaining_rm:,.0f} rm remaining",
        textposition="inside",textfont=dict(size=11,color=p["text3"])))
    fig_b.add_vline(x=CONTRACT_TOTAL_RM,line_dash="dot",line_color=p["green"],line_width=2,
        annotation_text=f"Total: {CONTRACT_TOTAL_RM:,.0f} rm",
        annotation_font=dict(color=p["green"],size=11),annotation_position="top right")
    fig_b.update_layout(barmode="stack",
        legend=dict(orientation="h",yanchor="bottom",y=1.05,xanchor="left",x=0,
                    bgcolor="rgba(255,255,255,.9)",bordercolor=p["border_s"],
                    borderwidth=1,font=dict(size=11)),
        yaxis=dict(showticklabels=False),
        xaxis=dict(title="Running Metres (rm)",tickformat=",",gridcolor=ct["gridcolor"]),
        **base_layout(height=130))
    st.plotly_chart(fig_b,use_container_width=True)

    with st.expander("Trajectory data",expanded=False):
        tdf=pd.DataFrame(tl)
        tdf["remaining_rm"]=(CONTRACT_TOTAL_RM-tdf["cumulative_rm"])
        tdf["completion_pct"]=(tdf["cumulative_rm"]/CONTRACT_TOTAL_RM*100).round(2)
        st.dataframe(tdf,use_container_width=True,hide_index=True)

elif selected == "Efficiency Analysis":
    section_title("Efficiency: rm Installed per Person per Day")
    if not eff.empty:
        disp=eff[["Month","Pipe_rm","Active_Days","Avg_Manpower",
                   "RM_per_Person_Day","Efficiency_Change_Pct","Efficiency_Trend"]].copy()
        disp.columns=["Month","Pipe (rm)","Active Days","Avg Manpower",
                       "rm/Person/Day","Efficiency Δ%","Trend"]
        for c,r in [("Pipe (rm)",1),("rm/Person/Day",4),("Efficiency Δ%",1)]:
            disp[c]=disp[c].round(r)
        st.dataframe(disp,use_container_width=True,hide_index=True)
        st.markdown("<br>",unsafe_allow_html=True)
        mo=eff["Month"].tolist()
        eff_clrs=[p["green"] if t=="Improved" else p["red"] if t=="Declined" else p["amber"]
                  for t in eff.get("Efficiency_Trend",["—"]*len(mo))]
        fig_e=make_subplots(rows=2,cols=2,
            subplot_titles=("Monthly Output & Manpower","Efficiency rm/Person/Day",
                            "Month-over-Month Change (%)","Pipe by Month"),
            vertical_spacing=.16,horizontal_spacing=.10)
        bar_c=[CHART_COLORS[i%len(CHART_COLORS)] for i in range(len(eff))]
        fig_e.add_trace(go.Bar(x=mo,y=eff["Pipe_rm"],name="Pipe (rm)",
            marker_color=bar_c,opacity=.82,
            text=eff["Pipe_rm"].round(0).astype(int).astype(str),
            textposition="outside",textfont=dict(size=9)),row=1,col=1)
        fig_e.add_trace(go.Scatter(x=mo,y=eff["Avg_Manpower"],name="Avg Manpower",
            mode="lines+markers",line=dict(color=p["amber"],width=2),
            marker=dict(size=7,symbol="diamond")),row=1,col=1)
        fig_e.add_trace(go.Bar(x=mo,y=eff["RM_per_Person_Day"],name="rm/Person/Day",
            marker_color=eff_clrs,opacity=.85,
            text=eff["RM_per_Person_Day"].round(3).astype(str),
            textposition="outside",textfont=dict(size=9),showlegend=False),row=1,col=2)
        for _,row in eff.iterrows():
            chg=row.get("Efficiency_Change_Pct",0)
            if pd.notna(chg) and chg!=0:
                fig_e.add_annotation(x=row["Month"],y=row["RM_per_Person_Day"]*1.08,
                    text=f"{'+'if chg>0 else''}{chg:.1f}%",showarrow=False,
                    font=dict(size=9,color=p["green"] if chg>0 else p["red"]),row=1,col=2)
        for ck,dlbl,dcl in [("Pipe_Change_Pct","Pipe",p["blue"]),
                              ("Manpower_Change_Pct","Manpower",p["amber"]),
                              ("Efficiency_Change_Pct","Efficiency",p["green"])]:
            if ck in eff.columns:
                fig_e.add_trace(go.Bar(x=mo,y=eff[ck].fillna(0),
                    name=dlbl,marker_color=dcl,opacity=.75),row=2,col=1)
        fig_e.add_hline(y=0,line_color=p["border"],line_width=1,row=2,col=1)
        df_s=eff.sort_values("Pipe_rm",ascending=True)
        fig_e.add_trace(go.Bar(y=df_s["Month"],x=df_s["Pipe_rm"],orientation="h",
            name="Pipe rm",
            marker_color=[p["blue"] if i==len(df_s)-1 else p["blue_l"]
                          for i in range(len(df_s))],
            opacity=.85,text=df_s["Pipe_rm"].round(0).astype(int).astype(str),
            textposition="outside",textfont=dict(size=10),showlegend=False),row=2,col=2)
        fig_e.update_layout(barmode="group",legend=_LEGEND,**base_layout(height=640))
        fig_e.update_annotations(font=dict(size=12,color=ct["font_color"]))
        _axes_all(fig_e)
        st.plotly_chart(fig_e,use_container_width=True)
    with st.expander("Full efficiency table",expanded=False):
        st.dataframe(eff,use_container_width=True,hide_index=True)
        st.download_button("⬇ Download",eff.to_csv(index=False).encode(),"efficiency.csv","text/csv")

elif selected == "Monthly Comparison":
    section_title("Month-over-Month Comparison")
    if months:
        rows=[]
        for i,lbl in enumerate(months):
            d=amd[lbl]; prev=amd[months[i-1]] if i>0 else None
            def _chg(c,pv): return round((c-pv)/pv*100,1) if pv and pv>0 else None
            rows.append({"Month":lbl,
                "Pipe (rm)":round(d["pipe_rm"],1),"Pipe Δ%":_chg(d["pipe_rm"],prev["pipe_rm"] if prev else None),
                "Avg Manpower":round(d["avg_manpower"],1),"Manpower Δ%":_chg(d["avg_manpower"],prev["avg_manpower"] if prev else None),
                "Excav (rm)":round(d["excav_rm"],1),"Excav Δ%":_chg(d["excav_rm"],prev["excav_rm"] if prev else None),
                "Active Days":d["active_days"],"Service Pits":int(d.get("pits",0))})
        comp=pd.DataFrame(rows)
        st.dataframe(comp,use_container_width=True,hide_index=True)
        st.markdown("<br>",unsafe_allow_html=True)
        mets=[("pipe_rm","Pipe (rm)"),("avg_manpower","Avg Manpower"),("excav_rm","Excav (rm)")]
        fig_c=make_subplots(rows=1,cols=3,subplot_titles=[m[1] for m in mets],horizontal_spacing=.10)
        for ci,(key,mlbl) in enumerate(mets,start=1):
            vals=[amd[m][key] for m in months]
            fig_c.add_trace(go.Bar(x=months,y=vals,name=mlbl,
                marker_color=[p["blue"],p["orange"],p["green"]][ci-1],opacity=.85,
                text=[f"{v:,.1f}" for v in vals],
                textposition="outside",textfont=dict(size=10),showlegend=False),row=1,col=ci)
        fig_c.update_layout(legend=_LEGEND,**base_layout(height=340))
        _axes_all(fig_c)
        fig_c.update_annotations(font=dict(size=12,color=ct["font_color"]))
        st.plotly_chart(fig_c,use_container_width=True)
        if len(months)>1:
            section_title("Month-over-Month Change (%)")
            fig_d=go.Figure()
            for ck,dlbl,dcl in [("Pipe Δ%","Pipe",p["blue"]),("Manpower Δ%","Manpower",p["amber"]),("Excav Δ%","Excavation",p["orange"])]:
                if ck in comp.columns:
                    fig_d.add_trace(go.Bar(x=comp["Month"],y=comp[ck].fillna(0),name=dlbl,marker_color=dcl,opacity=.8))
            fig_d.add_hline(y=0,line_color=p["border"],line_width=1)
            fig_d.update_layout(barmode="group",legend=_LEGEND,**base_layout(height=300))
            fig_d.update_yaxes(title_text="Change (%)",title_font=dict(size=10))
            apply_axes(fig_d,ct)
            st.plotly_chart(fig_d,use_container_width=True)
        with st.expander("Full table",expanded=False):
            st.dataframe(comp,use_container_width=True,hide_index=True)
            st.download_button("⬇ Download",comp.to_csv(index=False).encode(),"comparison.csv","text/csv")

elif selected == "Resource Calculator":
    section_title("Resource Requirements Calculator")
    avg_eff=float(eff["RM_per_Person_Day"].dropna().mean()) if not eff.empty else 0
    last_mp=float(eff["Avg_Manpower"].iloc[-1]) if not eff.empty else 0
    ic1,rc1=st.columns([1,2],gap="large")
    with ic1:
        target_rm=st.number_input("Target Pipe (rm)",min_value=1.0,
            max_value=float(CONTRACT_TOTAL_RM),value=min(1000.0,remaining_rm),step=100.0)
        mp_input=st.number_input("Daily Manpower (persons)",min_value=1,max_value=500,
            value=max(int(last_mp),10),step=5)
        wd_pm=st.slider("Working Days / Month",15,31,22)
        st.markdown(f"""
        <div style="background:{p['blue_ll']};border:1px solid {p['border_s']};
                    border-radius:10px;padding:.8rem 1rem;margin-top:.8rem;">
            <p style="font-size:.75rem;font-weight:700;color:{p['blue']};margin:0 0 .3rem 0;">
                Current Productivity Rate</p>
            <p style="font-size:.875rem;color:{p['text2']};margin:0;">
                {avg_eff:.4f} rm / person / day<br>
                Based on {months_count} months of data</p>
        </div>""",unsafe_allow_html=True)
    with rc1:
        if avg_eff>0 and mp_input>0:
            days_n=target_rm/(avg_eff*mp_input); mo_n=days_n/wd_pm
            daily_o=avg_eff*mp_input; mp_1mo=target_rm/(avg_eff*wd_pm)
            r1,r2,r3,r4=st.columns(4)
            kpi_card(r1,"Days Required",f"{days_n:.0f} days",f"@ {mp_input} persons/day",
                     val_cls="kpi-val-amber",card_cls="kpi-amber")
            kpi_card(r2,"Months Required",f"{mo_n:.1f} mo",f"{wd_pm} days/mo",
                     val_cls="kpi-val-amber",card_cls="kpi-amber")
            kpi_card(r3,"Daily Output",f"{daily_o:.1f} rm/day",f"{avg_eff:.4f} rm/p/day",
                     val_cls="kpi-val-amber",card_cls="kpi-amber")
            kpi_card(r4,"MP for 1 Month",f"{mp_1mo:.0f} persons",
                     f"to do {target_rm:,.0f} rm",
                     val_cls="kpi-val-amber",card_cls="kpi-amber")
            st.markdown("<br>",unsafe_allow_html=True)
            mp_r=list(range(5,301,5))
            days_r=[target_rm/(avg_eff*m) if avg_eff>0 else 0 for m in mp_r]
            mo_r=[d/wd_pm for d in days_r]
            fig_s=make_subplots(specs=[[{"secondary_y":True}]])
            fig_s.add_trace(go.Scatter(x=mp_r,y=days_r,name="Days Required",mode="lines",
                line=dict(color=p["blue"],width=2.5),fill="tozeroy",
                fillcolor="rgba(26,86,219,0.07)"),secondary_y=False)
            fig_s.add_trace(go.Scatter(x=mp_r,y=mo_r,name="Months Required",mode="lines",
                line=dict(color=p["amber"],width=2,dash="dash")),secondary_y=True)
            fig_s.add_trace(go.Scatter(x=[mp_input],y=[days_n],name="Your Selection",
                mode="markers",marker=dict(size=14,color=p["green"],symbol="star",
                    line=dict(width=2,color="#fff"))),secondary_y=False)
            fig_s.update_layout(title_text=f"Days vs Manpower for {target_rm:,.0f} rm",
                title_font=dict(size=13,color=ct["font_color"]),
                legend=_LEGEND,**base_layout(height=340))
            fig_s.update_yaxes(title_text="Days",secondary_y=False,
                gridcolor=ct["gridcolor"],title_font=dict(size=10))
            fig_s.update_yaxes(title_text="Months",secondary_y=True,
                showgrid=False,title_font=dict(size=10))
            fig_s.update_xaxes(title_text="Daily Manpower",gridcolor=ct["gridcolor"])
            apply_axes(fig_s,ct)
            st.plotly_chart(fig_s,use_container_width=True)
            section_title("What-If Scenarios")
            scen=[{"Daily Manpower":m,"Days Required":round(target_rm/(avg_eff*m),0),
                   "Months Required":round(target_rm/(avg_eff*m)/wd_pm,1),
                   "Daily Output (rm)":round(avg_eff*m,1)}
                  for m in [20,30,40,50,75,100,150,200]]
            st.dataframe(pd.DataFrame(scen),use_container_width=True,hide_index=True)
        else:
            st.warning("Not enough productivity data yet.")

st.markdown(f"""
<hr style="border:none;border-top:1px solid {p['border_s']};margin:2rem 0 .5rem 0;">
<p style="text-align:center;color:{p['text4']};font-size:.6875rem;">
    CCECC-HONESS-SMEDI JV &nbsp;·&nbsp; WD5B &nbsp;·&nbsp; Analytics & Forecasting
</p>""",unsafe_allow_html=True)