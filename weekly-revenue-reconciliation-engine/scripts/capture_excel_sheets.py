"""Export high-resolution images of Excel sheets using Excel COM interface.

Technique: copy the target range as a picture, paste it into a temporary
chart object, and export that chart straight to PNG. This renders the WHOLE
range regardless of how much is visible on screen, and never touches the
screen or system clipboard for the final image — so right-side charts (the
settlement gauge reaches ~column Q) and the detail table are never cut off,
unlike the earlier xlScreen window-grab approach.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import win32com.client

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
DOCS_IMG = ROOT / "docs" / "images"


def capture_range(excel, ws, rng: str, out_path: Path, zoom: int = 100) -> None:
    """Copy range ``rng`` to a temp chart and export it as PNG."""
    ws.Activate()
    excel.ActiveWindow.Zoom = zoom
    time.sleep(1.0)

    was_frozen = excel.ActiveWindow.FreezePanes
    excel.ActiveWindow.FreezePanes = False
    try:
        target = ws.Range(rng)
        last_error: Exception | None = None
        for _attempt in range(3):
            try:
                # xlPicture (EMF) is vector: it renders the complete range at
                # export resolution AND survives range boundaries that cut
                # floating charts. xlPrinter+xlBitmap silently fails on the
                # A1:Q49 width (GDI bitmap limit), which is why earlier
                # captures clipped the right side of the dashboard.
                co = ws.ChartObjects().Add(
                    10, float(ws.Range("A1").Top) + 4000.0,
                    float(target.Width), float(target.Height),
                )
                # Paint the temp chart dark (slate-900) so EMF rounding
                # margins never show as white slivers around the picture.
                co.Chart.ChartArea.Format.Fill.ForeColor.RGB = 2758415  # 0F172A
                co.Chart.ChartArea.Format.Line.Visible = 0
                pasted = False
                for appearance in (2, 1):  # xlPrinter first, xlScreen fallback
                    target.CopyPicture(Appearance=appearance, Format=-4147)
                    time.sleep(0.5)
                    try:
                        co.Activate()
                        time.sleep(0.3)
                        co.Chart.Paste()
                        pasted = True
                        break
                    except Exception:
                        continue
                if not pasted:
                    raise RuntimeError("Chart.Paste failed for both modes")
                co.Chart.Export(str(out_path), "PNG")
                co.Delete()
                print(f"Exported: {out_path}")
                return
            except Exception as exc:  # clipboard/COM flakiness: retry
                last_error = exc
                try:
                    ws.ChartObjects(ws.ChartObjects().Count).Delete()
                except Exception:
                    pass
                time.sleep(1.5)
        raise last_error  # type: ignore[misc]
    finally:
        excel.ActiveWindow.FreezePanes = was_frozen


# Find the latest generated Excel file
excel_files = sorted(
    REPORT_DIR.glob("Revenue_Reconciliation_Dashboard_*.xlsx"),
    key=os.path.getmtime,
    reverse=True,
)
if not excel_files:
    raise FileNotFoundError("No generated Excel dashboard found in reports/")

latest_excel = excel_files[0]
print(f"Opening Excel file: {latest_excel}")

excel = win32com.client.Dispatch("Excel.Application")
excel.Visible = True  # Chart objects need an active, visible window
excel.DisplayAlerts = False

try:
    wb = excel.Workbooks.Open(str(latest_excel))
    DOCS_IMG.mkdir(parents=True, exist_ok=True)

    # 1. Executive Dashboard tab: title, KPI hero cards, embedded charts and
    # the full weekly reconciliation detail table (rows through ~49).
    # Horizontal extent: the settlement gauge is 10 cm wide anchored at
    # column M, so it ends around column Q — the range must reach that far
    # or the gauge and the stat-pill column get clipped mid-arc.
    capture_range(
        excel, wb.Sheets("Executive Dashboard"), "A1:P49",
        DOCS_IMG / "06_excel_executive_dashboard.png", zoom=110,
    )

    # 2. Weekly Trends tab: the tab has 18 columns since Settled Base,
    # Settled Clearance %, Days Observed and Partial Week were added, so the
    # capture range is A1:R22 rather than the old A1:N22.
    capture_range(
        excel, wb.Sheets("Weekly Trends"), "A1:R22",
        DOCS_IMG / "07_excel_weekly_trends.png", zoom=100,
    )

finally:
    wb.Close(SaveChanges=False)
    excel.Quit()
    print("Excel closed cleanly.")
