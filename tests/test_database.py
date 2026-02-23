"""
Tests unitarios para src/database.py
Cada test usa una BD SQLite temporal aislada.
"""
import pytest
import sqlite3


# ══════════════════════════════════════════════════════════════
# TESTS: INSERT INSUMO
# ══════════════════════════════════════════════════════════════

class TestInsertInsumo:
    """Tests para el método insert_insumo."""

    def test_insertar_insumo_exitoso(self, db):
        """Debe insertar un insumo correctamente."""
        db.insert_insumo("MAT001", "Tubería HDPE", "IMPERMEABILIZACION", "MT", "Obs")
        
        db.cursor.execute('SELECT * FROM insumos WHERE "CODIGO SAP" = ?', ("MAT001",))
        resultado = db.cursor.fetchone()
        
        assert resultado is not None
        assert resultado[0] == "MAT001"
        assert resultado[1] == "Tubería HDPE"
        assert resultado[2] == "IMPERMEABILIZACION"
        assert resultado[3] == "MT"

    def test_insertar_insumo_duplicado(self, db):
        """No debe insertar un insumo con código SAP duplicado."""
        db.insert_insumo("MAT001", "Tubería HDPE", "IMPERMEABILIZACION", "MT", "")
        db.insert_insumo("MAT001", "Otro material", "OTRA", "UN", "")  # Duplicado
        
        db.cursor.execute('SELECT COUNT(*) FROM insumos WHERE "CODIGO SAP" = ?', ("MAT001",))
        count = db.cursor.fetchone()[0]
        assert count == 1  # Solo debe existir uno

    def test_insertar_insumo_sin_observaciones(self, db):
        """Debe aceptar observaciones vacías o None."""
        db.insert_insumo("MAT001", "Tubería", "IMP", "MT", None)
        
        db.cursor.execute('SELECT "OBSERVACIONES" FROM insumos WHERE "CODIGO SAP" = ?', ("MAT001",))
        resultado = db.cursor.fetchone()
        assert resultado is not None

    def test_insertar_multiples_insumos(self, db):
        """Debe insertar múltiples insumos distintos."""
        db.insert_insumo("MAT001", "Material 1", "CAT1", "MT", "")
        db.insert_insumo("MAT002", "Material 2", "CAT2", "UN", "")
        db.insert_insumo("MAT003", "Material 3", "CAT1", "M2", "")
        
        db.cursor.execute('SELECT COUNT(*) FROM insumos')
        count = db.cursor.fetchone()[0]
        assert count == 3


# ══════════════════════════════════════════════════════════════
# TESTS: INSERT INGRESO
# ══════════════════════════════════════════════════════════════

class TestInsertIngreso:
    """Tests para el método insert_ingreso."""

    def test_insertar_ingreso_exitoso(self, db):
        """Debe insertar un ingreso con todos los campos."""
        resultado = db.insert_ingreso(
            codigo_sap="MAT001",
            clasificacion="IMPERMEABILIZACION",
            descripcion="Tubería HDPE",
            um="MT",
            cantidad=50,
            fecha_ingreso="2026-01-15",
            precio_unitario=15000.0,
            reserva="5080832",
            guia_despacho="135973",
            oc="4510237047",
            uso="OPERACIONES",
            recibido_por="RENE MENDOZA",
            ubicacion="BODEGA",
            empresa="RELIX",
            observaciones="Ingreso de prueba"
        )
        
        assert resultado == True
        
        db.cursor.execute('SELECT COUNT(*) FROM ingresos')
        count = db.cursor.fetchone()[0]
        assert count == 1

    def test_insertar_ingreso_campos_minimos(self, db):
        """Debe insertar con solo campos obligatorios."""
        resultado = db.insert_ingreso(
            codigo_sap="MAT001",
            clasificacion="IMP",
            descripcion="Tubería",
            um="MT",
            cantidad=10,
            fecha_ingreso="2026-01-15",
            precio_unitario=5000.0
        )
        
        assert resultado == True

    def test_insertar_multiples_ingresos_mismo_codigo(self, db):
        """Debe permitir múltiples ingresos con el mismo código SAP."""
        for i in range(3):
            db.insert_ingreso("MAT001", "IMP", "Tubería", "MT", 10 * (i + 1),
                              f"2026-01-{15 + i}", 5000.0)
        
        db.cursor.execute('SELECT COUNT(*) FROM ingresos WHERE "CODIGO SAP" = ?', ("MAT001",))
        count = db.cursor.fetchone()[0]
        assert count == 3

    def test_ingreso_cantidad_cero(self, db):
        """Debe aceptar cantidad 0 (la validación está en la UI)."""
        resultado = db.insert_ingreso("MAT001", "IMP", "Tubería", "MT", 0, "2026-01-15", 0)
        assert resultado == True

