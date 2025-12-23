@echo off
:: =============================================
:: Samantha Bot - Script de Instalacion
:: =============================================

echo.
echo ========================================
echo   Samantha - Bot de Viaticos
echo   Script de Instalacion
echo ========================================
echo.

:: Verificar Python
echo [1/6] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH
    echo.
    echo Por favor instala Python 3.8 o superior desde:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: Durante la instalacion, marca la opcion "Add Python to PATH"
    pause
    exit /b 1
)
python --version
echo.

:: Crear entorno virtual
echo [2/6] Creando entorno virtual...
if exist "venv\" (
    echo Ya existe un entorno virtual, omitiendo...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
    echo OK - Entorno virtual creado
)
echo.

:: Activar entorno virtual
echo [3/6] Activando entorno virtual...
call venv\Scripts\activate.bat
echo.

:: Actualizar pip
echo [4/6] Actualizando pip...
python -m pip install --upgrade pip
echo.

:: Instalar dependencias
echo [5/6] Instalando dependencias de Python...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] No se pudieron instalar las dependencias
    pause
    exit /b 1
)
echo OK - Dependencias instaladas
echo.

:: Verificar Tesseract
echo [6/6] Verificando Tesseract OCR...
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo [ADVERTENCIA] Tesseract no esta instalado o no esta en el PATH
    echo.
    echo Tesseract es NECESARIO para el OCR de facturas
    echo.
    echo Por favor instala Tesseract desde:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Despues de instalarlo, agrega la ruta al PATH del sistema
    echo Ruta tipica: C:\Program Files\Tesseract-OCR
    echo.
) else (
    tesseract --version
    echo OK - Tesseract instalado correctamente
)
echo.

:: Crear carpetas necesarias
if not exist "facturas\" mkdir facturas
if not exist "logs\" mkdir logs
echo Carpetas creadas: facturas, logs
echo.

:: Configurar archivo .env
echo ========================================
echo   Configuracion del Bot
echo ========================================
echo.

if not exist ".env" (
    echo Creando archivo .env desde .env.example...
    copy .env.example .env >nul
    echo.
    echo [IMPORTANTE] Debes editar el archivo .env y configurar tu TOKEN
    echo.
    echo Pasos:
    echo 1. Abre Telegram y busca: @BotFather
    echo 2. Envia el comando: /newbot
    echo 3. Sigue las instrucciones para crear tu bot
    echo 4. Copia el TOKEN que te da BotFather
    echo 5. Abre el archivo .env con un editor de texto
    echo 6. Reemplaza "tu_token_aqui" con tu TOKEN real
    echo 7. Guarda el archivo .env
    echo.
    notepad .env
) else (
    echo El archivo .env ya existe
    echo.
)

echo.
echo ========================================
echo   Instalacion Completada!
echo ========================================
echo.
echo Que hacer ahora:
echo.
echo 1. Asegurate de haber configurado tu TOKEN en el archivo .env
echo 2. Ejecuta start.bat para iniciar el bot
echo.
echo Comandos utiles:
echo   start.bat        - Iniciar el bot
echo   install.bat      - Ejecutar esta instalacion nuevamente
echo.

deactivate
pause
