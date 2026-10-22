"""Plotly figure builders for the Streamlit pages (dark cockpit theme).

Every figure is derived from the engine output — no hardcoded series — and
is themed through :func:`streamlit_app.theme.apply_plotly_theme`.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from streamlit_app.theme import (
    ACCENT,
    ACCENT_DEEP,
    ACCENT_SOFT,
    BORDER,
    CARD_BG,
    GRID,
    NEGATIVE,
    NEUTRAL,
    POSITIVE,
    TEXT_LIGHT,
    TEXT_MUTED,
    WARNING,
    apply_plotly_theme,
)

LEAKAGE_BUCKETS = ["Cancellation Leakage", "Return Leakage", "Loss Leakage"]

# Financial bucket -> colour, shared by the donut and the HTML colour key.
BUCKET_PALETTE = {
    "Net Realized": POSITIVE,
    "Cancellation Leakage": NEGATIVE,
    "Return Leakage": WARNING,
    "Loss Leakage": NEUTRAL,
    "In-Transit": ACCENT,
    "Pending": ACCENT_SOFT,
}


def _short(v: float) -> str:
    """Indian short format for chart labels."""
    a = abs(v)
    if a >= 1e7:
        return f"{v / 1e7:.2f}Cr"
    if a >= 1e5:
        return f"{v / 1e5:.2f}L"
    return f"{v / 1e3:.1f}K"


def waterfall_gross_net(weekly: pd.DataFrame, df: pd.DataFrame | None = None) -> go.Figure:
    """Gross-to-Net waterfall: Gross -> leakage -> In-Transit/Pending -> Net.

    Args:
        weekly: Weekly KPI frame.
        df: Optional cleaned frame (used when transit/pending columns absent).

    Returns:
        A themed waterfall figure.
    """
    gross = float(weekly["gross_revenue"].sum())
    canc = -float(weekly["cancellation_leakage"].sum())
    ret = -float(weekly["return_leakage"].sum())
    loss = -float(weekly["loss_leakage"].sum())
    if "in_transit_value" in weekly.columns:
        transit = -float(weekly["in_transit_value"].sum())
        pending = -float(weekly["pending_value"].sum())
    elif df is not None:
        transit = -float(df.loc[df["financial_bucket"] == "In-Transit", "Amount"].sum())
        pending = -float(df.loc[df["financial_bucket"] == "Pending", "Amount"].sum())
    else:
        transit = pending = 0.0
    net = gross + canc + ret + loss + transit + pending

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "relative",
                 "relative", "relative", "total"],
        x=["Gross Invoiced", "Cancellations", "Returns", "Loss/Damage",
           "In-Transit", "Pending", "Net Realized"],
        y=[gross, canc, ret, loss, transit, pending, None],
        text=[_short(gross), _short(canc), _short(ret), _short(loss),
              _short(transit), _short(pending), _short(net)],
        textposition="outside",
        connector={"line": {"color": NEUTRAL}},
        increasing={"marker": {"color": POSITIVE}},
        decreasing={"marker": {"color": NEGATIVE}},
        totals={"marker": {"color": ACCENT}},
    ))
    return apply_plotly_theme(
        fig, height=440, title="Gross → Net Revenue Waterfall (all settlement states)"
    )


def weekly_combo(weekly: pd.DataFrame) -> go.Figure:
    """Bar Gross/Net + line Settled Clearance % on a secondary axis.

    Args:
        weekly: Weekly KPI frame.

    Returns:
        A themed combo figure.
    """
    fig = go.Figure()
    fig.add_bar(x=weekly["week_label"], y=weekly["gross_revenue"],
                name="Gross Invoiced", marker_color=ACCENT, opacity=0.85)
    fig.add_bar(x=weekly["week_label"], y=weekly["net_realized"],
                name="Net Realized", marker_color=NEUTRAL, opacity=0.9)
    clearance = (
        weekly["settled_clearance_rate"]
        if "settled_clearance_rate" in weekly.columns
        else weekly["clearance_rate"]
    )
    partial = (
        weekly["is_partial_week"].astype(bool)
        if "is_partial_week" in weekly.columns
        else pd.Series(False, index=weekly.index)
    )
    symbols = ["circle-open" if p else "circle" for p in partial]
    sizes = [11 if p else 7 for p in partial]
    colors = [NEUTRAL if p else ACCENT_SOFT for p in partial]
    # Break the line at partial weeks so the truncated window edge is not
    # drawn as a fall to zero.
    line_y = [None if p else v for p, v in zip(partial, clearance, strict=True)]
    fig.add_scatter(
        x=weekly["week_label"], y=line_y, name="Settled Clearance %",
        yaxis="y2", mode="lines", line=dict(color=ACCENT_SOFT, width=3),
        hoverinfo="skip", showlegend=False,
    )
    fig.add_scatter(
        x=weekly["week_label"], y=clearance, name="Settled Clearance %",
        yaxis="y2", mode="markers",
        marker=dict(size=sizes, symbol=symbols, color=colors,
                    line=dict(color=NEUTRAL, width=2)),
        hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>",
    )
    if bool(partial.any()):
        fig.add_scatter(
            x=[None], y=[None], yaxis="y2", mode="markers", name="Partial week",
            marker=dict(size=11, symbol="circle-open", color=NEUTRAL,
                        line=dict(width=2)),
        )
    fig.update_layout(
        barmode="group",
        yaxis=dict(title="Revenue (₹)"),
        yaxis2=dict(title="Settled Clearance %", overlaying="y", side="right",
                    range=[0, 100], showgrid=False),
    )
    return apply_plotly_theme(
        fig, height=430, title="Weekly Invoiced vs Realized Revenue"
    )


def leakage_stacked(weekly: pd.DataFrame) -> go.Figure:
    """Stacked weekly leakage bars by category.

    Args:
        weekly: Weekly KPI frame.

    Returns:
        A themed stacked-bar figure.
    """
    fig = go.Figure()
    fig.add_bar(x=weekly["week_label"], y=weekly["cancellation_leakage"],
                name="Cancellation", marker_color=NEGATIVE)
    fig.add_bar(x=weekly["week_label"], y=weekly["return_leakage"],
                name="Return", marker_color=WARNING)
    fig.add_bar(x=weekly["week_label"], y=weekly["loss_leakage"],
                name="Loss/Damage", marker_color=NEUTRAL)
    fig.update_layout(barmode="stack")
    return apply_plotly_theme(
        fig, height=420, title="Revenue Leakage Breakdown by Week"
    )


def settled_clearance_vs_target(weekly: pd.DataFrame, target: float = 70.0) -> go.Figure:
    """Settled clearance rate per week against the audit target.

    Args:
        weekly: Weekly KPI frame.
        target: Audit target percentage.

    Returns:
        A themed line figure.
    """
    col = (
        "settled_clearance_rate"
        if "settled_clearance_rate" in weekly.columns
        else "clearance_rate"
    )
    partial = (
        weekly["is_partial_week"].astype(bool)
        if "is_partial_week" in weekly.columns
        else pd.Series(False, index=weekly.index)
    )
    # Two traces keep the weeks in chronological order: the line trace breaks
    # (None) at partial weeks so a truncated window edge is never drawn as a
    # collapse to zero, while the marker trace still shows every week.
    fig = go.Figure()
    line_y = [None if p else v for p, v in zip(partial, weekly[col], strict=True)]
    fig.add_scatter(
        x=weekly["week_label"], y=line_y, mode="lines",
        name="Settled Clearance %", line=dict(color=ACCENT, width=3),
        hoverinfo="skip", showlegend=False,
    )
    symbols = ["circle-open" if p else "circle" for p in partial]
    sizes = [11 if p else 9 for p in partial]
    colors = [NEUTRAL if p else ACCENT for p in partial]
    fig.add_scatter(
        x=weekly["week_label"], y=weekly[col], mode="markers+text",
        name="Settled Clearance %", line=dict(color=ACCENT, width=3),
        marker=dict(size=sizes, symbol=symbols, color=colors,
                    line=dict(color=NEUTRAL, width=2)),
        text=[f"{v:.0f}%" for v in weekly[col]], textposition="top center",
        hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>",
    )
    if bool(partial.any()):
        fig.add_scatter(
            x=[None], y=[None], mode="markers", name="Partial week",
            marker=dict(size=11, symbol="circle-open", color=NEUTRAL,
                        line=dict(width=2)),
        )
    fig.add_hline(y=target, line=dict(color=NEUTRAL, dash="dash"),
                  annotation_text=f"Audit target ({target:.0f}%)",
                  annotation_position="top left",
                  annotation_font_color=TEXT_MUTED,
                  annotation_font_size=11)
    fig.update_layout(yaxis=dict(title="Settled Clearance %", range=[0, 105]))
    return apply_plotly_theme(
        fig, height=400, title="Settled Clearance Rate vs Target"
    )


def category_leakage_bar(leak: pd.DataFrame) -> go.Figure:
    """Leakage revenue by product category (horizontal stacked bars).

    Args:
        leak: Cleaned frame filtered to leakage buckets.

    Returns:
        A themed horizontal bar figure.
    """
    colors = dict(zip(LEAKAGE_BUCKETS, [NEGATIVE, WARNING, NEUTRAL], strict=False))
    fig = go.Figure()
    for bucket in LEAKAGE_BUCKETS:
        sub = leak[leak["financial_bucket"] == bucket]
        if not len(sub):
            continue
        agg = sub.groupby("Category")["Amount"].sum().sort_values().reset_index()
        fig.add_bar(
            y=agg["Category"], x=agg["Amount"], name=bucket,
            orientation="h", marker_color=colors[bucket],
            hovertemplate="%{y}<br>₹%{x:,.0f}<extra>" + bucket + "</extra>",
        )
    fig.update_layout(barmode="stack")
    return apply_plotly_theme(
        fig, height=440, title="Leakage ₹ by Product Category"
    )


def state_leakage_bar(leak: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Top N ship-states by leakage amount.

    Args:
        leak: Cleaned frame filtered to leakage buckets.
        top_n: Number of states to show.

    Returns:
        A themed horizontal bar figure.
    """
    agg = (
        leak.groupby("ship-state")["Amount"].sum()
        .sort_values(ascending=False).head(top_n).sort_values().reset_index()
    )
    fig = go.Figure(go.Bar(
        y=agg["ship-state"], x=agg["Amount"], orientation="h",
        marker_color=ACCENT,
        hovertemplate="%{y}<br>₹%{x:,.0f}<extra></extra>",
    ))
    return apply_plotly_theme(
        fig, height=440, title=f"Top {top_n} States by Leakage ₹"
    )


def fulfilment_settlement_bar(fulfil: pd.DataFrame) -> go.Figure:
    """Gross vs Net vs Leakage for each fulfilment channel.

    Args:
        fulfil: Frame from :func:`metrics.fulfilment_settlement`.

    Returns:
        A themed grouped bar figure.
    """
    fig = go.Figure()
    fig.add_bar(x=fulfil["Fulfilment"], y=fulfil["gross_revenue"],
                name="Gross Invoiced", marker_color=BORDER)
    fig.add_bar(x=fulfil["Fulfilment"], y=fulfil["net_realized"],
                name="Net Realized", marker_color=ACCENT)
    fig.add_bar(x=fulfil["Fulfilment"], y=fulfil["total_leakage"],
                name="Leakage", marker_color=NEGATIVE)
    fig.update_layout(barmode="group")
    return apply_plotly_theme(
        fig, height=420, title="Fulfilment Channel Settlement Comparison"
    )


def bucket_mix_donut(df: pd.DataFrame) -> go.Figure:
    """Revenue split across every financial bucket.

    Args:
        df: Cleaned transaction frame.

    Returns:
        A themed donut figure.
    """
    agg = df.groupby("financial_bucket")["Amount"].sum().sort_values(ascending=False)
    palette = {
        "Net Realized": POSITIVE,
        "Cancellation Leakage": NEGATIVE,
        "Return Leakage": WARNING,
        "Loss Leakage": NEUTRAL,
        "In-Transit": ACCENT,
        "Pending": ACCENT_SOFT,
    }
    fig = go.Figure(go.Pie(
        labels=agg.index, values=agg.values, hole=0.55,
        marker=dict(colors=[palette.get(i, NEUTRAL) for i in agg.index],
                    line=dict(color=BORDER, width=2)),
        textinfo="label+percent",
        hovertemplate="%{label}<br>₹%{value:,.0f} (%{percent})<extra></extra>",
    ))
    total = float(agg.sum())
    fig.add_annotation(
        text=f"<b>₹{total / 1e7:.2f} Cr</b><br>invoiced", showarrow=False,
        font=dict(color=TEXT_LIGHT, size=15),
    )
    fig = apply_plotly_theme(fig, height=430, title="Revenue by Financial Bucket")
    # A donut has no x-axis, so its legend goes below the plot.
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.02, x=0.5,
                    xanchor="center", font=dict(color=TEXT_MUTED, size=10)),
        margin=dict(t=64, b=96, l=10, r=10),
    )
    return fig


# ---------------------------------------------------------------------------
# Cockpit charts — the "Midnight Deck" rebuild.
#
# These mirror the reference CRM mock: a large filled area chart with an
# annotation callout, a small secondary area sparkline, a vertical volume bar
# chart and a radial gauge.
# ---------------------------------------------------------------------------


def _gradient_fill(color: str, top_alpha: float = 0.42, bottom_alpha: float = 0.02):
    """Build a vertical rgba gradient fill for a Plotly area trace.

    Args:
        color: Hex colour of the series.
        top_alpha: Opacity at the top of the area.
        bottom_alpha: Opacity at the baseline.

    Returns:
        A ``fillgradient`` dict accepted by ``go.Scatter``.
    """
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    return {
        "type": "vertical",
        "colorscale": [
            [0.0, f"rgba({r},{g},{b},{bottom_alpha})"],
            [1.0, f"rgba({r},{g},{b},{top_alpha})"],
        ],
    }


def cockpit_area_trend(weekly: pd.DataFrame, height: int = 380) -> go.Figure:
    """Filled area chart of Gross vs Net revenue with a peak-week callout.

    This is the centrepiece of the cockpit: two overlapping gradient areas
    (Gross Invoiced, Net Realized) with the best-performing week annotated
    inline, matching the reference dashboard's annotated area chart.

    Args:
        weekly: Weekly KPI frame.
        height: Figure height in pixels.

    Returns:
        A themed area figure.
    """
    fig = go.Figure()
    fig.add_scatter(
        x=weekly["week_label"], y=weekly["gross_revenue"],
        name="Gross Invoiced", mode="lines",
        line=dict(color=ACCENT_SOFT, width=2.4),
        fill="tozeroy", fillgradient=_gradient_fill(ACCENT_SOFT, 0.34, 0.01),
        hovertemplate="%{x}<br>₹%{y:,.0f}<extra>Gross Invoiced</extra>",
    )
    fig.add_scatter(
        x=weekly["week_label"], y=weekly["net_realized"],
        name="Net Realized", mode="lines",
        line=dict(color=POSITIVE, width=2.4),
        fill="tozeroy", fillgradient=_gradient_fill(POSITIVE, 0.30, 0.01),
        hovertemplate="%{x}<br>₹%{y:,.0f}<extra>Net Realized</extra>",
    )

    # Annotate the best net-realized week — the reference mock highlights a
    # single point on the curve with a boxed callout.
    if len(weekly):
        peak_idx = weekly["net_realized"].idxmax()
        peak_x = weekly.loc[peak_idx, "week_label"]
        peak_y = float(weekly.loc[peak_idx, "net_realized"])
        fig.add_trace(go.Scatter(
            x=[peak_x], y=[peak_y], mode="markers",
            marker=dict(size=11, color=ACCENT,
                        line=dict(color="#FFFFFF", width=2)),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_annotation(
            x=peak_x, y=peak_y, text=f"<b>Peak {peak_x}</b><br>₹{peak_y/1e7:,.2f} Cr",
            showarrow=True, arrowhead=2, arrowwidth=1.4,
            arrowcolor=ACCENT, ax=0, ay=-46,
            bgcolor=ACCENT_DEEP, bordercolor=ACCENT, borderwidth=1,
            borderpad=6, font=dict(color="#FFFFFF", size=11),
        )

    fig.update_layout(
        hovermode="x unified",
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(gridcolor=GRID, tickprefix="₹", tickformat="~s",
                   tickfont=dict(size=10), zeroline=False),
        # Extra headroom so the legend sits above the plot area instead of
        # overlapping it.
        margin=dict(t=44, b=44, l=58, r=18),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, yref="paper",
                    x=1.0, xanchor="right", font=dict(color=TEXT_MUTED, size=10)),
    )
    fig = apply_plotly_theme(fig, height=height)
    fig.update_layout(
        margin=dict(t=44, b=44, l=58, r=18),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, yref="paper",
                    x=1.0, xanchor="right", font=dict(color=TEXT_MUTED, size=10)),
    )
    return fig


def cockpit_gauge(value: float, label: str, height: int = 300) -> go.Figure:
    """Radial gauge showing one headline percentage.

    Reproduces the circular ring gauge from the reference mock, with the
    metric rendered in the hole of the donut.

    Args:
        value: Percentage to display (0-100).
        label: Caption rendered under the value inside the ring.
        height: Figure height in pixels.

    Returns:
        A themed gauge figure.
    """
    pct = max(0.0, min(100.0, float(value)))
    # Track / value / remainder of the ring.
    fig = go.Figure(go.Pie(
        values=[pct, 100 - pct],
        hole=0.72,
        sort=False,
        direction="clockwise",
        rotation=90,
        textinfo="none",
        marker=dict(
            colors=[ACCENT if pct >= 70 else WARNING, "#182338"],
            line=dict(color=CARD_BG, width=0),
        ),
        hoverinfo="skip",
        showlegend=False,
    ))
    fig.add_annotation(
        text=(
            f"<span style='font-size:30px;font-weight:800;color:{TEXT_LIGHT}'>"
            f"{pct:.1f}%</span><br>"
            f"<span style='font-size:11px;color:{TEXT_MUTED}'>{label}</span>"
        ),
        showarrow=False, x=0.5, y=0.5,
        font=dict(color=TEXT_LIGHT, size=12),
        align="center",
    )
    fig.update_layout(
        height=height,
        margin=dict(t=6, b=6, l=6, r=6),
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        showlegend=False,
    )
    return fig


def cockpit_mini_area(weekly: pd.DataFrame, height: int = 220) -> go.Figure:
    """Compact area sparkline of net realized revenue (no axes chrome).

    Args:
        weekly: Weekly KPI frame.
        height: Figure height in pixels.

    Returns:
        A themed mini area figure.
    """
    fig = go.Figure()
    fig.add_scatter(
        x=weekly["week_label"], y=weekly["net_realized"],
        mode="lines", line=dict(color=ACCENT, width=2.2, shape="spline"),
        fill="tozeroy", fillgradient=_gradient_fill(ACCENT, 0.45, 0.01),
        hovertemplate="%{x}<br>₹%{y:,.0f}<extra>Net Realized</extra>",
    )
    fig.update_layout(
        height=height,
        margin=dict(t=8, b=8, l=8, r=8),
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
        hovermode="x unified",
    )
    return fig


def cockpit_volume_bars(weekly: pd.DataFrame, height: int = 300) -> go.Figure:
    """Vertical bar chart of weekly transaction volume.

    Args:
        weekly: Weekly KPI frame.
        height: Figure height in pixels.

    Returns:
        A themed bar figure.
    """
    colors = [ACCENT if not p else ACCENT_DEEP for p in
              weekly["is_partial_week"].astype(bool)] if "is_partial_week" in weekly.columns \
        else [ACCENT] * len(weekly)
    fig = go.Figure(go.Bar(
        x=weekly["week_label"], y=weekly["total_orders"],
        marker=dict(color=colors, line=dict(color=ACCENT_SOFT, width=0.6)),
        hovertemplate="%{x}<br>%{y:,} lines<extra></extra>",
    ))
    fig.update_layout(
        height=height,
        margin=dict(t=10, b=40, l=46, r=10),
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        xaxis=dict(showgrid=False, tickfont=dict(size=9)),
        yaxis=dict(gridcolor=GRID, showgrid=True, zeroline=False,
                   tickfont=dict(size=9)),
        bargap=0.45,
        showlegend=False,
    )
    return fig


def cockpit_bucket_donut(df: pd.DataFrame, height: int = 300) -> go.Figure:
    """Donut of revenue by financial bucket.

    The colour key is rendered as HTML beside the chart (see
    :func:`bucket_legend_rows`) rather than as a Plotly legend, because
    Plotly positions legends in paper coordinates that drift outside the
    plot whenever the container is resized.

    Args:
        df: Cleaned transaction frame.
        height: Figure height in pixels.

    Returns:
        A themed donut figure.
    """
    agg = df.groupby("financial_bucket")["Amount"].sum().sort_values(ascending=False)
    palette = BUCKET_PALETTE
    labels = list(agg.index)
    values = list(agg.values)
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.62,
        marker=dict(
            colors=[palette.get(i, NEUTRAL) for i in labels],
            line=dict(color=CARD_BG, width=2),
        ),
        textinfo="none",
        showlegend=False,
        hovertemplate="%{label}<br>₹%{value:,.0f}<extra></extra>",
    ))
    total = float(sum(values))
    fig.add_annotation(
        text=(f"<span style='font-size:15px;font-weight:800;color:{TEXT_LIGHT}'>"
              f"₹{total/1e7:,.2f} Cr</span><br>"
              f"<span style='font-size:10px;color:{TEXT_MUTED}'>invoiced</span>"),
        showarrow=False, x=0.5, y=0.5, align="center",
    )
    fig.update_layout(
        height=height,
        margin=dict(t=6, b=6, l=6, r=6),
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        showlegend=False,
    )
    return fig


def bucket_legend_rows(df: pd.DataFrame) -> list[tuple[str, str, float]]:
    """Return the bucket mix as ``(label, colour, amount)`` rows.

    Args:
        df: Cleaned transaction frame.

    Returns:
        List of (bucket label, swatch colour, total amount), largest first.
    """
    agg = df.groupby("financial_bucket")["Amount"].sum().sort_values(ascending=False)
    return [
        (str(name), BUCKET_PALETTE.get(str(name), NEUTRAL), float(amount))
        for name, amount in agg.items()
    ]
