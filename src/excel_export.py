"""
Módulo de Exportación a Excel
Genera reportes de viáticos en formato Excel
"""

import os
import logging
from datetime import datetime
from typing import List, Tuple
import pandas as pd
from openpyxl.styles import Font, Alignment
from .config import EXCEL_CONFIG, FACTURAS_FOLDER

logger = logging.getLogger(__name__)


def generar_excel(facturas: List[Tuple]) -> Tuple[str, str]:
    """
    Genera archivo Excel con las facturas

    Args:
        facturas: Lista de tuplas con datos de facturas

    Returns:
        tuple: (filepath, filename) del archivo generado
    """
    try:
        if not facturas:
            logger.warning("No hay facturas para exportar")
            raise ValueError("No hay facturas para exportar")

        # Crear DataFrame
        df = pd.DataFrame(facturas, columns=EXCEL_CONFIG['columns'])

        # Crear nombre de archivo
        mes_actual = datetime.now().month
        anio_actual = datetime.now().year
        mes_nombre = datetime.now().strftime('%B')

        filename = f'viaticos_{mes_actual}_{anio_actual}.xlsx'
        filepath = os.path.join(FACTURAS_FOLDER, filename)

        logger.info(f"Generando Excel: {filepath}")

        # Crear Excel con formato
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Escribir DataFrame empezando en fila 7
            df.to_excel(writer, sheet_name='Sheet1',
                       startrow=EXCEL_CONFIG['data_start_row'] - 1,
                       index=False)

            # Obtener workbook y sheet
            workbook = writer.book
            sheet = writer.sheets['Sheet1']

            # Agregar encabezados de la plantilla
            _agregar_encabezados(sheet, mes_nombre)

            # Formatear headers
            _formatear_headers(sheet)

            # Ajustar anchos de columna
            _ajustar_anchos(sheet)

            # Agregar numeración
            _agregar_numeracion(sheet, len(df))

        logger.info(f"Excel generado exitosamente: {filename}")
        return filepath, filename

    except Exception as e:
        logger.error(f"Error al generar Excel: {type(e).__name__} - {str(e)}", exc_info=True)
        raise


def _agregar_encabezados(sheet, mes_nombre: str):
    """Agregar encabezados de la plantilla"""
    sheet['G2'] = 'PROYECTO :'
    sheet['G3'] = 'NOMBRE SUPERVISOR'
    sheet['G4'] = 'CODIGO MAESTRO'
    sheet['G5'] = 'PUESTO'
    sheet['H5'] = 'SUPERVISOR JR'
    sheet['G6'] = 'MES'
    sheet['H6'] = mes_nombre.upper()
    sheet['I6'] = 'FECHA'
    sheet['J6'] = datetime.now().strftime('%Y-%m-%d')


def _formatear_headers(sheet):
    """Formatear fila de headers (fila 7)"""
    header_font = Font(bold=True)
    header_alignment = Alignment(horizontal='center', vertical='center')

    for cell in sheet[EXCEL_CONFIG['data_start_row']]:
        cell.font = header_font
        cell.alignment = header_alignment


def _ajustar_anchos(sheet):
    """Ajustar anchos de columna"""
    for col, width in EXCEL_CONFIG['column_widths'].items():
        sheet.column_dimensions[col].width = width


def _agregar_numeracion(sheet, num_filas: int):
    """Agregar numeración en columna A"""
    start_row = EXCEL_CONFIG['data_start_row'] + 1
    for idx, row in enumerate(range(start_row, start_row + num_filas), start=1):
        sheet[f'A{row}'] = idx
