import streamlit as st
import pandas as pd
import sys
import os

sys.path.append('..')
from src.database import InventarioDatabase

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
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.subheader("📊 Resumen del Stock actual")
try:
    st.write("**🔍 Debug - Información de paths:**")
    st.write(f"**Current working directory:** {os.getcwd()}")
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

        st.dataframe(df,
                     use_container_width=True,
                     height=400,
                     column_config={
                         'DESCRIPCION DEL MATERIAL': 'Descripción del Material',
                         'STOCK ACTUAL': 'Stock Actual',
                         'Estado': 'Estado del Stock'})

    db.close()
except Exception as e:
    st.error(f"❌ Error al conectar con la base de datos: {e}")