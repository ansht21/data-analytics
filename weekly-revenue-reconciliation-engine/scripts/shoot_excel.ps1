param(
    [string]$Xlsx = "C:\Users\ansht\data-analytics\weekly-revenue-reconciliation-engine\reports\Revenue_Reconciliation_Dashboard_20261022_142512.xlsx",
    [string]$OutDir = "C:\Users\ansht\data-analytics\weekly-revenue-reconciliation-engine\docs\images"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Drawing;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdc, uint flags);
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
}
"@

# Sheet index (1-based) -> README image name.
$Sheets = @(
    @{ Index = 1; Name = "06_excel_executive_dashboard" },
    @{ Index = 2; Name = "07_excel_weekly_trends" }
)

if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }

$excel = New-Object -ComObject Excel.Application
$excel.DisplayAlerts = $false
try {
    $book = $excel.Workbooks.Open($Xlsx)
    $excel.Visible = $true
    $excel.WindowState = -4137          # xlMaximized
    $excel.ActiveWindow.Zoom = 80

    foreach ($spec in $Sheets) {
        $sheet = $book.Worksheets.Item($spec.Index)
        $sheet.Activate()
        $sheet.Range("A1").Select() | Out-Null
        $excel.ActiveWindow.ScrollRow = 1
        $excel.ActiveWindow.ScrollColumn = 1
        Start-Sleep -Seconds 4

        # PrintWindow renders the Excel window itself, so other apps on top
        # of it (the terminal) do not appear in the capture.
        $hwnd = [IntPtr]$excel.Hwnd
        $rect = New-Object Win32+RECT
        [Win32]::GetWindowRect($hwnd, [ref]$rect) | Out-Null
        $w = $rect.Right - $rect.Left
        $h = $rect.Bottom - $rect.Top
        $bmp = New-Object System.Drawing.Bitmap($w, $h)
        $gfx = [System.Drawing.Graphics]::FromImage($bmp)
        $hdc = $gfx.GetHdc()
        [Win32]::PrintWindow($hwnd, $hdc, 2) | Out-Null   # PW_RENDERFULLCONTENT
        $gfx.ReleaseHdc($hdc)
        $target = Join-Path $OutDir ($spec.Name + ".png")
        $bmp.Save($target, [System.Drawing.Imaging.ImageFormat]::Png)
        $gfx.Dispose(); $bmp.Dispose()
        Write-Output "Sheet $($spec.Index) -> $target ($w x $h)"
    }
    $book.Close($false)
}
finally {
    $excel.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
}
