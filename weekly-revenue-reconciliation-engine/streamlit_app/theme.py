"""Dark "Executive Slate" theme: palette tokens, CSS injection, Plotly skin.

Kept separate from :mod:`streamlit_app.common` so both the app pages and the
PNG renderer can share the exact same colour tokens without importing
Streamlit.

The palette is a unified monochromatic slate-navy identity: slate-900 canvas,
charcoal cards, and a single sapphire/sky-blue accent. Chart series are tonal
shades of the same blue; status flags are muted slate tones rather than bright
red/green/amber.
"""

from __future__ import annotations

# Canvas / surface / border tokens.
CANVAS_BG = "#0F172A"
PANEL_BG = "#1E293B"
CARD_BG = "#1E293B"
CARD_HI = "#27364A"
BORDER = "#334155"
CHIP_BG = "#27364A"
CHIP_EDGE = "#3D4F66"
GRID = "#24344B"

# Text tokens.
TEXT_LIGHT = "#E2E8F0"
TEXT_MUTED = "#94A3B8"

# Accent (executive sky blue) + semantic tokens.
ACCENT = "#38BDF8"
ACCENT_SOFT = "#7DD3FC"
ACCENT_DEEP = "#0284C7"
ACCENT_PALE = "#BAE6FD"
NEUTRAL = "#475569"

# Semantic series colours: tonal blues + muted slate flags (no circus colours).
POSITIVE = "#0EA5E9"
WARNING = "#94A3B8"
NEGATIVE = "#64748B"

# Hero-card gradients (CSS ``background`` values).
GRAD_HERO_A = "linear-gradient(135deg, #0369A1 0%, #0284C7 55%, #38BDF8 100%)"
GRAD_HERO_B = "linear-gradient(135deg, #0C4A6E 0%, #075985 55%, #7DD3FC 100%)"
GRAD_CTA = "linear-gradient(135deg, #0284C7 0%, #38BDF8 100%)"

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
    font-size: 11px;
    padding: 0 4px;
}}
/* Keep the filter chip lists compact so the sidebar stays scannable. */
[data-testid="stMultiSelect"] [data-baseweb="tag"] {{
    margin-bottom: 2px;
}}
[data-testid="stMultiSelect"] ul {{
    max-height: 92px;
    overflow-y: auto;
}}
[data-testid="stMultiSelect"] [data-baseweb="input"] > div {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
[data-testid="stMultiSelect"] input {{ color: {TEXT_LIGHT}; }}
[data-baseweb="tag"] svg {{ fill: {TEXT_MUTED}; }}
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

/* ---------- KPI card: dark tile with a cyan top accent ---------- */
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
.kpi-delta.up {{ color: {ACCENT_SOFT}; background: #0B2E4A; border-color: {ACCENT}; }}
.kpi-delta.down {{ color: {NEGATIVE}; background: #28303B; border-color: {NEGATIVE}; }}

/* ---------- Hero gradient card (the two large KPI blocks) ---------- */
.hero-card {{
    background: {GRAD_HERO_A};
    border-radius: 16px;
    padding: 20px 22px 18px 22px;
    margin-bottom: 14px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
    height: 100%;
}}
.hero-card.hero-alt {{ background: {GRAD_HERO_B}; }}
.hero-card::after {{
    content: "";
    position: absolute;
    right: -50px; top: -70px;
    width: 190px; height: 190px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.10);
}}
.hero-label {{
    color: rgba(255, 255, 255, 0.85);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    position: relative; z-index: 2;
}}
.hero-value {{
    color: #FFFFFF;
    font-size: 34px;
    font-weight: 800;
    line-height: 1.1;
    margin: 8px 0 4px 0;
    position: relative; z-index: 2;
}}
.hero-value .unit {{ font-size: 15px; font-weight: 700; opacity: 0.85; margin-left: 4px; }}
.hero-sub {{
    color: rgba(255, 255, 255, 0.90);
    font-size: 12px;
    font-weight: 600;
    position: relative; z-index: 2;
}}
.hero-foot {{
    color: rgba(255, 255, 255, 0.75);
    font-size: 11px;
    margin-top: 8px;
    position: relative; z-index: 2;
}}

/* ---------- Compact stat pill (icon + label + value chip) ---------- */
.pill {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 9px 12px;
    margin-bottom: 9px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}
.pill-left {{ display: flex; align-items: center; gap: 8px; }}
.pill-dot {{
    width: 26px; height: 26px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 800;
    color: #FFFFFF;
    flex: 0 0 auto;
}}
.pill-label {{ color: {TEXT_MUTED}; font-size: 12px; font-weight: 600; }}
.pill-value {{
    color: {TEXT_LIGHT};
    font-size: 13px;
    font-weight: 800;
    background: {CHIP_BG};
    border: 1px solid {CHIP_EDGE};
    border-radius: 999px;
    padding: 2px 9px;
}}
.pill-value.pos {{ color: {POSITIVE}; }}
.pill-value.warn {{ color: {WARNING}; }}
.pill-value.neg {{ color: {NEGATIVE}; }}

/* ---------- Panel wrapper (chart cards) ---------- */
.panel {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 14px 16px 12px 16px;
    margin-bottom: 14px;
}}
.panel-title {{
    color: {TEXT_LIGHT};
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 2px;
}}
.panel-sub {{ color: {TEXT_MUTED}; font-size: 11px; margin-bottom: 6px; }}

/* Re-skin Streamlit's bordered container as a dark chart panel. */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {CARD_BG};
    border: 1px solid {BORDER} !important;
    border-radius: 16px;
    padding: 12px 14px 8px 14px;
}}
[data-testid="stVerticalBlockBorderWrapper"] > div {{
    gap: 0.35rem;
}}

/* ---------- Colour-keyed legend (rendered as HTML) ---------- */
.lg-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
    border-bottom: 1px solid {GRID};
}}
.lg-row:last-child {{ border-bottom: none; }}
.lg-swatch {{
    width: 9px; height: 9px;
    border-radius: 3px;
    flex: 0 0 auto;
}}
.lg-label {{
    color: {TEXT_MUTED};
    font-size: 12px;
    font-weight: 600;
    flex: 1 1 auto;
}}
.lg-value {{
    color: {TEXT_LIGHT};
    font-size: 12px;
    font-weight: 700;
}}
.lg-share {{
    color: {ACCENT};
    font-size: 11px;
    font-weight: 700;
    width: 46px;
    text-align: right;
}}

/* ---------- Sidebar navigation ---------- */
.nav-brand {{
    color: {TEXT_LIGHT};
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 0.01em;
    padding: 2px 0 4px 0;
}}
.nav-brand span {{ color: {ACCENT}; }}
.nav-section {{
    color: {ACCENT};
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin: 18px 0 8px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.nav-section::after {{
    content: "";
    flex: 1 1 auto;
    height: 1px;
    background: {BORDER};
}}
.nav-item {{
    display: flex;
    align-items: center;
    gap: 9px;
    color: {TEXT_MUTED};
    font-size: 13px;
    font-weight: 600;
    padding: 7px 10px;
    border-radius: 9px;
    margin-bottom: 2px;
    border-left: 2px solid transparent;
}}
.nav-item.active {{
    color: {TEXT_LIGHT};
    background: {CARD_BG};
    border-left-color: {ACCENT};
    box-shadow: inset 0 0 0 1px {BORDER};
}}
.nav-item .ni-icon {{
    width: 20px; text-align: center;
    color: {ACCENT}; font-size: 13px;
}}
/* Real <a> nav links rendered by the bespoke sidebar */
.nav-link {{
    display: flex;
    align-items: center;
    gap: 9px;
    color: {TEXT_MUTED};
    font-size: 13px;
    font-weight: 600;
    text-decoration: none !important;
    padding: 7px 10px;
    border-radius: 9px;
    margin-bottom: 2px;
    border-left: 2px solid transparent;
    transition: background 120ms ease, color 120ms ease;
}}
.nav-link:hover {{
    color: {TEXT_LIGHT};
    background: {CARD_HI};
    text-decoration: none !important;
}}
.nav-link .ni-icon {{
    width: 20px; text-align: center;
    color: {ACCENT}; font-size: 13px;
    text-decoration: none;
}}
.nav-link.nav-active {{
    color: {TEXT_LIGHT};
    background: {CARD_BG};
    border-left-color: {ACCENT};
    box-shadow: inset 0 0 0 1px {BORDER};
}}
.nav-link.nav-active .ni-icon {{ color: {ACCENT}; }}
.nav-sub {{
    color: {TEXT_MUTED};
    font-size: 12px;
    padding: 4px 0 4px 31px;
    font-weight: 500;
}}
.nav-sub.active {{ color: {ACCENT_SOFT}; font-weight: 700; }}

/* Hide Streamlit's own multipage nav: we render a bespoke sidebar. */
[data-testid="stSidebarNav"] {{ display: none; }}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{ padding-top: 0.4rem; }}

/* ---------- Profile block + CTA at the bottom of the sidebar ---------- */
.profile {{
    display: flex;
    align-items: center;
    gap: 10px;
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 9px 11px;
    margin-top: 14px;
}}
.avatar {{
    width: 30px; height: 30px;
    border-radius: 9px;
    background: {GRAD_HERO_A};
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 800;
    display: flex; align-items: center; justify-content: center;
    flex: 0 0 auto;
}}
.profile-name {{ color: {TEXT_LIGHT}; font-size: 12px; font-weight: 700; }}
.profile-role {{ color: {TEXT_MUTED}; font-size: 10px; }}
.cta {{
    display: block;
    width: 100%;
    text-align: center;
    background: {GRAD_CTA};
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 700;
    padding: 9px 0;
    border-radius: 10px;
    margin-top: 10px;
    border: none;
}}
/* The sidebar "Export Report" download button wears the CTA gradient. */
[data-testid="stSidebar"] .stDownloadButton button {{
    background: {GRAD_CTA};
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 700;
    padding: 0.4rem 0;
    margin-top: 10px;
    width: 100%;
}}
[data-testid="stSidebar"] .stDownloadButton button:hover {{
    background: {ACCENT_DEEP};
    color: #FFFFFF;
    border: none;
}}

/* ---------- Section title + status banner ---------- */
.section-title {{
    color: {ACCENT};
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 6px 0 12px 0;
}}
.status-banner {{
    background: #0B1B24;
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
    layout = dict(
        template="plotly_dark",
        paper_bgcolor=CANVAS_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT_MUTED, family="Segoe UI, Inter, sans-serif", size=12),
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
    if title:
        # Only set a title when there is one: passing ``title=None`` resets
        # the title to the template default, which plotly.js then renders as
        # the literal string "undefined".
        layout["title"] = dict(
            text=title,
            font=dict(color=TEXT_LIGHT, size=14),
            x=0.0,
            xanchor="left",
            xref="container",
            y=0.99,
            yanchor="top",
            yref="container",
        )
    fig.update_layout(**layout)
    return fig
