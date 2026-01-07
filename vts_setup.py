import sqlite3
import pandas as pd
import os

DB_NAME = "vts_mardum.db"
MASTER_CSV = "data_s.csv"
INV_CSV = "data_v.csv"

def ejecutar_setup():
    print("🚀 INICIANDO DESPLIEGUE DE NÚCLEO VTS...")
    
    # 1. Limpieza preventiva
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print("🗑️ DB previa eliminada para limpieza total.")

    # 2. Verificación de fuentes
    fuentes_existen = os.path.exists(MASTER_CSV) and os.path.exists(INV_CSV)

    if not fuentes_existen:
        print(f"⚠️ Fuentes originales no encontradas. Creando estructura VACÍA...")
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE maestro (
                    sku TEXT PRIMARY KEY, producto TEXT, costo_neto REAL, 
                    precio_venta REAL, margen REAL, Seccion TEXT, 
                    comp_min INTEGER DEFAULT 0, comp_max INTEGER DEFAULT 0
                )""")
            cursor.execute("""
                CREATE TABLE inventario (
                    sku TEXT PRIMARY KEY, funcion TEXT, stock_actual INTEGER, 
                    aporte_hogar INTEGER DEFAULT 0, subtotal INTEGER,
                    FOREIGN KEY(sku) REFERENCES maestro(sku)
                )""")
        print("✅ Estructura creada. Usa vts_cloud_bridge.py para cargar tu Auditoría.")
        return 

    # 3. Proceso de Carga (Solo si existen los CSVs)
    try:
        df_m = pd.read_csv(MASTER_CSV)
        df_i = pd.read_csv(INV_CSV)

        mapeo_maestro = {
            'PRECIO VENTA FINAL (CON IVA)': 'precio_venta', 'COSTO (SIN IVA)': 'costo_neto',
            'MARGEN REAL (%)': 'margen', 'SKU': 'sku', 'Producto': 'producto'
        }
        mapeo_inventario = {
            'SKU': 'sku', 'Funcion': 'funcion', 'Inventario actual': 'stock_actual',
            'Aporte Hogar': 'aporte_hogar', 'Subtotal': 'subtotal'
        }

        df_m.rename(columns=mapeo_maestro, inplace=True)
        df_i.rename(columns=mapeo_inventario, inplace=True)

        columnas_necesarias = ['precio_venta', 'costo_neto', 'margen', 'comp_min', 'comp_max', 'Seccion']
        for col in columnas_necesarias:
            if col not in df_m.columns:
                df_m[col] = 0.0 if col != 'Seccion' else "General"

        with sqlite3.connect(DB_NAME) as conn:
            df_m.to_sql('maestro', conn, if_exists='replace', index=False)
            df_i.to_sql('inventario', conn, if_exists='replace', index=False)
            print("🚀 ¡INYECCIÓN COMPLETADA! El almacén SQL está lleno.")
        print("""
    =========================================
       ¡SISTEMA MARDUM LISTO PARA EL COMBATE!
              Desarrollado por
          Inversiones Vacadari SpA
    =========================================
        """)

    except Exception as e:
        print(f"🔥 ERROR CRÍTICO DURANTE LA CARGA: {e}")

if __name__ == "__main__":
    ejecutar_setup()