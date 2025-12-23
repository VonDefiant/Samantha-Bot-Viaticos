@echo off
:: =============================================
:: Script para cerrar todas las instancias del bot
:: =============================================

echo.
echo ========================================
echo   Cerrando instancias del bot...
echo ========================================
echo.

echo Buscando procesos de Python...
tasklist | findstr /I "python.exe" >nul

if errorlevel 1 (
    echo No se encontraron procesos de Python ejecutandose.
    echo.
    pause
    exit /b 0
)

echo Se encontraron procesos de Python.
echo Cerrando todos los procesos de Python...
taskkill /F /IM python.exe >nul 2>&1

if errorlevel 1 (
    echo [ADVERTENCIA] No se pudieron cerrar algunos procesos.
    echo Intenta cerrarlos manualmente desde el Administrador de Tareas.
) else (
    echo.
    echo ============================================
    echo   Todos los procesos cerrados exitosamente
    echo ============================================
    echo.
    echo Ya puedes ejecutar start.bat nuevamente
)

echo.
pause
