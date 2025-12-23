"""
Módulo de OCR mejorado para extracción de datos de facturas
"""

import re
import logging
import numpy as np
import cv2
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict, Optional, List, Tuple
from .config import OCR_CONFIG, NIT_EMPRESA

logger = logging.getLogger(__name__)


def extraer_datos_factura(image_path: str) -> Optional[Dict[str, any]]:
    """
    Extrae datos de la factura usando OCR con múltiples estrategias
    """
    try:
        logger.info(f"Procesando imagen: {image_path}")

        img = Image.open(image_path)

        texto_completo = []
        configs = [
            '--psm 6 --oem 3',
            '--psm 4 --oem 3',
            '--psm 3 --oem 3'
        ]

        for config in configs:
            img_procesada = _preprocesar_imagen_avanzado(img.copy())
            texto = pytesseract.image_to_string(img_procesada, lang=OCR_CONFIG['lang'], config=config)
            texto_completo.append(texto)

        texto_final = max(texto_completo, key=len)
        logger.debug(f"Texto extraido (primeras 300 chars): {texto_final[:300]}")

        lineas = texto_final.split('\n')
        texto_limpio = _limpiar_texto(texto_final)

        datos = {
            'nit': _extraer_nit_mejorado(lineas, texto_limpio),
            'nombre': _extraer_nombre_mejorado(lineas, texto_limpio),
            'serie': _extraer_serie_mejorado(lineas, texto_limpio),
            'numero': _extraer_numero_mejorado(lineas, texto_limpio),
            'monto': _extraer_monto_mejorado(lineas, texto_limpio)
        }

        logger.info(f"Datos extraidos: NIT={datos['nit']}, Serie={datos['serie']}, Numero={datos['numero']}, Monto={datos['monto']}")

        return datos

    except FileNotFoundError:
        logger.error(f"Archivo no encontrado: {image_path}")
        return None
    except Exception as e:
        logger.error(f"Error en OCR: {type(e).__name__} - {str(e)}", exc_info=True)
        return None


def _preprocesar_imagen_avanzado(img: Image) -> Image:
    """
    Preprocesamiento avanzado de imagen con OpenCV
    """
    try:
        img_array = np.array(img.convert('RGB'))
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        thresh = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        kernel = np.ones((1, 1), np.uint8)
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        img_final = Image.fromarray(morph)

        enhancer = ImageEnhance.Sharpness(img_final)
        img_final = enhancer.enhance(1.5)

        logger.debug("Imagen preprocesada con OpenCV")
        return img_final

    except Exception as e:
        logger.warning(f"Error en preprocesamiento avanzado: {e}. Usando preprocesamiento basico")
        return _preprocesar_imagen_basico(img)


def _preprocesar_imagen_basico(img: Image) -> Image:
    """
    Preprocesamiento básico si OpenCV falla
    """
    try:
        img = img.convert('L')

        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.5)

        img = img.filter(ImageFilter.SHARPEN)
        img = img.filter(ImageFilter.MedianFilter(size=3))

        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.3)

        return img
    except Exception as e:
        logger.warning(f"Error en preprocesamiento basico: {e}")
        return img


def _limpiar_texto(texto: str) -> str:
    """
    Limpia y normaliza el texto extraido
    """
    texto = re.sub(r'\s+', ' ', texto)
    texto = texto.replace('|', 'I').replace('l', '1').replace('O', '0')
    return texto.strip()


def _extraer_nit_mejorado(lineas: List[str], texto_completo: str) -> Optional[str]:
    """
    Extracción mejorada de NIT con múltiples estrategias
    """
    try:
        patrones_nit = [
            r'NIT[:\s]*(\d{6,12})',
            r'N\.?I\.?T\.?[:\s]*(\d{6,12})',
            r'TRIBUTARIO[:\s]*(\d{6,12})',
            r'REGISTRO[:\s]+TRIBUTARIO[:\s]*(\d{6,12})'
        ]

        for patron in patrones_nit:
            match = re.search(patron, texto_completo.upper())
            if match:
                nit = match.group(1)
                if nit != NIT_EMPRESA and len(nit) >= 6:
                    logger.debug(f"NIT encontrado con patron: {nit}")
                    return nit

        for i, linea in enumerate(lineas):
            if re.search(r'\bNIT\b', linea.upper()):
                for j in range(i, min(i+4, len(lineas))):
                    numeros = re.findall(r'\b(\d{6,12})\b', lineas[j])
                    for num in numeros:
                        if num != NIT_EMPRESA:
                            logger.debug(f"NIT encontrado en lineas cercanas: {num}")
                            return num

        logger.warning("No se pudo extraer NIT")
        return None

    except Exception as e:
        logger.error(f"Error extrayendo NIT: {e}")
        return None


def _extraer_nombre_mejorado(lineas: List[str], texto_completo: str) -> Optional[str]:
    """
    Extracción mejorada de nombre del proveedor
    """
    try:
        for i, linea in enumerate(lineas):
            if re.search(r'\bNIT\b', linea.upper()):
                for offset in [-3, -2, -1, 1, 2, 3, 4]:
                    idx = i + offset
                    if 0 <= idx < len(lineas):
                        candidato = lineas[idx].strip()

                        if (len(candidato) > 10 and
                            not re.match(r'^[\d\s]+$', candidato) and
                            'NIT' not in candidato.upper() and
                            'FACTURA' not in candidato.upper() and
                            'SERIE' not in candidato.upper()):

                            nombre = re.sub(r'[^A-Za-záéíóúñÑ\s&\.,\-]', '', candidato)
                            nombre = nombre.strip()

                            if len(nombre) > 10:
                                logger.debug(f"Nombre encontrado: {nombre}")
                                return nombre

        logger.warning("No se pudo extraer nombre del proveedor")
        return None

    except Exception as e:
        logger.error(f"Error extrayendo nombre: {e}")
        return None


def _extraer_serie_mejorado(lineas: List[str], texto_completo: str) -> Optional[str]:
    """
    Extracción mejorada de serie con múltiples patrones
    """
    try:
        patrones_serie = [
            r'SERIE[:\s]*([A-Z0-9]{6,15})',
            r'SER[IÍ]E[:\s]*([A-Z0-9]{6,15})',
            r'S[EÉ]RIE[:\s]*([A-Z0-9]{6,15})',
            r'AUTORIZACION[:\s]+([A-Z0-9]{6,15})',
            r'AUTORIZACI[OÓ]N[:\s]+([A-Z0-9]{6,15})',
            r'\bDTE[:\s]*([A-Z0-9]{6,15})',
            r'\bFEL[:\s]*([A-Z0-9]{6,15})'
        ]

        for patron in patrones_serie:
            match = re.search(patron, texto_completo.upper())
            if match:
                serie = match.group(1)
                if not serie.isdigit() or len(serie) <= 12:
                    logger.debug(f"Serie encontrada con patron: {serie}")
                    return serie

        for i, linea in enumerate(lineas):
            if re.search(r'\bSERIE\b|\bAUTORIZACI[OÓ]N\b', linea.upper()):
                for offset in [0, 1, 2, -1]:
                    idx = i + offset
                    if 0 <= idx < len(lineas):
                        matches = re.findall(r'\b([A-Z0-9]{6,15})\b', lineas[idx].upper())
                        for match in matches:
                            if (not match.isdigit() or len(match) <= 10):
                                logger.debug(f"Serie encontrada en lineas: {match}")
                                return match

        logger.warning("No se pudo extraer serie")
        return None

    except Exception as e:
        logger.error(f"Error extrayendo serie: {e}")
        return None


def _extraer_numero_mejorado(lineas: List[str], texto_completo: str) -> Optional[str]:
    """
    Extracción mejorada de número de factura
    """
    try:
        patrones_numero = [
            r'N[UÚ]MERO[:\s]*(\d{6,12})',
            r'NUMERO[:\s]*(\d{6,12})',
            r'N[UÚ]M[:\s]*(\d{6,12})',
            r'NUM[:\s]*(\d{6,12})',
            r'DOCUMENTO[:\s]*(\d{6,12})',
            r'CORRELATIVO[:\s]*(\d{6,12})'
        ]

        for patron in patrones_numero:
            match = re.search(patron, texto_completo.upper())
            if match:
                numero = match.group(1)
                logger.debug(f"Numero encontrado con patron: {numero}")
                return numero

        for i, linea in enumerate(lineas):
            if re.search(r'\bN[UÚ]MERO\b|\bNUMERO\b', linea.upper()):
                for offset in [0, 1, 2]:
                    idx = i + offset
                    if idx < len(lineas):
                        numeros = re.findall(r'\b(\d{6,12})\b', lineas[idx])
                        if numeros:
                            logger.debug(f"Numero encontrado en lineas: {numeros[0]}")
                            return numeros[0]

        logger.warning("No se pudo extraer numero de factura")
        return None

    except Exception as e:
        logger.error(f"Error extrayendo numero: {e}")
        return None


def _extraer_monto_mejorado(lineas: List[str], texto_completo: str) -> Optional[float]:
    """
    Extracción mejorada de monto con validación robusta
    """
    try:
        montos_candidatos = []

        palabras_clave = [
            'GRAN TOTAL', 'TOTAL A PAGAR', 'TOTAL GENERAL',
            'TOTAL FACTURA', 'MONTO TOTAL', 'TOTAL',
            'IMPORTE TOTAL', 'SUMA TOTAL', 'VALOR TOTAL'
        ]

        for palabra in palabras_clave:
            patron = rf'{palabra}[:\s]*Q?\s*([\d,]+\.?\d{{0,2}})'
            matches = re.finditer(patron, texto_completo.upper())
            for match in matches:
                try:
                    monto_str = match.group(1).replace(',', '')
                    monto = float(monto_str)
                    if 0.01 <= monto <= 999999:
                        montos_candidatos.append((palabra, monto))
                        logger.debug(f"Monto candidato con '{palabra}': {monto:.2f}")
                except ValueError:
                    continue

        if montos_candidatos:
            monto_final = max(montos_candidatos, key=lambda x: x[1])[1]
            logger.info(f"Monto seleccionado: {monto_final:.2f}")
            return monto_final

        patrones_monto = [
            r'Q\s*([\d,]+\.?\d{0,2})',
            r'GTQ\s*([\d,]+\.?\d{0,2})',
            r'QUETZALES\s*([\d,]+\.?\d{0,2})'
        ]

        for patron in patrones_monto:
            matches = list(re.finditer(patron, texto_completo))
            for match in reversed(matches):
                try:
                    monto_str = match.group(1).replace(',', '')
                    monto = float(monto_str)
                    if 0.01 <= monto <= 999999:
                        logger.debug(f"Monto encontrado: {monto:.2f}")
                        return monto
                except ValueError:
                    continue

        logger.warning("No se pudo extraer monto")
        return None

    except Exception as e:
        logger.error(f"Error extrayendo monto: {e}")
        return None
