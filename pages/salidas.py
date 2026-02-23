import streamlit as st
import pandas as pd
import sys
import json
from datetime import datetime, datetime
import time

sys.path.append('..')
from src.database import InventarioDatabase


# Cargar metadata
@st.cache_data
def cargar_metadata():
    try:
        with open('metadata/salidas.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error al cargar metadata: {e}")
        return {"categorias": {}, }

metadata = cargar_metadata()
# print(metadata)
categorias = metadata.get("categorias", {})
uso = categorias.get("uso", [])
entregado_a = categorias.get("entregado_a", [])
ubicacion_retiro = categorias.get("ubicacion_retiro", [])

st.title(" Registro de Salida")  

# Verificar si hay materiales pre-seleccionados en el carrito
materiales_carrito = st.session_state.get('materiales_seleccionados', [])

tab_registrar, tab_eliminar = st.tabs(["Registrar retiro", "Ver/Eliminar retiro"])

with tab_eliminar:
      # ══════════════════════════════════════════════
    # VER/ELIMINAR REGISTRO DE SALIDA
    # ══════════════════════════════════════════════
    st.subheader(" Ver/Eliminar registro de Salida")

    with st.container(border=True, width="stretch"):
        try:
            db_consulta = InventarioDatabase(r'src\db\inventario_lp02.db')
            columnas_sal, datos_salida = db_consulta.get_all_salidas()
            db_consulta.close()

            if datos_salida:
                df_salida = pd.DataFrame(datos_salida, columns=columnas_sal)
                
                st.info("Haz clic en una fila para seleccionar el registro a eliminar.")

                evento = st.dataframe(
                    df_salida,
                    width="stretch",
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    key="tabla_eliminar_salida"
                )

                if evento.selection.rows:
                    registro = df_salida.iloc[evento.selection.rows[0]]
                    st.warning(f"⚠️ Vas a eliminar: **ID {int(registro['ID'])}** — {registro.get('CODIGO SAP', '')} — {registro.get('DESCRIPCION DEL MATERIAL', '')} — Cant: {registro.get('CANTIDAD', '')}")

                    confirmar = st.checkbox("Confirmo que deseo eliminar este registro", key="confirmar_del_salida")
                    if st.button("🗑️ Eliminar", type="primary", disabled=not confirmar, key="btn_del_salida"):
                        db_del = InventarioDatabase(r'src\db\inventario_lp02.db')
                        codigo_sap_salida = registro.get('CODIGO SAP')
                        cantidad_salida = registro.get('CANTIDAD', 0)
                        resultado = db_del.delete_salida(int(registro['ID']))
                        if resultado:                            # Si se eliminó la salida, actualizar el stock sumando la cantidad eliminada
                            db_del.revert_stock_salida(codigo_sap_salida, cantidad_salida)
                        db_del.close()
                        if resultado:
                            st.success("✅ Eliminado y stock actualizado.")
                            st.cache_data.clear()
                            time.sleep(3)
                            st.rerun()
                        else:
                            st.error("No se pudo eliminar el registro.")
            else:
                st.info("No hay registros de salida.")
        except Exception as e:
            st.error(f"Error: {e}")

with tab_registrar:

    if not materiales_carrito:
        st.warning("⚠️ No hay materiales seleccionados para retirar.")
        st.info("Por favor, seleccione materiales desde el catálogo de insumos.")
        
        if st.button("📋 Ir al Catálogo de Insumos", type="primary"):
            st.switch_page("pages/1_insumos.py")
        
        st.stop()

    # Mostrar resumen de materiales seleccionados
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.success(f"**{len(materiales_carrito)} materiales seleccionados para retiro:**")
            st.caption("Los códigos SAP, descripciones y cantidades se mostrarán aquí.")

        with col2:
            if st.button("Cambiar selección de materiales", type="secondary"):
                st.switch_page("pages/1_insumos.py")

    st.markdown("----")

    # Tabs individual
    tab_individual, = st.tabs(["Salida"])

    with tab_individual:
        st.subheader("Registrar salida individual")

        # Selector de material del carrito
        opciones_materiales = [f"{mat['codigo_sap']} - {mat['descripcion']}" for mat in materiales_carrito]

        material_idx = st.selectbox("Selecciona el material a retirar:",
                                    options=range(len(opciones_materiales)),
                                    format_func=lambda x: opciones_materiales[x],
                                    key="select_material",
                                    index=0
                                    )
        
        material_actual = materiales_carrito[material_idx]

        # Mostrar información del amterial (solo lectura)

        with st.container(border=True):
            st.markdown("##### Información del material")
            col1, col2 = st.columns(2)

            with col1:
                st.text_input(
                    "Código SAP:", 
                    value=material_actual['codigo_sap'], 
                    disabled=True
                    )
                st.text_input(
                    "Categoría:", 
                    value=material_actual['clasificacion'], 
                    disabled=True)

            with col2:
                st.text_input(
                    "Descripción:", 
                    value=material_actual['descripcion'], 
                    disabled=True
                    )
                st.text_input(
                    "Unidad de medida:", 
                    value=material_actual['um'], 
                    disabled=True
                    )

        # Formulario de retiro
        with st.container(border=True):
            st.markdown("##### Datos del retiro")
            col1, col2= st.columns(2)

            with col1:
                cantidad = st.number_input(
                    "Cantidad a retirar:",
                    min_value=0.0,
                    step=1.0,
                    key="cantidad_individual"
                    )
            
            with col2:
                fecha_salida = st.date_input(
                    "Fecha de retiro:",
                    value=datetime.today(),
                    key="fecha"
                    )
            st.markdown("----")
            st.markdown("##### Información adicional (opcional)")

            col1, col2 = st.columns(2)

            with col1:
                # GUIA DE SALIDA
                guias_lista = ["Selecciona la guía de retiro"] + ["Agregar nueva guía de retiro"]
                guia_seleccionada = st.selectbox(
                    "N° de Guía de Retiro",
                    options=guias_lista
            )
                if guia_seleccionada == "Agregar nueva guía de retiro":
                    guia_salida = st.text_input(
                    "Ingrese el N° de Guía de Retiro",
                    placeholder="Ingrese el nuevo N° de Guía de Retiro"
                )
                elif guia_seleccionada == "Selecciona la guía de retiro":
                    guia_salida = None
                else:
                    guia_salida = guia_seleccionada

                # ENTREGADO A
                responsable_lista = ["Selecciona a quién se entregó"] + entregado_a + ["Agregar nuevo responsable"]
                responsable_seleccionado = st.selectbox(
                    "Entregado a",
                    options=responsable_lista,
                )
                if responsable_seleccionado == "Agregar nuevo responsable":
                    entregado_a = st.text_input(
                    "Ingrese el nombre de la persona que recibió el material",
                    placeholder="Ingrese el nuevo responsable"
                )
                elif responsable_seleccionado == "Selecciona a quién se entregó":
                    entregado_a = None
                else:
                    entregado_a = responsable_seleccionado

            with col2:
                uso_lista = ["Selecciona el uso: Operación / Proyecto"] + uso + ["Agregar nuevo uso: Operación / Proyecto"]
                uso_seleccionado = st.selectbox(
                    "Uso: Operación / Proyecto",
                    options=uso_lista
                )
                if uso_seleccionado == "Agregar nuevo uso: Operación / Proyecto":
                    uso = st.text_input(
                    "Ingrese el Uso: Operación / Proyecto",
                    placeholder="Ingrese el nuevo uso: Operación / Proyecto"
                )
                elif uso_seleccionado == "Selecciona el uso: Operación / Proyecto":
                    uso = None
                else:
                    uso = uso_seleccionado

                ubicacion_lista = ["Selecciona la ubicación de retiro"] + ubicacion_retiro + ["Agregar nueva ubicación de retiro"]
                ubicacion_seleccionada = st.selectbox(
                    "Ubicación de retiro",
                    options=ubicacion_lista
                )
                if ubicacion_seleccionada == "Agregar nueva ubicación de retiro":
                    ubicacion_retiro = st.text_input(
                    "Ingrese la nueva ubicación de retiro",
                    placeholder="Ingrese la nueva ubicación de retiro"
                )
                elif ubicacion_seleccionada == "Selecciona la ubicación de retiro":
                    ubicacion_retiro = None
                else:
                    ubicacion_retiro = ubicacion_seleccionada

            comentarios = st.text_area(
                "Comentarios",
                key="comentarios"
            )

    # BOTON DE GUARDAR
    if st.button("Registrar salida",
                type="primary",
                key="boton_registrar_salida"
                ):
        # Validaciones
        errores = []
        if cantidad <=0:
            errores.append("La cantidad a retirar debe ser mayor a cero.")
        if errores:
            for error in errores:
                st.error(error)
        else:
            try:
                db = InventarioDatabase(r'src\db\inventario_lp02.db')

                stock_actualizado, stock_actual = db.update_stock_on_salida(material_actual['codigo_sap'], cantidad)

                if not stock_actualizado:
                    if stock_actual is None:
                        st.error(f"El material {material_actual['codigo_sap']} no se encuentra en stock. La salida no se registró.")
                    else:
                        st.error(f"Stock insuficiente. Stock actual: **{stock_actual}** - Cantidad solicitada: **{cantidad}**")
                    db.close()
                
                else:

                    resultado = db.insert_salida(
                        codigo_sap=material_actual['codigo_sap'],
                        descripcion=material_actual['descripcion'],
                        clasificacion=material_actual['clasificacion'],
                        um=material_actual['um'],
                        cantidad=cantidad,
                        fecha_salida=fecha_salida.strftime("%Y-%m-%d"),
                        guia_salida=guia_salida if guia_salida else None,
                        uso=uso if uso else None,
                        entregado_a=entregado_a if entregado_a else None,
                        ubicacion=ubicacion_retiro if ubicacion_retiro else None,
                        comentarios=comentarios if comentarios else None
                    )

                    db.close()

                    if resultado:
                        st.success(f"Salida registrada exitosamente para {material_actual['codigo_sap']}.")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Error al registrar la salida. Por favor, intente nuevamente.")
            except Exception as e:
                st.error(f"Error: {e}")

    # Footer con navegación
    st.markdown("----")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Ver Stock", width="stretch", type="secondary"):
            st.switch_page("pages/stock.py")

