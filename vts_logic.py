# vts_logic
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
        termino = input("PRODUCTO / SKU: ").strip().lower()
        if termino in ["", "0"]: break

        with obtener_conexion() as conn:
            cursor = conn.cursor()
            query = """
            SELECT i.sku, i.funcion, i.subtotal, m.precio_venta 
            FROM inventario i
            LEFT JOIN maestro m ON i.sku = m.sku
            WHERE LOWER(i.funcion) LIKE ? OR LOWER(i.sku) LIKE ?
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
        
        # Ajustamos el SELECT para traer SKU y NOMBRE
        cursor.execute("SELECT sku, funcion, subtotal FROM inventario WHERE subtotal <= 1")
        criticos = cursor.fetchall()
        if criticos:
            print("\n⚠️ CRÍTICOS:")
            for c in criticos: 
                # c[0] es SKU, c[1] es descripción
                print(f" - [{c[0]:10}] {c[1][:35]:35} | {c[2]:3} un.")
    pausar()

def generar_lista_compras():
    limpiar_pantalla()
    print("🛒 SUGERENCIA DE REPOSICIÓN ESTRATÉGICA (Semáforo SQL)")
    imprimir_separador()
    
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        # Traemos datos de ambas tablas para calcular la decisión en el aire
        query = """
            SELECT i.sku, i.funcion, i.subtotal, m.costo_neto, 
                   m.margen, m.precio_venta, m.comp_min, m.comp_max 
            FROM inventario i 
            JOIN maestro m ON i.sku = m.sku
            WHERE i.subtotal <= 1
            ORDER BY m.margen DESC
        """
        cursor.execute(query)
        faltantes = cursor.fetchall()
        
        if faltantes:
            total_inversion = 0
            print(f"{'SKU':10} | {'PRODUCTO':25} | {'STOCK':5} | {'ESTRATEGIA'}")
            print("-" * 70)
            
            for f in faltantes:
                # Recuperamos la lógica de decisión ejecutiva
                decision = obtener_decision_ejecutiva(f[4], f[5], f[6], f[7])
                
                # Asignación de "color" visual (texto)
                emoji = "🔴" if "DESCARTE" in decision else "🟢" if "META" in decision else "🔥" if "GANCHO" in decision else "🟡"
                
                print(f"[{f[0]:8}] {f[1][:25]:25} | {f[2]:5} | {emoji} {decision}")
                total_inversion += (f[3] * 5) # Estimación base 5 unidades
            
            print("-" * 70)
            print(f"💰 INVERSIÓN ESTIMADA PARA REPOSICIÓN (Base 5 un.): ${total_inversion:,.0f}")
        else:
            print("✅ TODO EN ORDEN: No hay productos críticos en stock.")
    pausar()

def tablero_estrategico(df_m=None):
    limpiar_pantalla()
    print(f"{'PRODUCTO':50} | {'MARGEN':7} | {'ESTRATEGIA'}")
    imprimir_separador()
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT producto, margen, precio_venta, comp_min, comp_max FROM maestro ORDER BY margen DESC")
        for r in cursor.fetchall():
            decision = obtener_decision_ejecutiva(r[1], r[2], r[3], r[4])
            print(f"{r[0][:33]:50} | {r[1]*100:6.1f}% | {decision}")
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

def modulo_egreso():
    while True:
        limpiar_pantalla()
        imprimir_separador()
        print("📦 MÓDULO DE EGRESO DE MERCADERÍA")
        print(" 1. Registrar Venta (Egreso General)")
        print(" 2. Aporte Hogar (Consumo Interno)")
        print(" 3. Anular Salida (Corrección de stock)")
        print(" 0. Volver al menú principal")
        imprimir_separador()
        
        op = input("Seleccione tipo de salida: ")
        if op == "0": break
        
        sku = input("Ingrese SKU del producto: ").strip().upper()
        try:
            cantidad = int(input("Cantidad: "))
        except: 
            print("❌ Cantidad inválida."); pausar(); continue

        with obtener_conexion() as conn:
            cursor = conn.cursor()
            
            if op == "1": # Venta General
                cursor.execute("UPDATE inventario SET subtotal = subtotal - ? WHERE sku = ?", (cantidad, sku))
                print(f"✅ Venta registrada: -{cantidad} un. en {sku}")
            
            elif op == "2": # Aporte Hogar
                cursor.execute("""
                    UPDATE inventario 
                    SET subtotal = subtotal - ?, aporte_hogar = aporte_hogar + ? 
                    WHERE sku = ?""", (cantidad, cantidad, sku))
                print(f"✅ Aporte Hogar registrado: -{cantidad} un. en {sku}")
                
            elif op == "3": # Anulación (Suma al stock)
                cursor.execute("UPDATE inventario SET subtotal = subtotal + ? WHERE sku = ?", (cantidad, sku))
                print(f"✅ Stock corregido: +{cantidad} un. en {sku}")

            conn.commit()
            if cursor.rowcount == 0:
                print("❌ SKU no encontrado en la base de datos.")
        pausar()

def modulo_administracion():
    while True:
        limpiar_pantalla()
        imprimir_separador()
        print("🛠️ PANEL DE ADMINISTRACIÓN CENTRALIZADO")
        print(" 1. Sincronizar Auditoría (Cloud Bridge)")
        print(" 2. Editor de Maestro (Precios/Costos/Nuevos)")
        print(" 3. Bautismo de Secciones (Mapeo Masivo)")
        print(" 0. Volver al menú principal")
        imprimir_separador()
        
        op = input("VTS_ADMIN > ")
        if op == "0": break
        
        if op == "2": # EDITOR MAESTRO (Resuelve tus dudas de carga)
            sku = input("Ingrese SKU: ").strip().upper()
            with obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT producto, costo_neto, precio_venta FROM maestro WHERE sku = ?", (sku,))
                res = cursor.fetchone()
                
                if res: # SKU EXISTE -> ACTUALIZAR
                    print(f"Editando: {res[0]}")
                    n_costo = input(f"Nuevo Costo (actual {res[1]}): ") or res[1]
                    n_venta = input(f"Nuevo Precio (actual {res[2]}): ") or res[2]
                    cursor.execute("UPDATE maestro SET costo_neto = ?, precio_venta = ? WHERE sku = ?", (n_costo, n_venta, sku))
                    print("✅ Producto actualizado.")
                else: # SKU NUEVO -> REGISTRAR
                    print("✨ SKU detectado como NUEVO. Iniciando registro...")
                    nombre = input("Nombre del Producto: ")
                    costo = float(input("Costo Neto: "))
                    venta = float(input("Precio Venta: "))
                    seccion = input("Prefijo Sección (V-LIM, V-ELE, etc): ")
                    
                    cursor.execute("INSERT INTO maestro (sku, producto, costo_neto, precio_venta, seccion) VALUES (?,?,?,?,?)",
                                   (sku, nombre, costo, venta, seccion))
                    cursor.execute("INSERT INTO inventario (sku, funcion, subtotal, aporte_hogar) VALUES (?,?,0,0)",
                                   (sku, nombre))
                    print(f"✅ {nombre} registrado con éxito en Maestro e Inventario.")
                conn.commit()
            pausar()

def registrar_entrada():
    limpiar_pantalla()
    imprimir_separador()
    print("📦 REGISTRO DE ENTRADA / INGRESO DE STOCK")
    sku = input("Ingrese SKU: ").strip().upper()
    if sku in ["", "0"]: return

    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT producto, subtotal FROM inventario WHERE sku = ?", (sku,))
        res = cursor.fetchone()

        if res:
            print(f"Producto: {res[0]} | Stock actual: {res[1]}")
            try:
                cantidad = int(input("Cantidad a INGRESAR: "))
                cursor.execute("UPDATE inventario SET subtotal = subtotal + ? WHERE sku = ?", (cantidad, sku))
                conn.commit()
                print(f"✅ Stock actualizado: +{cantidad} unidades.")
            except ValueError: print("❌ Cantidad inválida.")
        else:
            print("⚠️ SKU no existe. ¿Desea crearlo en la Opción 7?")
    pausar()