"""
Módulo de Base de Datos
Maneja todas las operaciones de SQLite para el bot de viáticos
"""

import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional
import logging
from .config import DATABASE_NAME

logger = logging.getLogger(__name__)


class Database:
    """Clase para manejar operaciones de base de datos"""

    def __init__(self, db_name: str = DATABASE_NAME):
        """Inicializar conexión a base de datos"""
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Crear tabla de facturas si no existe"""
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS facturas
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          fecha TEXT,
                          nit_proveedor TEXT,
                          nombre_proveedor TEXT,
                          serie TEXT,
                          numero TEXT,
                          tipo_gasto TEXT,
                          monto REAL,
                          foto_path TEXT,
                          created_at TEXT)''')
            conn.commit()
            conn.close()
            logger.info("Base de datos inicializada correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar base de datos: {e}")
            raise

    def insertar_factura(self, fecha: str, nit: str, nombre: str,
                        serie: str, numero: str, tipo_gasto: str,
                        monto: float, foto_path: str) -> int:
        """
        Insertar nueva factura

        Returns:
            int: ID de la factura insertada
        """
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''INSERT INTO facturas
                         (fecha, nit_proveedor, nombre_proveedor, serie, numero,
                          tipo_gasto, monto, foto_path, created_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (fecha, nit, nombre, serie, numero, tipo_gasto, monto,
                       foto_path, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            factura_id = c.lastrowid
            conn.close()
            logger.info(f"Factura #{factura_id} insertada correctamente")
            return factura_id
        except Exception as e:
            logger.error(f"Error al insertar factura: {e}")
            raise

    def obtener_resumen(self) -> Tuple[float, int, List[Tuple]]:
        """
        Obtener resumen de gastos

        Returns:
            tuple: (total, cantidad, lista_por_tipo)
        """
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()

            # Total general
            c.execute('SELECT SUM(monto), COUNT(*) FROM facturas')
            total, cantidad = c.fetchone()
            total = total or 0
            cantidad = cantidad or 0

            # Por tipo de gasto
            c.execute('SELECT tipo_gasto, SUM(monto), COUNT(*) FROM facturas GROUP BY tipo_gasto')
            por_tipo = c.fetchall()

            conn.close()
            logger.debug(f"Resumen obtenido: total={total}, cantidad={cantidad}")
            return total, cantidad, por_tipo
        except Exception as e:
            logger.error(f"Error al obtener resumen: {e}")
            raise

    def obtener_facturas(self, limit: int = 20) -> List[Tuple]:
        """
        Obtener lista de facturas

        Args:
            limit: Número máximo de facturas a obtener

        Returns:
            list: Lista de tuplas con datos de facturas
        """
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('SELECT id, fecha, nombre_proveedor, tipo_gasto, monto FROM facturas ORDER BY id DESC LIMIT ?', (limit,))
            facturas = c.fetchall()
            conn.close()
            logger.debug(f"Obtenidas {len(facturas)} facturas")
            return facturas
        except Exception as e:
            logger.error(f"Error al obtener facturas: {e}")
            raise

    def obtener_todas_facturas(self) -> List[Tuple]:
        """
        Obtener todas las facturas para exportar

        Returns:
            list: Lista de tuplas con datos completos de facturas
        """
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''SELECT fecha, nit_proveedor, serie, numero, tipo_gasto, monto
                         FROM facturas ORDER BY fecha''')
            facturas = c.fetchall()
            conn.close()
            logger.debug(f"Obtenidas {len(facturas)} facturas para exportar")
            return facturas
        except Exception as e:
            logger.error(f"Error al obtener todas las facturas: {e}")
            raise

    def eliminar_factura(self, factura_id: int) -> bool:
        """
        Eliminar factura por ID

        Args:
            factura_id: ID de la factura a eliminar

        Returns:
            bool: True si se eliminó, False si no existía
        """
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('DELETE FROM facturas WHERE id = ?', (factura_id,))
            conn.commit()
            eliminada = c.rowcount > 0
            conn.close()

            if eliminada:
                logger.info(f"Factura #{factura_id} eliminada")
            else:
                logger.warning(f"Factura #{factura_id} no encontrada para eliminar")

            return eliminada
        except Exception as e:
            logger.error(f"Error al eliminar factura: {e}")
            raise
