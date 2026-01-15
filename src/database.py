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