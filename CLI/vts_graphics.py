import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from vts_utils import limpiar_pantalla, pausar

DB_NAME = "vts_mardum.db"

def visualizar_analitica_macro():
    """Genera un panel visual del estado del capital con blindaje contra Nones"""
    limpiar_pantalla()
    print("📊 CALCULANDO ANALÍTICA MACRO...")

    try:
        with sqlite3.connect(DB_NAME) as conn:
            # Query unificada para evitar múltiples llamadas
            query = """
                SELECT IFNULL(m.Seccion, 'Sin Sección') as Seccion, 
                       (i.stock_actual * m.costo_neto) as valor_item
                FROM inventario i
                JOIN maestro m ON i.sku = m.sku
                WHERE i.stock_actual > 0
            """
            df = pd.read_sql_query(query, conn)

        if df.empty:
            print("⚠️ No hay datos de stock/costo para graficar.")
            pausar(); return

        # --- BLINDAJE DE DATOS CON PANDAS ---
        # 1. Agrupamos por Sección
        df_grouped = df.groupby('Seccion')['valor_item'].sum().reset_index()
        # 2. Ordenamos para que el gráfico de barras se vea bien
        df_grouped = df_grouped.sort_values(by='valor_item', ascending=False)
        # 3. Aseguramos que 'Seccion' sea string (Evita el error que tuviste)
        df_grouped['Seccion'] = df_grouped['Seccion'].astype(str)

        # --- GENERACIÓN DEL DASHBOARD ---
        plt.style.use('dark_background')
        plt.rcParams.update({'font.size': 9})
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6)) 
        fig.suptitle('📈 VTS ANALYTICS - ESTADO MACRO DE INVENTARIO', fontsize=14, color='orchid')

        # Gráfico 1: Torta de Capital
        colores = plt.cm.Paired(range(len(df_grouped))) # Paleta de colores variada
        ax1.pie(df_grouped['valor_item'], 
                labels=df_grouped['Seccion'], 
                autopct='%1.1f%%', 
                startangle=140, 
                colors=colores)
        ax1.set_title("Distribución de Capital (%)")

        # Gráfico 2: Barras Inversión por Sección
        ax2.barh(df_grouped['Seccion'], df_grouped['valor_item'], color='orchid')
        ax2.set_xlabel('Valor Neto ($)')
        ax2.set_title("Inversión Total por Sección ($)")
        ax2.invert_yaxis() 

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        print("✅ Panel generado exitosamente.")
        # Sello de autoría en el dashboard
        plt.figtext(0.99, 0.01, '© 2026 VTS - Inversiones Vacadari SpA.', 
            horizontalalignment='right', fontsize=8, color='gray', alpha=0.5)
        plt.show()

    except Exception as e:
        print(f"❌ Error al generar gráficos: {e}")
        pausar()