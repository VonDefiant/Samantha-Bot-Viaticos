"""
Módulo de OCR
Extrae datos de facturas usando Tesseract OCR
"""

import re
import logging
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
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

        # Abrir imagen
        img = Image.open(image_path)

        # Preprocesar imagen para mejor OCR
        img = _preprocesar_imagen(img)

        # Hacer OCR con configuración mejorada
        config_ocr = '--psm 6 --oem 3'  # PSM 6: asume bloque uniforme de texto, OEM 3: mejor motor
        texto = pytesseract.image_to_string(img, lang=OCR_CONFIG['lang'], config=config_ocr)

        logger.debug(f"Texto extraído (primeras 300 chars): {texto[:300]}")

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


def _preprocesar_imagen(img: Image) -> Image:
    """
    Preprocesar imagen para mejorar resultados de OCR

    Args:
        img: Imagen PIL a procesar

    Returns:
        Image: Imagen procesada
    """
    try:
        # Convertir a escala de grises
        img = img.convert('L')

        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)

        # Aumentar nitidez
        img = img.filter(ImageFilter.SHARPEN)

        # Aumentar brillo ligeramente
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.2)

        logger.debug("Imagen preprocesada exitosamente")
        return img
    except Exception as e:
        logger.warning(f"Error en preprocesamiento de imagen: {e}. Usando imagen original.")
        return img


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
                # Buscar código alfanumérico después de SERIE (más flexible)
                # Acepta series de 6+ caracteres
                match = re.search(r'SERIE[:\s]*([A-Z0-9]{6,})', linea.upper())
                if match:
                    serie = match.group(1)
                    logger.debug(f"Serie encontrada en misma línea: {serie}")
                    return serie

                # Buscar en líneas cercanas (antes y después)
                for offset in [1, 2, -1]:
                    idx = i + offset
                    if 0 <= idx < len(lineas):
                        # Buscar secuencias alfanuméricas de 6+ caracteres
                        match = re.search(r'\b([A-Z0-9]{6,})\b', lineas[idx].upper())
                        if match:
                            serie = match.group(1)
                            # Validar que no sea un NIT (todos números)
                            if not serie.isdigit():
                                logger.debug(f"Serie encontrada cerca de SERIE: {serie}")
                                return serie
                            elif len(serie) <= 10:  # Series pueden ser numéricas pero cortas
                                logger.debug(f"Serie numérica encontrada: {serie}")
                                return serie

        # Si no encontró con SERIE, buscar patrones comunes en facturas guatemaltecas
        for linea in lineas:
            # Buscar patrones como "AUTORIZACION NUMERO SERIE" o solo series alfanuméricas
            match = re.search(r'\b([A-Z]{2,}[0-9]{6,})\b', linea.upper())
            if match:
                serie = match.group(1)
                logger.debug(f"Serie encontrada por patrón: {serie}")
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
        montos_encontrados = []

        # Buscar palabras clave de totales (en orden de prioridad)
        palabras_total = ['GRAN TOTAL', 'TOTAL A PAGAR', 'TOTAL GENERAL', 'TOTAL', 'MONTO']

        for palabra in palabras_total:
            for i, linea in enumerate(lineas):
                if palabra in linea.upper():
                    # Buscar en la misma línea y las 2 siguientes
                    for j in range(i, min(i + 3, len(lineas))):
                        # Buscar patrones de monto con Q
                        # Patrones: Q 123.45, Q123.45, Q 1,234.56, Q1234.56
                        matches = re.finditer(r'Q\s*[\d,]+\.?\d{0,2}', lineas[j])
                        for match in matches:
                            try:
                                # Limpiar y convertir
                                monto_str = match.group().replace('Q', '').replace(',', '').replace(' ', '').strip()
                                if monto_str:
                                    monto = float(monto_str)
                                    # Validar que el monto sea razonable (entre 0.01 y 999999)
                                    if 0.01 <= monto <= 999999:
                                        montos_encontrados.append((palabra, monto))
                                        logger.debug(f"Monto encontrado con '{palabra}': Q{monto:.2f}")
                            except ValueError:
                                continue

            # Si encontró montos con esta palabra, retornar el más alto
            if montos_encontrados:
                monto_final = max(montos_encontrados, key=lambda x: x[1])[1]
                logger.info(f"Monto seleccionado: Q{monto_final:.2f}")
                return monto_final

        # Si no encontró con palabras clave, buscar el último monto con Q en el documento
        # (generalmente el total está al final)
        for linea in reversed(lineas):
            matches = re.finditer(r'Q\s*[\d,]+\.?\d{0,2}', linea)
            for match in matches:
                try:
                    monto_str = match.group().replace('Q', '').replace(',', '').replace(' ', '').strip()
                    if monto_str:
                        monto = float(monto_str)
                        if 0.01 <= monto <= 999999:
                            logger.debug(f"Monto encontrado (último en documento): Q{monto:.2f}")
                            return monto
                except ValueError:
                    continue

        logger.warning("No se pudo extraer monto de la factura")

    except Exception as e:
        logger.error(f"Error extrayendo monto: {e}")
    return None
