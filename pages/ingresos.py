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
        with open('metadata/metadata_ingresos.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error al cargar metadata: {e}")
        return {"categorias": {}, }

metadata = cargar_metadata()
# print(metadata)
categorias = metadata.get("categorias", {})
# print(categorias)
n_reservas = categorias.get("reservas", [])
guia_despacho = categorias.get("guias_despacho", [])
ordenes_compra = categorias.get("ordenes_compra", [])
uso= categorias.get("uso", [])
recibido_por = categorias.get("recibido_por", [])
empresa = categorias.get("empresas", [])
print(f"-------------- KEYS DE CATEGORIAS {categorias.keys()}-----------------")

st.title("Registro de Ingreso")  

# Verificar si hay materiales pre-seleccionados en el carrito
materiales_carrito = st.session_state.get('materiales_seleccionados', [])

tab_registrar, tab_eliminar = st.tabs(["Registrar ingreso", "Ver/Eliminar ingreso"])

with tab_eliminar:
      # ══════════════════════════════════════════════
    # ELIMINAR REGISTRO DE INGRESO
    # ══════════════════════════════════════════════
    st.subheader(" Ver/Eliminar registro de Ingreso")

    with st.container(border=True, width="stretch"):
        try:
            db_consulta = InventarioDatabase(r'src\db\inventario_lp02.db')
            columnas_ing, datos_ingreso = db_consulta.get_all_ingresos()
            db_consulta.close()

            if datos_ingreso:
                df_ingreso = pd.DataFrame(datos_ingreso, columns=columnas_ing)

                # ── Filtros ──
                with st.expander("🔍 Filtros", expanded=True):
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        fecha_min = st.date_input(
                            "Desde:", 
                            value=None,
                            key="ing_fecha_min"
                        )
                    with col_f2:
                        fecha_max = st.date_input(
                            "Hasta:", 
                            value=None,
                            key="ing_fecha_max"
                        )
                    
                    col_f3, col_f4 = st.columns(2)
                    with col_f3:
                        clasificaciones_ing = ["Todas"] + sorted(df_ingreso["CLASIFICACION"].dropna().unique().tolist())
                        filtro_clasif_ing = st.selectbox("Clasificación:", clasificaciones_ing, key="ing_filtro_clasif")

                # ── Aplicar filtros ──
                df_ing_filtrado = df_ingreso.copy()
                
                if 'FECHA DE INGRESO' in df_ing_filtrado.columns:
                    df_ing_filtrado['_fecha_dt'] = pd.to_datetime(df_ing_filtrado['FECHA DE INGRESO'], errors='coerce')
                    if fecha_min:
                        df_ing_filtrado = df_ing_filtrado[df_ing_filtrado['_fecha_dt'] >= pd.to_datetime(fecha_min)]
                    if fecha_max:
                        df_ing_filtrado = df_ing_filtrado[df_ing_filtrado['_fecha_dt'] <= pd.to_datetime(fecha_max)]
                    df_ing_filtrado = df_ing_filtrado.drop(columns=['_fecha_dt'])

                if filtro_clasif_ing != "Todas":
                    df_ing_filtrado = df_ing_filtrado[df_ing_filtrado["CLASIFICACION"] == filtro_clasif_ing]
                
                st.info("Haz clic en una fila para seleccionar el registro a eliminar.")

                evento = st.dataframe(
                    df_ing_filtrado,
                    width="stretch",
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    key="tabla_eliminar_ingreso"
                )

                if evento.selection.rows:
                    registro = df_ing_filtrado.iloc[evento.selection.rows[0]]
                    st.warning(f"⚠️ Vas a eliminar: **ID {int(registro['ID'])}** — {registro.get('CODIGO SAP', '')} — {registro.get('DESCRIPCION DEL MATERIAL', '')} — Cant: {registro.get('CANTIDAD', '')}")

                    confirmar = st.checkbox("Confirmo que deseo eliminar este registro", key="confirmar_del_ing_sin")
                    if st.button("🗑️ Eliminar", type="primary", disabled=not confirmar, key="btn_del_ing_sin"):
                        db_del = InventarioDatabase(r'src\db\inventario_lp02.db')
                        codigo_sap_ingreso = str(registro.get('CODIGO SAP', None))
                        cantidad_ingreso = float(registro.get('CANTIDAD', 0))
                        resultado = db_del.delete_ingreso(int(registro['ID']))
                        stock_revertido = False
                        if resultado:
                            stock_revertido = db_del.revert_stock_ingreso(codigo_sap_ingreso, cantidad_ingreso)
                        db_del.close()
                        if resultado and stock_revertido:
                            st.success("✅ Eliminado y stock actualizado.")
                            st.cache_data.clear()
                            time.sleep(1.5)
                            st.rerun()

                        elif resultado and not stock_revertido:
                            st.warning("Registro eliminado pero no se pudo revertir el stock.")
                            st.cache_data.clear()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("No se pudo eliminar.")
            else:
                st.info("No hay registros de ingreso.")
        except Exception as e:
            st.error(f"Error: {e}")


with tab_registrar:
    if not materiales_carrito:
        st.warning("⚠️ No hay materiales seleccionados para ingresar.")
        st.info("Por favor, seleccione materiales desde el catálogo de insumos.")
        
        if st.button("📋 Ir al Catálogo de Insumos", type="primary"):
            st.switch_page("pages/1_insumos.py")
        
        st.stop()

    # Mostrar resumen de materiales seleccionados
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.success(f"**{len(materiales_carrito)} materiales seleccionados para ingreso:**")
            st.caption("Los códigos SAP, descripciones y cantidades se mostrarán aquí.")

        with col2:
            if st.button("Cambiar selección de materiales", type="secondary"):
                st.switch_page("pages/1_insumos.py")

    st.markdown("----")

    # Tabs individual o masivo
    tab_individual,  = st.tabs(["Ingreso Individual"])

    with tab_individual:
        st.subheader("Registrar ingreso")

        # Selector de material del carrito
        opciones_materiales = [f"{mat['codigo_sap']} - {mat['descripcion']}" for mat in materiales_carrito]

        material_idx = st.selectbox("Selecciona el material a ingresar:",
                                    options=range(len(opciones_materiales)),
                                    format_func=lambda x: opciones_materiales[x],
                                    key="select_material_individual",
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

        # Formulario de ingreso
        with st.container(border=True):
            st.markdown("##### Datos del ingreso")
            col1, col2, col3= st.columns(3)

            with col1:
                cantidad = st.number_input(
                    "Cantidad a ingresar:",
                    min_value=0.0,
                    step=1.0,
                    key="cantidad_individual"
                    )
            
            with col2:
                fecha_ingreso = st.date_input(
                    "Fecha de ingreso:",
                    value=datetime.today(),
                    key="fecha"
                    )
                
            with col3:
                precio_unitario = st.number_input(
                    "Precio unitario (CLP):",
                    min_value=0.0,
                    step=0.01,
                    format="%0.2f",
                    key="precio_individual"
                    )
                
            st.markdown("----")
            st.markdown("##### Información adicional (opcional)")

            col1, col2 = st.columns(2)

            with col1:
                # RESERVA
                reservas_lista = ["Selecciona un n° de reserva"] + n_reservas + ["Agregar nuevo n° de reserva"]
                reserva_seleccionada = st.selectbox(
                    "N° de Reserva",
                    options=reservas_lista,
                )
                if reserva_seleccionada == "Agregar nuevo n° de reserva":
                    reserva = st.text_input(
                    "Ingrese el N° de Reserva",
                    placeholder="Ingrese el nuevo N° de Reserva",
                    )
                elif reserva_seleccionada == "Selecciona un n° de reserva":
                    reserva = None
                else:
                    reserva = reserva_seleccionada

                # GUIA DESPACHO
                guias_lista = ["Selecciona la guía de despacho"] + guia_despacho + ["Agregar nueva guía de despacho"]
                guia_seleccionada = st.selectbox(
                    "N° de Guía de Despacho",
                    options=guias_lista
            )
                if guia_seleccionada == "Agregar nueva guía de despacho":
                    guia_despacho = st.text_input(
                    "Ingrese el N° de Guía de Despacho",
                    placeholder="Ingrese el nuevo N° de Guía de Despacho"
                )
                elif guia_seleccionada == "Selecciona la guía de despacho":
                    guia_despacho = None
                else:
                    guia_despacho = guia_seleccionada

                # ORDEN DE COMPRA
                oc_lista = ["Selecciona la orden de compra"] + ordenes_compra + ["Agregar nueva orden de compra"]
                oc_seleccionada = st.selectbox(
                    "N° de Orden de Compra",
                    options=oc_lista,
                )
                if oc_seleccionada == "Agregar nueva orden de compra":
                    oc = st.text_input(
                    "Ingrese el N° de Orden de Compra",
                    placeholder="Ingrese la nueva orden de compra"
                )
                elif oc_seleccionada == "Selecciona la orden de compra":
                    oc = None
                else:
                    oc = oc_seleccionada

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

                # RECIBIDO POR
                responsable_lista = ["Selecciona quién recibió"] + recibido_por + ["Agregar nuevo responsable"]
                responsable_seleccionado = st.selectbox(
                    "Recibido por",
                    options=responsable_lista,
                )
                if responsable_seleccionado == "Agregar nuevo responsable":
                    recibido_por = st.text_input(
                    "Ingrese el nombre de la persona que recibió",
                    placeholder="Ingrese el nuevo responsable"
                )
                elif responsable_seleccionado == "Selecciona quién recibió":
                    recibido_por = None
                else:
                    recibido_por = responsable_seleccionado

                # EMPRESA
                empresa_lista = ["Selecciona la empresa"] + empresa + ["Agregar nueva empresa"]
                empresa_seleccionada = st.selectbox(
                    "Empresa",
                    options=empresa_lista,
                )
                if empresa_seleccionada == "Agregar nueva empresa":
                    empresa = st.text_input(
                    "Ingrese el nombre de la empresa",
                    placeholder="Ingrese el nombre de la empresa"
                )
                elif empresa_seleccionada == "Selecciona la empresa":
                    empresa = None
                else:
                    empresa = empresa_seleccionada

            observaciones = st.text_area(
                "Observaciones",
                key="observaciones"
            )

            
    st.markdown("----")
    st.subheader("Vista previa del ingreso a registrar")

    datos_ingreso = {
        "Código SAP": material_actual['codigo_sap'],
        "Descripción": material_actual['descripcion'],
        "Categoría": material_actual['clasificacion'],
        "Unidad de medida": material_actual['um'],
        "Cantidad a ingresar": cantidad,
        "Fecha de ingreso": fecha_ingreso.strftime("%Y-%m-%d"),
        "Precio unitario (CLP)": f"{precio_unitario:,.2f}" if precio_unitario else "No especificado",
        "N° de Reserva": reserva if reserva else "No especificado",
        "N° de Guía de Despacho": guia_despacho if guia_despacho else "No especificado",
        "N° de Orden de Compra": oc if oc else "No especificado",
        "Uso: Operación / Proyecto": uso if uso else "No especificado",
        "Recibido por": recibido_por if recibido_por else "No especificado",
        "Empresa": empresa if empresa else "No especificado",
        "Observaciones": observaciones if observaciones else "No especificado"
    }


    df_preview = pd.DataFrame.from_dict(datos_ingreso, orient='index', columns=['Valor'])
    df_preview.index.name = 'Campo'
    st.dataframe(df_preview, width="stretch")

    # BOTON DE GUARDAR
    if st.button("Registrar ingreso",
                type="primary",
                key="boton_registrar_ingreso"
                ):
        # Validaciones
        errores = []
        if cantidad <=0:
            errores.append("La cantidad a ingresar debe ser mayor a cero.")
        if precio_unitario <=0:
            errores.append("El precio unitario debe ser mayor a cero.")
        if errores:
            for error in errores:
                st.error(error)
        else:
            try:
                db = InventarioDatabase(r'src\db\inventario_lp02.db')

                resultado = db.insert_ingreso(
                    codigo_sap=material_actual['codigo_sap'],
                    descripcion=material_actual['descripcion'],
                    clasificacion=material_actual['clasificacion'],
                    um=material_actual['um'],
                    cantidad=cantidad,
                    fecha_ingreso=fecha_ingreso.strftime("%Y-%m-%d"),
                    precio_unitario=precio_unitario,
                    reserva=reserva if reserva else None,
                    guia_despacho=guia_despacho if guia_despacho else None,
                    oc=oc if oc else None,
                    uso=uso if uso else None,
                    recibido_por=recibido_por if recibido_por else None,
                    empresa=empresa if empresa else None,
                    observaciones=observaciones if observaciones else None
                )

                if resultado:
                    stock_actualizado = db.update_stock_on_ingreso(
                        material_actual['codigo_sap'], 
                        cantidad,
                        clasificacion=material_actual['clasificacion'],
                        descripcion=material_actual['descripcion'],
                        um=material_actual['um']
                    )
                    db.close()
                    st.success(f"Ingreso registrado exitosamente para {material_actual['codigo_sap']}.")
                    if stock_actualizado:
                        st.info(f"Stock actualizado: {material_actual['codigo_sap']} + {cantidad}")
                    else:
                        st.warning(f"No se pudo actualizar el stock para {material_actual['codigo_sap']}.")
                    st.cache_data.clear()
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    db.close()
                    st.error("Error al registrar el ingreso. Por favor, intente nuevamente.")
            except Exception as e:
                st.error(f"Error: {e}")

    # Footer con navegación
    st.markdown("----")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Ver Stock", width="stretch", type="secondary"):
            st.switch_page("pages/stock.py")
