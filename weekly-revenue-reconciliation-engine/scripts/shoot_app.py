"""Launch the Streamlit app, screenshot every page, then shut it down.

Runs the real app (not a static preview) so the visual QA covers the
genuine Streamlit layout, including the bespoke sidebar and the Plotly
chart sizing behaviour. Writes the README images into ``docs/images``.

Usage:
    python scripts/shoot_app.py [port] [out_dir]
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8601
OUT_DIR = (Path(sys.argv[2]) if len(sys.argv) > 2
           else ROOT / "docs" / "images")
URL = f"http://localhost:{PORT}"

# Streamlit's URL pathname for each page, the README image name, and the
# number of Plotly charts the page must render. The chart count is what makes
# the capture reliable: Streamlit streams the page element by element, so a
# screenshot taken before the last chart arrives shows empty panels.
PAGES = [
    ("", "01_dashboard_home", 5),
    ("/Executive_Summary", "02_executive_summary", 4),
    ("/Weekly_Trends", "03_weekly_trends", 3),
    ("/Leakage_Analysis", "04_leakage_analysis", 4),
    ("/Exception_Audit", "05_exception_audit", 0),
]

# Streamlit pins the app shell to the viewport height and scrolls inside it.
# A full-page screenshot then clips everything below the fold, so the shell
# is unpinned before the capture is taken.
UNPIN_CSS = """
html, body, #root, [data-testid='stApp'] { height: auto !important; }
[data-testid='stAppViewContainer'], [data-testid='stMain'] {
    height: auto !important; overflow: visible !important;
}
section.main, [data-testid='stMainBlockContainer'] { height: auto !important; }
"""


def _wait_for_server(timeout: float = 90.0) -> bool:
    """Block until the Streamlit server answers.

    Args:
        timeout: Maximum seconds to wait.

    Returns:
        True if the server became reachable, False on timeout.
    """
    import urllib.error
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(URL, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(1.0)
    return False


def _wait_until_stable(page, expected_plots: int,
                       timeout: float = 120.0) -> None:
    """Block until the page has finished rendering.

    Streamlit streams a page element by element and Plotly draws its charts
    asynchronously afterwards, so a screenshot taken too early shows empty
    panels and misses the lower sections. Waiting for a *fixed* delay is not
    enough either, because the charts appear one after another.

    The page is ready once the expected number of charts is present with a
    drawn SVG, the script is no longer running (the "Stop" badge in the
    toolbar disappears), and the DOM signature has stopped changing for two
    consecutive polls.

    Args:
        page: The Playwright page to poll.
        expected_plots: Number of Plotly charts the page must render.
        timeout: Maximum seconds to wait.
    """
    signature_fn = """() => {
        const plots = document.querySelectorAll('.js-plotly-plot');
        const toolbar = document.querySelector('[data-testid="stToolbar"]');
        const running = !!toolbar && /Stop/.test(toolbar.innerText || '');
        return {
            plots: plots.length,
            svgs: document.querySelectorAll('.js-plotly-plot .main-svg').length,
            elements: document.querySelectorAll(
                '[data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"]'
            ).length,
            running: running,
        };
    }"""
    deadline = time.time() + timeout
    previous: dict | None = None
    stable_since: float | None = None
    while time.time() < deadline:
        current = page.evaluate(signature_fn)
        charts_drawn = (
            current["plots"] >= expected_plots
            and current["svgs"] >= current["plots"]
        )
        if current == previous and charts_drawn and not current["running"]:
            if stable_since is None:
                stable_since = time.time()
            elif time.time() - stable_since >= 2.0:
                return
        else:
            stable_since = None
        previous = current
        time.sleep(1.0)


def main() -> None:
    """Start the app, capture every page and stop the server."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # The server log goes to a file, never to a PIPE: a pipe that is never
    # drained fills up and blocks the server mid-render, which leaves the
    # later pages half-drawn.
    log_path = ROOT / "logs" / "shoot_app_server.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "w", encoding="utf-8")
    server = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app/Dashboard.py",
         "--server.port", str(PORT), "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=str(ROOT),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        if not _wait_for_server():
            print("server did not start")
            return
        time.sleep(6)  # let the first script run finish rendering
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for route, name, expected_plots in PAGES:
                # A fresh context per page: reusing one session carries the
                # sidebar filter state across pages, which makes Streamlit
                # re-run the script endlessly and leaves the page blank.
                context = browser.new_context(
                    viewport={"width": 1600, "height": 1200},
                    device_scale_factor=2,
                )
                page = context.new_page()
                page.goto(f"{URL}{route}", wait_until="networkidle")
                _wait_until_stable(page, expected_plots)
                # Streamlit pins the app to the viewport height and scrolls
                # inside it, which makes a full-page screenshot clip the
                # lower panels. Unpin it so the whole page can be captured.
                page.add_style_tag(content=UNPIN_CSS)
                page.wait_for_timeout(4000)
                target = OUT_DIR / f"{name}.png"
                page.screenshot(path=str(target), full_page=True)
                print(f"{route or '/'} -> {target.name}")
                context.close()
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        log_file.close()


if __name__ == "__main__":
    main()
