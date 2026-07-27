"""
Configuración compartida para todos los tests.
Crea una base de datos SQLite temporal en memoria para cada sesión de test.
"""
import pytest
import sqlite3
import os
import sys
import json
import tempfile

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print("CWD:", os.getcwd())
print("sys.path:", sys.path)
from src.database import InventarioDatabase


@pytest.fixture
def db_path(tmp_path):
    """Crea una ruta temporal para la base de datos de test."""
    return str(tmp_path / "test_inventario.db")


@pytest.fixture
def setup_db(db_path):
    """
    Crea la base de datos con el esquema completo para tests.
    Retorna la ruta de la BD temporal.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Crear tabla insumos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS insumos (
            "CODIGO SAP" TEXT PRIMARY KEY,
            "DESCRIPCION DEL MATERIAL" TEXT NOT NULL,
            "CLASIFICACION" TEXT,
            "UM" TEXT,
            "OBSERVACIONES" TEXT
        )
    ''')

    # Crear tabla ingresos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingresos (
            "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
            "CODIGO SAP" TEXT NOT NULL,
            "CLASIFICACION" TEXT,
            "DESCRIPCION DEL MATERIAL" TEXT,
            "UM" TEXT,
            "CANTIDAD" REAL NOT NULL,
            "FECHA DE INGRESO" TEXT NOT NULL,
            "RESERVA" TEXT,
            "GUIA DESPACHO" TEXT,
            "OC" TEXT,
            "USO: OPERACIONES/PROYECTO" TEXT,
            "RECIBIDO POR" TEXT,
            "UBICACION" TEXT,
            "EMPRESA" TEXT,
            "PRECIO UNITARIO" REAL,
            "OBSERVACIONES" TEXT
        )
    ''')

    # Crear tabla salidas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salidas (
            "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
            "CODIGO SAP" TEXT NOT NULL,
            "CLASIFICACION" TEXT,
            "DESCRIPCION DEL MATERIAL" TEXT,
            "UM" TEXT,
            "CANTIDAD" REAL NOT NULL,
            "FECHA DE SALIDA" TEXT NOT NULL,
            "N° DE GUIA DE SALIDA" TEXT,
            "USO: OPERACIONES/PROYECTO" TEXT,
            "ENTREGADO A" TEXT,
            "COMENTARIOS" TEXT,
            "UBICACION DE RETIRO" TEXT
        )
    ''')

    # Crear tabla stock
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock (
            "CODIGO SAP" TEXT PRIMARY KEY,
            "CLASIFICACION" TEXT,
            "DESCRIPCION DEL MATERIAL" TEXT,
            "UM" TEXT,
            "STOCK INICIAL" REAL DEFAULT 0,
            "INGRESOS" REAL DEFAULT 0,
            "SALIDAS" REAL DEFAULT 0,
            "STOCK ACTUAL" REAL DEFAULT 0,
            "PUNTO DE REORDENAMIENTO" REAL DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def db(setup_db):
    """Retorna una instancia de InventarioDatabase conectada a la BD de test."""
    database = InventarioDatabase(setup_db)
    yield database
    database.close()


@pytest.fixture
def db_con_datos(db):
    """
    BD con datos de prueba pre-cargados.
    Simula un inventario con 3 insumos, ingresos y stock.
    """
    # Insertar insumos de prueba
    db.insert_insumo("MAT001", "Tubería HDPE 200mm", "IMPERMEABILIZACION", "MT", "Material estándar")
    db.insert_insumo("MAT002", "Válvula compuerta 6 pulgadas", "PIEZAS ESPECIALES", "UN", "")
    db.insert_insumo("MAT003", "Geomembrana HDPE 1.5mm", "IMPERMEABILIZACION", "M2", "Alta densidad")

    # Insertar stock inicial
    db.insert_stock("MAT001", "IMPERMEABILIZACION", "Tubería HDPE 200mm", "MT", 100, 0, 0, 100, 20)
    db.insert_stock("MAT002", "PIEZAS ESPECIALES", "Válvula compuerta 6 pulgadas", "UN", 10, 0, 0, 10, 3)
    db.insert_stock("MAT003", "IMPERMEABILIZACION", "Geomembrana HDPE 1.5mm", "M2", 500, 0, 0, 500, 100)

    return db


@pytest.fixture
def metadata_insumos_path(tmp_path):
    """Crea un archivo de metadata temporal para tests."""
    metadata = {
        "version": "1.0",
        "categorias": {
            "IMPERMEABILIZACION": {
                "variaciones": ["Impermeabilizacion", "impermeabilizacion", "IMPERMEABILIZACIÓN"],
                "estandar": "IMPERMEABILIZACION"
            },
            "PIEZAS ESPECIALES": {
                "variaciones": ["Piezas Especiales", "piezas especiales"],
                "estandar": "PIEZAS ESPECIALES"
            }
        },
        "unidades_medida": {
            "MT": {
                "variaciones": ["Mt", "mt", "metros", "Metros"],
                "estandar": "MT"
            },
            "UN": {
                "variaciones": ["Un", "un", "unidad", "Unidad"],
                "estandar": "UN"
            },
            "M2": {
                "variaciones": ["m2", "M²", "metros cuadrados"],
                "estandar": "M2"
            }
        }
    }
    path = tmp_path / "metadata_insumos.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False)
    return str(path)