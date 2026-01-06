import sqlite3
import pandas as pd
from datetime import datetime
from vts_utils import limpiar_pantalla, pausar, imprimir_separador

DB_NAME = "vts_mardum.db"

def obtener_conexion():
    """Utilidad interna para conectar a la DB"""
    return sqlite3.connect(DB_NAME)

# --- FUNCIONES DE APOYO ---

def obtener_decision_ejecutiva(margen, precio, comp_min, comp_max):
    """Lógica pura: Mantiene la inteligencia de negocio original"""
    try:
        m, p = float(margen), float(precio)
        s3 = float(comp_min) if comp_min and comp_min != 0 else p
        u3 = float(comp_max) if comp_max and comp_max != 0 else p
    except: return "Faltan Datos"

    if m >= 0.2801:
        if p < s3: return "🔥 SUPER GANCHO"
        return "🟢 MARGEN META" if p <= u3 else "⚠️ ALTO MARGEN"
    elif m < 0.1401:
        if p < s3: return "🟡 MARGEN BAJO"
        return "🔴 DESCARTE" if p > u3 else "Decisión Estándar"
    return "Decisión Estándar"

def limpiar_precio(valor):
    """Mantenemos esta utilidad por si Pandas la necesita en imports futuros"""
    if pd.isnull(valor): return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    limpio = str(valor).replace('$', '').replace('.', '').replace(',', '.').strip()
    try: return float(limpio)
    except: return 0.0

# --- FUNCIONES DEL MENÚ (CABLEADAS A SQL) ---

def verificar_integridad_base(df_i_ignorado=None, df_m_ignorado=None):
    """Busca SKUs en maestro que no existen en inventario usando un EXCEPT de SQL"""
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        query = "SELECT sku FROM maestro EXCEPT SELECT sku FROM inventario"
        cursor.execute(query)
        faltantes = cursor.fetchall()
        if faltantes:
            print(f"\n⚠️ AVISO DE INTEGRIDAD: {len(faltantes)} SKUs nuevos sin inicializar.")
            return True
    return False

def busqueda_rapida(df_i=None, df_m=None):
    while True:
        limpiar_pantalla()
        imprimir_separador()
        print("🔍 BÚSQUEDA RÁPIDA SQL (0 para volver)")
        imprimir_separador()
        termino = input("PRODUCTO / SKU: ").strip().upper()
        if termino in ["", "0"]: break

        with obtener_conexion() as conn:
            cursor = conn.cursor()
            query = """
                SELECT i.sku, i.funcion, i.subtotal, m.precio_venta 
                FROM inventario i
                LEFT JOIN maestro m ON i.sku = m.sku
                WHERE i.funcion LIKE ? OR i.sku LIKE ?
            """
            cursor.execute(query, (f'%{termino}%', f'%{termino}%'))
            res = cursor.fetchall()
            if res:
                print(f"\n{'SKU':12} | {'PRODUCTO':30} | {'STOCK':6} | {'PRECIO'}")
                print("-" * 65)
                for r in res:
                    print(f"{r[0]:12} | {r[1][:30]:30} | {r[2]:6} | ${r[3]:,.0f}")
            else: print("\n❌ SIN COINCIDENCIAS.")
        pausar()

def exportar_datos(df_i_ignorado=None):
    limpiar_pantalla()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"VTS_SQL_EXPORT_{timestamp}.txt"
    with obtener_conexion() as conn:
        df = pd.read_sql_query("SELECT * FROM inventario", conn)
        df.to_csv(filename, sep='\t', index=False)
    print(f"✅ EXPORTADO: {filename}")
    pausar()

def valorizar_inventario(df_i=None, df_m=None):
    limpiar_pantalla()
    print("💰 AUDITORÍA DE VALORIZACIÓN SQL")
    imprimir_separador()
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        query = """
            SELECT SUM(i.subtotal * m.costo_neto), SUM(i.aporte_hogar)
            FROM inventario i
            JOIN maestro m ON i.sku = m.sku
        """
        cursor.execute(query)
        activos, hogar = cursor.fetchone()
        activos = activos if activos else 0
        print(f"VALOR TOTAL BODEGA: ${activos:,.0f}")
        print(f"CONSUMO INTERNO:   {hogar if hogar else 0} un.")
        
        # Alerta de stock crítico
        cursor.execute("SELECT funcion, subtotal FROM inventario WHERE subtotal <= 1")
        criticos = cursor.fetchall()
        if criticos:
            print("\n⚠️ CRÍTICOS:")
            for c in criticos: print(f" - {c[0]}: {c[1]} un.")
    pausar()

def tablero_estrategico(df_m=None):
    limpiar_pantalla()
    print(f"{'PRODUCTO':20} | {'MARGEN':7} | {'ESTRATEGIA'}")
    imprimir_separador()
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT producto, margen, precio_venta, comp_min, comp_max FROM maestro ORDER BY margen DESC")
        for r in cursor.fetchall():
            decision = obtener_decision_ejecutiva(r[1], r[2], r[3], r[4])
            print(f"{r[0][:20]:20} | {r[1]*100:6.1f}% | {decision}")
    pausar()

def generar_lista_compras(df_i=None, df_m=None):
    limpiar_pantalla()
    print("🛒 SUGERENCIA DE REPOSICIÓN SQL")
    imprimir_separador()
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        query = """
            SELECT i.funcion, i.subtotal, m.costo_neto 
            FROM inventario i JOIN maestro m ON i.sku = m.sku
            WHERE i.subtotal <= 1
        """
        cursor.execute(query)
        faltantes = cursor.fetchall()
        if faltantes:
            total = 0
            for f in faltantes:
                print(f"{f[0][:25]:25} | Stock: {f[1]} | Costo: ${f[2]:,.0f}")
                total += (f[2] * 5)
            print(f"\n💰 INVERSIÓN EST. (Base 5 un.): ${total:,.0f}")
        else: print("✅ TODO EN ORDEN.")
    pausar()

def ver_super_ganchos(df_m=None):
    limpiar_pantalla()
    print("🔥 SUPER GANCHOS DETECTADOS")
    imprimir_separador()
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        # Lógica SQL: Margen > 28% y precio < competencia_min
        query = "SELECT producto, precio_venta FROM maestro WHERE margen >= 0.2801 AND precio_venta < comp_min"
        cursor.execute(query)
        ganchos = cursor.fetchall()
        if ganchos:
            for g in ganchos: print(f"⭐ {g[0][:30]:30} | ${g[1]:,.0f}")
        else: print("No hay ganchos actualmente.")
    pausar()

def calculadora_packs(df_m=None):
    limpiar_pantalla()
    print("📦 CREADOR DE COMBOS SQL")
    imprimir_separador()
    entrada = input("SKUS (Coma): ").upper()
    if entrada in ["", "0"]: return
    skus = [s.strip() for s in entrada.split(',')]
    total = 0
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        for s in skus:
            cursor.execute("SELECT producto, precio_venta FROM maestro WHERE sku = ?", (s,))
            res = cursor.fetchone()
            if res:
                print(f" - {res[0]}: ${res[1]:,.0f}")
                total += res[1]
        if total > 0:
            print(f"\nTOTAL: ${total:,.0f} | COMBO (-10%): ${(total*0.9):,.0f}")
    pausar()