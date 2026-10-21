"""Export high-resolution images of Excel sheets using Excel COM interface."""
from __future__ import annotations

import os
import time
from pathlib import Path

import win32com.client
from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
DOCS_IMG = ROOT / "docs" / "images"

# Find the latest generated Excel file
excel_files = sorted(REPORT_DIR.glob("Revenue_Reconciliation_Dashboard_*.xlsx"), key=os.path.getmtime, reverse=True)
if not excel_files:
    raise FileNotFoundError("No generated Excel dashboard found in reports/")

latest_excel = excel_files[0]
print(f"Opening Excel file: {latest_excel}")

excel = win32com.client.Dispatch("Excel.Application")
excel.Visible = True  # Must be visible for Range.CopyPicture to grab clipboard
excel.DisplayAlerts = False

try:
    wb = excel.Workbooks.Open(str(latest_excel))
    DOCS_IMG.mkdir(parents=True, exist_ok=True)
    
    # 1. Executive Dashboard tab
    ws_exec = wb.Sheets("Executive Dashboard")
    ws_exec.Activate()
    excel.ActiveWindow.Zoom = 110
    time.sleep(1)
    
    # Copy range A1:M36 (covers title, 2x3 KPI cards, and embedded chart)
    rng_exec = ws_exec.Range("A1:M36")
    rng_exec.CopyPicture(Appearance=1, Format=2)  # xlScreen=1, xlBitmap=2
    time.sleep(1)
    
    img_exec = ImageGrab.grabclipboard()
    if img_exec:
        out_exec = DOCS_IMG / "06_excel_executive_dashboard.png"
        img_exec.save(str(out_exec), "PNG")
        print(f"Saved: {out_exec} ({img_exec.size})")
    else:
        print("Clipboard empty for Executive Dashboard")

    # 2. Weekly Trends tab
    # NOTE: the Trends tab now has 18 columns (Settled Base, Settled Clearance %,
    # Days Observed and Partial Week were added), so the capture range is
    # A1:R22 rather than the old A1:N22.
    ws_trends = wb.Sheets("Weekly Trends")
    ws_trends.Activate()
    excel.ActiveWindow.Zoom = 100
    time.sleep(1)
    
    rng_trends = ws_trends.Range("A1:R22")
    rng_trends.CopyPicture(Appearance=1, Format=2)
    time.sleep(1)
    
    img_trends = ImageGrab.grabclipboard()
    if img_trends:
        out_trends = DOCS_IMG / "07_excel_weekly_trends.png"
        img_trends.save(str(out_trends), "PNG")
        print(f"Saved: {out_trends} ({img_trends.size})")
    else:
        print("Clipboard empty for Weekly Trends")

finally:
    wb.Close(SaveChanges=False)
    excel.Quit()
    print("Excel closed cleanly.")
