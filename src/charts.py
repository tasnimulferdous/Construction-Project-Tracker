# src/charts.py
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ──────────────────────────────────────────────────────────────
# Shared theme
# ──────────────────────────────────────────────────────────────

_FONT = "Segoe UI, Arial, sans-serif"

_COLORS = {
    "cyan"  : "#00E5FF",
    "coral" : "#FF6B35",
    "lime"  : "#A8FF3E",
    "violet": "#C77DFF",
    "amber" : "#FFD166",
    "red"   : "#FF4560",
    "grey"  : "#4B5A78",
    "teal"  : "#00BFA5",
    "pink"  : "#FF4081",
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
# 1. Contract Progress Chart  (NEW)
# ──────────────────────────────────────────────────────────────

def contract_progress_chart(
    pipe_upto_feb: float,
    pipe_this_month: float,
    contract_total: float,
) -> go.Figure:
    """
    Horizontal stacked bar showing:
      - Completed upto Feb  (cyan)
      - Completed this month (lime)
      - Remaining           (dark grey)
    Against the full contract total of 201,730.54 rm.
    """
    completed_total = pipe_upto_feb + pipe_this_month
    remaining       = max(contract_total - completed_total, 0)
    pct_done        = round(completed_total / contract_total * 100, 2) if contract_total else 0

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Completed (Upto Feb)",
        x=[pipe_upto_feb],
        y=["Contract Progress"],
        orientation="h",
        marker_color=_COLORS["cyan"],
        opacity=0.9,
        text=f"{pipe_upto_feb:,.1f} rm",
        textposition="inside",
        textfont=dict(size=11, color="#000"),
    ))

    fig.add_trace(go.Bar(
        name="Completed (This Month)",
        x=[pipe_this_month],
        y=["Contract Progress"],
        orientation="h",
        marker_color=_COLORS["lime"],
        opacity=0.9,
        text=f"{pipe_this_month:,.1f} rm",
        textposition="inside",
        textfont=dict(size=11, color="#000"),
    ))

    fig.add_trace(go.Bar(
        name="Remaining",
        x=[remaining],
        y=["Contract Progress"],
        orientation="h",
        marker_color="rgba(75,90,120,0.35)",
        text=f"{remaining:,.1f} rm remaining",
        textposition="inside",
        textfont=dict(size=11, color="#A0A8C0"),
    ))

    # Contract total marker line
    fig.add_vline(
        x=contract_total,
        line_dash="dot",
        line_color=_COLORS["amber"],
        line_width=2,
        annotation_text=f"Contract Total: {contract_total:,.0f} rm",
        annotation_position="top right",
        annotation_font=dict(color=_COLORS["amber"], size=11),
    )

    fig.update_layout(
        barmode="stack",
        height=130,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="left", x=0),
        xaxis=dict(
            title=f"Running Metres (rm)   |   Overall: {pct_done}% complete",
            title_font=dict(size=11, color="#A0A8C0"),
            tickformat=",",
        ),
        yaxis=dict(showticklabels=False),
        margin=dict(l=16, r=16, t=48, b=32),
    )

    _theme(fig, "Overall Contract Progress — Pipe Installation")
    return fig


# ──────────────────────────────────────────────────────────────
# 2. Daily Progress Bar Chart  (NEW)
# ──────────────────────────────────────────────────────────────

def daily_progress_bar_chart(
    summary_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
    activity_filter: str = "Pipe",
) -> go.Figure:
    """
    Daily quantities as grouped bars (by SD zone) with a
    daily total line, for the selected activity and date range.
    """
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

    # Pivot by SD zone
    pivot = (
        df.groupby(["Date", "SD"])["Daily_Qty"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values("Date")
    )

    sd_cols = [c for c in pivot.columns if c != "Date"]
    pivot["Daily_Total"] = pivot[sd_cols].sum(axis=1)

    colors = [_COLORS["cyan"], _COLORS["coral"], _COLORS["lime"], _COLORS["violet"]]
    fig    = go.Figure()

    for i, sd in enumerate(sd_cols):
        fig.add_trace(go.Bar(
            x=pivot["Date"],
            y=pivot[sd],
            name=f"SD-{sd}",
            marker_color=colors[i % len(colors)],
            opacity=0.82,
        ))

    # Daily total line
    fig.add_trace(go.Scatter(
        x=pivot["Date"],
        y=pivot["Daily_Total"],
        name="Daily Total",
        mode="lines+markers+text",
        line=dict(color=_COLORS["amber"], width=2),
        marker=dict(size=6, symbol="circle"),
        text=pivot["Daily_Total"].round(1).astype(str),
        textposition="top center",
        textfont=dict(size=9, color=_COLORS["amber"]),
    ))

    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Quantity (rm)", title_font=dict(size=11))
    return _theme(fig, f"Daily Progress — {activity_filter} (rm per day)")


# ──────────────────────────────────────────────────────────────
# 3. Manpower Summary Chart  (NEW)
# ──────────────────────────────────────────────────────────────

def manpower_summary_chart(
    manpower_df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
) -> go.Figure:
    """
    3-panel manpower dashboard in one figure:
      Left  (col 1): Donut pie — breakdown by Company (total headcount)
      Right (col 2): Stacked bar by Role within each Company
      Bottom (row 2): Line curve — daily total headcount trend
    """
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

    # ── Aggregations ──────────────────────────────────────────
    by_company = df.groupby("Company")["Count"].sum().reset_index()
    by_company = by_company[by_company["Count"] > 0].sort_values("Count", ascending=False)

    by_role = (
        df.groupby(["Company", "Role"])["Count"]
        .sum()
        .reset_index()
    )
    by_role = by_role[by_role["Count"] > 0]

    daily_total = (
        df.groupby("Date")["Count"]
        .sum()
        .reset_index()
        .sort_values("Date")
    )

    # ── Figure layout: 2 rows, 2 cols ─────────────────────────
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

    # ── Panel 1: Donut pie ────────────────────────────────────
    fig.add_trace(
        go.Pie(
            labels=by_company["Company"],
            values=by_company["Count"],
            hole=0.52,
            marker=dict(colors=colors[:len(by_company)]),
            textinfo="percent+label",
            textfont=dict(size=10),
            showlegend=False,
        ),
        row=1, col=1,
    )

    # Total in donut centre via annotation
    total_headcount = int(by_company["Count"].sum())
    fig.add_annotation(
        text=f"<b>{total_headcount}</b><br>Total",
        x=0.17, y=0.67,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=14, color=_COLORS["cyan"]),
        align="center",
    )

    # ── Panel 2: Stacked bar by Company + Role ────────────────
    companies = by_role["Company"].unique()
    roles     = by_role["Role"].unique()

    for i, role in enumerate(roles):
        role_data = by_role[by_role["Role"] == role]
        fig.add_trace(
            go.Bar(
                x=role_data["Company"],
                y=role_data["Count"],
                name=role,
                marker_color=colors[i % len(colors)],
                opacity=0.85,
                text=role_data["Count"].astype(int).astype(str),
                textposition="inside",
                textfont=dict(size=9),
                showlegend=True,
            ),
            row=1, col=2,
        )

    fig.update_layout(barmode="stack")
    fig.update_xaxes(tickangle=-20, tickfont=dict(size=9), row=1, col=2)
    fig.update_yaxes(title_text="Headcount", title_font=dict(size=10), row=1, col=2)

    # ── Panel 3: Daily trend curve ────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=daily_total["Date"],
            y=daily_total["Count"],
            name="Daily Total",
            mode="lines+markers",
            line=dict(color=_COLORS["cyan"], width=2.5),
            marker=dict(size=7, symbol="circle"),
            fill="tozeroy",
            fillcolor="rgba(0,229,255,0.07)",
            showlegend=False,
        ),
        row=2, col=1,
    )

    # Rolling average
    daily_total["Rolling_7"] = daily_total["Count"].rolling(3, min_periods=1).mean()
    fig.add_trace(
        go.Scatter(
            x=daily_total["Date"],
            y=daily_total["Rolling_7"],
            name="3-day avg",
            mode="lines",
            line=dict(color=_COLORS["amber"], width=1.5, dash="dash"),
            showlegend=True,
        ),
        row=2, col=1,
    )

    fig.update_yaxes(title_text="Persons", title_font=dict(size=10), row=2, col=1)

    # ── Global theme ──────────────────────────────────────────
    fig.update_layout(
        height=620,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor ="rgba(15,17,26,0.55)",
        font_family  = _FONT,
        font_color   = "#D1D5E8",
        legend=dict(
            bgcolor     = "rgba(0,0,0,0)",
            bordercolor = "rgba(255,255,255,0.08)",
            borderwidth = 1,
            font        = dict(size=10),
            orientation = "v",
            x=1.01, y=1,
        ),
        margin=dict(l=16, r=120, t=60, b=16),
    )
    fig.update_annotations(font=dict(size=12, color="#A0A8C0"))

    for ax in fig.layout:
        if ax.startswith("xaxis") or ax.startswith("yaxis"):
            fig.layout[ax].gridcolor    = "#1E2A3A"
            fig.layout[ax].zerolinecolor = "#2A3A4A"

    return fig


# ──────────────────────────────────────────────────────────────
# 4. Daily Pipe Installation by SD Zone
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
        .sum()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values("Date")
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
            secondary_y=False,
        )

    fig.add_trace(
        go.Scatter(x=pivot["Date"], y=pivot["Cumulative"],
                   name="Cumulative (rm)", mode="lines+markers",
                   line=dict(color=_COLORS["amber"], width=2.5),
                   marker=dict(size=5)),
        secondary_y=True,
    )

    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Daily (rm)",      secondary_y=False, title_font=dict(size=11))
    fig.update_yaxes(title_text="Cumulative (rm)", secondary_y=True,  title_font=dict(size=11),
                     showgrid=False)
    return _theme(fig, "Daily Pipe Installation by SD Zone")


# ──────────────────────────────────────────────────────────────
# 5. Burn Rate Chart
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

    # Monthly target (deduplicated)
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
# 6. Activity Breakdown
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
# 7. Vehicle Utilisation
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
# 8. Completion Gauge
# ──────────────────────────────────────────────────────────────

def completion_gauge(
    achieved: float,
    target: float,
    label: str = "Monthly Target",
) -> go.Figure:
    pct   = round(achieved / target * 100, 1) if target else 0.0
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
        margin=dict(l=16, r=16, t=32, b=0),
        height=230,
    )
    return fig