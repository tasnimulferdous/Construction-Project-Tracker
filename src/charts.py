# src/charts.py
from __future__ import annotations
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

_FONT     = "Segoe UI, Arial, sans-serif"
_COLORS   = {
    "cyan"  : "#00E5FF",
    "coral" : "#FF6B35",
    "lime"  : "#A8FF3E",
    "violet": "#C77DFF",
    "amber" : "#FFD166",
    "red"   : "#FF4560",
    "grey"  : "#4B5A78",
    "teal"  : "#00BFA5",
    "pink"  : "#FF4081",
    "green" : "#00C853",
}
_COLORWAY = [
    "#00E5FF", "#FF6B35", "#A8FF3E",
    "#C77DFF", "#FFD166", "#FF4560",
    "#00BFA5", "#FF4081", "#4B5A78",
]


def _theme(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(
        title_text    = title,
        title_font    = dict(family=_FONT, size=14, color="#A0A8C0"),
        font_family   = _FONT,
        font_color    = "#D1D5E8",
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(15,17,26,0.55)",
        colorway      = _COLORWAY,
        hovermode     = "x unified",
        margin        = dict(l=16, r=16, t=50, b=16),
        legend        = dict(
            bgcolor     = "rgba(0,0,0,0)",
            bordercolor = "rgba(255,255,255,0.08)",
            borderwidth = 1,
            font        = dict(size=11),
        ),
    )
    fig.update_xaxes(gridcolor="#1E2A3A", zerolinecolor="#2A3A4A",
                     showline=False, tickfont=dict(size=10))
    fig.update_yaxes(gridcolor="#1E2A3A", zerolinecolor="#2A3A4A",
                     showline=False, tickfont=dict(size=10))
    return fig


def _empty(title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text="No data for selected period", showarrow=False,
                       xref="paper", yref="paper", x=0.5, y=0.5,
                       font=dict(size=13, color="#4B5A78"))
    return _theme(fig, title)


# ──────────────────────────────────────────────────────────────
# 1. Contract Trajectory Line Chart  (NEW)
# ──────────────────────────────────────────────────────────────

def contract_trajectory_chart(
    cumulative_by_month: list[dict],
    contract_total: float,
    contract_start: pd.Timestamp,
    contract_end_planned: pd.Timestamp,
    projected_finish: pd.Timestamp,
    avg_monthly_rate: float,
) -> go.Figure:
    """
    Line chart showing:
      - Planned trajectory: straight line from 0 → contract_total
      - Actual cumulative: month-by-month installed
      - Projected trajectory: extends actual pace to projected finish
      - Contract target line: horizontal at contract_total

    Parameters
    ----------
    cumulative_by_month : list of dicts
        Each dict: {"date": pd.Timestamp, "cumulative_rm": float, "label": str}
    contract_total      : float — 201,730.54 rm
    contract_start      : project start date
    contract_end_planned: planned contract completion date
    projected_finish    : projected finish at current pace
    avg_monthly_rate    : rm per month at current pace
    """
    if not cumulative_by_month:
        return _empty("Contract Progress Trajectory")

    actual_dates = [d["date"]          for d in cumulative_by_month]
    actual_vals  = [d["cumulative_rm"] for d in cumulative_by_month]
    labels       = [d["label"]         for d in cumulative_by_month]

    # Planned line: straight from contract_start (0) to contract_end (total)
    planned_dates = [contract_start, contract_end_planned]
    planned_vals  = [0, contract_total]

    # Projected line: from last actual point to projected finish
    last_actual_date = actual_dates[-1]
    last_actual_val  = actual_vals[-1]
    proj_dates = [last_actual_date]
    proj_vals  = [last_actual_val]

    if pd.notna(projected_finish) and avg_monthly_rate > 0:
        # Build monthly projection points
        current = last_actual_date
        current_val = last_actual_val
        while current < projected_finish and current_val < contract_total:
            current = current + pd.DateOffset(months=1)
            current_val = min(current_val + avg_monthly_rate, contract_total)
            proj_dates.append(current)
            proj_vals.append(current_val)

    fig = go.Figure()

    # ── Planned line ──────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=planned_dates, y=planned_vals,
        name="Planned Trajectory",
        mode="lines",
        line=dict(color=_COLORS["grey"], width=2, dash="dot"),
        hovertemplate="Planned: %{y:,.0f} rm<extra></extra>",
    ))

    # ── Projected line ────────────────────────────────────────
    if len(proj_dates) > 1:
        fig.add_trace(go.Scatter(
            x=proj_dates, y=proj_vals,
            name=f"Projected (@ {avg_monthly_rate:,.0f} rm/mo)",
            mode="lines",
            line=dict(color=_COLORS["amber"], width=2, dash="dash"),
            hovertemplate="Projected: %{y:,.0f} rm<extra></extra>",
        ))

    # ── Actual cumulative ─────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=actual_dates, y=actual_vals,
        name="Actual Cumulative",
        mode="lines+markers+text",
        line=dict(color=_COLORS["cyan"], width=3),
        marker=dict(size=9, symbol="circle",
                    color=_COLORS["cyan"],
                    line=dict(width=2, color="#fff")),
        text=[f"{v:,.0f}" for v in actual_vals],
        textposition="top center",
        textfont=dict(size=10, color=_COLORS["cyan"]),
        fill="tozeroy",
        fillcolor="rgba(0,229,255,0.06)",
        hovertemplate="%{text} rm<extra></extra>",
    ))

    # ── Contract total horizontal line ────────────────────────
    fig.add_hline(
        y=contract_total,
        line_dash="dot",
        line_color=_COLORS["lime"],
        line_width=1.5,
        annotation_text=f"Contract Total: {contract_total:,.0f} rm",
        annotation_position="right",
        annotation_font=dict(color=_COLORS["lime"], size=11),
    )

    # ── Projected finish annotation ───────────────────────────
    if pd.notna(projected_finish):
        fig.add_vline(
            x=projected_finish.timestamp() * 1000,
            line_dash="dash",
            line_color=_COLORS["amber"],
            line_width=1,
            annotation_text=f"Est. Finish: {projected_finish.strftime('%b %Y')}",
            annotation_position="top right",
            annotation_font=dict(color=_COLORS["amber"], size=10),
        )

    fig.update_layout(
        yaxis=dict(
            title="Cumulative Pipe Installed (rm)",
            title_font=dict(size=11),
            tickformat=",",
        ),
        xaxis=dict(title="", tickformat="%b %Y"),
        height=420,
    )
    return _theme(fig, "Contract Progress Trajectory — Actual vs Planned vs Projected")


# ──────────────────────────────────────────────────────────────
# 2. Monthly Efficiency Analysis Chart  (NEW)
# ──────────────────────────────────────────────────────────────

def monthly_efficiency_chart(efficiency_df: pd.DataFrame) -> go.Figure:
    """
    4-panel analysis chart showing month-by-month:
      Top-left    : Pipe installed per month (bar) vs manpower (line)
      Top-right   : Efficiency metric (rm per person per day) with trend
      Bottom-left : Month-over-month change % (pipe, manpower, efficiency)
      Bottom-right: Excavation vs Pipe ratio per month
    """
    if efficiency_df.empty or len(efficiency_df) < 1:
        return _empty("Monthly Efficiency Analysis")

    df = efficiency_df.copy()

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Monthly Output & Manpower",
            "Efficiency: rm per Person per Day",
            "Month-over-Month Change (%)",
            "Pipe Installed by Month",
        ),
        vertical_spacing=0.16,
        horizontal_spacing=0.10,
    )

    months = df["Month"].tolist()
    colors_bar = [_COLORS["cyan"], _COLORS["coral"], _COLORS["lime"],
                  _COLORS["violet"], _COLORS["amber"]]

    # ── Panel 1: Pipe installed bars + manpower line ──────────
    bar_colors = [colors_bar[i % len(colors_bar)] for i in range(len(df))]
    fig.add_trace(go.Bar(
        x=months, y=df["Pipe_rm"],
        name="Pipe Installed (rm)",
        marker_color=bar_colors,
        opacity=0.82,
        text=df["Pipe_rm"].round(0).astype(int).astype(str) + " rm",
        textposition="outside",
        textfont=dict(size=9),
        showlegend=True,
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=months, y=df["Avg_Manpower"],
        name="Avg Daily Manpower",
        mode="lines+markers",
        line=dict(color=_COLORS["amber"], width=2),
        marker=dict(size=7, symbol="diamond"),
        yaxis="y2",
        showlegend=True,
    ), row=1, col=1)

    fig.update_yaxes(title_text="Pipe (rm)", row=1, col=1, title_font=dict(size=10))

    # ── Panel 2: Efficiency metric bar with trend colour ──────
    eff_colors = []
    for _, row in df.iterrows():
        trend = row.get("Efficiency_Trend", "—")
        if trend == "Improved":
            eff_colors.append(_COLORS["lime"])
        elif trend == "Declined":
            eff_colors.append(_COLORS["red"])
        else:
            eff_colors.append(_COLORS["amber"])

    fig.add_trace(go.Bar(
        x=months, y=df["RM_per_Person_Day"],
        name="rm / Person / Day",
        marker_color=eff_colors,
        opacity=0.85,
        text=df["RM_per_Person_Day"].round(3).astype(str),
        textposition="outside",
        textfont=dict(size=9),
        showlegend=False,
    ), row=1, col=2)

    # Trend annotation on each bar
    for i, (_, row) in enumerate(df.iterrows()):
        trend = row.get("Efficiency_Trend", "—")
        chg   = row.get("Efficiency_Change_Pct", 0)
        if pd.notna(chg) and chg != 0:
            sign = "+" if chg > 0 else ""
            fig.add_annotation(
                x=row["Month"],
                y=row["RM_per_Person_Day"] * 1.08,
                text=f"{sign}{chg:.1f}%",
                showarrow=False,
                font=dict(size=9,
                          color=_COLORS["lime"] if chg > 0 else _COLORS["red"]),
                row=1, col=2,
            )

    fig.update_yaxes(title_text="rm / Person / Day", row=1, col=2, title_font=dict(size=10))

    # ── Panel 3: Month-over-month % change ────────────────────
    change_metrics = [
        ("Pipe_Change_Pct",       "Pipe Output",  _COLORS["cyan"]),
        ("Manpower_Change_Pct",   "Manpower",     _COLORS["amber"]),
        ("Efficiency_Change_Pct", "Efficiency",   _COLORS["lime"]),
    ]
    for col_name, label, color in change_metrics:
        if col_name in df.columns:
            fig.add_trace(go.Bar(
                x=months,
                y=df[col_name].fillna(0),
                name=label,
                marker_color=color,
                opacity=0.75,
                showlegend=True,
            ), row=2, col=1)

    fig.add_hline(y=0, line_color="rgba(255,255,255,0.2)",
                  line_width=1, row=2, col=1)
    fig.update_yaxes(title_text="Change (%)", row=2, col=1, title_font=dict(size=10))
    fig.update_layout(barmode="group")

    # ── Panel 4: Pipe installed per month as horizontal bars ──
    df_sorted = df.sort_values("Pipe_rm", ascending=True)
    fig.add_trace(go.Bar(
        y=df_sorted["Month"],
        x=df_sorted["Pipe_rm"],
        orientation="h",
        name="Pipe rm",
        marker_color=[_COLORS["cyan"] if i == len(df_sorted)-1
                      else _COLORS["violet"]
                      for i in range(len(df_sorted))],
        opacity=0.85,
        text=df_sorted["Pipe_rm"].round(0).astype(int).astype(str) + " rm",
        textposition="outside",
        textfont=dict(size=10),
        showlegend=False,
    ), row=2, col=2)

    fig.update_xaxes(title_text="Pipe Installed (rm)", row=2, col=2, title_font=dict(size=10))

    # ── Global layout ─────────────────────────────────────────
    fig.update_layout(
        height=640,
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor ="rgba(15,17,26,0.55)",
        font_family  = _FONT,
        font_color   = "#D1D5E8",
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(255,255,255,0.08)",
            borderwidth=1,
            font=dict(size=10),
            orientation="h",
            yanchor="bottom", y=-0.18,
            xanchor="center", x=0.5,
        ),
        margin=dict(l=16, r=16, t=60, b=80),
    )
    fig.update_annotations(font=dict(size=12, color="#A0A8C0"))
    for ax in fig.layout:
        if ax.startswith("xaxis") or ax.startswith("yaxis"):
            fig.layout[ax].gridcolor     = "#1E2A3A"
            fig.layout[ax].zerolinecolor = "#2A3A4A"

    return fig


# ──────────────────────────────────────────────────────────────
# 3. Contract Progress Bar
# ──────────────────────────────────────────────────────────────

def contract_progress_chart(
    pipe_upto_feb: float,
    pipe_this_month: float,
    contract_total: float,
) -> go.Figure:
    completed_total = pipe_upto_feb + pipe_this_month
    remaining       = max(contract_total - completed_total, 0)
    pct_done        = round(completed_total / contract_total * 100, 2) if contract_total else 0

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Completed (Upto Feb)",
        x=[pipe_upto_feb], y=["Contract Progress"],
        orientation="h", marker_color=_COLORS["cyan"], opacity=0.9,
        text=f"{pipe_upto_feb:,.1f} rm", textposition="inside",
        textfont=dict(size=11, color="#000"),
    ))
    fig.add_trace(go.Bar(
        name="Completed (This Month)",
        x=[pipe_this_month], y=["Contract Progress"],
        orientation="h", marker_color=_COLORS["lime"], opacity=0.9,
        text=f"{pipe_this_month:,.1f} rm", textposition="inside",
        textfont=dict(size=11, color="#000"),
    ))
    fig.add_trace(go.Bar(
        name="Remaining",
        x=[remaining], y=["Contract Progress"],
        orientation="h", marker_color="rgba(75,90,120,0.35)",
        text=f"{remaining:,.1f} rm remaining", textposition="inside",
        textfont=dict(size=11, color="#A0A8C0"),
    ))
    fig.add_vline(
        x=contract_total, line_dash="dot",
        line_color=_COLORS["amber"], line_width=2,
        annotation_text=f"Contract Total: {contract_total:,.0f} rm",
        annotation_position="top right",
        annotation_font=dict(color=_COLORS["amber"], size=11),
    )
    fig.update_layout(
        barmode="stack", height=130,
        xaxis=dict(title=f"Running Metres (rm)   |   Overall: {pct_done}% complete",
                   title_font=dict(size=11, color="#A0A8C0"), tickformat=","),
        yaxis=dict(showticklabels=False),
        margin=dict(l=16, r=16, t=48, b=32),
        legend=dict(orientation="h", yanchor="bottom", y=1.1,
                    xanchor="left", x=0),
    )
    _theme(fig, "Overall Contract Progress — Pipe Installation")
    return fig


# ──────────────────────────────────────────────────────────────
# 4. Daily Progress Bar Chart
# ──────────────────────────────────────────────────────────────

def daily_progress_bar_chart(
    summary_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
    activity_filter: str = "Pipe",
) -> go.Figure:
    if summary_df.empty:
        return _empty("Daily Progress")

    mask = (
        summary_df["Activity"].str.contains(activity_filter, case=False, na=False)
        & (summary_df["Date"] >= date_start)
        & (summary_df["Date"] <= date_end)
    )
    df = summary_df.loc[mask].copy()
    if df.empty:
        return _empty(f"Daily Progress — {activity_filter}")

    pivot = (
        df.groupby(["Date", "SD"])["Daily_Qty"]
        .sum().unstack(fill_value=0)
        .reset_index().sort_values("Date")
    )
    sd_cols = [c for c in pivot.columns if c != "Date"]
    pivot["Daily_Total"] = pivot[sd_cols].sum(axis=1)

    colors = [_COLORS["cyan"], _COLORS["coral"], _COLORS["lime"], _COLORS["violet"]]
    fig    = go.Figure()

    for i, sd in enumerate(sd_cols):
        fig.add_trace(go.Bar(
            x=pivot["Date"], y=pivot[sd],
            name=f"SD-{sd}",
            marker_color=colors[i % len(colors)],
            opacity=0.82,
        ))

    fig.add_trace(go.Scatter(
        x=pivot["Date"], y=pivot["Daily_Total"],
        name="Daily Total",
        mode="lines+markers+text",
        line=dict(color=_COLORS["amber"], width=2),
        marker=dict(size=6),
        text=pivot["Daily_Total"].round(1).astype(str),
        textposition="top center",
        textfont=dict(size=9, color=_COLORS["amber"]),
    ))

    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Quantity (rm)", title_font=dict(size=11))
    return _theme(fig, f"Daily Progress — {activity_filter} (rm per day)")


# ──────────────────────────────────────────────────────────────
# 5. Daily Pipe Installation by SD Zone
# ──────────────────────────────────────────────────────────────

def daily_pipe_installation_chart(
    summary_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
) -> go.Figure:
    if summary_df.empty:
        return _empty("Daily Pipe Installation")

    mask = (
        summary_df["Activity"].str.contains("Pipe", case=False, na=False)
        & (summary_df["Date"] >= date_start)
        & (summary_df["Date"] <= date_end)
    )
    df = summary_df.loc[mask].copy()
    if df.empty:
        return _empty("Daily Pipe Installation")

    pivot = (
        df.groupby(["Date", "SD"])["Daily_Qty"]
        .sum().unstack(fill_value=0)
        .reset_index().sort_values("Date")
    )
    sd_cols = [c for c in pivot.columns if c != "Date"]
    pivot["Total"]      = pivot[sd_cols].sum(axis=1)
    pivot["Cumulative"] = pivot["Total"].cumsum()

    fig    = make_subplots(specs=[[{"secondary_y": True}]])
    colors = [_COLORS["cyan"], _COLORS["coral"], _COLORS["lime"], _COLORS["violet"]]

    for i, sd in enumerate(sd_cols):
        fig.add_trace(
            go.Bar(x=pivot["Date"], y=pivot[sd], name=f"SD-{sd}",
                   marker_color=colors[i % len(colors)], opacity=0.82),
            secondary_y=False)

    fig.add_trace(
        go.Scatter(x=pivot["Date"], y=pivot["Cumulative"],
                   name="Cumulative (rm)", mode="lines+markers",
                   line=dict(color=_COLORS["amber"], width=2.5),
                   marker=dict(size=5)),
        secondary_y=True)

    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Daily (rm)",      secondary_y=False, title_font=dict(size=11))
    fig.update_yaxes(title_text="Cumulative (rm)", secondary_y=True,  title_font=dict(size=11),
                     showgrid=False)
    return _theme(fig, "Daily Pipe Installation by SD Zone")


# ──────────────────────────────────────────────────────────────
# 6. Burn Rate
# ──────────────────────────────────────────────────────────────

def burn_rate_chart(
    summary_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
    activity_filter: str = "Pipe",
) -> go.Figure:
    if summary_df.empty:
        return _empty("Burn Rate")

    mask = (
        summary_df["Activity"].str.contains(activity_filter, case=False, na=False)
        & (summary_df["Date"] >= date_start)
        & (summary_df["Date"] <= date_end)
    )
    df = summary_df.loc[mask].copy()
    if df.empty:
        return _empty("Burn Rate")

    daily = df.groupby("Date")["Daily_Qty"].sum().reset_index().sort_values("Date")
    daily["Cumulative_Actual"] = daily["Daily_Qty"].cumsum()

    monthly_target = float(
        summary_df[
            summary_df["Activity"].str.contains(activity_filter, case=False, na=False)
        ].drop_duplicates(subset=["Activity", "SD", "Pipe_Dia"])["Qty_Mar"].sum()
    )

    daily_planned_rate = monthly_target / 31
    planned_dates      = pd.date_range(date_start, date_end, freq="D")
    planned_series     = pd.DataFrame({
        "Date"              : planned_dates,
        "Cumulative_Planned": [(i + 1) * daily_planned_rate for i in range(len(planned_dates))],
    })

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=planned_series["Date"], y=planned_series["Cumulative_Planned"],
        name="Planned (linear)", mode="lines",
        line=dict(color=_COLORS["grey"], width=2, dash="dot"),
    ))
    fig.add_trace(go.Scatter(
        x=daily["Date"], y=daily["Cumulative_Actual"],
        name="Actual (cumulative)", mode="lines+markers",
        line=dict(color=_COLORS["cyan"], width=2.5),
        marker=dict(size=6),
        fill="tozeroy", fillcolor="rgba(0,229,255,0.08)",
    ))
    fig.update_yaxes(title_text="Running metres (rm)", title_font=dict(size=11))
    return _theme(fig, f"Burn Rate — {activity_filter} Installation (Cumulative)")


# ──────────────────────────────────────────────────────────────
# 7. Activity Breakdown
# ──────────────────────────────────────────────────────────────

def activity_breakdown_chart(
    summary_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
) -> go.Figure:
    if summary_df.empty:
        return _empty("Activity Breakdown")

    mask = (
        (summary_df["Date"] >= date_start)
        & (summary_df["Date"] <= date_end)
    )
    df = summary_df.loc[mask].copy()
    if df.empty:
        return _empty("Activity Breakdown")

    agg = (
        df.groupby(["Activity", "SD", "Pipe_Dia"])
        .agg(Achieved=("Daily_Qty", "sum"), Target=("Qty_Mar", "first"))
        .reset_index()
    )
    agg["Label"] = (agg["Activity"] + " SD-" + agg["SD"] + " " + agg["Pipe_Dia"])
    agg["Label"] = agg["Label"].str.replace(r"\s+", " ", regex=True).str.strip()
    agg = agg.sort_values("Achieved", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=agg["Label"], x=agg["Achieved"],
        name="Achieved", orientation="h",
        marker_color=_COLORS["cyan"], opacity=0.85,
        text=agg["Achieved"].round(1).astype(str),
        textposition="outside", textfont=dict(size=9),
    ))
    fig.add_trace(go.Scatter(
        y=agg["Label"], x=agg["Target"],
        name="Monthly Target", mode="markers",
        marker=dict(symbol="line-ns", size=14,
                    color=_COLORS["amber"],
                    line=dict(width=2, color=_COLORS["amber"])),
    ))
    fig.update_layout(barmode="overlay", height=max(300, len(agg) * 36))
    fig.update_xaxes(title_text="Quantity (rm / Pcs)")
    return _theme(fig, "Work Activity — Period Totals vs Monthly Target")


# ──────────────────────────────────────────────────────────────
# 8. Vehicle Utilisation
# ──────────────────────────────────────────────────────────────

def vehicle_utilisation_chart(
    vehicle_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
) -> go.Figure:
    if vehicle_df.empty:
        return _empty("Vehicle Utilisation")

    mask = (
        (vehicle_df["Date"] >= date_start)
        & (vehicle_df["Date"] <= date_end)
    )
    df = vehicle_df.loc[mask].copy()
    if df.empty:
        return _empty("Vehicle Utilisation")

    pivot = (
        df.groupby(["Date", "Vehicle"])["Hours"]
        .sum().unstack(fill_value=0)
        .reset_index().sort_values("Date")
    )
    fig = go.Figure()
    for i, veh in enumerate([c for c in pivot.columns if c != "Date"]):
        fig.add_trace(go.Bar(
            x=pivot["Date"], y=pivot[veh], name=veh,
            marker_color=_COLORWAY[i % len(_COLORWAY)], opacity=0.85,
        ))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Hours", title_font=dict(size=11))
    return _theme(fig, "Equipment / Vehicle Utilisation (hrs)")


# ──────────────────────────────────────────────────────────────
# 9. Manpower Summary
# ──────────────────────────────────────────────────────────────

def manpower_summary_chart(
    manpower_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
) -> go.Figure:
    if manpower_df.empty:
        return _empty("Manpower Summary")

    mask = (
        (manpower_df["Date"] >= date_start)
        & (manpower_df["Date"] <= date_end)
        & (manpower_df["Shift"] == "Day")
    )
    df = manpower_df.loc[mask].copy()
    if df.empty:
        return _empty("Manpower Summary")

    by_company  = df.groupby("Company")["Count"].sum().reset_index()
    by_company  = by_company[by_company["Count"] > 0].sort_values("Count", ascending=False)
    by_role     = df.groupby(["Company", "Role"])["Count"].sum().reset_index()
    by_role     = by_role[by_role["Count"] > 0]
    daily_total = df.groupby("Date")["Count"].sum().reset_index().sort_values("Date")

    fig = make_subplots(
        rows=2, cols=2,
        row_heights=[0.55, 0.45],
        column_widths=[0.38, 0.62],
        specs=[
            [{"type": "domain"}, {"type": "xy"}],
            [{"type": "xy", "colspan": 2}, None],
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.06,
        subplot_titles=(
            "Headcount by Company",
            "Role Breakdown by Company",
            "Daily Total Manpower Trend (Day Shift)",
        ),
    )

    colors = _COLORWAY

    # Donut pie
    fig.add_trace(
        go.Pie(labels=by_company["Company"], values=by_company["Count"],
               hole=0.52, marker=dict(colors=colors[:len(by_company)]),
               textinfo="percent+label", textfont=dict(size=10),
               showlegend=False),
        row=1, col=1)

    total_hc = int(by_company["Count"].sum())
    fig.add_annotation(
        text=f"<b>{total_hc}</b><br>Total",
        x=0.17, y=0.67,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=14, color=_COLORS["cyan"]),
        align="center",
    )

    # Role breakdown stacked bar
    roles = by_role["Role"].unique()
    for i, role in enumerate(roles):
        rd = by_role[by_role["Role"] == role]
        fig.add_trace(
            go.Bar(x=rd["Company"], y=rd["Count"], name=role,
                   marker_color=colors[i % len(colors)], opacity=0.85,
                   text=rd["Count"].astype(int).astype(str),
                   textposition="inside", textfont=dict(size=9)),
            row=1, col=2)

    fig.update_layout(barmode="stack")
    fig.update_xaxes(tickangle=-20, tickfont=dict(size=9), row=1, col=2)
    fig.update_yaxes(title_text="Headcount", title_font=dict(size=10), row=1, col=2)

    # Daily trend curve
    daily_total["Rolling_3"] = daily_total["Count"].rolling(3, min_periods=1).mean()
    fig.add_trace(
        go.Scatter(x=daily_total["Date"], y=daily_total["Count"],
                   name="Daily Total", mode="lines+markers",
                   line=dict(color=_COLORS["cyan"], width=2.5),
                   marker=dict(size=7),
                   fill="tozeroy", fillcolor="rgba(0,229,255,0.07)",
                   showlegend=False),
        row=2, col=1)
    fig.add_trace(
        go.Scatter(x=daily_total["Date"], y=daily_total["Rolling_3"],
                   name="3-day avg", mode="lines",
                   line=dict(color=_COLORS["amber"], width=1.5, dash="dash")),
        row=2, col=1)

    fig.update_yaxes(title_text="Persons", title_font=dict(size=10), row=2, col=1)

    fig.update_layout(
        height=620,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor ="rgba(15,17,26,0.55)",
        font_family  = _FONT,
        font_color   = "#D1D5E8",
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.08)",
                    borderwidth=1, font=dict(size=10),
                    orientation="v", x=1.01, y=1),
        margin=dict(l=16, r=120, t=60, b=16),
    )
    fig.update_annotations(font=dict(size=12, color="#A0A8C0"))
    for ax in fig.layout:
        if ax.startswith("xaxis") or ax.startswith("yaxis"):
            fig.layout[ax].gridcolor     = "#1E2A3A"
            fig.layout[ax].zerolinecolor = "#2A3A4A"
    return fig


# ──────────────────────────────────────────────────────────────
# 10. Completion Gauge
# ──────────────────────────────────────────────────────────────

def completion_gauge(
    achieved: float,
    target: float,
    label: str = "Monthly Target",
) -> go.Figure:
    pct   = round(achieved / target * 100, 1) if target else 0.0
    color = (_COLORS["lime"] if pct >= 90
             else _COLORS["amber"] if pct >= 60
             else _COLORS["red"])
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct,
        number=dict(suffix="%", font=dict(size=30, family=_FONT, color=color)),
        delta=dict(reference=100, relative=False, suffix="%", valueformat=".1f"),
        gauge=dict(
            axis=dict(range=[0, 100], tickfont=dict(size=9)),
            bar=dict(color=color, thickness=0.22),
            bgcolor="rgba(255,255,255,0.03)",
            borderwidth=0,
            steps=[
                dict(range=[0,  60], color="rgba(255,69,96,0.12)"),
                dict(range=[60, 90], color="rgba(255,209,102,0.12)"),
                dict(range=[90,100], color="rgba(168,255,62,0.12)"),
            ],
            threshold=dict(line=dict(color="white", width=2), thickness=0.8, value=100),
        ),
        title=dict(text=label, font=dict(size=12, family=_FONT, color="#A0A8C0")),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_family=_FONT, font_color="#D1D5E8",
        margin=dict(l=16, r=16, t=32, b=0), height=230,
    )
    return fig