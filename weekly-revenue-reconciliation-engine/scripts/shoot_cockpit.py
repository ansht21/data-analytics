"""Screenshot the static cockpit preview with Playwright (visual QA).

Usage:
    python scripts/shoot_cockpit.py [html_path] [png_path]
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Render the preview HTML and save a full-page PNG."""
    html = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "reports" / "cockpit_preview.html"
    png = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "reports" / "cockpit_preview.png"
    png.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1000},
                                device_scale_factor=2)
        page.goto(html.resolve().as_uri())
        page.wait_for_timeout(4000)
        page.screenshot(path=str(png), full_page=True)
        browser.close()
    print(f"Screenshot -> {png}")


if __name__ == "__main__":
    main()
