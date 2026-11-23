import os
import sqlite3
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "GestionPanol"
else:
    DATA_DIR = Path(__file__).resolve().parents[1]

DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "panol_gestion.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS personal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                dni_cuit TEXT UNIQUE NOT NULL,
                rol TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ubicaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS materiales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                precio REAL DEFAULT 0,
                stock INTEGER DEFAULT 0,
                stock_minimo INTEGER DEFAULT 0,
                ubicacion_id INTEGER,
                FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones(id) ON DELETE SET NULL
            )
            """
        )

        # Migración automática para bases de datos creadas en versiones anteriores
        cursor.execute("PRAGMA table_info(materiales)")
        columnas_materiales = [col["name"] for col in cursor.fetchall()]
        if "ubicacion_id" not in columnas_materiales:
            cursor.execute(
                "ALTER TABLE materiales ADD COLUMN ubicacion_id INTEGER REFERENCES ubicaciones(id)"
            )
        if "stock_minimo" not in columnas_materiales:
            cursor.execute(
                "ALTER TABLE materiales ADD COLUMN stock_minimo INTEGER DEFAULT 0"
            )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS herramientas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                marca TEXT NOT NULL,
                modelo TEXT NOT NULL,
                antiguedad_anios INTEGER DEFAULT 0,
                estado_mantenimiento TEXT DEFAULT 'Operativo',
                personal_id INTEGER,
                FOREIGN KEY (personal_id) REFERENCES personal(id)
            )
            """
        )

        cursor.execute(
            """
            UPDATE herramientas
            SET estado_mantenimiento = 'Operativo'
            WHERE estado_mantenimiento IS NULL
               OR TRIM(estado_mantenimiento) = ''
               OR estado_mantenimiento = 'Óptimo'
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cabecera_transacciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personal_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                fecha TEXT DEFAULT CURRENT_TIMESTAMP,
                observaciones TEXT,
                FOREIGN KEY (personal_id) REFERENCES personal(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS detalle_transacciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaccion_id INTEGER NOT NULL,
                material_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                FOREIGN KEY (transaccion_id) REFERENCES cabecera_transacciones(id),
                FOREIGN KEY (material_id) REFERENCES materiales(id)
            )
            """
        )

        conn.commit()
    finally:
        conn.close()


init_db()