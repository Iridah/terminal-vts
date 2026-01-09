#VTS_logic
import os
import sqlite3
import pandas as pd
import shutil
from datetime import datetime
from vts_utils import limpiar_pantalla, pausar, imprimir_separador

# --- 0. CONFIGURACIÓN Y CONEXIÓN ---
DB_NAME = "vts_mardum.db"

def obtener_conexion():
    return sqlite3.connect(DB_NAME)

# --- 1. UTILIDADES ADMINISTRATIVAS ---

def generar_plantilla_auditoria():
    limpiar_pantalla()
    print("📝 GENERANDO PLANTILLA DE AUDITORÍA...")
    try:
        with obtener_conexion() as conn:
            query = "SELECT i.sku, i.stock_actual as producto, i.stock_actual FROM inventario i"
            df = pd.read_sql_query(query, conn)
        df['inventario_real'] = ""
        df['nuevo_costo'] = ""
        filename = f"AUDITORIA_VTS_{datetime.now().strftime('%d_%m')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n✅ ¡ARCHIVO CREADO!: {filename}")
    except Exception as e:
        print(f"❌ Error al exportar: {e}")
    pausar()

def verificar_integridad_base():
    """Comprueba que todos los SKUs en maestro existan en inventario"""
    try:
        with obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sku FROM maestro EXCEPT SELECT sku FROM inventario")
            faltan = cursor.fetchall()
            if faltan:
                print(f"⚠️ INTEGRIDAD: Faltan {len(faltan)} SKUs en la tabla inventario.")
            else:
                print("✅ Sincronización de tablas íntegra.")
    except Exception as e:
        print(f"⚠️ No se pudo verificar integridad: {e}")

# --- 2. GESTIÓN OPERATIVA ---

def registrar_movimiento_mercaderia():
    """Registro unificado: stock_actual + lógica fiscal"""
    limpiar_pantalla()
    sku = input("Ingrese SKU para movimiento: ").strip().upper()
    if sku in ["", "0"]: return

    print("\n1. 📥 INGRESO (Compra) | 2. 📤 EGRESO (Venta/Hogar)")
    op_mov = input("Seleccione: ")

    with obtener_conexion() as conn:
        cursor = conn.cursor()
        
        if op_mov == "1":
            print("\n1. Boleta | 2. Factura")
            t_doc = "Factura" if input("Seleccione: ") == "2" else "Boleta"
            try:
                cant = int(input(f"Cantidad a INGRESAR: "))
                cursor.execute("UPDATE maestro SET tipo_documento = ? WHERE sku = ?", (t_doc, sku))
                cursor.execute("UPDATE inventario SET stock_actual = stock_actual + ? WHERE sku = ?", (cant, sku))
                conn.commit()
                print(f"✅ {cant} unidades ingresadas como {t_doc}.")
            except ValueError: print("❌ Error: Número inválido.")

        elif op_mov == "2":
            print("\n1. VENTA | 2. USO HOGAR")
            destino = "Hogar" if input("Seleccione: ") == "2" else "Venta"
            try:
                cant = int(input(f"Cantidad que SALE: "))
                cursor.execute("UPDATE inventario SET stock_actual = stock_actual - ? WHERE sku = ?", (cant, sku))
                conn.commit()
                print(f"✅ {cant} unidades descontadas para {destino}.")
            except ValueError: print("❌ Error: Número inválido.")
    pausar()

def busqueda_rapida():
    """Búsqueda de productos por nombre o SKU"""
    while True:
        limpiar_pantalla()
        print("🔍 BÚSQUEDA RÁPIDA (0 para volver)")
        imprimir_separador()
        termino = input("PRODUCTO / SKU: ").strip().lower()
        if termino in ["", "0"]: break
        
        with obtener_conexion() as conn:
            cursor = conn.cursor()
            q = """SELECT i.sku, m.producto, i.stock_actual, m.precio_venta 
                   FROM inventario i JOIN maestro m ON i.sku = m.sku 
                   WHERE LOWER(m.producto) LIKE ? OR LOWER(i.sku) LIKE ?"""
            cursor.execute(q, (f'%{termino}%', f'%{termino}%'))
            res = cursor.fetchall()
            if res:
                for r in res: print(f"{r[0]:12} | {r[1][:30]:30} | {r[2]:4} un | ${r[3]:,.0f}")
            else: print("❌ Sin coincidencias.")
        pausar()

def generar_lista_compras():
    """Reporte de stock crítico para reposición"""
    limpiar_pantalla()
    print("🛒 SUGERENCIA DE REPOSICIÓN (Stock <= 1)")
    imprimir_separador()
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        query = """SELECT i.sku, m.producto, i.stock_actual, m.costo_neto 
                   FROM inventario i JOIN maestro m ON i.sku = m.sku 
                   WHERE i.stock_actual <= 1"""
        cursor.execute(query)
        faltantes = cursor.fetchall()
        for f in faltantes:
            print(f"📦 [{f[0]:8}] {f[1][:30]:30} | STOCK: {f[2]} | COSTO REF: ${f[3]:,.0f}")
    pausar()



# --- 3. INTELIGENCIA Y REPORTES ---

def tablero_estrategico():
    """Vista general de valorización y rentabilidad"""
    limpiar_pantalla()
    with obtener_conexion() as conn:
        total = conn.execute("SELECT SUM(i.stock_actual * m.costo_neto) FROM inventario i JOIN maestro m ON i.sku = m.sku").fetchone()[0] or 0
        print(f"💰 VALOR TOTAL BODEGA: ${total:,.0f}")
        
    # Ajuste de anchos para incluir SKU (12 chars)
    # Anchos: SKU(12) + Prod(30) + Marg(8) + Estado(20) + Stock(15) + separadores
    linea_sep = "=" * 95
    print(linea_sep)
    print(f"{'SKU':12} | {'PRODUCTO':30} | {'MARGEN':8} | {'ESTADO':20} | {'STOCK'}")
    print(linea_sep)
    
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.sku, m.producto, IFNULL(m.margen, 0), i.stock_actual, IFNULL(m.comp_max, 10) 
            FROM maestro m JOIN inventario i ON m.sku = i.sku 
            WHERE m.producto IS NOT NULL AND m.producto NOT IN ('', ' ', 'General')
            ORDER BY m.margen DESC
        """)
        for r in cursor.fetchall():
            sku, nom, marg, actual, m_max = r
            t_margen = obtener_termometro_rentabilidad(marg)
            t_stock = obtener_termometro_stock(actual, m_max)
            # Acortamos las etiquetas para que quepan en el nuevo ancho
            t_margen_corto = t_margen.replace("MAX ENGAGEMENT - ", "") 
            
            print(f"{sku:12} | {nom[:28]:30} | {marg*100:6.1f}% | {t_margen_corto:20} | {t_stock}")
    
    print(linea_sep)
    pausar()

def obtener_termometro_rentabilidad(margen):
    try:
        m = float(margen)
        if m < 0.05: return "🟤 [ZONA PÉRDIDA]"
        if m < 0.14: return "🔴 [SOBREVIVENCIA]"
        if m < 0.22: return "🟡 [ZONA NEUTRA]"
        if m < 0.28: return "🟢 [SALUDABLE]"
        return "🟣 [ILLIDARI]"
    except: return "⚪ [SIN DATOS]"

def obtener_termometro_stock(actual, maximo):
    try:
        pct = (float(actual) / (float(maximo) or 1)) * 100
        if actual <= 0: return "🟤 [QUIEBRE]"
        if pct <= 25: return "🔴 [CRÍTICO]"
        if pct <= 60: return "🟡 [REVISAR]"
        if pct <= 100: return "🟢 [ÓPTIMO]"
        return "🔵 [SOBRESTOCK]"
    except: return "⚪ [ERROR]"

# --- 4. CENTRO ADMINISTRATIVO ---

def ver_inventario_completo():
    """Muestra la tabla de inventario pura"""
    limpiar_pantalla()
    print("📦 LISTADO COMPLETO DE EXISTENCIAS")
    linea = "-" * 70
    print(linea)
    print(f"{'SKU':15} | {'PRODUCTO':35} | {'STOCK ACTUAL'}")
    print(linea)
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.sku, m.producto, i.stock_actual 
            FROM inventario i 
            JOIN maestro m ON i.sku = m.sku
            ORDER BY i.sku ASC
        """)
        for r in cursor.fetchall():
            print(f"{r[0]:15} | {r[1][:33]:35} | {r[2]:4} unidades")
    print(linea)
    pausar()

def modulo_administracion():
    limpiar_pantalla()
    print("⚙️ MÓDULO ADMINISTRATIVO\n1. Ver Inventario\n2. Editor Maestro\n3. Backups\n0. Volver")
    op = input("\nSeleccione: ")
    
    if op == "1":
        ver_inventario_completo()

    if op == "2":
        limpiar_pantalla()
        sku = input("Ingrese SKU para bautismo/edición (0 para volver): ").strip().upper()
        if sku in ["", "0"]: 
                return
            with obtener_conexion() as conn:
                cursor = conn.cursor()
                # Buscamos si ya existe en el maestro
                cursor.execute("SELECT producto, costo_neto, precio_venta FROM maestro WHERE sku = ?", (sku,))
                existe = cursor.fetchone()
                
                if existe:
                    print(f"\n📝 PRODUCTO ENCONTRADO: {existe[0]}")
                    print(f"Costo actual: ${existe[1]:,.0f} | Venta: ${existe[2]:,.0f}")
                    print("-" * 30)
                    print("1. Cambiar Origen Fiscal (Boleta/Factura)")
                    print("2. Actualizar Costo/Venta")
                    sub_op = input("Seleccione: ")
                    
                    if sub_op == "1":
                        fisc = "Factura" if input("Tipo (1: Bol / 2: Fac): ") == "2" else "Boleta"
                        cursor.execute("UPDATE maestro SET tipo_documento = ? WHERE sku = ?", (fisc, sku))
                        print("✅ Origen fiscal actualizado.")
                    elif sub_op == "2":
                        c = float(input("Nuevo Costo Neto: ") or existe[1])
                        v = float(input("Nuevo Precio Venta: ") or existe[2])
                        m = (v - c) / v if v > 0 else 0
                        cursor.execute("UPDATE maestro SET costo_neto = ?, precio_venta = ?, margen = ? WHERE sku = ?", (c, v, m, sku))
                        print("✅ Valores actualizados.")
                
                else:
                    print("\n✨ DETECTADO COMO PRODUCTO NUEVO")
                    nom = input("Nombre Producto: ")
                    c = float(input("Costo Neto: ") or 0)
                    v = float(input("Precio Venta: ") or 0)
                    fisc = "Factura" if input("Tipo (1: Bol / 2: Fac): ") == "2" else "Boleta"
                    m = (v - c) / v if v > 0 else 0
                    
                    # Insertar en Maestro (Aquí va el margen y datos base)
                    cursor.execute("""INSERT INTO maestro (sku, producto, costo_neto, precio_venta, margen, tipo_documento, comp_max) 
                                   VALUES (?,?,?,?,?,?,?)""", (sku, nom, c, v, m, fisc, 10))
                    
                    # Insertar en Inventario (Solo stock y SKUs, sin comp_max aquí)
                    cursor.execute("INSERT INTO inventario (sku, stock_actual) VALUES (?, 0)", (sku,))
                    print(f"✅ {nom} bautizado e ingresado a inventario con stock 0.")
                
                conn.commit()
        pausar()

    elif op == "3":
        ejecutar_backup(forzar=True)
        pausar()

def ejecutar_backup(forzar=False):
    fecha = datetime.now().strftime("%Y%m%d")
    archivo_bak = f"vts_backup_{fecha}.db.bak"
    try:
        if not os.path.exists(archivo_bak) or forzar:
            shutil.copy2(DB_NAME, archivo_bak)
            print(f"✅ Respaldo: {archivo_bak}")
    except Exception as e: print(f"⚠️ Error backup: {e}")