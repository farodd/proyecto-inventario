"""
Tests de integración para el sistema de inventario.
Verifican el flujo completo entre componentes:
  Insumos → Ingresos → Stock → Salidas → Eliminaciones
"""
import pytest


class TestFlujoIngresoStock:
    """
    Verifica que registrar un ingreso actualice correctamente el stock.
    Flujo: insert_ingreso → update_stock_on_ingreso → verificar stock.
    """

    def test_ingreso_actualiza_stock(self, db_con_datos):
        """El flujo completo de ingreso debe reflejarse en stock."""
        # 1. Registrar ingreso
        resultado_ingreso = db_con_datos.insert_ingreso(
            "MAT001", "IMPERMEABILIZACION", "Tubería HDPE 200mm", "MT",
            50, "2026-01-15", 15000.0
        )
        assert resultado_ingreso == True
        
        # 2. Actualizar stock
        resultado_stock = db_con_datos.update_stock_on_ingreso("MAT001", 50)
        assert resultado_stock == True
        
        # 3. Verificar stock final
        db_con_datos.cursor.execute(
            'SELECT "STOCK ACTUAL" FROM stock WHERE "CODIGO SAP" = ?', ("MAT001",)
        )
        stock_actual = db_con_datos.cursor.fetchone()[0]
        assert stock_actual == 150  # 100 inicial + 50 ingresados

    def test_multiples_ingresos_acumulan_stock(self, db_con_datos):
        """Varios ingresos sucesivos deben sumar correctamente al stock."""
        cantidades = [25, 30, 45]
        
        for i, cant in enumerate(cantidades):
            db_con_datos.insert_ingreso(
                "MAT001", "IMP", "Tubería", "MT",
                cant, f"2026-01-{15 + i}", 5000.0
            )
            db_con_datos.update_stock_on_ingreso("MAT001", cant)
        
        db_con_datos.cursor.execute(
            'SELECT "STOCK ACTUAL" FROM stock WHERE "CODIGO SAP" = ?', ("MAT001",)
        )
        stock_actual = db_con_datos.cursor.fetchone()[0]
        assert stock_actual == 200  # 100 + 25 + 30 + 45


class TestFlujoSalidaStock:
    """
    Verifica que registrar una salida descuente correctamente del stock.
    Flujo: update_stock_on_salida → insert_salida → verificar stock.
    """

    def test_salida_descuenta_stock(self, db_con_datos):
        """La salida debe descontar del stock correctamente."""
        # 1. Verificar stock antes de la salida
        exito, stock_restante = db_con_datos.update_stock_on_salida("MAT001", 30)
        assert exito == True
        
        # 2. Registrar la salida
        resultado = db_con_datos.insert_salida(
            "MAT001", "IMPERMEABILIZACION", "Tubería HDPE 200mm", "MT",
            30, "2026-01-20", uso="OPERACIONES"
        )
        assert resultado == True
        
        # 3. Verificar stock final
        db_con_datos.cursor.execute(
            'SELECT "STOCK ACTUAL" FROM stock WHERE "CODIGO SAP" = ?', ("MAT001",)
        )
        stock_actual = db_con_datos.cursor.fetchone()[0]
        assert stock_actual == 70  # 100 - 30

    def test_salida_rechazada_por_stock_insuficiente(self, db_con_datos):
        """No debe registrar salida si el stock es insuficiente."""
        # MAT002 tiene stock = 10
        exito, stock_actual = db_con_datos.update_stock_on_salida("MAT002", 50)
        
        assert exito == False
        assert stock_actual == 10
        
        # Verificar que el stock NO cambió
        db_con_datos.cursor.execute(
            'SELECT "STOCK ACTUAL" FROM stock WHERE "CODIGO SAP" = ?', ("MAT002",)
        )
        stock_bd = db_con_datos.cursor.fetchone()[0]
        assert stock_bd == 10  # Sin cambios


class TestFlujoCompletoIngresoSalida:
    """
    Test de integración del ciclo completo:
    Ingreso → Stock sube → Salida → Stock baja → Verificar coherencia
    """

    def test_ciclo_ingreso_salida_completo(self, db_con_datos):
        """Ciclo completo: ingreso + salida = stock coherente."""
        # Estado inicial: MAT001 con stock = 100
        
        # PASO 1: Ingresar 50 unidades
        db_con_datos.insert_ingreso(
            "MAT001", "IMP", "Tubería", "MT", 50, "2026-01-15", 5000
        )
        db_con_datos.update_stock_on_ingreso("MAT001", 50)
        
        # Verificar: stock = 150
        db_con_datos.cursor.execute(
            'SELECT "STOCK ACTUAL" FROM stock WHERE "CODIGO SAP" = ?', ("MAT001",)
        )
        assert db_con_datos.cursor.fetchone()[0] == 150
        
        # PASO 2: Retirar 80 unidades
        exito, _ = db_con_datos.update_stock_on_salida("MAT001", 80)
        assert exito == True
        db_con_datos.insert_salida("MAT001", "IMP", "Tubería", "MT", 80, "2026-01-20")
        
        # Verificar: stock = 70
        db_con_datos.cursor.execute(
            'SELECT "STOCK ACTUAL" FROM stock WHERE "CODIGO SAP" = ?', ("MAT001",)
        )
        assert db_con_datos.cursor.fetchone()[0] == 70
        
        # PASO 3: Nuevo ingreso de 30
        db_con_datos.insert_ingreso(
            "MAT001", "IMP", "Tubería", "MT", 30, "2026-01-25", 5000
        )
        db_con_datos.update_stock_on_ingreso("MAT001", 30)
        
        # Verificar final: stock = 100
        db_con_datos.cursor.execute(
            'SELECT "STOCK ACTUAL" FROM stock WHERE "CODIGO SAP" = ?', ("MAT001",)
        )
        assert db_con_datos.cursor.fetchone()[0] == 100


class TestFlujoEliminacionReversion:
    """
    Verifica que eliminar un ingreso o salida revierta correctamente el stock.
    Simula el comportamiento de la UI al eliminar registros.
    """

    def test_eliminar_ingreso_revierte_stock(self, db_con_datos):
        """Al eliminar un ingreso, el stock debe volver a su valor anterior."""
        # Registrar ingreso de 50
        db_con_datos.insert_ingreso(
            "MAT001", "IMP", "Tubería", "MT", 50, "2026-01-15", 5000
        )
        db_con_datos.update_stock_on_ingreso("MAT001", 50)
        
        # Stock ahora = 150
        
        # Obtener ID del ingreso
        db_con_datos.cursor.execute('SELECT ID FROM ingresos ORDER BY ID DESC LIMIT 1')
        id_ingreso = db_con_datos.cursor.fetchone()[0]
        
        # Eliminar ingreso y revertir stock (como hace la UI)
        db_con_datos.delete_ingreso(id_ingreso)
        db_con_datos.revert_stock_ingreso("MAT001", 50)
        
        # Verificar: stock vuelve a 100
        db_con_datos.cursor.execute(
            'SELECT "STOCK ACTUAL" FROM stock WHERE "CODIGO SAP" = ?', ("MAT001",)
        )
        assert db_con_datos.cursor.fetchone()[0] == 100

    def test_eliminar_salida_revierte_stock(self, db_con_datos):
        """Al eliminar una salida, el stock debe restaurarse."""
        # Registrar salida de 30
        db_con_datos.update_stock_on_salida("MAT001", 30)
        db_con_datos.insert_salida("MAT001", "IMP", "Tubería", "MT", 30, "2026-01-20")
        
        # Stock ahora = 70
        
        # Obtener ID de la salida
        db_con_datos.cursor.execute('SELECT ID FROM salidas ORDER BY ID DESC LIMIT 1')
        id_salida = db_con_datos.cursor.fetchone()[0]
        
        # Eliminar salida y revertir stock
        db_con_datos.delete_salida(id_salida)
        db_con_datos.revert_stock_salida("MAT001", 30)
        
        # Verificar: stock vuelve a 100
        db_con_datos.cursor.execute(
            'SELECT "STOCK ACTUAL" FROM stock WHERE "CODIGO SAP" = ?', ("MAT001",)
        )
        assert db_con_datos.cursor.fetchone()[0] == 100

    def test_eliminar_ingreso_sin_afectar_otros_materiales(self, db_con_datos):
        """Eliminar ingreso de un material NO debe afectar a otros."""
        # Stock inicial: MAT001=100, MAT002=10
        db_con_datos.insert_ingreso("MAT001", "IMP", "Tubería", "MT", 50, "2026-01-15", 5000)
        db_con_datos.update_stock_on_ingreso("MAT001", 50)
        
        db_con_datos.cursor.execute('SELECT ID FROM ingresos ORDER BY ID DESC LIMIT 1')
        id_ingreso = db_con_datos.cursor.fetchone()[0]
        
        db_con_datos.delete_ingreso(id_ingreso)
        db_con_datos.revert_stock_ingreso("MAT001", 50)
        
        # MAT002 debe seguir igual
        db_con_datos.cursor.execute(
            'SELECT "STOCK ACTUAL" FROM stock WHERE "CODIGO SAP" = ?', ("MAT002",)
        )
        assert db_con_datos.cursor.fetchone()[0] == 10


class TestIntegridadDatos:
    """
    Tests que verifican la coherencia de datos entre tablas.
    """

    def test_stock_nunca_negativo_tras_operaciones(self, db_con_datos):
        """El stock nunca debe quedar negativo tras cualquier operación."""
        # Intentar retirar más de lo que hay
        db_con_datos.update_stock_on_salida("MAT002", 999)  # Rechazado
        
        db_con_datos.cursor.execute(
            'SELECT "STOCK ACTUAL" FROM stock WHERE "CODIGO SAP" = ?', ("MAT002",)
        )
        stock = db_con_datos.cursor.fetchone()[0]
        assert stock >= 0

    def test_coherencia_stock_tras_operaciones_mixtas(self, db_con_datos):
        """Stock debe ser coherente tras múltiples operaciones."""
        # MAT003: stock inicial = 500
        operaciones = [
            ('ingreso', 100),   # 600
            ('salida', 200),    # 400
            ('ingreso', 50),    # 450
            ('salida', 150),    # 300
            ('ingreso', 200),   # 500
        ]
        
        stock_esperado = 500
        for tipo, cantidad in operaciones:
            if tipo == 'ingreso':
                db_con_datos.insert_ingreso(
                    "MAT003", "IMP", "Geomembrana", "M2", cantidad, "2026-01-15", 1000
                )
                db_con_datos.update_stock_on_ingreso("MAT003", cantidad)
                stock_esperado += cantidad
            else:
                exito, _ = db_con_datos.update_stock_on_salida("MAT003", cantidad)
                assert exito == True
                db_con_datos.insert_salida(
                    "MAT003", "IMP", "Geomembrana", "M2", cantidad, "2026-01-20"
                )
                stock_esperado -= cantidad
        
        db_con_datos.cursor.execute(
            'SELECT "STOCK ACTUAL" FROM stock WHERE "CODIGO SAP" = ?', ("MAT003",)
        )
        stock_real = db_con_datos.cursor.fetchone()[0]
        assert stock_real == stock_esperado

    def test_conteo_registros_ingresos_salidas(self, db_con_datos):
        """La cantidad de registros debe coincidir con las operaciones realizadas."""
        # 3 ingresos
        for i in range(3):
            db_con_datos.insert_ingreso(
                "MAT001", "IMP", "Tubería", "MT", 10, f"2026-01-{15+i}", 5000
            )
        
        # 2 salidas
        for i in range(2):
            db_con_datos.insert_salida(
                "MAT001", "IMP", "Tubería", "MT", 5, f"2026-01-{20+i}"
            )
        
        _, ingresos = db_con_datos.get_all_ingresos()
        _, salidas = db_con_datos.get_all_salidas()
        
        assert len(ingresos) == 3
        assert len(salidas) == 2

    def test_material_nuevo_via_ingreso_crea_stock(self, db_con_datos):
        """
        Un ingreso de un material que no está en stock
        debe crear automáticamente el registro de stock.
        """
        # MAT_NUEVO no existe en stock
        db_con_datos.insert_ingreso(
            "MAT_NUEVO", "CAT", "Material nuevo", "UN", 25, "2026-02-01", 3000
        )
        resultado = db_con_datos.update_stock_on_ingreso(
            "MAT_NUEVO", 25, "CAT", "Material nuevo", "UN"
        )
        
        # Debe haberse creado
        db_con_datos.cursor.execute(
            'SELECT "STOCK ACTUAL" FROM stock WHERE "CODIGO SAP" = ?', ("MAT_NUEVO",)
        )
        resultado = db_con_datos.cursor.fetchone()
        assert resultado is not None
        assert resultado[0] == 25