@echo off
REM Create a log file for console output
set CONSOLE_LOG=run_log.txt
echo Twitter Crawler Launcher > %CONSOLE_LOG%
echo =========================== >> %CONSOLE_LOG%
echo Start time: %date% %time% >> %CONSOLE_LOG%

echo Twitter Crawler Launcher
echo ===========================

REM Set environment variables
set PYTHON_URL=https://www.python.org/ftp/python/3.9.13/python-3.9.13-embed-amd64.zip
set PIP_URL=https://bootstrap.pypa.io/get-pip.py
set PORTABLE_PYTHON_DIR=%~dp0python
set APP_DIR=%~dp0
set PYTHON_EXECUTABLE=

echo Initial configuration set >> %CONSOLE_LOG%

REM Check for existing Python installation
echo Checking for existing Python installation...
echo Checking for existing Python installation... >> %CONSOLE_LOG%
where python >nul 2>nul
if %errorlevel% equ 0 (
    echo Found existing Python installation.
    echo Found existing Python installation >> %CONSOLE_LOG%
    set PYTHON_EXECUTABLE=python
) else (
    echo No system-wide Python found. Checking for portable version...
    echo No system-wide Python found. Checking for portable version... >> %CONSOLE_LOG%
    if exist "%PORTABLE_PYTHON_DIR%\python.exe" (
        echo Found portable Python.
        echo Found portable Python >> %CONSOLE_LOG%
        set PYTHON_EXECUTABLE="%PORTABLE_PYTHON_DIR%\python.exe"
    ) else (
        echo No Python found. Downloading portable version...
        echo No Python found. Downloading portable version... >> %CONSOLE_LOG%
        
        REM Download and set up portable Python
        mkdir "%PORTABLE_PYTHON_DIR%" 2>nul
        echo Downloading Python...please wait...
        echo Downloading Python...please wait... >> %CONSOLE_LOG%
        curl -L "%PYTHON_URL%" -o "%TEMP%\python.zip" 2>> %CONSOLE_LOG%
        if %errorlevel% neq 0 (
            echo Failed to download Python: %errorlevel% >> %CONSOLE_LOG%
            echo Failed to download Python. Check network or curl installation.
            pause
            exit /b 1
        )
        echo Python download completed. >> %CONSOLE_LOG%

        echo Extracting Python...
        echo Extracting Python... >> %CONSOLE_LOG%
        powershell -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%TEMP%\python.zip' -DestinationPath '%PORTABLE_PYTHON_DIR%' -Force" 2>> %CONSOLE_LOG%
        if %errorlevel% neq 0 (
            echo Failed to extract Python: %errorlevel% >> %CONSOLE_LOG%
            echo Failed to extract Python. Check PowerShell execution policy.
            pause
            exit /b 1
        )
        echo Python extraction completed. >> %CONSOLE_LOG%

        REM Configure portable Python for pip
        if exist "%PORTABLE_PYTHON_DIR%\python39._pth" (
            powershell -ExecutionPolicy Bypass -Command "(Get-Content '%PORTABLE_PYTHON_DIR%\python39._pth') -replace '#import', 'import' | Out-File '%PORTABLE_PYTHON_DIR%\python39._pth' -Encoding ASCII" 2>> %CONSOLE_LOG%
        )
        echo Portable Python configured. >> %CONSOLE_LOG%

        set PYTHON_EXECUTABLE="%PORTABLE_PYTHON_DIR%\python.exe"

        REM Install pip for portable Python
        echo Installing pip...
        echo Installing pip... >> %CONSOLE_LOG%
        curl -L "%PIP_URL%" -o "%PORTABLE_PYTHON_DIR%\get-pip.py" 2>> %CONSOLE_LOG%
        %PYTHON_EXECUTABLE% "%PORTABLE_PYTHON_DIR%\get-pip.py" --no-warn-script-location >> %CONSOLE_LOG% 2>&1
        if %errorlevel% neq 0 (
            echo Failed to install pip: %errorlevel% >> %CONSOLE_LOG%
            echo Failed to install pip.
            pause
            exit /b 1
        )
        echo Pip installation completed. >> %CONSOLE_LOG%
    )
)

REM Install dependencies using the selected Python
echo Installing dependencies...
echo Installing dependencies... >> %CONSOLE_LOG%
%PYTHON_EXECUTABLE% -m pip install --no-warn-script-location -r requirements.txt >> %CONSOLE_LOG% 2>&1
if %errorlevel% neq 0 (
    echo Failed to install dependencies: %errorlevel% >> %CONSOLE_LOG%
    echo Failed to install dependencies. Please check requirements.txt and your connection.
    pause
    exit /b 1
)
echo Dependencies installation completed. >> %CONSOLE_LOG%


REM Launch application
echo Environment ready, starting Twitter Crawler...
echo Environment ready, starting Twitter Crawler... >> %CONSOLE_LOG%
echo Starting application... >> %CONSOLE_LOG%

cd /d "%APP_DIR%"
%PYTHON_EXECUTABLE% twitter_crawler_ui.py >> %CONSOLE_LOG% 2>&1
set EXIT_CODE=%errorlevel%

if %EXIT_CODE% neq 0 (
    echo Program exited with error code: %EXIT_CODE% >> %CONSOLE_LOG%
    echo.
    echo Program exited with an error. Check %CONSOLE_LOG% for details.
    pause
)

echo Script execution completed. >> %CONSOLE_LOG%