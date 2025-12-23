#!/bin/bash
# Script de instalación para Samantha Bot en Linux/Debian
# Instala dependencias y configura el entorno

echo "=========================================="
echo "  Instalación de Samantha Bot - Linux"
echo "=========================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar si Python 3 está instalado
echo "Verificando Python 3..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no está instalado${NC}"
    echo "Instalando Python 3..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
else
    echo -e "${GREEN}✓ Python 3 encontrado: $(python3 --version)${NC}"
fi

# Verificar si pip está instalado
echo ""
echo "Verificando pip..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 no está instalado${NC}"
    echo "Instalando pip3..."
    sudo apt-get install -y python3-pip
else
    echo -e "${GREEN}✓ pip3 encontrado${NC}"
fi

# Verificar si Tesseract está instalado
echo ""
echo "Verificando Tesseract OCR..."
if ! command -v tesseract &> /dev/null; then
    echo -e "${YELLOW}⚠ Tesseract OCR no está instalado${NC}"
    echo "Instalando Tesseract OCR y el paquete de idioma español..."
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr tesseract-ocr-spa
    echo -e "${GREEN}✓ Tesseract OCR instalado${NC}"
else
    echo -e "${GREEN}✓ Tesseract OCR encontrado: $(tesseract --version | head -n 1)${NC}"

    # Verificar si tiene el paquete de español
    if ! tesseract --list-langs 2>/dev/null | grep -q "spa"; then
        echo -e "${YELLOW}⚠ Instalando paquete de idioma español...${NC}"
        sudo apt-get install -y tesseract-ocr-spa
    fi
fi

# Crear entorno virtual
echo ""
echo "Creando entorno virtual..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠ El entorno virtual ya existe. Eliminando para crear uno nuevo...${NC}"
    rm -rf venv
fi

python3 -m venv venv
echo -e "${GREEN}✓ Entorno virtual creado${NC}"

# Activar entorno virtual e instalar dependencias
echo ""
echo "Instalando dependencias de Python..."
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencias instaladas correctamente${NC}"
else
    echo -e "${RED}❌ Error al instalar dependencias${NC}"
    deactivate
    exit 1
fi

# Crear archivo .env si no existe
echo ""
if [ ! -f ".env" ]; then
    echo "Creando archivo .env desde .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✓ Archivo .env creado${NC}"
    echo ""
    echo -e "${YELLOW}=========================================="
    echo "  ⚠ IMPORTANTE ⚠"
    echo "=========================================="
    echo "Debes editar el archivo .env y agregar tu token de Telegram:"
    echo ""
    echo "  nano .env"
    echo ""
    echo "O usa tu editor favorito (vim, vi, etc.)"
    echo -e "==========================================${NC}"
else
    echo -e "${GREEN}✓ Archivo .env ya existe${NC}"
fi

# Crear directorios necesarios
echo ""
echo "Creando directorios necesarios..."
mkdir -p logs
mkdir -p facturas
echo -e "${GREEN}✓ Directorios creados${NC}"

deactivate

echo ""
echo -e "${GREEN}=========================================="
echo "  ✓ Instalación completada"
echo "==========================================${NC}"
echo ""
echo "Próximos pasos:"
echo "1. Edita el archivo .env con tu token: nano .env"
echo "2. Inicia el bot con: ./start.sh"
echo ""
echo "Para detener el bot usa: ./stop.sh"
echo ""
