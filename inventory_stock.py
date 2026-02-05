import streamlit as st
import pandas as pd
import sys
import os

# Agregar el directorio 'src' al path para importar modulo
from src.database import InventarioDatabase
from src.data_process import estandarizar_datos


st.set_page_config(
    page_title="Sistema de Inventario - LP02",
    page_icon="📦",
    layout="wide"
)

# Estado compartido mínimo
if 'inventario_data' not in st.session_state:
    st.session_state.inventario_data = {
        'datos_cargados': False,
        'ultima_actualizacion': None
    }
    
st.title("📦 Sistema de Inventario de Insumos Operacionales - LP02")
st.markdown("---")

st.markdown("""
## 🏠 Página Principal

Bienvenido al sistema de inventario de insumos operacionales para el proyecto de la Bodega LP02.

### 📋 Páginas disponibles:

**📊 Gestión de Inventario:**
- **📋 Insumos**: Gestión de insumos operacionales (agregar, ver y actualizar insumos)
- **📈 Registro de Ingreso**: Registro de ingresos de insumos al inventario
- **📉 Registro de Salida**: Registro de salidas de insumos del inventario  
- **📦 Control de Stock**: Visualización y gestión del stock actual de insumos

### ⚠️ Consideraciones importantes:

- Asegúrese de ingresar datos válidos y completos en cada sección
- La aplicación tiene restricciones para evitar errores en la gestión del inventario
- Mantenga la integridad del inventario siguiendo el flujo de procesos

### 🚀 Para comenzar:

1. **Primero**: Configure o verifique los insumos en la sección **Insumos**
2. **Luego**: Registre ingresos de material usando **Registro de Ingreso**
3. **Gestione salidas** con **Registro de Salida**
4. **Monitoree** el estado general en **Control de Stock**
""")

# Estado del sistema
st.markdown("---")
col1, col2, col3 = st.columns([0.75, 1, 0.75])
with col2:
    st.subheader("📊 Resumen del Stock actual")
try:
    db = InventarioDatabase('src/db/inventario_lp02.db')
    cursor = db.cursor
    cursor.execute("""SELECT [DESCRIPCION DEL MATERIAL],
                   [STOCK ACTUAL], [PUNTO DE REORDENAMIENTO] FROM stock""")
    resultados = cursor.fetchall()

    if resultados:
        df = pd.DataFrame(resultados, columns=['DESCRIPCION DEL MATERIAL', 'STOCK ACTUAL', 'PUNTO DE REORDENAMIENTO'])

        def determinar_estado(row):
            if row['STOCK ACTUAL'] <= 0:
                return "🚫 Sin Stock"
            elif row['STOCK ACTUAL'] <= row['PUNTO DE REORDENAMIENTO']:
                return "⚠️ Stock Bajo"
            else:
                return "✅ Normal"
            
        df['Estado'] = df.apply(determinar_estado, axis=1)

        # Ordenar por prioridad de estado
        estado_prioridad = {"🚫 Sin Stock": 1, "⚠️ Stock Bajo": 2, "✅ Normal": 3}
        df['Prioridad'] = df['Estado'].map(estado_prioridad)
        df = df.sort_values(by='Prioridad').drop(columns=['Prioridad'])

        st.dataframe(df,
                     width='stretch',
                     height=400,
                     column_config={
                         'DESCRIPCION DEL MATERIAL': 'Descripción del Material',
                         'STOCK ACTUAL': 'Stock Actual',
                         'Estado': 'Estado del Stock'})

    db.close()
except Exception as e:
    st.error(f"❌ Error al conectar con la base de datos: {e}")