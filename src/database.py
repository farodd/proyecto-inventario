import sqlite3

class InventarioDatabase:
    """
    Gestiona todas las operaciones de BD para 
    el inventario de insumos operacionales
    """
    def __init__(self, db_path='db/inventario_lp02.db'):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

    def insert_insumo(self, codigo_sap, descripcion, clasificacion, um, observaciones):
        """ Insertar o actualizar un insumo en la tabla """
        try:
            self.cursor.execute('''
                INSERT INTO insumos ("CODIGO SAP", "DESCRIPCION DEL MATERIAL", "CLASIFICACION", "UM", "OBSERVACIONES")
                VALUES (?, ?, ?, ?, ?)
            ''', (codigo_sap, descripcion, clasificacion, um, observaciones))
            self.connection.commit()
            print(f"Insumo con código SAP {codigo_sap} insertado correctamente.")

        except sqlite3.IntegrityError:
            print(f"El insumo con código SAP {codigo_sap} ya existe en la base de datos.")

    def insert_ingreso(self, codigo_sap, clasificacion, descripcion, um, cantidad, fecha_ingreso,precio_unitario,
                    reserva=None, guia_despacho=None, oc=None, uso=None, recibido_por=None, 
                    ubicacion=None, empresa=None, observaciones=None):
        """ Insertar un nuevo ingreso en la tabla """
        try:
            self.cursor.execute('''
                INSERT INTO ingresos (
                    "CODIGO SAP", "CLASIFICACION", "DESCRIPCION DEL MATERIAL", "UM", 
                    "CANTIDAD", "FECHA DE INGRESO", "RESERVA", "GUIA DESPACHO", "OC",
                    "USO: OPERACIONES/PROYECTO", "RECIBIDO POR", "UBICACION", 
                    "EMPRESA", "PRECIO UNITARIO", "OBSERVACIONES"
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (codigo_sap, clasificacion, descripcion, um, cantidad, fecha_ingreso,
                reserva, guia_despacho, oc, uso, recibido_por, ubicacion, 
                empresa, precio_unitario, observaciones))
            self.connection.commit()
            print(f"✓ Ingreso con código SAP {codigo_sap} insertado correctamente.")
            return True
            
        except sqlite3.IntegrityError as e:
            print(f"❌ Error de integridad: {e}")
            return False
        except Exception as e:
            print(f"❌ Error al insertar ingreso: {e}")
            return False
        
    def insert_salida(self, codigo_sap, clasificacion, descripcion, um, cantidad, fecha_salida,
                    guia_salida=None, uso=None, entregado_a=None, comentarios=None, ubicacion=None):
        """ Insertar una nueva salida en la tabla """
        try:
            self.cursor.execute('''
                INSERT INTO salidas (
                    "CODIGO SAP", "CLASIFICACION", "DESCRIPCION DEL MATERIAL", "UM", 
                    "CANTIDAD", "FECHA DE SALIDA", "N° DE GUIA DE SALIDA",
                    "USO: OPERACIONES/PROYECTO", "ENTREGADO A", "COMENTARIOS", 
                    "UBICACION DE RETIRO"
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (codigo_sap, clasificacion, descripcion, um, cantidad, fecha_salida,
                guia_salida, uso, entregado_a, comentarios, ubicacion))
            self.connection.commit()
            print(f"✓ salida con código SAP {codigo_sap} insertado correctamente.")
            return True
            
        except sqlite3.IntegrityError as e:
            print(f"❌ Error de integridad: {e}")
            return False
        except Exception as e:
            print(f"❌ Error al insertar salida: {e}")
            return False
        
    def insert_stock(self, codigo_sap, clasificacion, descripcion, um, stock_inicial, ingreso,
                    salida, stock_actual, punto_reordenamiento):
        """ Insertar un nuevo stock en la tabla """
        try:
            self.cursor.execute('''
                INSERT INTO stock (
                    "CODIGO SAP", "CLASIFICACION", "DESCRIPCION DEL MATERIAL", "UM", 
                    "STOCK INICIAL", "INGRESOS", "SALIDAS", "STOCK ACTUAL",
                    "PUNTO DE REORDENAMIENTO")
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (codigo_sap, clasificacion, descripcion, um, stock_inicial, ingreso,
                salida, stock_actual, punto_reordenamiento))
            self.connection.commit()
            print(f"✓ stock con código SAP {codigo_sap} insertado correctamente.")
            return True
            
        except sqlite3.IntegrityError as e:
            print(f"❌ Error de integridad: {e}")
            return False
        except Exception as e:
            print(f"❌ Error al insertar stock: {e}")
            return False


    def update_insumo(self, codigo_sap, descripcion=None, clasificacion=None, um=None, observaciones=None):
        """Actualizar un insumo existente"""
        updates = []
        values = []
        
        if descripcion:
            updates.append("DESCRIPCION_MATERIAL = ?")
            values.append(descripcion)
        if clasificacion:
            updates.append("CLASIFICACION = ?")
            values.append(clasificacion)
        if um:
            updates.append("UM = ?")
            values.append(um)
        if observaciones:
            updates.append("OBSERVACIONES = ?")
            values.append(observaciones)
        
        if not updates:
            print("❌ No hay campos para actualizar")
            return False
        
        values.append(codigo_sap)
        sql = f"UPDATE insumos SET {', '.join(updates)} WHERE CODIGO_SAP = ?"
        
        try:
            self.cursor.execute(sql, values)
            if self.cursor.rowcount > 0:
                self.connection.commit()
                print(f"✓ Insumo {codigo_sap} actualizado correctamente")
                return True
            else:
                print(f"❌ El insumo {codigo_sap} no existe")
                return False
        except Exception as e:
            print(f"❌ Error al actualizar: {e}")
            return False
            
    def close(self):
        self.connection.close()