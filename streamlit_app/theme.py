"""Dark "Metric Flow" theme: palette tokens, CSS injection, Plotly skin.

Kept separate from :mod:`streamlit_app.common` so both the app pages and the
PNG renderer can share the exact same colour tokens without importing
Streamlit.
"""

from __future__ import annotations

# Canvas / surface / border tokens.
CANVAS_BG = "#131316"
PANEL_BG = "#1B1B1F"
CARD_BG = "#202024"
CARD_HI = "#26262B"
BORDER = "#31313A"
CHIP_BG = "#2B2B31"
CHIP_EDGE = "#3C3C45"
GRID = "#34343C"

# Text tokens.
TEXT_LIGHT = "#F4F4F5"
TEXT_MUTED = "#9CA0A8"

# Accent (single coral) + semantic tokens.
ACCENT = "#F4573D"
ACCENT_SOFT = "#F79C8D"
ACCENT_DEEP = "#C23F2C"
ACCENT_PALE = "#FBD5CE"
NEUTRAL = "#7C8089"

# Semantic series colours used in charts.
POSITIVE = "#2FA37C"
WARNING = "#D9A441"
NEGATIVE = "#D1495B"

CSS = f"""
<style>
.stApp {{ background: {CANVAS_BG}; }}
[data-testid="stSidebar"] {{
    background: {PANEL_BG};
    border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{ color: {ACCENT}; }}
h1, h2, h3, h4 {{ color: {TEXT_LIGHT}; }}
p, span, label, li {{ color: {TEXT_MUTED}; }}
[data-testid="stMetricValue"] {{ color: {TEXT_LIGHT}; font-weight: 700; }}
[data-testid="stMetricLabel"] {{ color: {TEXT_MUTED}; }}

/* Header/toolbar: keep the Streamlit chrome on the dark canvas */
header[data-testid="stHeader"] {{ background: {CANVAS_BG}; }}
[data-testid="stToolbar"] {{ background: {CANVAS_BG}; }}
[data-testid="stDecoration"] {{ display: none; }}
[data-testid="stStatusWidget"] {{ background: {PANEL_BG}; }}

/* Multiselect / chip widgets: dark chips on the panel surface */
[data-baseweb="tag"] {{
    background: {CHIP_BG};
    border: 1px solid {CHIP_EDGE};
    border-radius: 8px;
    color: {TEXT_LIGHT};
}}
[data-baseweb="tag"] svg {{ fill: {TEXT_MUTED}; }}
[data-testid="stMultiSelect"] [data-baseweb="input"] > div {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
[data-testid="stMultiSelect"] input {{ color: {TEXT_LIGHT}; }}
[data-testid="stMultiSelect"] [data-baseweb="popover"] {{ background: {CARD_BG}; }}
[data-testid="stMultiSelect"] li {{ background: {CARD_BG}; color: {TEXT_LIGHT}; }}
[data-testid="stMultiSelect"] li:hover {{ background: {CARD_HI}; }}

/* Number input */
[data-testid="stNumberInput"] input {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
    color: {TEXT_LIGHT};
}}

/* Dataframes */
[data-testid="stDataFrame"] {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}

/* Buttons */
.stDownloadButton button, .stButton button {{
    background: {ACCENT};
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    font-weight: 700;
}}
.stDownloadButton button:hover, .stButton button:hover {{
    background: {ACCENT_DEEP};
    color: #FFFFFF;
}}

/* KPI card: rounded dark tile with a coral top accent */
.kpi-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 16px 18px 14px 18px;
    margin-bottom: 12px;
    position: relative;
    overflow: hidden;
    height: 100%;
}}
.kpi-card::before {{
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: {ACCENT};
}}
.kpi-label {{
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    margin-bottom: 8px;
}}
.kpi-value {{
    color: {TEXT_LIGHT};
    font-size: 28px;
    font-weight: 800;
    line-height: 1.15;
}}
.kpi-sub {{ color: {TEXT_MUTED}; font-size: 12px; margin-top: 6px; }}
.kpi-delta {{
    display: inline-block;
    margin-top: 10px;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    border: 1px solid {BORDER};
}}
.kpi-delta.up {{ color: {ACCENT_SOFT}; background: #2E2320; border-color: {ACCENT}; }}
.kpi-delta.down {{ color: {TEXT_MUTED}; background: {CHIP_BG}; }}
.section-title {{
    color: {ACCENT};
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 6px 0 12px 0;
}}
.status-banner {{
    background: #2A1D1A;
    border: 1px solid {ACCENT};
    border-radius: 12px;
    padding: 12px 16px;
    text-align: center;
}}
.status-banner .sb-title {{
    color: {ACCENT};
    font-weight: 800;
    letter-spacing: 0.06em;
    font-size: 13px;
}}
.status-banner .sb-sub {{
    color: {TEXT_MUTED};
    font-size: 12px;
    margin-top: 3px;
}}
</style>
"""


def apply_plotly_theme(fig, height: int = 400, title: str = ""):
    """Apply the dark cockpit theme to a Plotly figure.

    Args:
        fig: A Plotly figure.
        height: Figure height in pixels.
        title: Optional chart title.

    Returns:
        The same figure, themed.
    """
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CANVAS_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI, Inter, sans-serif", size=12),
        title=dict(
            text=title,
            font=dict(color=TEXT_LIGHT, size=14),
            x=0.0,
            xanchor="left",
            xref="container",
            y=0.99,
            yanchor="top",
            yref="container",
        ) if title else None,
        height=height,
        margin=dict(t=64 if title else 30, b=78, l=62, r=26),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=BORDER),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=BORDER),
        # Legend sits below the x-axis so it can never collide with the
        # title or the plotted series.
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.16,
            x=0.0,
            xanchor="left",
            font=dict(color=TEXT_MUTED),
            title=None,
        ),
        hoverlabel=dict(bgcolor=PANEL_BG, font_color=TEXT_LIGHT, bordercolor=BORDER),
    )
    return fig
