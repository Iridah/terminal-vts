#vts_graphics.py
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
            # 1. Capital por Sección (Para la Torta)
            query_seccion = """
                SELECT m.Seccion, SUM(i.subtotal * m.costo_neto) as valor
                FROM inventario i
                JOIN maestro m ON i.sku = m.sku
                WHERE i.subtotal > 0
                GROUP BY m.Seccion
            """
            df_cap = pd.read_sql_query(query_seccion, conn)

            # 2. Inversión Total por Sección (Para las Barras)
            # Cambiamos 'funcion' por 'Seccion' y 'valor_total' por 'inversion'
            query_top = """
                SELECT m.Seccion, SUM(i.subtotal * m.costo_neto) as inversion
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
        plt.rcParams.update({'font.size': 8}) # Letra más pequeña para monitores viejos
        fig, ax = plt.subplots(figsize=(6, 4)) # Tamaño compacto
        fig.suptitle('📈 VTS ANALYTICS - ESTADO MACRO DE INVENTARIO', fontsize=16)

        # Gráfico 1: Torta de Capital
        ax1.pie(df_cap['valor'], labels=df_cap['Seccion'], autopct='%1.1f%%', startangle=140)
        ax1.set_title("Distribución de Capital por Sección")

        # Gráfico 2: Barras Inversión por Sección
        # USAMOS LOS NOMBRES DE COLUMNA DEL SQL: 'Seccion' e 'inversion'
        ax2.barh(df_top['Seccion'], df_top['inversion'], color='skyblue') # Nombres corregidos
        ax2.set_xlabel('Valor en Pesos ($)')
        ax2.set_title("Inversión Total por Departamento")
        ax2.invert_yaxis() # Invertir para que la mayor inversión esté arriba

        plt.tight_layout() # Crucial para monitores pequeños
        print("✅ Gráficos generados. Cierra la ventana para volver al VTS.")
        plt.show()

    except Exception as e:
        print(f"❌ Error al generar gráficos: {e}")
        pausar()