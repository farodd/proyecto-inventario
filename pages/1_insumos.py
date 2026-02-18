import streamlit as st
import pandas as pd
import sys
import json
import time

sys.path.append('..')
from src.database import InventarioDatabase



# Cargar metadata de insumos al inicio
@st.cache_data
def cargar_metadata():
    """ Cargar metadata de insumos desde la base de datos """
    try:
        with open('metadata/metadata_insumos.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error al cargar metadata:{e}")
        return {"categorias": {}, "unidades_medida": {}}
    
def verificar_insumos_pendientes():
    """Verifica si hay insumos pendientes de catalogar"""
    
    # ✅ Solo ejecutar si no está en session_state
    if 'insumos_pendientes' not in st.session_state:
        try:
            db = InventarioDatabase('src/db/inventario_lp02.db')
            cursor = db.cursor
            
            cursor.execute("""
                SELECT COUNT(*) FROM insumos 
                WHERE [CODIGO SAP] LIKE 'POR_CATALOGAR%' 
            """)
            
            pendientes = cursor.fetchone()[0]
            db.close()
            
            # ✅ Guardar en session_state
            st.session_state['insumos_pendientes'] = pendientes
            
        except Exception:
            st.session_state['insumos_pendientes'] = 0
    
    # ✅ Devolver valor guardado
    return st.session_state['insumos_pendientes']
    
# Cargar metadata
metadata = cargar_metadata()

st.title("📋 Gestión de Insumos")

pendientes = verificar_insumos_pendientes()
if pendientes > 0:
    st.warning(f"""⚠️ Hay {pendientes} insumos pendientes de catalogar. Por favor, complete su información.
               Presentan el codigo asociado 'POR_CATALOGAR_XXX'.""")

# Tabs para diferentes funciones
tab1, tab2, tab3 = st.tabs(["👁️ Ver Insumos", "➕ Agregar Insumo", "✏️ Editar Insumos"])

with tab1:
    st.subheader("👁️ Catálogo de Insumos")
    
    # Filtros de búsqueda
    col1, col2 = st.columns(2)
    
    with col1:
        buscar_codigo = st.text_input("🔍 Buscar por código SAP:", placeholder="Ej: MAT001")
    
    with col2:
        # Utilizar clasificaciones desde metadata si esta disponible
        clasificaciones = ["Todas las clasificaciones"] + list(metadata.get("categorias", {}).keys())
        filtro_clasificacion = st.selectbox(
            "📂 Filtrar por clasificación:",
            clasificaciones
        )
    
    # Mostrar tabla de insumos
    try:
        db = InventarioDatabase('src/db/inventario_lp02.db')
        cursor = db.cursor
        
        # Construir consulta con filtros
        query = "SELECT [CODIGO SAP], [DESCRIPCION DEL MATERIAL], [CLASIFICACION], [UM], [OBSERVACIONES] FROM insumos"
        params = []
        
        conditions = []
        if buscar_codigo:
            conditions.append("[CODIGO SAP] LIKE ?")
            params.append(f"%{buscar_codigo}%")
        
        if filtro_clasificacion != "Todas las clasificaciones":
            conditions.append("[CLASIFICACION] = ?")
            params.append(filtro_clasificacion)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY [CODIGO SAP]"
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        
        if resultados:
            df = pd.DataFrame(resultados, columns=[
                'Código SAP', 'Descripción', 'Clasificación', 'UM', 'Observaciones'
            ])

            # Generar key única para forzar reset de selección cuando sea necesario
            tabla_key = f"tabla_insumos_{st.session_state.get('tabla_reset_counter', 0)}"

            event = st.dataframe(
            df,
            height=400,
            selection_mode="multi-row",
            on_select="rerun",
            key=tabla_key,
            column_config={
                "Código SAP": st.column_config.TextColumn("Código SAP", width=75),
                "Descripción": st.column_config.TextColumn("Descripción", width=165),
                "Clasificación": st.column_config.TextColumn("Clasificación", width=165),
                "UM": st.column_config.TextColumn("UM", width=65),
                "Observaciones": st.column_config.TextColumn("Observaciones", width="medium")
            }
            )
            
            st.info(f"📊 Se encontraron {len(df)} insumos")
                
            st.markdown("---")

            # Boton para seleccionar fila
            if event.selection.rows and not st.session_state.get('materiales_guardados', False):
                filas_seleccionadas = event.selection.rows

                # Header de la sección
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.markdown(f"### Materiales seleccionados ({len(filas_seleccionadas)})")
                with col2:
                    if st.button("**Usar selección**", type="primary"):

                        materiales_seleccionados = st.session_state.get('materiales_seleccionados', [])
                        codigos_existentes = {m['codigo_sap'] for m in materiales_seleccionados}
                        for fila in filas_seleccionadas:
                            material_fila = df.iloc[fila]
                            codigo_sap = material_fila['Código SAP']

                            # Evitar duplicados
                            if codigo_sap not in codigos_existentes:
                                materiales_seleccionados.append({
                                    'codigo_sap': material_fila['Código SAP'],
                                    'descripcion': material_fila['Descripción'],
                                    'clasificacion': material_fila['Clasificación'],
                                    'um': material_fila['UM'],
                                    'observaciones': material_fila['Observaciones']
                                })
                        print(f"-------------------- MATERIALES SELECCIONADOS{materiales_seleccionados}--------------------")


                        # Verificar si ya habian materiales guardados
                        materiales_previos = 'materiales_seleccionados' in st.session_state
                        print(f"-------------------- MATERIALES SELECCIONADOS {materiales_previos}--------------------")

                        # Reemplazar ocmpletamente
                        st.session_state['materiales_seleccionados'] = materiales_seleccionados
                        st.session_state['materiales_guardados'] = True

                        # Mensaje de confirmación
                        if materiales_previos:
                            st.toast(f"➕ {len(filas_seleccionadas)} materiales agregados. Total: {len(materiales_seleccionados)}", icon="✅")
                        else:
                            st.toast(f"📦 {len(materiales_seleccionados)} Materiales agregados al carrito", icon="🛒")
                        st.rerun()

                # ✅ Mostrar materiales seleccionados en cards
                for i, fila in enumerate(filas_seleccionadas):
                    material = df.iloc[fila]
                    
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([2, 3, 1])
                        
                        with col1:
                            st.markdown(f"**{material['Código SAP']}**")
                            st.caption(f"📏 {material['UM']}")
                        
                        with col2:
                            st.markdown(f"{material['Descripción']}")
                            st.caption(f"📂 {material['Clasificación']}")
                        
                        with col3:
                            st.markdown(f"**#{i+1}**")

            elif not st.session_state.get('materiales_guardados', False):
                st.info("Seleccione una o más filas de la tabla para gestionar los materiales.")
            
        else:
            st.warning("⚠️ No se encontraron insumos con los criterios de búsqueda")
        
        db.close()
        
    except Exception as e:
        st.error(f"❌ Error al consultar insumos: {e}")

    # CARRITO DE MATERIALES SELECCIONADOS
    if st.session_state.get('materiales_guardados', False):

        # Header con información y botón de limpiar
        col1, col2, = st.columns([0.7, 0.3])

        with col1:
            materiales = st.session_state.get('materiales_seleccionados', [])
            st.markdown(f"### 📦 Materiales seleccionados para gestión ({len(materiales)})")
            st.caption("Listos para usar en ingresos o salidas")

        with col2:
            if st.button("🗑️ Limpiar selección", 
                        type="secondary", 
                        help="Borrar materiales guardados y volver a seleccionar"):
                # Incrementar contador para resetear tabla
                st.session_state['tabla_reset_counter'] = st.session_state.get('tabla_reset_counter', 0) + 1
                # Limpiar todo
                if 'materiales_seleccionados' in st.session_state:
                    del st.session_state['materiales_seleccionados']
                st.session_state['materiales_guardados'] = False
                st.toast("🗑️ Selección de materiales limpiada", icon="✅")
                st.rerun()

        with st.container(border=True):
            materiales = st.session_state.get('materiales_seleccionados', [])
            
            st.markdown("**Materiales seleccionados:**")

            # ✅ Díalogo de confirmación para eliminar
            @st.dialog(f"confirmar_eliminar")
            def confirmar_eliminacion(material,indice):
                st.write(f"¿Eliminar **{material['codigo_sap']}**?")
                st.write(f"**Descripción:** {material['descripcion']}")
                st.info("**Nota:** Al eliminar este material hara qué se deseleccionen todos los materiales de la tabla principal" \
                " Pero, los materiales restantes siguen en el carrito.")
                
                col_si, col_no = st.columns(2)
                with col_si:
                    if st.button("✅ Sí", type="primary"):
                        # Eliminar este material

                        materiales = st.session_state.get('materiales_seleccionados', [])
                        materiales_filtrados = [m for j, m in enumerate(materiales) if j != indice]
                        print(f"-------------------- MATERIALES FILTRADOS {materiales_filtrados}--------------------")
                        
                        st.session_state['materiales_seleccionados'] = materiales_filtrados

                        st.session_state['tabla_reset_counter'] = st.session_state.get('tabla_reset_counter', 0) + 1
                        
                        if len(materiales_filtrados) == 0:
                            st.session_state['tabla_reset_counter'] = st.session_state.get('tabla_reset_counter', 0) + 1
                            st.session_state['materiales_guardados'] = False
                            # Solo resetear tablla si ya no quedan materiales
                            st.toast(f"🗑️ {material['codigo_sap']} eliminado. Lista quedó vacía", icon="✅")
                        else:
                            st.toast(f"🗑️ {material['codigo_sap']} eliminado. Quedan {len(materiales_filtrados)} materiales", icon="✅")
                        time.sleep(2)
                        st.rerun()
                
                with col_no:
                    if st.button("❌ No", key=f"no_{i}", type = "secondary"):
                        st.rerun()
            
            for i, material in enumerate(materiales):
                col1, col2 = st.columns([0.85, 0.15])
                
                with col1:
                    st.write(f"**{i+1}. {material['codigo_sap']} - {material['descripcion']}**")
                    st.caption(f"📂 {material['clasificacion']} | 📏 {material['um']}")
                
                with col2:
                    # Botón que activa diálogo
                    if st.button("🗑️", type="secondary", help="Eliminar material", key=f"eliminar_{i}"):
                        confirmar_eliminacion(material, i)

        # Botones de navegación
        st.markdown ("### ¿Qué desea hacer con estos materiales?")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📥 **Ir a Ingresos**", type="primary", use_container_width=True):
                st.session_state['material_seleccionado'] = False
                st.switch_page("pages/ingresos.py")

        with col2:
            if st.button("📤 **Ir a Salidas**", type="primary", use_container_width=True):
                st.session_state['material_seleccionado'] = False
                st.switch_page("pages/salidas.py")

        with col3:
            if st.button("➕ **Agregar Más**", type="secondary", use_container_width=True):
                # Mantener los materiales pero permitir agregar más
                st.session_state['materiales_guardados'] = False
                st.info("💡 Puedes seleccionar materiales adicionales de la tabla")
                st.rerun()

with tab2:
    st.subheader("➕ Agregar Nuevo Insumo")
    st.info("**Complete el formulario para agregar un nuevo insumo al catálogo.**")
    
    codigo_sap = st.text_input("Código SAP:", 
                                placeholder="Ej: MAT001", 
                                max_chars=20, 
                                help="Código único del material en SAP"
                                )
    descripcion = st.text_area("Descripción del Material:",
                                placeholder="ingrese una descripción detallada del material", 
                                max_chars=100,
                                height=100
                                )
    
    col1, col2 = st.columns(2)

    with col1:
        categorias_lista = list(metadata.get("categorias", {}).keys())
        opciones_categoria = ["Seleccione una categoría"] + categorias_lista + ["Agregar nueva categoría"]
        clasificacion = st.selectbox(
            "Clasificación:", 
            options=opciones_categoria
        )
        nueva_categoria = None
        if clasificacion == "Agregar nueva categoría":
            nueva_categoria = st.text_input(
                "Nueva categoría: *", 
                placeholder="Ingrese el nombre de la nueva categoría"
            )
        
    with col2:
        um_lista = list(metadata.get("unidades_medida", {}).keys())
        opciones_unidades = ["Seleccione una unidad de medida"] + um_lista + ["Agregar nueva unidad de medida"]
        unidad_medida = st.selectbox(
            "Unidad de Medida (UM):",
            options=opciones_unidades
        )

        nueva_medida = None
        if unidad_medida == "Agregar nueva unidad de medida":
            nueva_medida = st.text_input(
                "Nueva Unidad de Medida: *", 
                placeholder="Ingrese la nueva unidad de medida"
            )
    observaciones = st.text_area(
        "Observaciones:", 
        max_chars=150,
        height=80
    )
    
    st.markdown("---")
    st.caption("* Campos obligatorios")

    if st.button("Guardar insumo", type="primary"):

        clasificacion_final = nueva_categoria.strip().upper() if clasificacion == "Agregar nueva categoría" else clasificacion
        um_final = nueva_medida.strip().upper() if unidad_medida == "Agregar nueva unidad de medida" else unidad_medida
        errores = []
        if not codigo_sap.strip():
            errores.append("El código SAP es obligatorio.")
        if not descripcion.strip():
            errores.append("La descripción del material es obligatoria.")
        if clasificacion == "Seleccione una categoría":
            errores.append("Debe seleccionar una categoría")
        if clasificacion == "Agregar nueva categoría" and not nueva_categoria.strip():
            errores.append("Debe ingresar el nombre de la nueva categoría.")
        if unidad_medida == "Seleccione una unidad de medida":
            errores.append("Debe seleccionar una unidad de medida.")
        if unidad_medida == "Agregar nueva unidad de medida" and not nueva_medida.strip():
            errores.append("Debe ingresar la nueva unidad de medida.")
        
        if errores:
            for error in errores:
                st.error(error)

        else:
            try:
                db = InventarioDatabase('src/db/inventario_lp02.db')
                cursor = db.cursor

                # Verificar si el código SAP ya existe
                cursor.execute("SELECT COUNT(*) FROM insumos WHERE [CODIGO SAP] = ?", (codigo_sap,))
                existe = cursor.fetchone()[0]
                if existe:
                    st.error(f"❌ El código SAP {codigo_sap} ya existe en el catálogo.")
                    db.close()

                else:
                    db.insert_insumo(
                        codigo_sap=codigo_sap,
                        descripcion=descripcion,
                        clasificacion=clasificacion_final,
                        um=um_final,
                        observaciones=observaciones
                    )
                    db.close()
                
                    msg = f"Insumo {codigo_sap} agregado correctamente al catálogo"
                    if clasificacion == "Agregar nueva categoría":
                        msg += f" y categoría '{nueva_categoria}' creada."
                    if unidad_medida == "Agregar nueva unidad de medida":
                        msg += f" y unidad de medida '{nueva_medida}' creada."
                    
                    st.success(msg)
                    time.sleep(1.5)
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Error al agregar insumo: {e}")
    
with tab3:
    st.subheader(" Editar Insumos")
    st.info("**Seleccione un insumo de la tabla para editarlo.**")
    
    # Cargar insumos
    try:
        db = InventarioDatabase('src/db/inventario_lp02.db')
        cursor = db.cursor
        
        cursor.execute("SELECT [CODIGO SAP], [DESCRIPCION DEL MATERIAL], [CLASIFICACION], [UM], [OBSERVACIONES] " \
        "FROM insumos")
        resultados = cursor.fetchall()
        db.close()
        
        if resultados:
            df_editar = pd.DataFrame(resultados, columns=[
                'Código SAP', 'Descripción', 'Clasificación', 'UM', 'Observaciones'
            ])
            
            # Tabla con selección única
            event_editar = st.dataframe(
                df_editar,
                height=300,
                selection_mode="single-row",
                on_select="rerun",
                key="tabla_editar_insumos",
                column_config={
                    "Código SAP": st.column_config.TextColumn("Código SAP", width=100),
                    "Descripción": st.column_config.TextColumn("Descripción", width=200),
                    "Clasificación": st.column_config.TextColumn("Clasificación", width=150),
                    "UM": st.column_config.TextColumn("UM", width=80),
                    "Observaciones": st.column_config.TextColumn("Observaciones", width="medium")
                }
            )
            
            # Si hay una fila seleccionada, mostrar formulario de edición
            if event_editar.selection.rows:
                fila_seleccionada = event_editar.selection.rows[0]
                insumo = df_editar.iloc[fila_seleccionada]

                codigo_key = insumo['Código SAP']
                
                st.markdown("---")
                st.markdown(f"###  Editando: **{codigo_key}**")
                
                with st.container(border=True):
                    # Código SAP (solo lectura)
                    st.text_input(
                        "Código SAP:",
                        value=insumo['Código SAP'],
                        disabled=True,
                        key=f"edit_codigo_sap_{codigo_key}"
                    )
                    
                    # Descripción editable
                    nueva_descripcion = st.text_area(
                        "Descripción del Material: *",
                        value=insumo['Descripción'] if insumo['Descripción'] else "",
                        height=100,
                        key=f"edit_descripcion_{codigo_key}"
                    )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Clasificación
                        categorias_lista_edit = list(metadata.get("categorias", {}).keys())
                        opciones_clasificacion_edit = categorias_lista_edit + ["➕ Agregar nueva categoría"]
                        
                        # Encontrar índice actual
                        try:
                            idx_clasificacion = categorias_lista_edit.index(insumo['Clasificación'])
                        except ValueError:
                            categorias_lista_edit.insert(0, insumo['Clasificación'])
                            opciones_clasificacion_edit = categorias_lista_edit + ["➕ Agregar nueva categoría"]
                            idx_clasificacion = 0
                        
                        nueva_clasificacion = st.selectbox(
                            "Clasificación: *",
                            options=opciones_clasificacion_edit,
                            index=idx_clasificacion,
                            key="edit_clasificacion"
                        )
                        
                        # Campo para nueva clasificación
                        nueva_categoria_edit = None
                        if nueva_clasificacion == "➕ Agregar nueva categoría":
                            nueva_categoria_edit = st.text_input(
                                "Nueva categoría: *",
                                placeholder="Ingrese el nombre de la nueva categoría",
                                key="edit_nueva_categoria"
                            )
                    
                    with col2:
                        # Unidad de medida
                        um_lista_edit = list(metadata.get("unidades_medida", {}).keys())
                        opciones_um_edit = um_lista_edit + ["➕ Agregar nueva unidad de medida"]
                        
                        # Encontrar índice actual
                        try:
                            idx_um = um_lista_edit.index(insumo['UM'])
                        except ValueError:
                            um_lista_edit.insert(0, insumo['UM'])
                            opciones_um_edit = um_lista_edit + ["➕ Agregar nueva unidad de medida"]
                            idx_um = 0
                        
                        nueva_um = st.selectbox(
                            "Unidad de Medida: *",
                            options=opciones_um_edit,
                            index=idx_um,
                            key="edit_um"
                        )
                        
                        # Campo para nueva UM
                        nueva_medida_edit = None
                        if nueva_um == "➕ Agregar nueva unidad de medida":
                            nueva_medida_edit = st.text_input(
                                "Nueva Unidad de Medida: *",
                                placeholder="Ingrese la nueva unidad de medida",
                                key="edit_nueva_um"
                            )
                    
                    # Observaciones
                    nuevas_observaciones = st.text_area(
                        "Observaciones:",
                        value=insumo['Observaciones'] if insumo['Observaciones'] else "",
                        height=80,
                        key="edit_observaciones"
                    )
                    
                    st.markdown("---")
                    
                    col_guardar, col_eliminar = st.columns([0.7, 0.3])
                    
                    with col_guardar:
                        if st.button("💾 Guardar cambios", type="primary", use_container_width=True, key="btn_guardar_edicion"):
                            # Validaciones
                            errores = []
                            
                            if not nueva_descripcion or not nueva_descripcion.strip():
                                errores.append("La descripción es obligatoria.")
                            
                            if nueva_clasificacion == "➕ Agregar nueva categoría":
                                if nueva_categoria_edit is None or not nueva_categoria_edit.strip():
                                    errores.append("Debe ingresar el nombre de la nueva categoría.")
                            
                            if nueva_um == "➕ Agregar nueva unidad de medida":
                                if nueva_medida_edit is None or not nueva_medida_edit.strip():
                                    errores.append("Debe ingresar la nueva unidad de medida.")
                            
                            if errores:
                                for error in errores:
                                    st.error(f"❌ {error}")
                            else:
                                # Determinar valores finales
                                if nueva_clasificacion == "➕ Agregar nueva categoría":
                                    clasificacion_final = nueva_categoria_edit.strip().upper()
                                else:
                                    clasificacion_final = nueva_clasificacion
                                
                                if nueva_um == "➕ Agregar nueva unidad de medida":
                                    um_final = nueva_medida_edit.strip().upper()
                                else:
                                    um_final = nueva_um
                                
                                try:
                                    db = InventarioDatabase('src/db/inventario_lp02.db')
                                    cursor = db.cursor
                                    
                                    cursor.execute('''
                                        UPDATE insumos 
                                        SET [DESCRIPCION DEL MATERIAL] = ?,
                                            [CLASIFICACION] = ?,
                                            [UM] = ?,
                                            [OBSERVACIONES] = ?
                                        WHERE [CODIGO SAP] = ?
                                    ''', (
                                        nueva_descripcion.strip(),
                                        clasificacion_final,
                                        um_final,
                                        nuevas_observaciones.strip() if nuevas_observaciones else None,
                                        insumo['Código SAP']
                                    ))
                                    
                                    db.connection.commit()
                                    db.close()
                                    
                                    st.success(f"✅ Insumo '{insumo['Código SAP']}' actualizado correctamente")
                                    time.sleep(1.5)
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Error al actualizar: {e}")
                    
                    with col_eliminar:
                        if st.button("🗑️ Eliminar insumo", type="secondary", use_container_width=True, key="btn_eliminar_insumo"):
                            st.session_state['confirmar_eliminar_insumo'] = insumo['Código SAP']
                            st.rerun()
                
                # Diálogo de confirmación para eliminar
                if st.session_state.get('confirmar_eliminar_insumo') == insumo['Código SAP']:
                    with st.container(border=True):
                        st.warning(f"⚠️ ¿Está seguro de eliminar el insumo **{insumo['Código SAP']}**?")
                        st.caption("Esta acción no se puede deshacer.")
                        
                        col_si, col_no = st.columns(2)
                        with col_si:
                            if st.button("✅ Sí, eliminar", type="primary", key="confirmar_eliminar"):
                                try:
                                    db = InventarioDatabase('src/db/inventario_lp02.db')
                                    cursor = db.cursor
                                    
                                    cursor.execute("DELETE FROM insumos WHERE [CODIGO SAP] = ?", (insumo['Código SAP'],))
                                    db.connection.commit()
                                    db.close()
                                    
                                    del st.session_state['confirmar_eliminar_insumo']
                                    st.success(f"✅ Insumo '{insumo['Código SAP']}' eliminado")
                                    time.sleep(1.5)
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Error al eliminar: {e}")
                        
                        with col_no:
                            if st.button("❌ Cancelar", type="secondary", key="cancelar_eliminar"):
                                del st.session_state['confirmar_eliminar_insumo']
                                st.rerun()
            else:
                st.info("👆 Seleccione una fila de la tabla para editar el insumo.")
        else:
            st.warning("⚠️ No hay insumos registrados.")
            
    except Exception as e:
        st.error(f"❌ Error al cargar insumos: {e}")