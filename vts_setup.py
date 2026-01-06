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
    if not os.path.exists(MASTER_CSV) or not os.path.exists(INV_CSV):
        print(f"❌ ERROR: No se encuentran los archivos {MASTER_CSV} o {INV_CSV}")
        return

    try:
        # 3. Carga a Pandas
        df_m = pd.read_csv(MASTER_CSV)
        df_i = pd.read_csv(INV_CSV)

        # Mapeo inteligente: "Si existe esta columna, cámbiale el nombre a este"
        # Esto evita el error de "Length mismatch" porque no fuerza todas las columnas
        mapeo_maestro = {
            'PRECIO VENTA FINAL (CON IVA)': 'precio_venta',
            'Precio Venta': 'precio_venta',
            'COSTO (SIN IVA)': 'costo_neto',
            'Costo': 'costo_neto',
            'MARGEN REAL (%)': 'margen',
            'Margen': 'margen',
            'SKU': 'sku',
            'Producto': 'producto',
            'COMP_MIN': 'comp_min',
            'COMP_MAX': 'comp_max'
        }
        
        mapeo_inventario = {
            'SKU': 'sku',
            'Funcion': 'funcion',
            'Inventario actual': 'stock_actual',
            'Aporte Hogar': 'aporte_hogar',
            'Subtotal': 'subtotal'
        }

        df_m.rename(columns=mapeo_maestro, inplace=True)
        df_i.rename(columns=mapeo_inventario, inplace=True)

        # Asegurar que existan las columnas críticas antes de subir a SQL
        columnas_necesarias = ['precio_venta', 'costo_neto', 'margen', 'comp_min', 'comp_max']
        for col in columnas_necesarias:
            if col not in df_m.columns:
                df_m[col] = 0.0  # Creamos la columna vacía si no existe

        # 4. Conexión y Volcado
        with sqlite3.connect(DB_NAME) as conn:
            # Usamos index=False para no crear una columna 'index' innecesaria
            df_m.to_sql('maestro', conn, if_exists='replace', index=False)
            df_i.to_sql('inventario', conn, if_exists='replace', index=False)
            
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tablas = cursor.fetchall()
            print(f"✅ Tablas creadas exitosamente: {tablas}")

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