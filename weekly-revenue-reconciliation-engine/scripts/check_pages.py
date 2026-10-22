"""Smoke-test every Streamlit page with AppTest.

Runs each page script in-process and reports any exception, so a broken
page is caught without launching the app.

Usage:
    python scripts/check_pages.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PAGES = [
    "streamlit_app/Dashboard.py",
    "streamlit_app/pages/1_Executive_Summary.py",
    "streamlit_app/pages/2_Weekly_Trends.py",
    "streamlit_app/pages/3_Leakage_Analysis.py",
    "streamlit_app/pages/4_Exception_Audit.py",
]


def main() -> None:
    """Run every page and report failures."""
    failures = 0
    for page in PAGES:
        path = ROOT / page
        if not path.exists():
            print(f"MISSING  {page}")
            failures += 1
            continue
        try:
            app = AppTest.from_file(str(path), default_timeout=180)
            app.run()
            if app.exception:
                failures += 1
                print(f"FAIL     {page}")
                for exc in app.exception:
                    print(f"         {exc.value}")
            else:
                print(f"OK       {page}  "
                      f"(markdown={len(app.markdown)}, "
                      f"dataframes={len(app.dataframe)})")
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures += 1
            print(f"ERROR    {page}: {type(exc).__name__}: {exc}")
    print(f"\n{failures} failing page(s)")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
