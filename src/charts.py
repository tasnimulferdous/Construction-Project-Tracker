# src/charts.py
# ============================================================
#  Chart factory for CCECC Master Tracker dashboard.
#  All functions accept clean DataFrames from cleaner.py
#  and return Plotly Figure objects.  No st.* calls here.
# ============================================================

from __future__ import annotations
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ──────────────────────────────────────────────────────────────
# Shared theme
# ──────────────────────────────────────────────────────────────

_FONT = "IBM Plex Mono, Courier New, monospace"

_COLORS = {
    "cyan"   : "#00E5FF",
    "coral"  : "#FF6B35",
    "lime"   : "#A8FF3E",
    "violet" : "#C77DFF",
    "amber"  : "#FFD166",
    "red"    : "#FF4560",
    "grey"   : "#4B5A78",
}

_COLORWAY = list(_COLORS.values())


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
        margin        = dict(l=16, r=16, t=44, b=16),
        legend        = dict(
            bgcolor     = "rgba(0,0,0,0)",
            bordercolor = "rgba(255,255,255,0.08)",
            borderwidth = 1,
            font        = dict(size=11),
        ),
    )
    fig.update_xaxes(
        gridcolor="#1E2A3A", zerolinecolor="#2A3A4A",
        showline=False, tickfont=dict(size=10),
    )
    fig.update_yaxes(
        gridcolor="#1E2A3A", zerolinecolor="#2A3A4A",
        showline=False, tickfont=dict(size=10),
    )
    return fig


def _empty(title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text="No data for selected period", showarrow=False,
        xref="paper", yref="paper", x=0.5, y=0.5,
        font=dict(size=13, color="#4B5A78"),
    )
    return _theme(fig, title)


# ──────────────────────────────────────────────────────────────
# 1. Daily Pipe Installation — Actual vs Cumulative
# ──────────────────────────────────────────────────────────────

def daily_pipe_installation_chart(
    summary_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
) -> go.Figure:
    """
    Bar chart of daily pipe installation (rm) grouped by SD zone,
    with a cumulative total line overlaid on a secondary Y axis.
    """
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

    # Daily totals by SD zone
    pivot = (
        df.groupby(["Date", "SD"])["Daily_Qty"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values("Date")
    )

    # Cumulative total across all SD zones
    sd_cols = [c for c in pivot.columns if c != "Date"]
    pivot["Total"] = pivot[sd_cols].sum(axis=1)
    pivot["Cumulative"] = pivot["Total"].cumsum()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    colors = [_COLORS["cyan"], _COLORS["coral"], _COLORS["lime"], _COLORS["violet"]]
    for i, sd in enumerate(sd_cols):
        fig.add_trace(
            go.Bar(
                x=pivot["Date"], y=pivot[sd],
                name=f"SD-{sd}",
                marker_color=colors[i % len(colors)],
                opacity=0.82,
            ),
            secondary_y=False,
        )

    fig.add_trace(
        go.Scatter(
            x=pivot["Date"], y=pivot["Cumulative"],
            name="Cumulative (rm)",
            mode="lines+markers",
            line=dict(color=_COLORS["amber"], width=2.5),
            marker=dict(size=5, symbol="circle"),
        ),
        secondary_y=True,
    )

    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Daily (rm)", secondary_y=False, title_font=dict(size=11))
    fig.update_yaxes(title_text="Cumulative (rm)", secondary_y=True, title_font=dict(size=11),
                     showgrid=False)

    return _theme(fig, "Daily Pipe Installation by SD Zone")


# ──────────────────────────────────────────────────────────────
# 2. Monthly Progress Burn-Rate (Planned vs Actual)
# ──────────────────────────────────────────────────────────────

def burn_rate_chart(
    summary_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
    activity_filter: str = "Pipe",
) -> go.Figure:
    """
    Cumulative actual vs linear planned target line.
    The planned line assumes uniform daily distribution of Qty_Mar target.
    """
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

    # Linear planned: total monthly target spread evenly across all days in range
    monthly_target = float(
        summary_df[
            summary_df["Activity"].str.contains(activity_filter, case=False, na=False)
        ]["Qty_Mar"].drop_duplicates().sum()
    )
    n_days = max((date_end - date_start).days + 1, 1)
    daily_planned_rate = monthly_target / 31  # per day of month

    planned_dates = pd.date_range(date_start, date_end, freq="D")
    planned_series = pd.DataFrame({
        "Date"             : planned_dates,
        "Cumulative_Planned": [(i + 1) * daily_planned_rate for i in range(len(planned_dates))],
    })

    fig = go.Figure()

    # Planned dashed line
    fig.add_trace(go.Scatter(
        x=planned_series["Date"],
        y=planned_series["Cumulative_Planned"],
        name="Planned (linear)",
        mode="lines",
        line=dict(color=_COLORS["grey"], width=2, dash="dot"),
    ))

    # Actual filled area
    fig.add_trace(go.Scatter(
        x=daily["Date"],
        y=daily["Cumulative_Actual"],
        name="Actual (cumulative)",
        mode="lines+markers",
        line=dict(color=_COLORS["cyan"], width=2.5),
        marker=dict(size=6),
        fill="tozeroy",
        fillcolor="rgba(0,229,255,0.08)",
    ))

    fig.update_yaxes(title_text="Running metres (rm)", title_font=dict(size=11))
    return _theme(fig, f"Burn Rate — {activity_filter} Installation (Cumulative)")


# ──────────────────────────────────────────────────────────────
# 3. Work Activity Breakdown — Horizontal Bar
# ──────────────────────────────────────────────────────────────

def activity_breakdown_chart(
    summary_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
) -> go.Figure:
    """
    Horizontal grouped bar: total quantity per Activity+SD in the period,
    with the monthly target shown as a marker for reference.
    """
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
        .agg(
            Achieved=("Daily_Qty", "sum"),
            Target=("Qty_Mar", "first"),
        )
        .reset_index()
    )
    agg["Label"] = agg["Activity"] + " SD-" + agg["SD"] + " " + agg["Pipe_Dia"]
    agg["Label"] = agg["Label"].str.replace(r"\s+", " ", regex=True).str.strip()
    agg = agg.sort_values("Achieved", ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=agg["Label"],
        x=agg["Achieved"],
        name="Achieved (this period)",
        orientation="h",
        marker_color=_COLORS["cyan"],
        opacity=0.85,
        text=agg["Achieved"].round(1).astype(str) + " rm",
        textposition="outside",
        textfont=dict(size=9),
    ))

    # Monthly target dots
    fig.add_trace(go.Scatter(
        y=agg["Label"],
        x=agg["Target"],
        name="Monthly Target",
        mode="markers",
        marker=dict(
            symbol="line-ns",
            size=14,
            color=_COLORS["amber"],
            line=dict(width=2, color=_COLORS["amber"]),
        ),
    ))

    fig.update_layout(
        barmode="overlay",
        height=max(300, len(agg) * 36),
    )
    fig.update_xaxes(title_text="Quantity (rm / Pcs)")
    return _theme(fig, "Work Activity — Period Totals vs Monthly Target")


# ──────────────────────────────────────────────────────────────
# 4. Vehicle Utilisation Chart
# ──────────────────────────────────────────────────────────────

def vehicle_utilisation_chart(
    vehicle_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
) -> go.Figure:
    """
    Stacked bar chart of daily equipment/vehicle hours used.
    """
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
        .sum()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values("Date")
    )

    fig = go.Figure()
    colors = _COLORWAY
    for i, veh in enumerate([c for c in pivot.columns if c != "Date"]):
        fig.add_trace(go.Bar(
            x=pivot["Date"],
            y=pivot[veh],
            name=veh,
            marker_color=colors[i % len(colors)],
            opacity=0.85,
        ))

    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Hours", title_font=dict(size=11))
    return _theme(fig, "Equipment / Vehicle Utilisation (hrs)")


# ──────────────────────────────────────────────────────────────
# 5. Manpower Daily Headcount
# ──────────────────────────────────────────────────────────────

def manpower_headcount_chart(
    manpower_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
) -> go.Figure:
    """
    Stacked bar chart of daily manpower headcount grouped by Company.
    """
    if manpower_df.empty:
        return _empty("Manpower Headcount")

    mask = (
        (manpower_df["Date"] >= date_start)
        & (manpower_df["Date"] <= date_end)
    )
    df = manpower_df.loc[mask].copy()
    if df.empty:
        return _empty("Manpower Headcount")

    group_col = "Company" if "Company" in df.columns else "Role"

    pivot = (
        df.groupby(["Date", group_col])["Count"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values("Date")
    )

    fig = go.Figure()
    colors = _COLORWAY
    group_cols = [c for c in pivot.columns if c != "Date"]

    for i, grp in enumerate(group_cols):
        fig.add_trace(go.Bar(
            x=pivot["Date"],
            y=pivot[grp],
            name=grp,
            marker_color=colors[i % len(colors)],
            opacity=0.85,
            text=pivot[grp].where(pivot[grp] > 0),
            textposition="inside",
            textfont=dict(size=9),
        ))

    pivot["Total"] = pivot[group_cols].sum(axis=1)
    fig.add_trace(go.Scatter(
        x=pivot["Date"],
        y=pivot["Total"],
        name="Total Headcount",
        mode="lines+markers",
        line=dict(color=_COLORS["amber"], width=2.5, dash="dash"),
        marker=dict(size=7, symbol="diamond"),
    ))

    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Headcount (persons)", title_font=dict(size=11))
    return _theme(fig, "Daily Manpower Headcount by Company")


# ──────────────────────────────────────────────────────────────
# 6. Completion Gauge
# ──────────────────────────────────────────────────────────────

def completion_gauge(
    achieved: float,
    target: float,
    label: str = "Monthly Target",
) -> go.Figure:
    pct = round(achieved / target * 100, 1) if target else 0.0
    color = (
        _COLORS["lime"]  if pct >= 90
        else _COLORS["amber"] if pct >= 60
        else _COLORS["red"]
    )
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
                dict(range=[0, 60],  color="rgba(255,69,96,0.12)"),
                dict(range=[60, 90], color="rgba(255,209,102,0.12)"),
                dict(range=[90,100], color="rgba(168,255,62,0.12)"),
            ],
            threshold=dict(line=dict(color="white", width=2), thickness=0.8, value=100),
        ),
        title=dict(text=label, font=dict(size=12, family=_FONT, color="#A0A8C0")),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_family=_FONT,
        font_color="#D1D5E8",
        margin=dict(l=16, r=16, t=32, b=0),
        height=230,
    )
    return fig