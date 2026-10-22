param(
    [string]$Xlsx = "C:\Users\ansht\data-analytics\weekly-revenue-reconciliation-engine\reports\Command_Center_Preview.xlsx",
    [string]$Png  = "C:\Users\ansht\data-analytics\weekly-revenue-reconciliation-engine\reports\command_center_excel.png",
    [string]$Png2 = "C:\Users\ansht\data-analytics\weekly-revenue-reconciliation-engine\reports\command_center_excel_lower.png"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Drawing;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
}
"@

$excel = New-Object -ComObject Excel.Application
$excel.DisplayAlerts = $false
try {
    $book = $excel.Workbooks.Open($Xlsx)
    $sheet = $book.Worksheets.Item(1)
    $sheet.Activate()
    $excel.Visible = $true
    $excel.WindowState = -4137          # xlMaximized
    $excel.ActiveWindow.Zoom = 80
    $sheet.Range("A1").Select() | Out-Null
    Start-Sleep -Seconds 4

    # PrintWindow renders the Excel window itself, so other apps on top of
    # it (the terminal) do not appear in the capture.
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
    $bmp.Save($Png, [System.Drawing.Imaging.ImageFormat]::Png)
    $gfx.Dispose(); $bmp.Dispose()

    # Second capture: scrolled to the lower half of the dashboard.
    $sheet.Range("A28").Select() | Out-Null
    $excel.ActiveWindow.ScrollRow = 26
    $excel.ActiveWindow.ScrollColumn = 1
    Start-Sleep -Seconds 3
    $bmp2 = New-Object System.Drawing.Bitmap($w, $h)
    $gfx2 = [System.Drawing.Graphics]::FromImage($bmp2)
    $hdc2 = $gfx2.GetHdc()
    [Win32]::PrintWindow($hwnd, $hdc2, 2) | Out-Null
    $gfx2.ReleaseHdc($hdc2)
    $bmp2.Save($Png2, [System.Drawing.Imaging.ImageFormat]::Png)
    $gfx2.Dispose(); $bmp2.Dispose()

    $book.Close($false)
    Write-Output "Exported -> $Png / $Png2 ($w x $h)"
}
finally {
    $excel.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
}
