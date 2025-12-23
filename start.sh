#!/bin/bash
# Script de inicio para Samantha Bot en Linux

echo "=========================================="
echo "  Iniciando Samantha Bot"
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

# Verificar si hay procesos de Python corriendo con el bot
echo "Verificando procesos existentes..."
EXISTING_PROCESSES=$(ps aux | grep "python.*main.py" | grep -v grep | wc -l)

if [ $EXISTING_PROCESSES -gt 0 ]; then
    echo -e "${YELLOW}⚠ Hay $EXISTING_PROCESSES proceso(s) del bot corriendo${NC}"
    echo ""
    echo "Procesos encontrados:"
    ps aux | grep "python.*main.py" | grep -v grep
    echo ""
    read -p "¿Quieres detenerlos antes de continuar? (s/n): " response

    if [[ "$response" == "s" || "$response" == "S" ]]; then
        echo "Deteniendo procesos..."
        pkill -f "python.*main.py"
        sleep 2
        echo -e "${GREEN}✓ Procesos detenidos${NC}"
    else
        echo -e "${YELLOW}⚠ El bot puede tener conflictos si hay múltiples instancias corriendo${NC}"
    fi
fi

# Activar entorno virtual
echo ""
echo "Activando entorno virtual..."
source venv/bin/activate

# Verificar que Python está disponible
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Error: Python no está disponible en el entorno virtual${NC}"
    exit 1
fi

# Iniciar el bot
echo ""
echo -e "${GREEN}✓ Iniciando Samantha Bot...${NC}"
echo ""
echo "Presiona Ctrl+C para detener el bot"
echo "=========================================="
echo ""

python main.py

# Desactivar entorno virtual al salir
deactivate

echo ""
echo "Bot detenido."
