# vts_logic
import os
import sqlite3
import pandas as pd
from datetime import datetime
from vts_utils import limpiar_pantalla, pausar, imprimir_separador

# --- 0. CONFIGURACIÓN Y CONEXIÓN ---
DB_NAME = "vts_mardum.db"

def obtener_conexion():
    """Utilidad interna para conectar a la DB"""
    return sqlite3.connect(DB_NAME)

# --- 1. UTILIDADES ADMINISTRATIVAS (Ex-Cloud Bridge) ---

def generar_plantilla_auditoria():
    """Genera el CSV maestro basado en la DB actual para conteo físico"""
    limpiar_pantalla()
    print("📝 GENERANDO PLANTILLA DE AUDITORÍA...")
    try:
        with obtener_conexion() as conn:
            query = """
                SELECT i.sku, i.funcion as producto, m.Seccion, i.subtotal as stock_sistema 
                FROM inventario i
                JOIN maestro m ON i.sku = m.sku
            """
            df = pd.read_sql_query(query, conn)
        
        df['inventario_real'] = "" 
        df['nuevo_costo'] = "" 
        
        filename = f"AUDITORIA_VTS_{datetime.now().strftime('%d_%m')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n✅ ¡ARCHIVO CREADO!: {filename}")
        print("📊 Instrucciones: Llena la columna 'inventario_real' y guarda.")
    except Exception as e:
        print(f"❌ Error al exportar: {e}")

def sincronizar_auditoria_csv(archivo_csv):
    """Sincronización robusta: CSV -> SQL Engine"""
    limpiar_pantalla()
    print(f"📥 INICIANDO SINCRONIZACIÓN: {archivo_csv}")
    imprimir_separador()
    
    try:
        df_real = pd.read_csv(archivo_csv)
        df_real = df_real[df_real['inventario_real'].notnull()]

        with obtener_conexion() as conn:
            cursor = conn.cursor()
            for _, fila in df_real.iterrows():
                sku = str(fila['sku']).upper().strip()
                stock_fisico = int(fila['inventario_real'])
                costo = fila['nuevo_costo'] if pd.notnull(fila['nuevo_costo']) and fila['nuevo_costo'] != "" else None

                cursor.execute("SELECT sku FROM inventario WHERE sku = ?", (sku,))
                if cursor.fetchone():
                    cursor.execute("UPDATE inventario SET stock_actual = ?, subtotal = ? WHERE sku = ?", 
                                 (stock_fisico, stock_fisico, sku))
                    if costo is not None:
                        cursor.execute("UPDATE maestro SET costo_neto = ? WHERE sku = ?", (costo, sku))
                    print(f"✅ SKU {sku:12} | SINCRONIZADO")
                else:
                    nombre = fila['producto'] if 'producto' in fila else f"NUEVO ({sku})"
                    cursor.execute("""
                        INSERT INTO maestro (sku, producto, costo_neto, precio_venta, margen, Seccion) 
                        VALUES (?, ?, ?, 0, 0, 'General')""", 
                        (sku, nombre, costo if costo else 0))
                    cursor.execute("""
                        INSERT INTO inventario (sku, funcion, stock_actual, aporte_hogar, subtotal) 
                        VALUES (?, ?, ?, 0, ?)""", 
                        (sku, nombre, stock_fisico, stock_fisico))
                    print(f"✨ SKU {sku:12} | CREADO")
            conn.commit()
            print("\n⚖️ SINCRONIZACIÓN FINALIZADA CON ÉXITO.")
    except Exception as e:
        print(f"🔥 ERROR EN CARGA: {e}")
    pausar()

def ejecutar_bautismo_sql():
    """Mapeo masivo basado en prefijos de SKU Vacadari"""
    mapeo = {
        'V-LIM': 'Limpieza', 'V-ELE': 'Electronica', 'V-BOU': 'Boutique',
        'V-BAN': 'Bano', 'V-MEN': 'Menaje', 'V-LIB': 'Libreria', 'V-ABA': 'Abarrotes'
    }
    try:
        with obtener_conexion() as conn:
            cursor = conn.cursor()
            for prefijo, nombre in mapeo.items():
                cursor.execute("UPDATE maestro SET Seccion = ? WHERE sku LIKE ?", (nombre, f"{prefijo}%"))
            conn.commit()
        print("✅ Bautismo Masivo completado.")
    except Exception as e:
        print(f"❌ Error en Bautismo: {e}")

# --- 2. GESTIÓN OPERATIVA ---

def registrar_entrada():
    limpiar_pantalla(); imprimir_separador()
    print("📦 REGISTRO DE ENTRADA / INGRESO DE STOCK")
    sku = input("Ingrese SKU: ").strip().upper()
    if sku in ["", "0"]: return

    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT funcion, subtotal FROM inventario WHERE sku = ?", (sku,))
        res = cursor.fetchone()
        if res:
            print(f"Producto: {res[0]} | Stock actual: {res[1]}")
            try:
                cantidad = int(input("Cantidad a INGRESAR: "))
                cursor.execute("UPDATE inventario SET subtotal = subtotal + ? WHERE sku = ?", (cantidad, sku))
                conn.commit()
                print(f"✅ Stock actualizado.")
            except: print("❌ Cantidad inválida.")
        else:
            print("⚠️ SKU no existe. Créalo en la Opción 7.")
    pausar()

def modulo_egreso():
    while True:
        limpiar_pantalla(); imprimir_separador()
        print("📦 MÓDULO DE EGRESO DE MERCADERÍA")
        print(" 1. Venta\n 2. Aporte Hogar\n 3. Anular Salida\n 0. Volver")
        op = input("Seleccione: ")
        if op == "0": break
        sku = input("SKU: ").strip().upper()
        try:
            cant = int(input("Cantidad: "))
            with obtener_conexion() as conn:
                cursor = conn.cursor()
                if op == "1":
                    cursor.execute("UPDATE inventario SET subtotal = subtotal - ? WHERE sku = ?", (cant, sku))
                elif op == "2":
                    cursor.execute("UPDATE inventario SET subtotal = subtotal - ?, aporte_hogar = aporte_hogar + ? WHERE sku = ?", (cant, cant, sku))
                elif op == "3":
                    cursor.execute("UPDATE inventario SET subtotal = subtotal + ? WHERE sku = ?", (cant, sku))
                conn.commit()
                print("✅ Procesado.")
        except: print("❌ Error de datos."); pausar()

# --- 3. INTELIGENCIA Y REPORTES ---

def busqueda_rapida():
    while True:
        limpiar_pantalla(); imprimir_separador()
        print("🔍 BÚSQUEDA RÁPIDA SQL (0 para volver)")
        termino = input("PRODUCTO / SKU: ").strip().lower()
        if termino in ["", "0"]: break
        with obtener_conexion() as conn:
            cursor = conn.cursor()
            q = "SELECT i.sku, i.funcion, i.subtotal, m.precio_venta FROM inventario i JOIN maestro m ON i.sku = m.sku WHERE LOWER(i.funcion) LIKE ? OR LOWER(i.sku) LIKE ?"
            cursor.execute(q, (f'%{termino}%', f'%{termino}%'))
            res = cursor.fetchall()
            if res:
                for r in res: print(f"{r[0]:12} | {r[1][:30]:30} | {r[2]:4} un | ${r[3]:,.0f}")
            else: print("❌ Sin coincidencias.")
        pausar()

def tablero_estrategico():
    limpiar_pantalla()
    # 1. Primero la Valorización (Cabecera rápida)
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        query_val = "SELECT SUM(i.subtotal * m.costo_neto) FROM inventario i JOIN maestro m ON i.sku = m.sku"
        total = cursor.execute(query_val).fetchone()[0] or 0
        print(f"💰 VALOR TOTAL BODEGA: ${total:,.0f}")
        imprimir_separador()

    # 2. Luego el Tablero
    print(f"{'PRODUCTO':35} | {'MARGEN':7} | {'ESTRATEGIA'}")
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT producto, margen, precio_venta, comp_min, comp_max FROM maestro ORDER BY margen DESC")
        for r in cursor.fetchall():
            decision = obtener_decision_ejecutiva(r[1], r[2], r[3], r[4])
            print(f"{r[0][:33]:35} | {r[1]*100:6.1f}% | {decision}")
    pausar()

def obtener_decision_ejecutiva(margen, precio, comp_min, comp_max):
    try:
        m, p = float(margen), float(precio)
        s3 = float(comp_min) if comp_min else p
        u3 = float(comp_max) if comp_max else p
        if m >= 0.2801: return "🔥 SUPER GANCHO" if p < s3 else "🟢 MARGEN META"
        if m < 0.1401: return "🔴 DESCARTE" if p > u3 else "🟡 MARGEN BAJO"
        return "Decisión Estándar"
    except: return "Error Datos"

def valorizar_inventario(df_i=None, df_m=None):
    limpiar_pantalla(); print("💰 AUDITORÍA DE VALORIZACIÓN SQL")
    imprimir_separador()
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        query = "SELECT SUM(i.subtotal * m.costo_neto), SUM(i.aporte_hogar) FROM inventario i JOIN maestro m ON i.sku = m.sku"
        cursor.execute(query)
        activos, hogar = cursor.fetchone()
        print(f"VALOR TOTAL BODEGA: ${ (activos if activos else 0):,.0f}")
        print(f"CONSUMO INTERNO:   { (hogar if hogar else 0) } un.")
    pausar()

def ver_super_ganchos(df_m=None):
    limpiar_pantalla(); print("🔥 SUPER GANCHOS DETECTADOS")
    imprimir_separador()
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT producto, precio_venta FROM maestro WHERE margen >= 0.2801 AND precio_venta < comp_min")
        ganchos = cursor.fetchall()
        for g in ganchos: print(f"⭐ {g[0][:30]:30} | ${g[1]:,.0f}")
    pausar()

def generar_lista_compras():
    limpiar_pantalla(); print("🛒 SUGERENCIA DE REPOSICIÓN (Stock <= 1)")
    imprimir_separador()
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        query = """SELECT i.sku, i.funcion, i.subtotal, m.costo_neto, m.margen, m.precio_venta, m.comp_min, m.comp_max 
                   FROM inventario i JOIN maestro m ON i.sku = m.sku WHERE i.subtotal <= 1"""
        cursor.execute(query)
        faltantes = cursor.fetchall()
        for f in faltantes:
            dec = obtener_decision_ejecutiva(f[4], f[5], f[6], f[7])
            print(f"[{f[0]:8}] {f[1][:25]:25} | {f[2]:2} un | {dec}")
    pausar()

# --- 4. CENTRO ADMINISTRATIVO ---

def modulo_administracion():
    while True:
        limpiar_pantalla(); imprimir_separador()
        print("🛠️  CENTRO DE COMANDO ADMINISTRATIVO VTS 🐮")
        print(" 1. ☁️  BRIDGE (Sincronizar CSV)\n 2. 📝 EDITOR (Maestro)\n 3. 🏷️  BAUTISMO (Secciones)\n 4. 🗃️  PLANTILLA (CSV)\n 0. Volver")
        op = input("VTS_ADMIN > ")
        if op == "0": break

        if op == "1":
            arch = input("Archivo [Enter para AUDITORIA_VTS.csv]: ") or "AUDITORIA_VTS.csv"
            if os.path.exists(arch): sincronizar_auditoria_csv(arch)
            else: print("❌ No encontrado."); pausar()
        
        if op == "2": # EL EDITOR MAESTRO ESTÁ AQUÍ
            limpiar_pantalla()
            print("📝 EDITOR MAESTRO (Presione ENTER o 0 para cancelar)")
            sku = input("Ingrese SKU: ").strip().upper()
            
            if sku in ["", "0"]: # <-- ESTE ES TU BOTÓN DE ESCAPE
                continue 

            with obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT producto, costo_neto, precio_venta FROM maestro WHERE sku = ?", (sku,))
                res = cursor.fetchone()
                
                if res:
                    print(f"Editando: {res[0]}")
                    nc = input(f"Nuevo Costo ({res[1]}): ") or res[1]
                    nv = input(f"Nuevo Venta ({res[2]}): ") or res[2]
                    cursor.execute("UPDATE maestro SET costo_neto = ?, precio_venta = ? WHERE sku = ?", (nc, nv, sku))
                    conn.commit()
                    print("✅ Actualizado.")
                else:
                    print("✨ REGISTRANDO SKU NUEVO")
                    nom = input("Nombre: ")
                    if nom == "": continue
                    c = float(input("Costo: ") or 0)
                    v = float(input("Venta: ") or 0)
                    cursor.execute("INSERT INTO maestro (sku, producto, costo_neto, precio_venta, Seccion) VALUES (?,?,?,?,'General')", (sku, nom, c, v))
                    cursor.execute("INSERT INTO inventario (sku, funcion, stock_actual, subtotal) VALUES (?,?,0,0)", (sku, nom))
                    conn.commit()
                    print("✅ Creado con éxito.")
            pausar()

        elif op == "3":
            if input("¿Ejecutar Bautismo? (s/n): ").lower() == 's': ejecutar_bautismo_sql()
            pausar()

        elif op == "4":
            generar_plantilla_auditoria(); pausar()

# --- 5. EXPORTACIÓN Y OTROS ---

def exportar_datos(df_i_ignorado=None):
    limpiar_pantalla()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"VTS_SQL_EXPORT_{timestamp}.txt"
    with obtener_conexion() as conn:
        df = pd.read_sql_query("SELECT * FROM inventario", conn)
        df.to_csv(filename, sep='\t', index=False)
    print(f"✅ EXPORTADO: {filename}"); pausar()

def verificar_integridad_base():
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sku FROM maestro EXCEPT SELECT sku FROM inventario")
        faltan = cursor.fetchall()
        if faltan: print(f"⚠️ Faltan {len(faltan)} SKUs en inventario")

def calculadora_packs():
    limpiar_pantalla(); print("📦 CALCULADORA COMBOS")
    skus = input("SKUS (Separados por coma): ").upper().split(',')
    total = 0
    with obtener_conexion() as conn:
        for s in skus:
            res = conn.execute("SELECT precio_venta FROM maestro WHERE sku=?", (s.strip(),)).fetchone()
            if res: total += res[0]
    print(f"\nTOTAL: ${total:,.0f} | COMBO (-10%): ${total*0.9:,.0f}"); pausar()