@echo off
chcp 65001 >nul
title WESTVISION ARTS
cd /d "%~dp0"

echo ========================================
echo        WESTVISION ARTS - Kuanza
echo ========================================
echo.

REM --- Angalia Python ---
python --version >nul 2>&1
if errorlevel 1 (
  echo [KOSA] Python haijapatikana kwenye kompyuta hii.
  echo Tafadhali sakinisha Python kutoka: https://python.org/downloads
  echo Wakati wa ku-install, weka alama kwenye "Add Python to PATH".
  echo.
  pause
  exit /b
)

REM --- Sakinisha mahitaji (mara ya kwanza) ---
if not exist ".deps_done" (
  echo Inasakinisha mahitaji... subiri kidogo.
  python -m pip install --disable-pip-version-check -q -r requirements.txt
  if errorlevel 1 (
     echo [KOSA] Imeshindikana kusakinisha mahitaji. Angalia intaneti yako.
     pause
     exit /b
  )
  echo done > .deps_done
)

echo.
echo App inaanza... Browser itafunguka yenyewe baada ya sekunde chache.
echo ---------------------------------------------------------------
echo  USIFUNGE dirisha hili. App ipo hai mradi tu dirisha hili lipo wazi.
echo  Kufunga app: funga dirisha hili au bonyeza CTRL + C.
echo ---------------------------------------------------------------
echo.

REM --- Fungua browser baada ya sekunde 4 (wakati server inaanza) ---
start "" cmd /c "timeout /t 4 >nul & start http://127.0.0.1:5000"

REM --- Anzisha server ---
python app.py

echo.
echo App imezimika.
pause
