import streamlit as st
import pandas as pd
import sys
from datetime import datetime, datetime

sys.path.append('..')
from src.database import InventarioDatabase

st.title("📈 Registro de Ingreso")  

# Verificar si hay materiales pre-seleccionados
if 'material_seleccionado' in st.session_state:
    material_seleccionado = st.session_state['material_seleccionado']
    st.success(f"Material pre-seleccionado: {material_seleccionado}")

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.success(f"**{len(material_seleccionado)} materiales pre-seleccionados para ingreso** desde catálogo")
            st.caption("Los codigos SAP y descripciones no se pueden modificar aquí. " \
            "Complete los campos restantes para registrar el ingreso.")
        with col2:
            if st.button("Cambiar selección"):
                st.switch_page("pages/1_insumos.py")