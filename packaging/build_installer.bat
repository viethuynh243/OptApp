@echo off
REM build_installer.bat - Dong goi OptApp thanh bo cai OptApp_Setup_x.y.z.exe
REM Quy trinh: tao icon -> PyInstaller (dist) -> Inno Setup (installer)
REM Yeu cau: Python + pyinstaller + Pillow; Inno Setup 6 (ISCC.exe)
setlocal
cd /d "%~dp0\.."

echo [1/3] Tao icon...
python packaging\make_icon.py || goto :err

echo [2/3] Build PyInstaller (onedir, windowed)...
python -m PyInstaller packaging\OptApp.spec --noconfirm --clean ^
  --distpath packaging\dist --workpath packaging\build || goto :err

echo [3/3] Bien dich Inno Setup...
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo Khong tim thay ISCC.exe. Cai Inno Setup 6: winget install JRSoftware.InnoSetup
  goto :err
)
"%ISCC%" packaging\OptApp.iss || goto :err

echo.
echo === HOAN TAT: packaging\OptApp_Setup_1.0.0.exe ===
goto :eof

:err
echo.
echo *** LOI khi dong goi. Xem thong bao ben tren. ***
exit /b 1
