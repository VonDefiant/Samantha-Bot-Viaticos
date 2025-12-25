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

        # Intentar con múltiples estrategias de preprocesamiento
        texto_completo = []
        configs = [
            ('basico', '--psm 6 --oem 3'),
            ('basico', '--psm 4 --oem 3'),
            ('avanzado', '--psm 6 --oem 3'),
            ('original', '--psm 6 --oem 3'),  # Sin preprocesamiento
        ]

        for tipo, config in configs:
            if tipo == 'avanzado':
                img_procesada = _preprocesar_imagen_avanzado(img.copy())
            elif tipo == 'basico':
                img_procesada = _preprocesar_imagen_basico(img.copy())
            else:
                # Imagen original sin preprocesamiento
                img_procesada = img.copy()

            texto = pytesseract.image_to_string(img_procesada, lang=OCR_CONFIG['lang'], config=config)
            texto_completo.append(texto)
            logger.debug(f"Texto extraído con {tipo}/{config}: {len(texto)} caracteres")

        # Combinar todos los textos para maximizar extracción
        texto_combinado = '\n'.join(texto_completo)
        texto_final = max(texto_completo, key=len)

        logger.debug(f"Texto final (primeras 500 chars):\n{texto_final[:500]}")

        lineas = texto_final.split('\n')
        lineas_combinadas = texto_combinado.split('\n')
        texto_limpio = _limpiar_texto(texto_final)

        # Intentar extracción con todos los textos disponibles
        datos = {
            'nit': _extraer_nit_mejorado(lineas_combinadas, texto_combinado),
            'nombre': _extraer_nombre_mejorado(lineas_combinadas, texto_combinado),
            'serie': _extraer_serie_mejorado(lineas_combinadas, texto_combinado),
            'numero': _extraer_numero_mejorado(lineas_combinadas, texto_combinado),
            'monto': _extraer_monto_mejorado(lineas_combinadas, texto_combinado)
        }

        logger.info(f"Datos extraídos: NIT={datos['nit']}, Nombre={datos['nombre'][:30] if datos['nombre'] else None}, Serie={datos['serie']}, Numero={datos['numero']}, Monto={datos['monto']}")

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
    Extracción mejorada de NIT del PROVEEDOR (excluyendo NIT del comprador/empresa)
    """
    try:
        # Dividir texto para identificar secciones
        texto_upper = texto_completo.upper()

        # Primero: buscar explícitamente en sección del proveedor/vendedor
        # Evitar sección "DATOS DEL COMPRADOR" o similar
        secciones_comprador = ['DATOS DEL COMPRADOR', 'COMPRADOR', 'CLIENTE', 'ADQUIRENTE']

        # Encontrar todos los NITs con contexto
        nits_encontrados = []

        # Patrón para encontrar NITs con su contexto
        patron_nit_contexto = r'(.{0,100})NIT[:\s-]*(\d{6,12})(.{0,100})'
        matches = re.finditer(patron_nit_contexto, texto_upper, re.MULTILINE)

        for match in matches:
            contexto_antes = match.group(1)
            nit = match.group(2)
            contexto_despues = match.group(3)
            contexto_completo = contexto_antes + contexto_despues

            # Verificar que NO sea el NIT de nuestra empresa
            if nit == NIT_EMPRESA:
                logger.debug(f"NIT {nit} excluido (es NIT_EMPRESA)")
                continue

            # Verificar que NO esté en sección de comprador
            es_seccion_comprador = any(seccion in contexto_completo for seccion in secciones_comprador)

            if not es_seccion_comprador:
                # Este NIT probablemente es del proveedor
                prioridad = 10

                # Dar mayor prioridad si está cerca de palabras clave de proveedor
                if any(palabra in contexto_completo for palabra in ['PROVEEDOR', 'VENDEDOR', 'EMISOR', 'RAZON SOCIAL']):
                    prioridad = 20

                nits_encontrados.append((nit, prioridad))
                logger.debug(f"NIT candidato: {nit} (prioridad {prioridad}, contexto: {contexto_completo[:50]}...)")

        # Ordenar por prioridad y tomar el mejor
        if nits_encontrados:
            nits_encontrados.sort(key=lambda x: x[1], reverse=True)
            nit_seleccionado = nits_encontrados[0][0]
            logger.info(f"NIT del proveedor seleccionado: {nit_seleccionado}")
            return nit_seleccionado

        # Plan B: Buscar el PRIMER NIT que aparezca y que NO sea NIT_EMPRESA
        # (usualmente el NIT del proveedor aparece primero en la factura)
        patron_simple = r'\bNIT[:\s-]*(\d{6,12})'
        matches = re.finditer(patron_simple, texto_upper)
        for match in matches:
            nit = match.group(1)
            if nit != NIT_EMPRESA:
                # Verificar que no esté en línea con "COMPRADOR"
                inicio_match = match.start()
                fin_match = match.end()
                contexto = texto_upper[max(0, inicio_match-100):min(len(texto_upper), fin_match+100)]

                if not any(palabra in contexto for palabra in secciones_comprador):
                    logger.debug(f"NIT encontrado (primer NIT válido): {nit}")
                    return nit

        # Plan C: Buscar en líneas que NO contengan palabras de comprador
        for i, linea in enumerate(lineas):
            linea_upper = linea.upper()

            # Saltar líneas de sección comprador
            if any(palabra in linea_upper for palabra in secciones_comprador):
                continue

            if re.search(r'\bNIT\b', linea_upper):
                for j in range(i, min(i+5, len(lineas))):
                    if any(palabra in lineas[j].upper() for palabra in secciones_comprador):
                        break  # Saltar si llegamos a sección comprador

                    numeros = re.findall(r'\b(\d{6,12})\b', lineas[j])
                    for num in numeros:
                        if num != NIT_EMPRESA and len(num) >= 6:
                            logger.debug(f"NIT encontrado en líneas (no comprador): {num}")
                            return num

        # Último recurso: tomar cualquier NIT de 7-9 dígitos que NO sea NIT_EMPRESA
        numeros_candidatos = re.findall(r'\b(\d{7,9})\b', texto_completo)
        for num in numeros_candidatos:
            if num != NIT_EMPRESA:
                logger.debug(f"NIT candidato (último recurso): {num}")
                return num

        logger.warning("No se pudo extraer NIT del proveedor")
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
        # Patrones más flexibles para número
        patrones_numero = [
            r'N[UÚ]MERO[:\s-]*(\d{6,12})',
            r'NUMERO[:\s-]*(\d{6,12})',
            r'N[UÚ]M\.?[:\s-]*(\d{6,12})',
            r'NUM\.?[:\s-]*(\d{6,12})',
            r'DOCUMENTO[:\s-]*(\d{6,12})',
            r'CORRELATIVO[:\s-]*(\d{6,12})',
            r'NO\.[:\s]*(\d{6,12})',
            r'#[:\s]*(\d{6,12})',
        ]

        for patron in patrones_numero:
            matches = re.finditer(patron, texto_completo.upper(), re.MULTILINE)
            for match in matches:
                numero = match.group(1)
                logger.debug(f"Número encontrado con patrón '{patron}': {numero}")
                return numero

        # Buscar en líneas cercanas a NÚMERO
        for i, linea in enumerate(lineas):
            if re.search(r'\b(?:N[UÚ]MERO|NUMERO|NUM|NO\.)\b', linea.upper()):
                for offset in [0, 1, 2, 3]:
                    idx = i + offset
                    if idx < len(lineas):
                        numeros = re.findall(r'\b(\d{6,12})\b', lineas[idx])
                        if numeros:
                            logger.debug(f"Número encontrado en líneas cercanas: {numeros[0]}")
                            return numeros[0]

        # Buscar después de SERIE (el número suele venir después de la serie)
        for i, linea in enumerate(lineas):
            if re.search(r'\bSERIE\b', linea.upper()):
                for offset in [1, 2, 3]:
                    idx = i + offset
                    if idx < len(lineas):
                        # Buscar números largos (8+ dígitos que no sean NITs)
                        numeros = re.findall(r'\b(\d{8,12})\b', lineas[idx])
                        if numeros:
                            logger.debug(f"Número encontrado después de SERIE: {numeros[0]}")
                            return numeros[0]

        logger.warning("No se pudo extraer número de factura")
        return None

    except Exception as e:
        logger.error(f"Error extrayendo número: {e}")
        return None


def _extraer_monto_mejorado(lineas: List[str], texto_completo: str) -> Optional[float]:
    """
    Extracción mejorada de monto con validación robusta
    """
    try:
        montos_candidatos = []

        # Palabras clave ordenadas por prioridad (más específicas primero)
        palabras_clave = [
            ('GRAN TOTAL', 10),
            ('TOTAL A PAGAR', 10),
            ('TOTAL GENERAL', 9),
            ('TOTAL FACTURA', 9),
            ('MONTO TOTAL', 8),
            ('SUMA TOTAL', 8),
            ('VALOR TOTAL', 7),
            ('TOTAL', 5),  # Menos prioridad porque es genérico
        ]

        for palabra, prioridad in palabras_clave:
            # Patrones más flexibles para montos
            patrones = [
                rf'{palabra}[:\s]*Q\s*([\d,]+\.?\d{{0,2}})',
                rf'{palabra}[:\s]*([\d,]+\.?\d{{0,2}})',
                rf'{palabra}[^\d]{{0,10}}Q\s*([\d,]+\.?\d{{0,2}})',
            ]

            for patron in patrones:
                matches = re.finditer(patron, texto_completo.upper())
                for match in matches:
                    try:
                        monto_str = match.group(1).replace(',', '').replace(' ', '')
                        monto = float(monto_str)
                        if 0.01 <= monto <= 999999:
                            montos_candidatos.append((palabra, monto, prioridad))
                            logger.debug(f"Monto candidato con '{palabra}' (prioridad {prioridad}): Q{monto:.2f}")
                    except ValueError:
                        continue

        # Seleccionar monto con mayor prioridad, y si hay empate, el mayor monto
        if montos_candidatos:
            monto_final = max(montos_candidatos, key=lambda x: (x[2], x[1]))[1]
            logger.info(f"Monto seleccionado: Q{monto_final:.2f}")
            return monto_final

        # Patrones generales de monto (Q, GTQ, QUETZALES)
        patrones_monto = [
            r'Q\s*([\d,]+\.?\d{0,2})',
            r'GTQ\s*([\d,]+\.?\d{0,2})',
            r'QUETZALES\s*([\d,]+\.?\d{0,2})',
            r'\$\s*([\d,]+\.?\d{0,2})',  # Por si usan $ en lugar de Q
        ]

        todos_montos = []
        for patron in patrones_monto:
            matches = re.finditer(patron, texto_completo)
            for match in matches:
                try:
                    monto_str = match.group(1).replace(',', '').replace(' ', '')
                    monto = float(monto_str)
                    if 0.01 <= monto <= 999999:
                        todos_montos.append(monto)
                except ValueError:
                    continue

        # Tomar el monto más grande (suele ser el total)
        if todos_montos:
            monto_final = max(todos_montos)
            logger.debug(f"Monto encontrado (máximo de todos): Q{monto_final:.2f}")
            return monto_final

        logger.warning("No se pudo extraer monto")
        return None

    except Exception as e:
        logger.error(f"Error extrayendo monto: {e}")
        return None
