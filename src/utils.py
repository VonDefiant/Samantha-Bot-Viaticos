"""
Módulo de Utilidades
Funciones auxiliares y configuración de logging
"""

import logging
import os
from datetime import datetime


def configurar_logging(nivel=logging.INFO):
    """
    Configura el sistema de logging

    Args:
        nivel: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
    """
    # Crear carpeta de logs si no existe
    os.makedirs('logs', exist_ok=True)

    # Formato del log
    formato = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formato_fecha = '%Y-%m-%d %H:%M:%S'

    # Nombre del archivo de log con fecha
    log_filename = f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log'

    # Configurar logging
    logging.basicConfig(
        level=nivel,
        format=formato,
        datefmt=formato_fecha,
        handlers=[
            # Handler para archivo
            logging.FileHandler(log_filename, encoding='utf-8'),
            # Handler para consola
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Sistema de logging configurado")
    logger.info(f"Archivo de log: {log_filename}")
    logger.info("=" * 60)


def formatear_monto(monto: float) -> str:
    """
    Formatea un monto en formato de moneda

    Args:
        monto: Monto a formatear

    Returns:
        str: Monto formateado (ej: "Q150.50")
    """
    return f"Q{monto:.2f}" if monto is not None else "Q0.00"


def truncar_texto(texto: str, max_len: int = 40) -> str:
    """
    Trunca un texto si es muy largo

    Args:
        texto: Texto a truncar
        max_len: Longitud máxima

    Returns:
        str: Texto truncado con "..."
    """
    if not texto:
        return ""
    return texto[:max_len] + '...' if len(texto) > max_len else texto


def validar_monto(monto_str: str) -> float:
    """
    Valida y convierte un string a monto

    Args:
        monto_str: String con el monto

    Returns:
        float: Monto validado

    Raises:
        ValueError: Si el monto no es válido
    """
    try:
        # Limpiar string
        monto_limpio = monto_str.replace('Q', '').replace(',', '').strip()
        monto = float(monto_limpio)

        if monto < 0:
            raise ValueError("El monto no puede ser negativo")

        return monto
    except (ValueError, AttributeError):
        raise ValueError("Formato de monto inválido")


def formatear_error(error: Exception) -> str:
    """
    Formatea un error para mostrarlo al usuario

    Args:
        error: Excepción capturada

    Returns:
        str: Mensaje de error formateado
    """
    error_type = type(error).__name__
    error_msg = str(error)

    return f"⚠️ Error: {error_type}\n{error_msg}"


MESES_NOMBRES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}


def obtener_nombre_mes(mes: int) -> str:
    """Retorna el nombre del mes"""
    return MESES_NOMBRES.get(mes, str(mes))


def obtener_mes_actual() -> int:
    """Retorna el mes actual"""
    return datetime.now().month


def obtener_anio_actual() -> int:
    """Retorna el año actual"""
    return datetime.now().year


def formatear_periodo(mes: int, anio: int) -> str:
    """Formatea un periodo como 'Enero 2024'"""
    return f"{obtener_nombre_mes(mes)} {anio}"
