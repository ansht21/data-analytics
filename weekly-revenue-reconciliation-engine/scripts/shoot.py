"""Capture full-page screenshots of the live Streamlit dashboard pages.

Run AFTER `streamlit run streamlit_app/Dashboard.py` is up on :8501.
Output: docs/images/*.png (used by README.md).
"""

from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8501"
OUT = Path(__file__).resolve().parents[1] / "docs" / "images"

PAGES = [
    ("", "01_dashboard_home"),
    ("/Executive_Summary", "02_executive_summary"),
    ("/Weekly_Trends", "03_weekly_trends"),
    ("/Leakage_Analysis", "04_leakage_analysis"),
    ("/Exception_Audit", "05_exception_audit"),
]

# Prefer the Playwright-managed browser; fall back to a local install.
CHROMIUM_FALLBACKS = [
    Path.home() / "AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe",
    Path.home() / "AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe",
]


def _launch(p):
    """Launch Chromium, preferring the Playwright-managed build."""
    try:
        return p.chromium.launch(headless=True)
    except Exception:
        for exe in CHROMIUM_FALLBACKS:
            if exe.exists():
                return p.chromium.launch(executable_path=str(exe), headless=True)
        raise


def main() -> None:
    """Screenshot every dashboard page at 1600px width."""
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = _launch(p)
        page = browser.new_page(viewport={"width": 1600, "height": 1200},
                                device_scale_factor=1)
        for url, name in PAGES:
            print(f"Shooting {name} ...", flush=True)
            page.goto(BASE + url, wait_until="networkidle", timeout=90000)
            # Wait for Streamlit app container + spinner to disappear.
            page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=60000)
            time.sleep(10)  # data load + plotly render
            page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
            print(f"  -> {name}.png ({(OUT / f'{name}.png').stat().st_size // 1024} KB)",
                  flush=True)
        browser.close()
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
