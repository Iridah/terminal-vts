# vts_cloud_bridge
import sqlite3
import pandas as pd
from datetime import datetime
from vts_utils import limpiar_pantalla, pausar

DB_NAME = "vts_mardum.db"

def generar_plantilla_auditoria():
    """Genera el CSV maestro basado en la DB actual para conteo físico"""
    limpiar_pantalla()
    print("📝 GENERANDO PLANTILLA DE AUDITORÍA...")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            query = """
                SELECT i.sku, i.funcion as producto, m.Seccion, i.subtotal as stock_sistema 
                FROM inventario i
                JOIN maestro m ON i.sku = m.sku
            """
            df = pd.read_sql_query(query, conn)
        
        df['inventario_real'] = "" 
        df['nuevo_costo'] = "" 
        
        filename = f"AUDITORIA_VTS_{datetime.now().strftime('%d_%m')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n✅ ¡ARCHIVO CREADO!: {filename}")
        print("📊 Instrucciones: Llena la columna 'inventario_real' y guarda.")
    except Exception as e:
        print(f"❌ Error al exportar: {e}")
    pausar()

def ejecutar_carga_real(archivo_csv):
    """Sobrescribe o crea registros basados en el CSV físico"""
    limpiar_pantalla()
    print(f"📥 CARGANDO DATOS DESDE: {archivo_csv}...")
    try:
        df_real = pd.read_csv(archivo_csv)
        # Filtramos para procesar solo lo que marcaste en el inventario
        df_real = df_real[df_real['inventario_real'].notnull()]

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            for _, fila in df_real.iterrows():
                sku = str(fila['sku']).upper().strip()
                stock_fisico = int(fila['inventario_real'])
                costo = fila['nuevo_costo'] if pd.notnull(fila['nuevo_costo']) else 0.0

                # Lógica UPSERT (Update or Insert)
                cursor.execute("SELECT sku FROM inventario WHERE sku = ?", (sku,))
                if cursor.fetchone():
                    # UPDATE: La verdad del conteo físico manda
                    cursor.execute("UPDATE inventario SET stock_actual = ?, subtotal = ? WHERE sku = ?", 
                                 (stock_fisico, stock_fisico, sku))
                    if costo > 0:
                        cursor.execute("UPDATE maestro SET costo_neto = ? WHERE sku = ?", (costo, sku))
                    print(f"✅ Sincronizado: {sku}")
                else:
                    # INSERT: Capturamos el nombre real desde el CSV
                    nombre_real = fila['producto'] if 'producto' in fila else f"NUEVO ({sku})"
                    print(f"⚠️ NUEVO SKU ENCONTRADO: {sku} -> {nombre_real}")
                    
                    # Insert en Maestro
                    cursor.execute("""
                        INSERT INTO maestro (sku, producto, costo_neto, precio_venta, margen) 
                        VALUES (?, ?, ?, 0, 0)""", 
                        (sku, nombre_real, costo))
                    
                    # Insert en Inventario
                    cursor.execute("""
                        INSERT INTO inventario (sku, funcion, stock_actual, aporte_hogar, subtotal) 
                        VALUES (?, ?, ?, 0, ?)""", 
                        (sku, nombre_real, stock_fisico, stock_fisico))

            conn.commit()
            print(f"\n⚖️ BASE DE DATOS ACTUALIZADA CON ÉXITO.")
    except Exception as e:
        print(f"🔥 Error en carga: {e}")
    pausar()

# EL DISPARADOR (Corregido para que funcione al ejecutar el archivo)
if __name__ == "__main__":
    while True:
        limpiar_pantalla()
        # Generamos el nombre sugerido basado en la fecha actual
        fecha_hoy = datetime.now().strftime('%d_%m')
        nombre_default = f"AUDITORIA_VTS_{fecha_hoy}.csv"

        print("🚀 VTS CLOUD BRIDGE - MODO OFFLINE")
        print("="*40)
        print(f"1. GENERAR PLANTILLA ({nombre_default})")
        print(f"2. CARGAR INVENTARIO (Default: {nombre_default})")
        print("3. SALIR")
        print("="*40)
        op = input("Selecciona: ")
        
        if op == "1":
            generar_plantilla_auditoria()
        elif op == "2":
            archivo = input(f"Nombre del archivo [Enter para {nombre_default}]: ")
            # Si el input está vacío, usa el default
            if not archivo.strip():
                archivo = nombre_default
            ejecutar_carga_real(archivo)
        elif op == "3":
            break