"""
Módulo de OCR
Extrae datos de facturas usando Tesseract OCR
"""

import re
import logging
import pytesseract
from PIL import Image
from typing import Dict, Optional
from .config import OCR_CONFIG, NIT_EMPRESA

logger = logging.getLogger(__name__)


def extraer_datos_factura(image_path: str) -> Optional[Dict[str, any]]:
    """
    Extrae datos de la factura usando OCR

    Args:
        image_path: Ruta de la imagen a procesar

    Returns:
        dict: Diccionario con nit, nombre, serie, numero, monto
        None: Si hubo error en el procesamiento
    """
    try:
        logger.info(f"Procesando imagen: {image_path}")

        # Abrir imagen y hacer OCR
        img = Image.open(image_path)
        texto = pytesseract.image_to_string(img, lang=OCR_CONFIG['lang'])

        logger.debug(f"Texto extraído (primeras 200 chars): {texto[:200]}")

        datos = {
            'nit': None,
            'nombre': None,
            'serie': None,
            'numero': None,
            'monto': None
        }

        lineas = texto.split('\n')

        # Buscar NIT del emisor
        datos['nit'] = _extraer_nit(lineas)

        # Buscar nombre del proveedor
        datos['nombre'] = _extraer_nombre(lineas)

        # Buscar SERIE
        datos['serie'] = _extraer_serie(lineas)

        # Buscar NÚMERO de factura
        datos['numero'] = _extraer_numero(lineas)

        # Buscar MONTO
        datos['monto'] = _extraer_monto(lineas)

        logger.info(f"Datos extraídos: NIT={datos['nit']}, Serie={datos['serie']}, Numero={datos['numero']}, Monto={datos['monto']}")

        return datos

    except FileNotFoundError as e:
        logger.error(f"Archivo no encontrado: {image_path}")
        return None
    except Exception as e:
        logger.error(f"Error en OCR: {type(e).__name__} - {str(e)}", exc_info=True)
        return None


def _extraer_nit(lineas: list) -> Optional[str]:
    """Extraer NIT del proveedor"""
    try:
        for i, linea in enumerate(lineas):
            if 'NIT' in linea.upper():
                # Buscar números en líneas cercanas
                for j in range(i, min(i+3, len(lineas))):
                    numeros = re.findall(r'\d+', lineas[j])
                    for num in numeros:
                        if len(num) >= 6 and num != NIT_EMPRESA:
                            logger.debug(f"NIT encontrado: {num}")
                            return num
    except Exception as e:
        logger.error(f"Error extrayendo NIT: {e}")
    return None


def _extraer_nombre(lineas: list) -> Optional[str]:
    """Extraer nombre del proveedor"""
    try:
        # Buscar líneas cerca de NIT que contengan el nombre
        for i, linea in enumerate(lineas):
            if 'NIT' in linea.upper():
                # Buscar en líneas cercanas
                for k in range(max(0, i-2), min(i+5, len(lineas))):
                    if lineas[k].strip() and not re.match(r'^\d+$', lineas[k].strip()):
                        if len(lineas[k].strip()) > 10 and 'NIT' not in lineas[k].upper():
                            nombre = lineas[k].strip()
                            logger.debug(f"Nombre encontrado: {nombre}")
                            return nombre
    except Exception as e:
        logger.error(f"Error extrayendo nombre: {e}")
    return None


def _extraer_serie(lineas: list) -> Optional[str]:
    """Extraer SERIE de la factura"""
    try:
        for i, linea in enumerate(lineas):
            if 'SERIE' in linea.upper():
                # Buscar código alfanumérico después de SERIE
                match = re.search(r'SERIE[:\s]*([A-Z0-9]+)', linea.upper())
                if match:
                    serie = match.group(1)
                    logger.debug(f"Serie encontrada: {serie}")
                    return serie
                else:
                    # Buscar en la siguiente línea
                    if i + 1 < len(lineas):
                        match = re.search(r'([A-Z0-9]{8,})', lineas[i + 1].upper())
                        if match:
                            serie = match.group(1)
                            logger.debug(f"Serie encontrada (línea siguiente): {serie}")
                            return serie
    except Exception as e:
        logger.error(f"Error extrayendo serie: {e}")
    return None


def _extraer_numero(lineas: list) -> Optional[str]:
    """Extraer NÚMERO de la factura"""
    try:
        for i, linea in enumerate(lineas):
            if 'NUMERO' in linea.upper() or 'NÚMERO' in linea.upper():
                # Buscar número después de NUMERO
                match = re.search(r'N[UÚ]MERO[:\s]*(\d+)', linea.upper())
                if match:
                    numero = match.group(1)
                    logger.debug(f"Número encontrado: {numero}")
                    return numero
                else:
                    # Buscar en la siguiente línea
                    if i + 1 < len(lineas):
                        numeros = re.findall(r'\d{6,}', lineas[i + 1])
                        if numeros:
                            numero = numeros[0]
                            logger.debug(f"Número encontrado (línea siguiente): {numero}")
                            return numero
    except Exception as e:
        logger.error(f"Error extrayendo número: {e}")
    return None


def _extraer_monto(lineas: list) -> Optional[float]:
    """Extraer MONTO de la factura"""
    try:
        # Buscar TOTAL con Q
        for linea in lineas:
            if 'TOTAL' in linea.upper() and 'Q' in linea:
                match = re.search(r'Q\s*[\d,]+\.?\d*', linea)
                if match:
                    monto_str = match.group().replace('Q', '').replace(',', '').replace(' ', '')
                    try:
                        monto = float(monto_str)
                        logger.debug(f"Monto encontrado (TOTAL): {monto}")
                        return monto
                    except ValueError:
                        continue

        # Si no encontró monto, buscar cualquier cantidad con Q
        for linea in reversed(lineas):
            if 'Q' in linea:
                match = re.search(r'Q\s*(\d+[\.,]?\d*)', linea)
                if match:
                    try:
                        monto_str = match.group(1).replace(',', '.')
                        monto = float(monto_str)
                        logger.debug(f"Monto encontrado (genérico): {monto}")
                        return monto
                    except ValueError:
                        continue

    except Exception as e:
        logger.error(f"Error extrayendo monto: {e}")
    return None
