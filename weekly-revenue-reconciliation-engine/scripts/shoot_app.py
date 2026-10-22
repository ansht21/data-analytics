"""Launch the Streamlit app, screenshot it, then shut it down.

Runs the real app (not the static preview) so the visual QA covers the
genuine Streamlit layout, including the bespoke sidebar and the Plotly
chart sizing behaviour.

Usage:
    python scripts/shoot_app.py [port] [png_path]
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8601
PNG = (Path(sys.argv[2]) if len(sys.argv) > 2
       else ROOT / "reports" / "app_dashboard.png")
URL = f"http://localhost:{PORT}"


def _wait_for_server(timeout: float = 60.0) -> bool:
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


def main() -> None:
    """Start the app, capture a screenshot and stop the server."""
    server = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app/Dashboard.py",
         "--server.port", str(PORT), "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
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
            page = browser.new_page(viewport={"width": 1600, "height": 1000},
                                    device_scale_factor=2)
            page.goto(URL, wait_until="networkidle")
            page.wait_for_timeout(8000)
            page.screenshot(path=str(PNG), full_page=True)
            browser.close()
        print(f"Screenshot -> {PNG}")
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
