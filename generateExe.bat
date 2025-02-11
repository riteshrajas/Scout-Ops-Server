@echo off

REM Create the Output directory if it doesn't exist
if not exist ".\Output" (
    mkdir ".\Output"
)

REM Start PowerShell loading bar in a separate process
start /b powershell -Command "Write-Progress -Activity 'Compiling' -Status 'In Progress' -PercentComplete 0; while ($true) { for ($i = 0; $i -le 100; $i += 10) { Write-Progress -Activity 'Compiling' -Status 'In Progress' -PercentComplete $i; Start-Sleep -Seconds 1 } }"

REM Run PyInstaller with icon and suppressed output
pyinstaller --noconfirm --onefile --console --icon ".\templates\logo.ico" --log-level ERROR ^
--add-data ".\README.md;." ^
--add-data ".\requirements.txt;." ^
--add-data ".\server.py;." ^
--add-data ".\App;App/" ^
--add-data ".\output;output/" ^
--add-data ".\templates;templates/" ^
--add-data ".\templates\clear_data.html;." ^
--add-data ".\templates\clear_devices.html;." ^
--add-data ".\templates\client_images.html;." ^
--add-data ".\templates\data.html;." ^
--add-data ".\templates\delete_device.html;." ^
--add-data ".\templates\devices.html;." ^
--add-data ".\templates\index.html;." ^
--add-data ".\templates\info.html;." ^
--add-data ".\App\app-release.apk;." ^
--distpath ".\Output" ^
"./server.py"

REM Stop the PowerShell loading bar
powershell -Command "Stop-Process -Name powershell -Force"

REM Display a message box indicating completion
powershell -command "Add-Type -AssemblyName PresentationFramework;[System.Windows.MessageBox]::Show('The executable has been compiled and is located in the Output folder. ', 'Compilation Complete')"
powershell -command "Add-Type -AssemblyName PresentationFramework;[System.Windows.MessageBox]::Show('Init Clean Up. ', 'Compilation Complete')"

REM Run the cleanup script
call cleanup.bat