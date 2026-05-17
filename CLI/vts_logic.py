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

def sanear_base_datos():
    """Limpia inconsistencias, espacios en blanco y errores de duplicidad"""
    limpiar_pantalla()
    print("🧹 INICIANDO SANEAMIENTO DE BASE DE DATOS...")
    
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        try:
            # 1. Quitar espacios y estandarizar a Mayúsculas
            cursor.execute("UPDATE maestro SET sku = UPPER(TRIM(sku))")
            cursor.execute("UPDATE inventario SET sku = UPPER(TRIM(sku))")
            
            # 2. Eliminar posibles duplicados (si existen por error de espacios)
            # Esto es preventivo para asegurar integridad
            print("🔄 Normalizando índices de SKU...")
            
            # 3. Verificar si el stock de V-LIM-003 está "atrapado"
            cursor.execute("SELECT stock_actual FROM inventario WHERE sku = 'V-LIM-003'")
            res = cursor.fetchone()
            print(f"📍 Estado actual V-LIM-003 en DB: {res[0] if res else 'No encontrado'}")
            
            conn.commit()
            print("\n✅ SANEAMIENTO COMPLETADO: SKUs normalizados.")
        except Exception as e:
            print(f"❌ Error durante saneamiento: {e}")
            conn.rollback()
    pausar()

def ver_log_movimientos():

    """Visualizador de la tabla historial (Opción 6.5)"""
    limpiar_pantalla()
    print("📜 LOG DE MOVIMIENTOS (Trazabilidad)")
    imprimir_separador()
    print(f"{'FECHA':16} | {'SKU':12} | {'TIPO':8} | {'CANT':4} | {'MOTIVO'}")
    imprimir_separador()
    
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        # Mostramos los últimos 20 movimientos
        cursor.execute("SELECT fecha, sku, tipo, cantidad, motivo FROM historial ORDER BY id DESC LIMIT 20")
        for r in cursor.fetchall():
            print(f"{r[0]:16} | {r[1]:12} | {r[2]:8} | {r[3]:4} | {r[4]}")
    
    imprimir_separador()
    pausar()
# --- 2. GESTIÓN OPERATIVA ---

def registrar_movimiento_mercaderia():
    """Registro unificado: Ingresos y 4 tipos de Egreso con Log"""
    limpiar_pantalla()
    sku_input = input("Ingrese SKU para movimiento: ").strip().upper()
    if sku_input in ["", "0"]: return

    with obtener_conexion() as conn:
        cursor = conn.cursor()
        # Verificamos existencia y traemos nombre para el feedback
        cursor.execute("SELECT i.sku, i.stock_actual, m.producto FROM inventario i JOIN maestro m ON i.sku = m.sku WHERE i.sku = ?", (sku_input,))
        res = cursor.fetchone()
        
        if not res:
            print(f"❌ Error: El SKU [{sku_input}] no existe.")
            pausar(); return

        sku_db, stock_actual, nombre = res
        print(f"\n📦 PRODUCTO: {nombre}")
        print(f"📊 STOCK ACTUAL: {stock_actual}")
        imprimir_separador()
        
        print("1. 📥 INGRESO (Compra/Reposición)")
        print("2. 📤 EGRESO (Retiro de Inventario)")
        op_principal = input("\nSeleccione operación: ")

        try:
            if op_principal == "1":
                cant = int(input("Cantidad a INGRESAR: "))
                motivo = "Compra/Reposición"
                tipo_log = "INGRESO"
                nueva_cant = stock_actual + cant
            
            elif op_principal == "2":
                print("\n--- SELECCIONE MOTIVO DE RETIRO ---")
                print("1. VENTA")
                print("2. APORTE HOGAR")
                print("3. GARANTÍA")
                print("4. AJUSTE MANUAL")
                m_op = input("Seleccione (1-4): ")
                
                # Mapeo exacto de tus 4 retiros
                mapa_motivos = {
                    "1": "Venta",
                    "2": "Aporte Hogar",
                    "3": "Garantia",
                    "4": "Ajuste Manual"
                }
                motivo = mapa_motivos.get(m_op, "Otros")
                cant = int(input(f"Cantidad para {motivo.upper()}: "))
                tipo_log = "EGRESO"
                nueva_cant = stock_actual - cant
            else: return

            # --- EJECUCIÓN ATÓMICA ---
            fecha_log = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # 1. Actualizar Inventario
            cursor.execute("UPDATE inventario SET stock_actual = ? WHERE sku = ?", (nueva_cant, sku_db))
            
            # 2. Registrar en Historial
            cursor.execute("""
                INSERT INTO historial (fecha, sku, tipo, cantidad, motivo) 
                VALUES (?, ?, ?, ?, ?)
            """, (fecha_log, sku_db, tipo_log, cant, motivo))
            
            conn.commit()
            print(f"\n✅ CONSOLIDADO: {motivo} de {cant} unidades.")
            print(f"🔍 Nuevo Stock en DB: {nueva_cant}")

        except ValueError:
            print("❌ Error: Ingrese un número válido.")
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

def purgar_base_datos():
    """Elimina tablas y reconstruye estructura (Doble Confirmación)"""
    limpiar_pantalla()
    print("⚠️  ADVERTENCIA: ESTÁS POR BORRAR TODO EL INVENTARIO ⚠️")
    print("Esta acción es irreversible.")
    
    confirm1 = input("\n¿Está seguro? (Presione ENTER para continuar o 'N' para cancelar): ")
    if confirm1.lower() == 'n': return

    confirm2 = input("Escriba 'BORRAR TODO' para confirmar la destrucción: ")
    
    if confirm2 == "BORRAR TODO":
        try:
            with obtener_conexion() as conn:
                conn.execute("DROP TABLE IF EXISTS maestro")
                conn.execute("DROP TABLE IF EXISTS inventario")
                conn.execute("DROP TABLE IF EXISTS historial")
                # Aquí llamarías a tu función de inicialización de tablas si la tienes
            print("\n🔥 Base de datos purgada. El sistema se reiniciará limpio.")
            os._exit(0) # Forzamos salida para que al volver a abrir se creen tablas nuevas
        except Exception as e:
            print(f"❌ Error en la purga: {e}")
    else:
        print("\n✅ Purga cancelada. No se tocó nada.")
    pausar()

# --- 3. INTELIGENCIA Y REPORTES ---

def tablero_estrategico():
    """Vista general de valorización y rentabilidad"""
    limpiar_pantalla()
    with obtener_conexion() as conn:
        total = conn.execute("SELECT SUM(i.stock_actual * m.costo_neto) FROM inventario i JOIN maestro m ON i.sku = m.sku").fetchone()[0] or 0
        print(f"💰 VALOR TOTAL BODEGA: ${total:,.0f}.- NETO")
        
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

def calculadora_packs():
    """Lógica para calcular precio por pack (3 un, 6 un, etc.)"""
    limpiar_pantalla()
    print("🧮 CALCULADORA DE PACKS")
    try:
        precio_un = float(input("Precio unitario: $") or 0)
        cant = int(input("Cantidad del pack: ") or 1)
        descto = float(input("Porcentaje descuento (ej: 10): ") or 0) / 100
        
        total = (precio_un * cant) * (1 - descto)
        print(f"\n💰 PRECIO PACK: ${total:,.0f}")
        print(f"📉 AHORRO TOTAL: ${(precio_un * cant) - total:,.0f}")
    except ValueError:
        print("❌ Error: Datos inválidos.")
    pausar()

# --- 4. CENTRO ADMINISTRATIVO ---

def ver_inventario_completo():
    limpiar_pantalla()
    print("📦 LISTADO COMPLETO DE EXISTENCIAS")
    linea = "-" * 85 # Ampliamos la línea
    print(linea)
    print(f"{'SKU':15} | {'PRODUCTO':35} | {'STOCK'} | {'ESTADO'}")
    print(linea)
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.sku, m.producto, i.stock_actual, m.comp_max 
            FROM inventario i JOIN maestro m ON i.sku = m.sku
            ORDER BY i.sku ASC
        """)
        for r in cursor.fetchall():
            term = obtener_termometro_stock(r[2], r[3])
            print(f"{r[0]:15} | {r[1][:33]:35} | {r[2]:5} | {term}")
    print(linea)
    pausar()

def modulo_administracion():
    limpiar_pantalla()
    print("⚙️ MÓDULO ADMINISTRATIVO\n1. Ver Inventario\n2. Editor Maestro\n3. Backups\n4. Saneamiento DB\n5. Ver Log de Movimientos\n0. Volver")
    op = input("\nSeleccione: ")
    
    if op == "1":
        ver_inventario_completo()

    elif op == "2": # Cambiado a elif para mejor flujo
        limpiar_pantalla()
        sku = input("Ingrese SKU (0 para volver): ").strip().upper()
        if sku in ["", "0"]: 
            return
            
        with obtener_conexion() as conn:
            cursor = conn.cursor()
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
                
                cursor.execute("""INSERT INTO maestro (sku, producto, costo_neto, precio_venta, margen, tipo_documento, comp_max) 
                               VALUES (?,?,?,?,?,?,?)""", (sku, nom, c, v, m, fisc, 10))
                cursor.execute("INSERT INTO inventario (sku, stock_actual) VALUES (?, 0)", (sku,))
                print(f"✅ {nom} bautizado e ingresado a inventario con stock 0.")
            
            conn.commit()
        pausar()

    if op == "3":
        ejecutar_backup(forzar=True)
        pausar()

    if op == "4":
        sanear_base_datos()

    elif op == "5":
        ver_log_movimientos()

def ejecutar_backup(forzar=False):
    fecha = datetime.now().strftime("%Y%m%d")
    archivo_bak = f"vts_backup_{fecha}.db.bak"
    try:
        if not os.path.exists(archivo_bak) or forzar:
            shutil.copy2(DB_NAME, archivo_bak)
            print(f"✅ Respaldo: {archivo_bak}")
    except Exception as e: print(f"⚠️ Error backup: {e}")

def ver_historial_movimientos():
    limpiar_pantalla()
    print("📜 HISTORIAL RECIENTE DE MOVIMIENTOS")
    print("-" * 80)
    print(f"{'FECHA':16} | {'SKU':12} | {'TIPO':8} | {'CANT':4} | {'MOTIVO'}")
    print("-" * 80)
    
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT fecha, sku, tipo, cantidad, motivo FROM historial ORDER BY id DESC LIMIT 15")
        for r in cursor.fetchall():
            print(f"{r[0]:16} | {r[1]:12} | {r[2]:8} | {r[3]:4} | {r[4]}")
    print("-" * 80)
    pausar()