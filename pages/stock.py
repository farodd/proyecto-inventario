import streamlit as st
import pandas as pd
import sys
import time

sys.path.append('..')
from src.database import InventarioDatabase

DB_PATH = r'src\db\inventario_lp02.db'

# ---- Funciones de carga ----
@st.cache_data(ttl=30)
def cargar_stock():
    db = InventarioDatabase(DB_PATH)
    columnas, datos = db.get_all_stock()
    db.close()
    if datos:
        return pd.DataFrame(datos, columns=columnas)
    return pd.DataFrame()

@st.cache_data(ttl=30)
def cargar_alertas():
    db = InventarioDatabase(DB_PATH)
    columnas, datos = db.get_stock_alerts()
    db.close()
    if datos:
        return pd.DataFrame(datos, columns=columnas)
    return pd.DataFrame()


st.title("📦 Control de Stock")

# Botón para refrescar datos
if st.button("🔄 Actualizar datos", type="secondary"):
    st.cache_data.clear()
    st.rerun()

df_stock = cargar_stock()
df_alertas = cargar_alertas()

if df_stock.empty:
    st.warning("No hay datos de stock en la base de datos.")
    st.stop()

# ══════════════════════════════════════════════
# MÉTRICAS GENERALES
# ══════════════════════════════════════════════
st.markdown("---")

n_sin_stock = len(df_alertas[df_alertas["ALERTA"] == "SIN STOCK"]) if not df_alertas.empty else 0
n_critico = len(df_alertas[df_alertas["ALERTA"] == "STOCK CRITICO"]) if not df_alertas.empty else 0
n_reordenar = len(df_alertas[df_alertas["ALERTA"] == "PROXIMO A REORDENAR"]) if not df_alertas.empty else 0
n_sobrestock = len(df_alertas[df_alertas["ALERTA"] == "SOBRE STOCK"]) if not df_alertas.empty else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Materiales", len(df_stock))
col2.metric("🔴 Sin Stock", n_sin_stock)
col3.metric("🟠 Stock Crítico", n_critico)
col4.metric("🟡 Próx. Reorden", n_reordenar)
col5.metric("🔵 Sobre Stock", n_sobrestock)

# ══════════════════════════════════════════════
# ALERTAS
# ══════════════════════════════════════════════
st.markdown("---")
st.subheader("⚠️ Alertas de Inventario")

if df_alertas.empty:
    st.success("✅ No hay alertas activas. Todos los materiales están dentro de los niveles normales.")
else:
    tab_sin, tab_crit, tab_reord, tab_sobre = st.tabs([
        f"🔴 Sin Stock ({n_sin_stock})",
        f"🟠 Stock Crítico ({n_critico})",
        f"🟡 Próximo a Reordenar ({n_reordenar})",
        f"🔵 Sobre Stock ({n_sobrestock})"
    ])

    cols_mostrar = ["CODIGO SAP", "CLASIFICACION", "DESCRIPCION DEL MATERIAL", 
                    "UM", "STOCK ACTUAL", "PUNTO DE REORDENAMIENTO"]

    with tab_sin:
        df_sin = df_alertas[df_alertas["ALERTA"] == "SIN STOCK"]
        if df_sin.empty:
            st.info("No hay materiales sin stock.")
        else:
            st.error(f"**{n_sin_stock} materiales sin stock disponible.** Requieren reposición inmediata.")
            st.dataframe(df_sin[cols_mostrar], width='stretch', hide_index=True)

    with tab_crit:
        df_crit = df_alertas[df_alertas["ALERTA"] == "STOCK CRITICO"]
        if df_crit.empty:
            st.info("No hay materiales en stock crítico.")
        else:
            st.warning(f"**{n_critico} materiales en nivel crítico** (por debajo del 50% del punto de reordenamiento).")
            st.dataframe(df_crit[cols_mostrar], width='stretch', hide_index=True)

    with tab_reord:
        df_reord = df_alertas[df_alertas["ALERTA"] == "PROXIMO A REORDENAR"]
        if df_reord.empty:
            st.info("No hay materiales próximos a reordenar.")
        else:
            st.warning(f"**{n_reordenar} materiales** están alcanzando su punto de reordenamiento.")
            st.dataframe(df_reord[cols_mostrar], width='stretch', hide_index=True)

    with tab_sobre:
        df_sobre = df_alertas[df_alertas["ALERTA"] == "SOBRE STOCK"]
        if df_sobre.empty:
            st.info("No hay materiales con sobre stock.")
        else:
            st.info(f"**{n_sobrestock} materiales** superan 3x su punto de reordenamiento.")
            st.dataframe(df_sobre[cols_mostrar], width='stretch', hide_index=True)

# ══════════════════════════════════════════════
# TABLA GENERAL DE STOCK
# ══════════════════════════════════════════════
st.markdown("---")
st.subheader("📋 Inventario General de Stock")

# Filtros
with st.expander("🔍 Filtros", expanded=True):
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        clasificaciones = ["Todas"] + sorted(df_stock["CLASIFICACION"].unique().tolist())
        filtro_clasif = st.selectbox("Clasificación:", clasificaciones, key="filtro_clasif")

    with col_f2:
        filtro_stock = st.selectbox("Estado de stock:", [
            "Todos", "Sin stock", "Stock crítico", "Próximo a reordenar", "Sobre stock", "Normal"
        ], key="filtro_estado")

    with col_f3:
        buscar = st.text_input("Buscar por código o descripción:", key="buscar_stock")

# Aplicar filtros
df_filtrado = df_stock.copy()

if filtro_clasif != "Todas":
    df_filtrado = df_filtrado[df_filtrado["CLASIFICACION"] == filtro_clasif]

if buscar:
    mask = (
        df_filtrado["CODIGO SAP"].astype(str).str.contains(buscar, case=False, na=False) |
        df_filtrado["DESCRIPCION DEL MATERIAL"].str.contains(buscar, case=False, na=False)
    )
    df_filtrado = df_filtrado[mask]

if filtro_stock != "Todos":
    if filtro_stock == "Sin stock":
        df_filtrado = df_filtrado[df_filtrado["STOCK ACTUAL"] == 0]
    elif filtro_stock == "Stock crítico":
        df_filtrado = df_filtrado[
            (df_filtrado["PUNTO DE REORDENAMIENTO"] > 0) &
            (df_filtrado["STOCK ACTUAL"] > 0) &
            (df_filtrado["STOCK ACTUAL"] <= df_filtrado["PUNTO DE REORDENAMIENTO"] * 0.5)
        ]
    elif filtro_stock == "Próximo a reordenar":
        df_filtrado = df_filtrado[
            (df_filtrado["PUNTO DE REORDENAMIENTO"] > 0) &
            (df_filtrado["STOCK ACTUAL"] > df_filtrado["PUNTO DE REORDENAMIENTO"] * 0.5) &
            (df_filtrado["STOCK ACTUAL"] <= df_filtrado["PUNTO DE REORDENAMIENTO"])
        ]
    elif filtro_stock == "Sobre stock":
        df_filtrado = df_filtrado[
            (df_filtrado["PUNTO DE REORDENAMIENTO"] > 0) &
            (df_filtrado["STOCK ACTUAL"] > df_filtrado["PUNTO DE REORDENAMIENTO"] * 3)
        ]
    elif filtro_stock == "Normal":
        df_filtrado = df_filtrado[
            (df_filtrado["STOCK ACTUAL"] > 0) &
            (
                (df_filtrado["PUNTO DE REORDENAMIENTO"] == 0) |
                (
                    (df_filtrado["STOCK ACTUAL"] > df_filtrado["PUNTO DE REORDENAMIENTO"]) &
                    (df_filtrado["STOCK ACTUAL"] <= df_filtrado["PUNTO DE REORDENAMIENTO"] * 3)
                )
            )
        ]

st.caption(f"Mostrando **{len(df_filtrado)}** de **{len(df_stock)}** materiales")
st.dataframe(df_filtrado, width='stretch', hide_index=True)

# ══════════════════════════════════════════════
# ELIMINAR REGISTRO DE STOCK
# ══════════════════════════════════════════════
st.markdown("---")
st.subheader("🗑️ Eliminar registro de Stock")

with st.expander("Eliminar un material del stock", expanded=False):
    st.warning("⚠️ Esta acción es irreversible. El registro será eliminado permanentemente de la base de datos.")

    opciones_eliminar = [f"{row['CODIGO SAP']} - {row['DESCRIPCION DEL MATERIAL']}" 
                         for _, row in df_stock.iterrows()]
    
    seleccion_eliminar = st.selectbox(
        "Seleccione el material a eliminar:",
        options=["Seleccione un material..."] + opciones_eliminar,
        key="select_eliminar"
    )

    if seleccion_eliminar != "Seleccione un material...":
        codigo_eliminar = seleccion_eliminar.split(" - ")[0]
        
        # Mostrar datos del material seleccionado
        material_info = df_stock[df_stock["CODIGO SAP"] == codigo_eliminar].iloc[0]
        
        st.markdown("**Datos del material a eliminar:**")
        col1, col2 = st.columns(2)
        with col1:
            st.text(f"Código SAP: {material_info['CODIGO SAP']}")
            st.text(f"Descripción: {material_info['DESCRIPCION DEL MATERIAL']}")
            st.text(f"Clasificación: {material_info['CLASIFICACION']}")
        with col2:
            st.text(f"Stock Actual: {material_info['STOCK ACTUAL']}")
            st.text(f"Pto. Reorden: {material_info['PUNTO DE REORDENAMIENTO']}")
            st.text(f"UM: {material_info['UM']}")

        confirmar = st.checkbox("Confirmo que deseo eliminar este registro", key="confirmar_eliminar")
        
        if st.button("🗑️ Eliminar registro", type="primary", disabled=not confirmar):
            try:
                db = InventarioDatabase(DB_PATH)
                resultado = db.delete_stock(codigo_eliminar)
                db.close()

                if resultado:
                    st.success(f"✅ Material {codigo_eliminar} eliminado correctamente.")
                    st.cache_data.clear()
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("No se pudo eliminar el registro.")
            except Exception as e:
                st.error(f"Error: {e}")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📋 Ir a Insumos", width='stretch', type="secondary"):
        st.switch_page("pages/1_insumos.py")
with col2:
    if st.button("📈 Ir a Ingresos", width='stretch', type="secondary"):
        st.switch_page("pages/ingresos.py")
with col3:
    if st.button("📉 Ir a Salidas", width='stretch', type="secondary"):
        st.switch_page("pages/salidas.py")