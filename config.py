# Configuración del Bot de Viáticos
# ===================================

# Token de Telegram Bot (obtener de @BotFather)
TELEGRAM_TOKEN = "8228909123:AAEy0xFK9Ui1VtPRKBrammzeY-yT9hTwCB4"

# NIT de tu empresa (para excluir de proveedores)
NIT_EMPRESA = "71224556"

# Tipos de gasto permitidos
TIPOS_GASTO = ["ALIMENTACIÓN", "COMBUSTIBLE"]

# Configuración de OCR
OCR_CONFIG = {
    # Idioma para Tesseract
    "lang": "spa",
    
    # Configuración de Tesseract (mejora precisión)
    "config": "--psm 6",  # PSM 6 = Bloque uniforme de texto
    
    # Ruta de Tesseract (solo Windows, comentar si está en PATH)
    # "tesseract_cmd": r"C:\Program Files\Tesseract-OCR\tesseract.exe"
}

# Configuración de Base de Datos
DATABASE = {
    "name": "viaticos.db",
    "backup_enabled": True,
    "backup_interval_days": 7
}

# Configuración de Archivos
FILES = {
    "facturas_folder": "facturas",
    "excel_prefix": "viaticos",
    "photo_prefix": "factura"
}

# Configuración de Excel
EXCEL_CONFIG = {
    # Fila donde empiezan los datos (después de headers)
    "data_start_row": 7,
    
    # Columnas del formato
    "columns": [
        "No.",
        "FECHA",
        "NIT PROVEEDOR",
        "SERIE", 
        "No. COMPROBANTE",
        "TIPO DE GASTO",
        "MONTO Q."
    ],
    
    # Anchos de columna
    "column_widths": {
        "A": 8,   # No.
        "B": 12,  # FECHA
        "C": 12,  # NIT
        "D": 18,  # SERIE
        "E": 15,  # No. COMPROBANTE
        "F": 18,  # TIPO DE GASTO
        "G": 12   # MONTO
    }
}

# Patrones para extracción OCR (expresiones regulares)
OCR_PATTERNS = {
    # NIT: números de 6+ dígitos
    "nit": r"\d{6,}",
    
    # Serie: código alfanumérico de 8+ caracteres
    "serie": r"[A-Z0-9]{8,}",
    
    # Número de factura: números de 6+ dígitos
    "numero": r"\d{6,}",
    
    # Monto: patrón Q seguido de números
    "monto": r"Q\s*[\d,]+\.?\d*"
}

# Palabras clave para búsqueda en OCR
OCR_KEYWORDS = {
    "nit": ["NIT", "NUMERO DE NIT"],
    "serie": ["SERIE", "SERIE:"],
    "numero": ["NUMERO", "NÚMERO", "No.", "No"],
    "total": ["TOTAL", "TOTAL A PAGAR", "MONTO TOTAL"],
    "fecha": ["FECHA", "FECHA DE EMISION", "FECHA EMISION"]
}

# Mensajes del bot
MESSAGES = {
    "welcome": "🧾 *Bot de Control de Viáticos*\n\n"
               "Comandos disponibles:\n"
               "/nueva - Registrar nueva factura\n"
               "/resumen - Ver resumen de gastos\n"
               "/exportar - Exportar a Excel\n"
               "/lista - Ver todas las facturas\n"
               "/help - Ayuda",
    
    "processing": "⏳ Procesando factura...",
    "success": "✅ Factura registrada exitosamente!",
    "cancelled": "❌ Operación cancelada.",
    "invalid_amount": "❌ Monto inválido. Ingresa solo números (ej: 150.50)",
    "no_data": "❌ No pude extraer los datos de la factura.",
    "invalid_type": "❌ Debe ser ALIMENTACIÓN o COMBUSTIBLE"
}

# Configuración de logging
LOGGING = {
    "enabled": True,
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "file": "bot_viaticos.log",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}
