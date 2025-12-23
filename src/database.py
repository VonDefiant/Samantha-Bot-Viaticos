"""
Módulo de Base de Datos con soporte multi-usuario
"""

import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional
import logging
from .config import DATABASE_NAME

logger = logging.getLogger(__name__)


class Database:

    def __init__(self, db_name: str = DATABASE_NAME):
        self.db_name = db_name
        self.init_db()
        self._migrate_if_needed()

    def init_db(self):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()

            c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                         (user_id INTEGER PRIMARY KEY,
                          nombre TEXT NOT NULL,
                          telefono TEXT,
                          created_at TEXT,
                          updated_at TEXT)''')

            c.execute('''CREATE TABLE IF NOT EXISTS facturas
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          user_id INTEGER NOT NULL,
                          fecha TEXT,
                          nit_proveedor TEXT,
                          nombre_proveedor TEXT,
                          serie TEXT,
                          numero TEXT,
                          tipo_gasto TEXT,
                          monto REAL,
                          foto_path TEXT,
                          created_at TEXT,
                          FOREIGN KEY (user_id) REFERENCES usuarios (user_id))''')

            c.execute('CREATE INDEX IF NOT EXISTS idx_facturas_user ON facturas(user_id)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_facturas_fecha ON facturas(fecha)')

            conn.commit()
            conn.close()
            logger.info("Base de datos inicializada correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar base de datos: {e}")
            raise

    def _migrate_if_needed(self):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()

            c.execute("PRAGMA table_info(facturas)")
            columns = [col[1] for col in c.fetchall()]

            if 'user_id' not in columns:
                logger.info("Migrando base de datos a sistema multi-usuario")

                c.execute('ALTER TABLE facturas ADD COLUMN user_id INTEGER')
                c.execute('UPDATE facturas SET user_id = 0 WHERE user_id IS NULL')

                c.execute("SELECT COUNT(*) FROM usuarios WHERE user_id = 0")
                if c.fetchone()[0] == 0:
                    c.execute('''INSERT INTO usuarios (user_id, nombre, created_at)
                                 VALUES (0, 'Usuario Legacy', ?)''',
                              (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))

                conn.commit()
                logger.info("Migración completada")

            conn.close()
        except Exception as e:
            logger.error(f"Error en migración: {e}")

    def registrar_usuario(self, user_id: int, nombre: str, telefono: str = None) -> bool:
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute('''INSERT OR REPLACE INTO usuarios
                         (user_id, nombre, telefono, created_at, updated_at)
                         VALUES (?, ?, ?,
                                 COALESCE((SELECT created_at FROM usuarios WHERE user_id = ?), ?),
                                 ?)''',
                      (user_id, nombre, telefono, user_id, now, now))

            conn.commit()
            conn.close()
            logger.info(f"Usuario {user_id} registrado/actualizado: {nombre}")
            return True
        except Exception as e:
            logger.error(f"Error al registrar usuario: {e}")
            return False

    def usuario_existe(self, user_id: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('SELECT user_id FROM usuarios WHERE user_id = ?', (user_id,))
            existe = c.fetchone() is not None
            conn.close()
            return existe
        except Exception as e:
            logger.error(f"Error al verificar usuario: {e}")
            return False

    def obtener_usuario(self, user_id: int) -> Optional[Tuple]:
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('SELECT user_id, nombre, telefono FROM usuarios WHERE user_id = ?', (user_id,))
            usuario = c.fetchone()
            conn.close()
            return usuario
        except Exception as e:
            logger.error(f"Error al obtener usuario: {e}")
            return None

    def actualizar_nombre_usuario(self, user_id: int, nuevo_nombre: str) -> bool:
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''UPDATE usuarios SET nombre = ?, updated_at = ?
                         WHERE user_id = ?''',
                      (nuevo_nombre, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
            conn.commit()
            conn.close()
            logger.info(f"Nombre actualizado para usuario {user_id}: {nuevo_nombre}")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar nombre: {e}")
            return False

    def insertar_factura(self, user_id: int, fecha: str, nit: str, nombre: str,
                        serie: str, numero: str, tipo_gasto: str,
                        monto: float, foto_path: str) -> int:
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''INSERT INTO facturas
                         (user_id, fecha, nit_proveedor, nombre_proveedor, serie, numero,
                          tipo_gasto, monto, foto_path, created_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (user_id, fecha, nit, nombre, serie, numero, tipo_gasto, monto,
                       foto_path, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            factura_id = c.lastrowid
            conn.close()
            logger.info(f"Factura #{factura_id} insertada para usuario {user_id}")
            return factura_id
        except Exception as e:
            logger.error(f"Error al insertar factura: {e}")
            raise

    def obtener_resumen(self, user_id: int, mes: int = None, anio: int = None) -> Tuple[float, int, List[Tuple]]:
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()

            if mes and anio:
                fecha_inicio = f"{anio}-{mes:02d}-01"
                if mes == 12:
                    fecha_fin = f"{anio + 1}-01-01"
                else:
                    fecha_fin = f"{anio}-{mes + 1:02d}-01"

                c.execute('''SELECT SUM(monto), COUNT(*) FROM facturas
                             WHERE user_id = ? AND fecha >= ? AND fecha < ?''',
                          (user_id, fecha_inicio, fecha_fin))
            else:
                c.execute('SELECT SUM(monto), COUNT(*) FROM facturas WHERE user_id = ?', (user_id,))

            total, cantidad = c.fetchone()
            total = total or 0
            cantidad = cantidad or 0

            if mes and anio:
                c.execute('''SELECT tipo_gasto, SUM(monto), COUNT(*) FROM facturas
                             WHERE user_id = ? AND fecha >= ? AND fecha < ?
                             GROUP BY tipo_gasto''',
                          (user_id, fecha_inicio, fecha_fin))
            else:
                c.execute('''SELECT tipo_gasto, SUM(monto), COUNT(*) FROM facturas
                             WHERE user_id = ? GROUP BY tipo_gasto''', (user_id,))

            por_tipo = c.fetchall()

            conn.close()
            logger.debug(f"Resumen obtenido para usuario {user_id}: total={total}, cantidad={cantidad}")
            return total, cantidad, por_tipo
        except Exception as e:
            logger.error(f"Error al obtener resumen: {e}")
            raise

    def obtener_facturas(self, user_id: int, limit: int = 20) -> List[Tuple]:
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''SELECT id, fecha, nombre_proveedor, tipo_gasto, monto
                         FROM facturas WHERE user_id = ?
                         ORDER BY id DESC LIMIT ?''', (user_id, limit))
            facturas = c.fetchall()
            conn.close()
            logger.debug(f"Obtenidas {len(facturas)} facturas para usuario {user_id}")
            return facturas
        except Exception as e:
            logger.error(f"Error al obtener facturas: {e}")
            raise

    def obtener_todas_facturas(self, user_id: int, mes: int = None, anio: int = None) -> List[Tuple]:
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()

            if mes and anio:
                fecha_inicio = f"{anio}-{mes:02d}-01"
                if mes == 12:
                    fecha_fin = f"{anio + 1}-01-01"
                else:
                    fecha_fin = f"{anio}-{mes + 1:02d}-01"

                c.execute('''SELECT fecha, nit_proveedor, nombre_proveedor, serie, numero, tipo_gasto, monto
                             FROM facturas
                             WHERE user_id = ? AND fecha >= ? AND fecha < ?
                             ORDER BY fecha''',
                          (user_id, fecha_inicio, fecha_fin))
            else:
                c.execute('''SELECT fecha, nit_proveedor, nombre_proveedor, serie, numero, tipo_gasto, monto
                             FROM facturas WHERE user_id = ?
                             ORDER BY fecha''', (user_id,))

            facturas = c.fetchall()
            conn.close()
            logger.debug(f"Obtenidas {len(facturas)} facturas para exportar (usuario {user_id})")
            return facturas
        except Exception as e:
            logger.error(f"Error al obtener todas las facturas: {e}")
            raise

    def eliminar_factura(self, user_id: int, factura_id: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('DELETE FROM facturas WHERE id = ? AND user_id = ?', (factura_id, user_id))
            conn.commit()
            eliminada = c.rowcount > 0
            conn.close()

            if eliminada:
                logger.info(f"Factura #{factura_id} eliminada por usuario {user_id}")
            else:
                logger.warning(f"Factura #{factura_id} no encontrada para usuario {user_id}")

            return eliminada
        except Exception as e:
            logger.error(f"Error al eliminar factura: {e}")
            raise

    def obtener_meses_con_datos(self, user_id: int) -> List[Tuple[int, int, int]]:
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''SELECT DISTINCT
                         CAST(strftime('%Y', fecha) AS INTEGER) as anio,
                         CAST(strftime('%m', fecha) AS INTEGER) as mes,
                         COUNT(*) as cantidad
                         FROM facturas
                         WHERE user_id = ? AND fecha IS NOT NULL
                         GROUP BY anio, mes
                         ORDER BY anio DESC, mes DESC''', (user_id,))
            meses = c.fetchall()
            conn.close()
            return meses
        except Exception as e:
            logger.error(f"Error al obtener meses con datos: {e}")
            return []
