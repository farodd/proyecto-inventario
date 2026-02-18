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