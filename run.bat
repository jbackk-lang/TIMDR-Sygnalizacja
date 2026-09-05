@echo off
setlocal
cd /d "%~dp0"

if not exist venv (
    echo [1/3] Tworze srodowisko wirtualne...
    python -m venv venv
    if errorlevel 1 (
        echo Nie mozna utworzyc venv - sprawdz czy Python jest zainstalowany i w PATH.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

echo [2/3] Instaluje zaleznosci z requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo Instalacja zaleznosci nie powiodla sie.
    pause
    exit /b 1
)

echo [3/3] Uruchamiam serwer na http://127.0.0.1:5000 ...
start "" http://127.0.0.1:5000/
python -m src.api.server

endlocal
