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

# --- METODOS DE CONSULTA STOCK ---

    def get_all_stock(self):
        """ Obtener todos los registros de stock """
        try:
            self.cursor.execute("SELECT * FROM stock")
            columnas = [description[0] for description in self.cursor.description]
            datos = self.cursor.fetchall()
            return columnas, datos
        except Exception as e:
            print(f"❌ Error al obtener stock: {e}")
            return [], []
        
    def delete_stock(self,codigo_sap):
        """ Eliminar un registro de stock por código SAP """
        try:
            self.cursor.execute('''DELETE FROM stock WHERE "CODIGO SAP" = ?''', (codigo_sap,))
            if self.cursor.rowcount > 0:
                self.connection.commit()
                print(f"✓ Stock con código SAP {codigo_sap} eliminado correctamente.")
                return True
            else:
                print(f"❌ No se encontró stock con código SAP {codigo_sap}.")
                return False
        except Exception as e:
            print(f"❌ Error al eliminar stock: {e}")
            return False
        
    def get_stock_alerts(self):
        """Obtener alertas de stock clasificadas"""
        try:
            self.cursor.execute(''' SELECT "CODIGO SAP",
                                "CLASIFICACION",
                                "DESCRIPCION DEL MATERIAL",
                                "UM",
                                "STOCK ACTUAL",
                                "PUNTO DE REORDENAMIENTO",
                                CASE
                                    WHEN "STOCK ACTUAL" = 0 THEN 'SIN STOCK'
                                    WHEN "PUNTO DE REORDENAMIENTO" > 0
                                        AND "STOCK ACTUAL" <= "PUNTO DE REORDENAMIENTO" * 0.5
                                        THEN 'STOCK CRITICO'
                                    WHEN "PUNTO DE REORDENAMIENTO" > 0
                                        AND "STOCK ACTUAL" > "PUNTO DE REORDENAMIENTO" * 0.5
                                        AND "STOCK ACTUAL" <= "PUNTO DE REORDENAMIENTO"
                                        THEN 'PROXIMO A REORDENAR'
                                    WHEN "PUNTO DE REORDENAMIENTO" > 0
                                        AND "STOCK ACTUAL" > "PUNTO DE REORDENAMIENTO" * 3
                                        THEN 'SOBRE STOCK'
                                    ELSE 'NORMAL'
                                END AS "ALERTA"
                                FROM stock
                                WHERE "STOCK ACTUAL" = 0
                                  OR ("PUNTO DE REORDENAMIENTO" > 0 AND "STOCK ACTUAL" <= "PUNTO DE REORDENAMIENTO")
                                  OR ("PUNTO DE REORDENAMIENTO" > 0 AND "STOCK ACTUAL" > "PUNTO DE REORDENAMIENTO" * 1.05 AND "STOCK ACTUAL" <= "PUNTO DE REORDENAMIENTO" * 1.20)
                                  OR ("PUNTO DE REORDENAMIENTO" > 0 AND "STOCK ACTUAL" > "PUNTO DE REORDENAMIENTO" * 3)
                                ORDER BY
                                    CASE
                                        WHEN "STOCK ACTUAL" = 0 THEN 1
                                        WHEN "STOCK ACTUAL" <= "PUNTO DE REORDENAMIENTO" * 0.5 THEN 2
                                        WHEN "STOCK ACTUAL" <= "PUNTO DE REORDENAMIENTO" THEN 3
                                        ELSE 4
                                    END
                                ''')
            columnas = [description[0] for description in self.cursor.description]
            datos = self.cursor.fetchall()
            return columnas, datos
        except Exception as e:
            print(f"❌ Error al obtener alertas de stock: {e}")
            return [], []

# --- METODO CONSULTAS DE INGRESOS ---

    def get_all_ingresos(self):
        """ Obtener todos los registros de ingresos """
        try:
            self.cursor.execute('SELECT * FROM ingresos ORDER BY "FECHA DE INGRESO" DESC')
            columnas = [description[0] for description in self.cursor.description]
            datos = self.cursor.fetchall()
            return columnas, datos
        except Exception as e:
            print(f"❌ Error al obtener ingresos: {e}")
            return [], []
        
    def delete_ingreso(self, id):
        """ Eliminar un registro de ingreso por ID """
        try:
            self.cursor.execute('DELETE FROM ingresos WHERE "ID" = ?', (id,))
            if self.cursor.rowcount > 0:
                self.connection.commit()
                print(f"✓ Ingreso con ID {id} eliminado correctamente.")
                return True
            else:
                print(f"❌ No se encontró ingreso con ID {id}.")
                return False
        except Exception as e:
            print(f"❌ Error al eliminar ingreso: {e}")
            return False
            
# --- METODO CONSULTAS DE SALIDAS ---

    def get_all_salidas(self):
        """ Obtener todos los registros de salidas """
        try:
            self.cursor.execute('SELECT * FROM salidas ORDER BY "FECHA DE SALIDA" DESC')
            columnas = [description[0] for description in self.cursor.description]
            datos = self.cursor.fetchall()
            return columnas, datos
        except Exception as e:
            print(f"❌ Error al obtener salidas: {e}")
            return [], []
        
    def delete_salida(self, id):
        """ Eliminar un registro de salida por ID """
        try:
            self.cursor.execute('DELETE FROM salidas WHERE "ID" = ?', (id,))
            if self.cursor.rowcount > 0:
                self.connection.commit()
                print(f"✓ Salida con ID {id} eliminado correctamente.")
                return True
            else:
                print(f"❌ No se encontró salida con ID {id}.")
                return False
        except Exception as e:
            print(f"❌ Error al eliminar salida: {e}")
            return False
        
# --- METODOS DE ACTUALIZACIÓN DE STOCK ---

    def update_stock_on_ingreso(self, codigo_sap, cantidad, clasificacion=None, descripcion=None, um=None):
        """ Al registrar ingreso: sumar cantidad a STOCK ACTUAL e INGRESOS """
        try:
            self.cursor.execute('''
                UPDATE stock
                SET "STOCK ACTUAL" = COALESCE("STOCK ACTUAL", 0) + ?,
                    "INGRESOS" = COALESCE("INGRESOS", 0) + ?
                WHERE CAST("CODIGO SAP" AS TEXT) = CAST(? AS TEXT)
            ''', (cantidad, cantidad, codigo_sap))

            if self.cursor.rowcount > 0:
                self.connection.commit()
                print(f"Stock actualizado: {codigo_sap} incrementado en {cantidad}.")
                return True
            else:
                self.cursor.execute('''
                    INSERT INTO stock (
                        "CODIGO SAP", "CLASIFICACION", "DESCRIPCION DEL MATERIAL", "UM",
                        "STOCK INICIAL", "INGRESOS", "SALIDAS", "STOCK ACTUAL", "PUNTO DE REORDENAMIENTO"
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (codigo_sap, clasificacion, descripcion, um, cantidad, cantidad, 0, cantidad, 0))
                self.connection.commit()
                print(f"Material {codigo_sap} no encontrado en stock. Se ha creado un nuevo registro.")
                return False
        except Exception as e:
            print(f"❌ Error al actualizar stock: {e}")
            return False
        
    def update_stock_on_salida(self, codigo_sap, cantidad):
        """ Al registrar salida: restar cantidad a STOCK ACTUAL y sumar a SALIDAS """
        try:
            self.cursor.execute('''
                SELECT "STOCK ACTUAL" FROM stock
                WHERE CAST("CODIGO SAP" AS TEXT) = CAST(? AS TEXT)
            ''', (codigo_sap,))
            row = self.cursor.fetchone()
            if not row:
                print(f"Material {codigo_sap} no encontrado en stock.")
                return False, None

            stock_actual = row[0] or 0
            if stock_actual < cantidad:
                print(f"Stock insuficiente para {codigo_sap}. Stock actual: {stock_actual}, cantidad solicitada: {cantidad}.")
                return False, int(stock_actual)

            self.cursor.execute('''
                UPDATE stock
                SET "STOCK ACTUAL" = MAX(0, COALESCE("STOCK ACTUAL",0) - ?),
                    "SALIDAS" = COALESCE("SALIDAS",0) + ?
                WHERE CAST("CODIGO SAP" AS TEXT) = CAST(? AS TEXT)
            ''', (cantidad, cantidad, codigo_sap))
            self.connection.commit()

            self.cursor.execute('''
                SELECT "STOCK ACTUAL" FROM stock
                WHERE CAST("CODIGO SAP" AS TEXT) = CAST(? AS TEXT)
            ''', (codigo_sap,))
            nuevo_stock = self.cursor.fetchone()[0] or 0

            print(f"Stock actualizado: {codigo_sap} decrementado en {cantidad}.")
            return True, int(nuevo_stock)
        except Exception as e:
            print(f"❌ Error al actualizar stock: {e}")
            return False, str(e)
        
    def revert_stock_ingreso(self, codigo_sap, cantidad):
        """ Al eliminar ingreso: restar cantidad a STOCK ACTUAL"""
        try:
            self.cursor.execute('''
                UPDATE stock
                SET "STOCK ACTUAL" = MAX(0, "STOCK ACTUAL" - ?)
                WHERE CAST("CODIGO SAP" AS TEXT) = CAST(? AS TEXT)
            ''', (cantidad, codigo_sap))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Error al revertir stock por eliminación de ingreso: {e}")
            return False
        
    def revert_stock_salida(self, codigo_sap, cantidad):
        """ Al eliminar salida: sumar cantidad a STOCK ACTUAL"""
        try:
            self.cursor.execute('''
                UPDATE stock
                SET "STOCK ACTUAL" = "STOCK ACTUAL" + ?
                WHERE CAST("CODIGO SAP" AS TEXT) = CAST(? AS TEXT)
            ''', (cantidad, codigo_sap))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Error al revertir stock por eliminación de salida: {e}")
            return False
