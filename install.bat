@echo off
echo ====================================
echo Bot de Viaticos - Instalacion
echo ====================================
echo.

REM Verificar Python
echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    echo Por favor instala Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK - Python instalado
echo.

REM Instalar dependencias
echo [2/4] Instalando dependencias de Python...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)
echo OK - Dependencias instaladas
echo.

REM Verificar Tesseract
echo [3/4] Verificando Tesseract OCR...
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo ADVERTENCIA: Tesseract no esta instalado o no esta en el PATH
    echo.
    echo Por favor instala Tesseract desde:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Despues de instalarlo, agrega la ruta al PATH del sistema
    echo Ruta tipica: C:\Program Files\Tesseract-OCR
    echo.
    pause
) else (
    echo OK - Tesseract instalado
)
echo.

REM Configurar token
echo [4/4] Configuracion del TOKEN...
echo.
echo IMPORTANTE: Necesitas configurar tu TOKEN de Telegram
echo.
echo 1. Abre Telegram y busca: @BotFather
echo 2. Envia: /newbot
echo 3. Sigue las instrucciones
echo 4. Copia el TOKEN que te da
echo 5. Abre bot_viaticos.py y pega el TOKEN en la linea 20:
echo    TOKEN = 'TU_TOKEN_AQUI'
echo.
pause

echo.
echo ====================================
echo Instalacion completada!
echo ====================================
echo.
echo Para ejecutar el bot:
echo   python bot_viaticos.py
echo.
pause
