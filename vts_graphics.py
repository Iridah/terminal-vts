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
            # 1. Capital por Sección
            query_seccion = """
                SELECT m.Seccion, SUM(i.subtotal * m.costo_neto) as valor
                FROM inventario i
                JOIN maestro m ON i.sku = m.sku
                WHERE i.subtotal > 0
                GROUP BY m.Seccion
            """
            df_cap = pd.read_sql_query(query_seccion, conn)

            # 2. Top 10 Productos con más capital retenido
            query_top = """
                SELECT i.funcion, (i.subtotal * m.costo_neto) as valor_total
                FROM inventario i
                JOIN maestro m ON i.sku = m.sku
                ORDER BY valor_total DESC LIMIT 10
            """
            df_top = pd.read_sql_query(query_top, conn)

        if df_cap.empty:
            print("⚠️ No hay suficiente stock para generar gráficos.")
            pausar(); return

        # --- GENERACIÓN DEL DASHBOARD ---
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('📈 VTS ANALYTICS - ESTADO MACRO DE INVENTARIO', fontsize=16)

        # Gráfico 1: Torta de Capital
        ax1.pie(df_cap['valor'], labels=df_cap['Seccion'], autopct='%1.1f%%', startangle=140)
        ax1.set_title("Distribución de Capital por Sección")

        # Gráfico 2: Barras Top Inversión
        ax2.barh(df_top['funcion'], df_top['valor_total'], color='skyblue')
        ax2.set_xlabel('Valor en Pesos ($)')
        ax2.set_title("Top 10: Mayor Inversión en Bodega")
        plt.gca().invert_yaxis()

        plt.tight_layout()
        print("✅ Gráficos generados. Cierra la ventana para volver al VTS.")
        plt.show()

    except Exception as e:
        print(f"❌ Error al generar gráficos: {e}")
        pausar()