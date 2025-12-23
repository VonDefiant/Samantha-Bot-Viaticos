"""
Configuración del Bot de Viáticos Samantha
Carga variables de entorno y constantes del sistema
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ==================== CONFIGURACIÓN PRINCIPAL ====================

# Token de Telegram Bot (desde variable de entorno)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# NIT de tu empresa (para excluir de proveedores)
NIT_EMPRESA = os.getenv('NIT_EMPRESA', '71224556')

# ==================== ESTADOS DE CONVERSACIÓN ====================
TIPO_GASTO, PHOTO, CONFIRMAR, EDITAR_CAMPO, EDITAR_VALOR = range(5)

# ==================== TIPOS DE GASTO ====================
TIPOS_GASTO = ['ALIMENTACIÓN', 'COMBUSTIBLE']

# ==================== CONFIGURACIÓN DE ARCHIVOS ====================
FACTURAS_FOLDER = 'facturas'
DATABASE_NAME = 'viaticos.db'

# ==================== CONFIGURACIÓN DE OCR ====================
OCR_CONFIG = {
    'lang': 'spa',
    'config': '--psm 6'
}

# ==================== PATRONES REGEX PARA OCR ====================
OCR_PATTERNS = {
    'nit': r'\d{6,}',
    'serie': r'[A-Z0-9]{8,}',
    'numero': r'\d{6,}',
    'monto': r'Q\s*[\d,]+\.?\d*'
}

# ==================== CONFIGURACIÓN DE EXCEL ====================
EXCEL_CONFIG = {
    'data_start_row': 7,
    'columns': ['FECHA', 'NIT PROVEEDOR', 'SERIE', 'No. COMPROBANTE', 'TIPO DE GASTO', 'MONTO Q.'],
    'column_widths': {
        'A': 8,
        'B': 12,
        'C': 12,
        'D': 18,
        'E': 15,
        'F': 18,
        'G': 18,
        'H': 12
    }
}

# ==================== VALIDACIÓN ====================
def validate_config():
    """Validar que la configuración esté completa"""
    if not TELEGRAM_TOKEN:
        raise ValueError(
            "❌ ERROR: TELEGRAM_TOKEN no está configurado.\n"
            "Por favor, crea un archivo .env con tu token:\n"
            "TELEGRAM_TOKEN=tu_token_aqui"
        )
    return True
