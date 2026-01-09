# vts_graphics.py
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from vts_utils import limpiar_pantalla, pausar

DB_NAME = "vts_mardum.db"

def visualizar_analitica_macro():
    """Genera un panel visual del estado del capital"""
    limpiar_pantalla()
    print("📊 CALCULANDO ANALÍTICA MACRO...")

    try:
        with sqlite3.connect(DB_NAME) as conn:
            # 1. Capital por Sección (Para la Torta) - Ajustado a tu DB actual
            query_seccion = """
                SELECT m.Seccion, SUM(i.stock_actual * m.costo_neto) as valor
                FROM inventario i
                JOIN maestro m ON i.sku = m.sku
                WHERE i.stock_actual > 0
                GROUP BY m.Seccion
            """
            df_cap = pd.read_sql_query(query_seccion, conn)

            # 2. Inversión Total por Sección (Para las Barras)
            query_top = """
                SELECT m.Seccion, SUM(i.stock_actual * m.costo_neto) as inversion
                FROM inventario i
                JOIN maestro m ON i.sku = m.sku
                GROUP BY m.Seccion
                ORDER BY inversion DESC
            """
            df_top = pd.read_sql_query(query_top, conn)

        if df_cap.empty:
            print("⚠️ No hay suficiente stock para generar gráficos.")
            pausar(); return

        # --- GENERACIÓN DEL DASHBOARD ---
        plt.style.use('dark_background') # Opcional: queda más "pro" y cansa menos la vista
        plt.rcParams.update({'font.size': 9})
        
        # CORRECCIÓN AQUÍ: Creamos 1 fila y 2 columnas, asignando ax1 y ax2
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5)) 
        fig.suptitle('📈 VTS ANALYTICS - ESTADO MACRO DE INVENTARIO', fontsize=14)

        # Gráfico 1: Torta de Capital
        ax1.pie(df_cap['valor'], labels=df_cap['Seccion'], autopct='%1.1f%%', startangle=140, shadow=True)
        ax1.set_title("Distribución de Capital (%)")

        # Gráfico 2: Barras Inversión por Sección
        ax2.barh(df_top['Seccion'], df_top['inversion'], color='orchid') # Color "Illidari" para las barras
        ax2.set_xlabel('Valor en Pesos ($)')
        ax2.set_title("Inversión Total ($)")
        ax2.invert_yaxis() 

        plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Ajuste para que el título no tape nada
        print("✅ Gráficos generados. Cierra la ventana para volver al VTS.")
        plt.show()

    except Exception as e:
        print(f"❌ Error al generar gráficos: {e}")
        pausar()