import streamlit as st
import pandas as pd
import sys
import os

# Agregar el directorio 'src' al path para importar modulo
from src.database import InventarioDatabase
from src.data_process import estandarizar_datos


def main():
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
    
    # Definir las páginas con tus secciones específicas
    pages = {
        "🏠 Sistema LP02": [
            st.Page("pages/inicio.py", title="Inicio", icon="🏠")
        ],
        "📊 Gestión de Inventario": [
            st.Page("pages/insumos.py", title="Insumos", icon="📋"),
            st.Page("pages/ingresos.py", title="Ingreso", icon="📈"),
            st.Page("pages/salidas.py", title="Salida", icon="📉"),
            st.Page("pages/stock.py", title="Stock", icon="📦")
        ]
    }

    pg = st.navigation(pages)
    
    # Ejecutar la página seleccionada
    pg.run()

if __name__ == "__main__":
    main()