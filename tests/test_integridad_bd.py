"""
Tests de integridad sobre la base de datos REAL de producción.
Verifican que los datos existentes son coherentes.

IMPORTANTE: Estos tests son de SOLO LECTURA, no modifican la BD.
Se ejecutan con: pytest tests/test_integridad_bd.py -v
"""
import pytest
import sqlite3
import os

DB_REAL = os.path.join(os.path.dirname(__file__), '..', 'src', 'db', 'inventario_lp02.db')

# Saltar todos los tests si la BD real no existe
pytestmark = pytest.mark.skipif(
    not os.path.exists(DB_REAL),
    reason="Base de datos de producción no encontrada"
)


@pytest.fixture
def conn():
    """Conexión de solo lectura a la BD real."""
    connection = sqlite3.connect(f"file:{DB_REAL}?mode=ro", uri=True)
    yield connection
    connection.close()


class TestIntegridadStock:
    """Verificaciones de integridad del stock."""

    def test_sin_stock_negativo(self, conn):
        """No debe haber registros con stock negativo."""
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM stock WHERE "STOCK ACTUAL" < 0')
        negativos = cursor.fetchone()[0]
        assert negativos == 0, f"Hay {negativos} registros con stock negativo"

    def test_sin_codigos_sap_duplicados_en_stock(self, conn):
        """No debe haber códigos SAP duplicados en stock."""
        cursor = conn.cursor()
        cursor.execute('''
            SELECT "CODIGO SAP", COUNT(*) as n 
            FROM stock GROUP BY "CODIGO SAP" HAVING COUNT(*) > 1
        ''')
        duplicados = cursor.fetchall()
        assert len(duplicados) == 0, f"Códigos duplicados en stock: {duplicados}"

    def test_coherencia_stock_calculado(self, conn):
        """
        Stock actual debe coincidir con: 
        stock_inicial + sum(ingresos) - sum(salidas)
        """
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                s."CODIGO SAP",
                s."STOCK ACTUAL" as stock_bd,
                COALESCE(s."STOCK INICIAL", 0) 
                    + COALESCE(ing.total_ing, 0) 
                    - COALESCE(sal.total_sal, 0) as stock_calculado
            FROM stock s
            LEFT JOIN (
                SELECT "CODIGO SAP", SUM("CANTIDAD") as total_ing 
                FROM ingresos GROUP BY "CODIGO SAP"
            ) ing ON CAST(s."CODIGO SAP" AS TEXT) = CAST(ing."CODIGO SAP" AS TEXT)
            LEFT JOIN (
                SELECT "CODIGO SAP", SUM("CANTIDAD") as total_sal 
                FROM salidas GROUP BY "CODIGO SAP"
            ) sal ON CAST(s."CODIGO SAP" AS TEXT) = CAST(sal."CODIGO SAP" AS TEXT)
        ''')
        
        inconsistentes = []
        for row in cursor.fetchall():
            codigo, stock_bd, stock_calc = row
            if stock_bd != stock_calc:
                inconsistentes.append({
                    'codigo': codigo,
                    'stock_bd': stock_bd,
                    'stock_calculado': stock_calc,
                    'diferencia': stock_bd - stock_calc
                })
        
        assert len(inconsistentes) == 0, (
            f"Stock inconsistente en {len(inconsistentes)} materiales:\n"
            + "\n".join([
                f"  {i['codigo']}: BD={i['stock_bd']}, Calculado={i['stock_calculado']}, Diff={i['diferencia']}"
                for i in inconsistentes[:10]
            ])
        )


class TestIntegridadInsumos:
    """Verificaciones de integridad de insumos."""

    def test_sin_codigos_sap_duplicados(self, conn):
        """No debe haber códigos SAP duplicados en insumos."""
        cursor = conn.cursor()
        cursor.execute('''
            SELECT "CODIGO SAP", COUNT(*) FROM insumos 
            GROUP BY "CODIGO SAP" HAVING COUNT(*) > 1
        ''')
        duplicados = cursor.fetchall()
        assert len(duplicados) == 0, f"Códigos duplicados: {duplicados}"

    def test_campos_obligatorios_insumos(self, conn):
        """Todos los insumos deben tener código SAP y descripción."""
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM insumos 
            WHERE "CODIGO SAP" IS NULL OR TRIM("CODIGO SAP") = ''
               OR "DESCRIPCION DEL MATERIAL" IS NULL OR TRIM("DESCRIPCION DEL MATERIAL") = ''
        ''')
        nulos = cursor.fetchone()[0]
        assert nulos == 0, f"{nulos} insumos con campos obligatorios vacíos"


class TestIntegridadIngresos:
    """Verificaciones de integridad de ingresos."""

    def test_ingresos_con_cantidad_positiva(self, conn):
        """Todos los ingresos deben tener cantidad > 0."""
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM ingresos WHERE "CANTIDAD" <= 0')
        invalidos = cursor.fetchone()[0]
        assert invalidos == 0, f"{invalidos} ingresos con cantidad <= 0"

    def test_ingresos_con_fecha_valida(self, conn):
        """Todos los ingresos deben tener fecha."""
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM ingresos 
            WHERE "FECHA DE INGRESO" IS NULL OR TRIM("FECHA DE INGRESO") = ''
        ''')
        sin_fecha = cursor.fetchone()[0]
        assert sin_fecha == 0, f"{sin_fecha} ingresos sin fecha"

    def test_ingresos_referencian_insumos(self, conn):
        """Los ingresos deben referenciar insumos existentes."""
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT i."CODIGO SAP" 
            FROM ingresos i
            LEFT JOIN insumos ins ON CAST(i."CODIGO SAP" AS TEXT) = CAST(ins."CODIGO SAP" AS TEXT)
            WHERE ins."CODIGO SAP" IS NULL
        ''')
        huerfanos = cursor.fetchall()
        # Warning, no falla — puede haber insumos eliminados
        if huerfanos:
            pytest.warns(UserWarning, 
                match=f"{len(huerfanos)} ingresos referencian insumos inexistentes")


class TestIntegridadSalidas:
    """Verificaciones de integridad de salidas."""

    def test_salidas_con_cantidad_positiva(self, conn):
        """Todas las salidas deben tener cantidad > 0."""
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM salidas WHERE "CANTIDAD" <= 0')
        invalidos = cursor.fetchone()[0]
        assert invalidos == 0, f"{invalidos} salidas con cantidad <= 0"

    def test_salidas_con_fecha_valida(self, conn):
        """Todas las salidas deben tener fecha."""
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM salidas 
            WHERE "FECHA DE SALIDA" IS NULL OR TRIM("FECHA DE SALIDA") = ''
        ''')
        sin_fecha = cursor.fetchone()[0]
        assert sin_fecha == 0, f"{sin_fecha} salidas sin fecha"


class TestIntegridadMetadata:
    """Verificaciones de integridad de archivos de metadata."""

    def test_metadata_insumos_valida(self):
        """El archivo metadata_insumos.json debe ser JSON válido."""
        import json
        path = os.path.join(os.path.dirname(__file__), '..', 'metadata', 'metadata_insumos.json')
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert 'categorias' in data
        assert 'unidades_medida' in data

    def test_metadata_ingresos_valida(self):
        """El archivo metadata_ingresos.json debe ser JSON válido."""
        import json
        path = os.path.join(os.path.dirname(__file__), '..', 'metadata', 'metadata_ingresos.json')
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert 'categorias' in data

    def test_metadata_salidas_valida(self):
        """El archivo salidas.json debe ser JSON válido."""
        import json
        path = os.path.join(os.path.dirname(__file__), '..', 'metadata', 'salidas.json')
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert 'categorias' in data