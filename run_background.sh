#!/bin/bash
# Script para ejecutar Samantha Bot en segundo plano (background)
# Útil para servidores donde quieres que el bot siga corriendo

echo "=========================================="
echo "  Iniciando Samantha Bot en Background"
echo "=========================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificar si el entorno virtual existe
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Error: El entorno virtual no existe${NC}"
    echo "Ejecuta primero: ./install.sh"
    exit 1
fi

# Verificar si .env existe
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: El archivo .env no existe${NC}"
    echo "Crea el archivo .env con tu token de Telegram"
    exit 1
fi

# Verificar si hay procesos corriendo
EXISTING_PROCESSES=$(ps aux | grep "python.*main.py" | grep -v grep | wc -l)

if [ $EXISTING_PROCESSES -gt 0 ]; then
    echo -e "${YELLOW}⚠ El bot ya está corriendo${NC}"
    echo "Usa ./stop.sh para detenerlo primero"
    exit 1
fi

# Activar entorno virtual e iniciar en background
echo "Iniciando bot en segundo plano..."

# Ir al directorio del script
cd "$(dirname "$0")"

# Iniciar con nohup para que siga corriendo después de cerrar la sesión
nohup venv/bin/python main.py > logs/bot_output.log 2>&1 &

# Obtener PID del proceso
BOT_PID=$!

# Esperar un momento para verificar que inició correctamente
sleep 3

# Verificar si el proceso sigue corriendo
if ps -p $BOT_PID > /dev/null; then
    echo -e "${GREEN}✓ Bot iniciado correctamente en segundo plano${NC}"
    echo ""
    echo "PID del proceso: $BOT_PID"
    echo "Logs en: logs/bot_output.log"
    echo ""
    echo "Para ver los logs en tiempo real:"
    echo "  tail -f logs/bot_output.log"
    echo ""
    echo "Para detener el bot:"
    echo "  ./stop.sh"
    echo ""

    # Guardar PID en archivo para referencia
    echo $BOT_PID > .bot_pid
else
    echo -e "${RED}❌ Error: El bot no pudo iniciarse${NC}"
    echo "Revisa los logs en: logs/bot_output.log"
    exit 1
fi
