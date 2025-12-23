@echo off
:: =============================================
:: Samantha Bot - Script de Inicio
:: =============================================

echo.
echo ========================================
echo   Samantha - Bot de Viaticos
echo ========================================
echo.

:: Verificar si ya hay instancias de Python corriendo
tasklist | findstr /I "python.exe" >nul
if not errorlevel 1 (
    echo [ADVERTENCIA] Se detectaron procesos de Python en ejecucion
    echo.
    echo Esto puede causar conflictos. Deseas cerrarlos? [S/N]
    choice /C SN /N /M "Presiona S para cerrar o N para continuar: "
    if errorlevel 2 (
        echo.
        echo Continuando con procesos existentes...
        echo Si hay errores, ejecuta kill_bot.bat primero
        echo.
    ) else (
        echo.
        echo Cerrando procesos de Python...
        taskkill /F /IM python.exe >nul 2>&1
        echo Procesos cerrados.
        timeout /t 2 >nul
        echo.
    )
)
echo.

:: Verificar que existe el archivo .env
if not exist ".env" (
    echo [ERROR] No se encontro el archivo .env
    echo.
    echo Por favor crea un archivo .env con tu configuracion:
    echo   1. Copia .env.example a .env
    echo   2. Edita .env y agrega tu TELEGRAM_TOKEN
    echo.
    pause
    exit /b 1
)

:: Verificar que existe el entorno virtual
if not exist "venv\" (
    echo [AVISO] No se encontro el entorno virtual
    echo Ejecuta install.bat primero para instalar las dependencias
    echo.
    pause
    exit /b 1
)

:: Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat

:: Ejecutar bot
echo Iniciando bot...
echo.
python main.py

:: En caso de error
if errorlevel 1 (
    echo.
    echo [ERROR] El bot se detuvo con errores
    echo Revisa los logs en la carpeta logs/
    echo.
    pause
)

deactivate
