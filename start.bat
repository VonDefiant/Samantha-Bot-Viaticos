@echo off
:: =============================================
:: Samantha Bot - Script de Inicio
:: =============================================

echo.
echo ========================================
echo   Samantha - Bot de Viaticos
echo ========================================
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
