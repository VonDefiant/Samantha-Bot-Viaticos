#!/bin/bash
# Script para detener Samantha Bot en Linux

echo "=========================================="
echo "  Deteniendo Samantha Bot"
echo "=========================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Buscar procesos del bot
PROCESSES=$(ps aux | grep "python.*main.py" | grep -v grep)

if [ -z "$PROCESSES" ]; then
    echo -e "${YELLOW}⚠ No se encontraron procesos del bot corriendo${NC}"
    exit 0
fi

echo "Procesos encontrados:"
echo "$PROCESSES"
echo ""

# Preguntar confirmación
read -p "¿Quieres detener estos procesos? (s/n): " response

if [[ "$response" == "s" || "$response" == "S" ]]; then
    echo "Deteniendo procesos..."
    pkill -f "python.*main.py"

    # Esperar un momento
    sleep 2

    # Verificar si se detuvieron
    REMAINING=$(ps aux | grep "python.*main.py" | grep -v grep | wc -l)

    if [ $REMAINING -eq 0 ]; then
        echo -e "${GREEN}✓ Todos los procesos del bot han sido detenidos${NC}"
    else
        echo -e "${YELLOW}⚠ Algunos procesos no se pudieron detener${NC}"
        echo "Intenta forzar el cierre con: pkill -9 -f 'python.*main.py'"
    fi
else
    echo "Operación cancelada."
fi
