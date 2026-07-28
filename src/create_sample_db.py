#!/usr/bin/env python3
"""
Crea una base de datos SQLite de ejemplo para probar la app.
Genera: src/db/inventario_lp02_sample.db
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

from pyparsing import line

DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "db" / "inventario_lp02_sample.db"

def create_tables(conn):
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS insumos (
        "CODIGO SAP" TEXT PRIMARY KEY,
        "DESCRIPCION DEL MATERIAL" TEXT,
        "CLASIFICACION" TEXT,
        "UM" TEXT,
        "OBSERVACIONES" TEXT
    )''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS ingresos (
        "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
        "CODIGO SAP" TEXT NOT NULL,
        "CLASIFICACION" TEXT NOT NULL,
        "DESCRIPCION DEL MATERIAL" TEXT NOT NULL,
        "UM" TEXT NOT NULL,
        "CANTIDAD" INTEGER NOT NULL,
        "FECHA DE INGRESO" DATE NOT NULL,
        "RESERVA" TEXT,
        "GUIA DESPACHO" TEXT,
        "OC" TEXT,
        "USO: OPERACIONES/PROYECTO" TEXT,
        "RECIBIDO POR" TEXT,
        "UBICACION" TEXT,
        "EMPRESA" TEXT,
        "PRECIO UNITARIO" REAL,
        "OBSERVACIONES" TEXT,
        FOREIGN KEY("CODIGO SAP") REFERENCES insumos("CODIGO SAP")
    )''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS salidas (
        "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
        "CODIGO SAP" TEXT NOT NULL,
        "CLASIFICACION" TEXT NOT NULL,
        "DESCRIPCION DEL MATERIAL" TEXT NOT NULL,
        "UM" TEXT NOT NULL,
        "CANTIDAD" INTEGER NOT NULL,
        "FECHA DE SALIDA" DATE NOT NULL,
        "N° DE GUIA DE SALIDA" TEXT,
        "USO: OPERACIONES/PROYECTO" TEXT,
        "ENTREGADO A" TEXT,
        "COMENTARIOS" TEXT,
        "UBICACION DE RETIRO" TEXT,
        FOREIGN KEY("CODIGO SAP") REFERENCES insumos("CODIGO SAP")
    )''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS stock (
        "CODIGO SAP" TEXT PRIMARY KEY,
        "CLASIFICACION" TEXT,
        "DESCRIPCION DEL MATERIAL" TEXT,
        "UM" TEXT,
        "STOCK INICIAL" INTEGER,
        "INGRESOS" INTEGER,
        "SALIDAS" INTEGER,
        "STOCK ACTUAL" INTEGER,
        "PUNTO DE REORDENAMIENTO" INTEGER
    )''')
    conn.commit()

def insert_sample_data(conn):
    cur = conn.cursor()
    insumos = [
        ("MAT001", "Tornillo M8 x 20mm", "FERRETERIA", "UN", ""),
        ("MAT002", "Tuerca M8", "FERRETERIA", "UN", ""),
        ("MAT003", "Lubricante 1L", "MANTENCION", "LT", ""),
        ("MAT004", "Guantes Nitrilo", "EPP", "PAR", ""),
        ("MAT005", "Cinta PVC 50mm", "FERRETERIA", "ROLLO", ""),
        ("MAT006", "Motor bomba 1HP", "ELECTRICO", "UN", ""),
        ("MAT007", "Filtro aire", "MANTENCION", "UN", ""),
        ("MAT008", "Aceite hidráulico 20L", "MANTENCION", "LT", ""),
        ("MAT009", "Tubo PVC 2\"", "SANEAMIENTO", "M", ""),
        ("MAT010", "Etiqueta QR", "IDENTIFICACION", "UN", "")
    ]
    cur.executemany('''
        INSERT OR IGNORE INTO insumos ("CODIGO SAP","DESCRIPCION DEL MATERIAL","CLASIFICACION","UM","OBSERVACIONES")
        VALUES (?, ?, ?, ?, ?)
    ''', insumos)

    # Stock inicial (some items)
    stock_rows = [
        ("MAT001","FERRETERIA","Tornillo M8 x 20mm","UN",100,0,0,100,50),
        ("MAT002","FERRETERIA","Tuerca M8","UN",200,0,0,200,100),
        ("MAT003","MANTENCION","Lubricante 1L","LT",50,0,0,50,20),
        ("MAT004","EPP","Guantes Nitrilo","PAR",150,0,0,150,50),
        ("MAT005","FERRETERIA","Cinta PVC 50mm","ROLLO",80,0,0,80,30),
    ]
    cur.executemany('''
        INSERT OR IGNORE INTO stock (
            "CODIGO SAP","CLASIFICACION","DESCRIPCION DEL MATERIAL","UM",
            "STOCK INICIAL","INGRESOS","SALIDAS","STOCK ACTUAL","PUNTO DE REORDENAMIENTO")
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', stock_rows)

    # Crear ingresos de ejemplo (últimos 6 meses)
    today = datetime.today().date()
    ingresos = []
    for i, code in enumerate(["MAT001","MAT002","MAT003","MAT004","MAT005"]):
        fecha = today - timedelta(days=30*(5-i))
        qty = [50, 30, 20, 40, 25][i]
        precio = [40, 20, 40, 10, 8][i]
        ingresos.append((
            code,
            "FERRETERIA" if "MAT00" in code and code not in ("MAT003","MAT004") else ("MANTENCION" if code=="MAT003" else "EPP"),
            "Descripción ejemplo " + code,
            "UN" if code not in ("MAT003","MAT008") else "LT",
            qty,
            fecha.isoformat(),
            None,
            f"GD-{100+i}",
            f"OC-{200+i}",
            "OPERACIONES",
            "Juan Perez",
            "Bodega LP02",
            "EmpresaX",
            precio,
            "Ingreso de prueba"
        ))
    cur.executemany('''
        INSERT INTO ingresos (
            "CODIGO SAP","CLASIFICACION","DESCRIPCION DEL MATERIAL","UM",
            "CANTIDAD","FECHA DE INGRESO","RESERVA","GUIA DESPACHO","OC",
            "USO: OPERACIONES/PROYECTO","RECIBIDO POR","UBICACION","EMPRESA","PRECIO UNITARIO","OBSERVACIONES"
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', ingresos)

    # Crear salidas de ejemplo
    salidas = [
        ("MAT001","FERRETERIA","Tornillo M8 x 20mm","UN",20,(today - timedelta(days=10)).isoformat(),"GS-001","OPERACIONES","Operario A","Salida de prueba","Sector A"),
        ("MAT002","FERRETERIA","Tuerca M8","UN",15,(today - timedelta(days=5)).isoformat(),"GS-002","OPERACIONES","Operario B","Salida de prueba","Sector B"),
    ]
    cur.executemany('''
        INSERT INTO salidas (
            "CODIGO SAP","CLASIFICACION","DESCRIPCION DEL MATERIAL","UM",
            "CANTIDAD","FECHA DE SALIDA","N° DE GUIA DE SALIDA","USO: OPERACIONES/PROYECTO",
            "ENTREGADO A","COMENTARIOS","UBICACION DE RETIRO"
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
    ''', salidas)

    # Actualizar stock: sumar ingresos y restar salidas, y actualizar campos INGRESOS/SALIDAS/STOCK ACTUAL
    for code, _, _, _, qty, fecha, *rest in ingresos:
        cur.execute('''
            UPDATE stock
            SET "INGRESOS" = COALESCE("INGRESOS",0) + ?,
                "STOCK ACTUAL" = COALESCE("STOCK ACTUAL",0) + ?
            WHERE "CODIGO SAP" = ?
        ''', (qty, qty, code))
    for code, _, _, _, qty, fecha, *rest in salidas:
        cur.execute('''
            UPDATE stock
            SET "SALIDAS" = COALESCE("SALIDAS",0) + ?,
                "STOCK ACTUAL" = MAX(0, COALESCE("STOCK ACTUAL",0) - ?)
            WHERE "CODIGO SAP" = ?
        ''', (qty, qty, code))
    conn.commit()

def main():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        print(f"Se sobreescribirá (si desea evitarlo, haga copia): {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    try:
        create_tables(conn)
        insert_sample_data(conn)
        print(f"Base de datos de ejemplo creada en: {DB_PATH}")
    finally:
        conn.close()
    
if __name__ == "__main__":
    main()