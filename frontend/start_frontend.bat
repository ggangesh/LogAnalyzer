@echo off
echo Starting LogSage AI Frontend...
echo.

REM Check if .env file exists, if not create from template
if not exist .env (
    if exist env.template (
        echo Creating .env file from template...
        copy env.template .env
        echo Please edit .env file with your configuration settings.
        echo.
    )
)

REM Start the Flask application
echo Starting Flask server on http://localhost:3000
echo Press Ctrl+C to stop the server
echo.

C:\Users\GangeshG\AppData\Local\Programs\Python\Python310\python run.py

pause