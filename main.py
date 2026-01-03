import pandas as pd
import os
from datetime import datetime
import time

# CONFIGURACIÓN DE SEGURIDAD
MASTER_FILE = "data_s.csv"
INV_FILE = "data_v.csv"
BACKUP_FILE = "sync_backup.txt"

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("     🐮 VTS 🐮     ")
    print("  [======|======> <======|======]")
    print("-" * 40)

def verificar_conexion():
    return os.path.exists(MASTER_FILE) and os.path.exists(INV_FILE)

# --- FUNCIONES DE LÓGICA (Se mantienen igual, solo una versión de cada una) ---

def obtener_decision_ejecutiva(margen, precio, comp_min, comp_max):
    try:
        m, p = float(margen), float(precio)
        s3 = float(comp_min) if pd.notnull(comp_min) and comp_min != 0 else p
        u3 = float(comp_max) if pd.notnull(comp_max) and comp_max != 0 else p
    except: return "Faltan Datos"

    if m >= 0.2801:
        if p < s3: return "🔥 SUPER GANCHO"
        return "🟢 MARGEN META" if p <= u3 else "⚠️ ALTO MARGEN"
    elif m < 0.1401:
        if p < s3: return "🟡 MARGEN BAJO"
        return "🔴 DESCARTE" if p > u3 else "Decisión Estándar"
    return "Decisión Estándar"

def limpiar_precio(valor):
    """Limpia formatos de Excel: '$', '.', ' ' y los vuelve flotantes"""
    if pd.isnull(valor): return 0.0
    # Si ya es un número, lo devolvemos tal cual
    if isinstance(valor, (int, float)): return float(valor)
    
    # Si es texto (ej: '$ 1.250'), operamos:
    limpio = str(valor).replace('$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(limpio)
    except:
        return 0.0

def verificar_integridad_base(df_i, df_m):
    # Buscamos SKUs que están en el maestro pero no en el inventario local
    faltantes = df_m[~df_m['SKU'].isin(df_i['SKU'])]
    if not faltantes.empty:
        print(f"\n⚠️  AVISO DE INTEGRIDAD: Hay {len(faltantes)} productos nuevos en el Maestro")
        print("   que no han sido inicializados en el Inventario local.")
        print(f"   Ejemplo: {faltantes.iloc[0]['PRODUCTO']} ({faltantes.iloc[0]['SKU']})")
        print("-" * 50)
        return True
    return False

def busqueda_rapida(df_i, df_m):
    limpiar_pantalla()
    print("🔍 BÚSQUEDA RÁPIDA (TERMINAL VTS)")
    query = input("INGRESE NOMBRE O SKU: ").upper()
    
    # Cruce de datos: Inventario + Precios del Maestro
    df_res = pd.merge(df_i, df_m[['SKU', 'PRECIO VENTA FINAL (CON IVA)']], on='SKU', how='left')
    
    resultado = df_res[df_res['Funcion'].str.contains(query, na=False, case=False) | 
                       df_res['SKU'].str.contains(query, na=False, case=False)]

    if not resultado.empty:
        print("\n" + "="*50)
        for _, r in resultado.iterrows():
            print(f"PRODUCTO: {r['Funcion']}")
            print(f"SKU:      {r['SKU']}")
            print(f"STOCK DISP: {r['Subtotal']}")
            print(f"VENTA (IVA): ${r['PRECIO VENTA FINAL (CON IVA)']:,.0f}")
            print("-" * 20)
    else:
        print("\n❌ NO SE ENCONTRARON COINCIDENCIAS.")
    input("\nENTER PARA VOLVER...")

def registrar_aporte_hogar(df_i):
    limpiar_pantalla()
    print("🏠 REGISTRO DE APORTE HOGAR")
    sku = input("INGRESE SKU DEL PRODUCTO: ").upper()
    
    if sku in df_i['SKU'].values:
        try:
            cantidad = int(input(f"CANTIDAD PARA CONSUMO INTERNO: "))
            idx = df_i.index[df_i['SKU'] == sku].tolist()[0]
            
            # Lógica contable: Suma al gasto hogar, resta al disponible
            actual_hogar = float(df_i.at[idx, 'Aporte Hogar']) if pd.notnull(df_i.at[idx, 'Aporte Hogar']) else 0.0
            df_i.at[idx, 'Aporte Hogar'] = actual_hogar + cantidad
            
            # Recalculamos Subtotal
            df_i.at[idx, 'Subtotal'] = df_i.at[idx, 'Inventario actual'] - df_i.at[idx, 'Aporte Hogar']
            
            # Guardado persistente en el CSV local (fuera de Git)
            df_i.to_csv(INV_FILE, index=False)
            print("\n✅ BASE DE DATOS LOCAL ACTUALIZADA.")
        except ValueError:
            print("\n❌ ERROR: INGRESE UN NÚMERO VÁLIDO.")
    else:
        print("\n❌ SKU NO ENCONTRADO.")
    input("\nENTER PARA CONTINUAR...")

def exportar_datos(df_i):
    limpiar_pantalla()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"VTS_EXPORT_{timestamp}.txt"
    with open(filename, "w") as f:
        f.write(f"VTS SYSTEM EXPORT - {timestamp}\n\n")
        f.write(df_i.to_string(index=False))
    print(f"✅ ARCHIVO EXPORTADO: {filename}")
    input("ENTER...")

def valorizar_inventario(df_i, df_m):
    limpiar_pantalla()
    print("💰 AUDITORÍA DE VALORIZACIÓN - VACADARI STORE")
    print("="*50)
    
    # Cruzamos inventario con el costo del maestro
    df_val = pd.merge(df_i, df_m[['SKU', 'COSTO (SIN IVA)']], on='SKU', how='left')
    
    # Cálculo: (Subtotal de unidades que quedan) * (Costo Neto de compra)
    df_val['valor_neto_linea'] = df_val['Subtotal'] * df_val['COSTO (SIN IVA)']
    
    total_activos = df_val['valor_neto_linea'].sum()
    total_hogar_unidades = df_i['Aporte Hogar'].sum()
    
    print(f"RESUMEN DE CAPITAL:")
    print(f"--------------------------------------------------")
    print(f"VALOR TOTAL EN BODEGA (Costo):  ${total_activos:,.0f}")
    print(f"CONSUMO INTERNO (Aporte Hogar): {total_hogar_unidades:.0f} un.")
    print(f"--------------------------------------------------")
    
    # Alerta de stock crítico (productos con 1 o 0 unidades)
    criticos = df_val[df_val['Subtotal'] <= 1][['Funcion', 'Subtotal']]
    if not criticos.empty:
        print("\n⚠️ ALERTA DE REPOSICIÓN (Stock <= 1):")
        for _, r in criticos.iterrows():
            print(f" - {r['Funcion']}: {r['Subtotal']} un.")
            
    input("\nENTER PARA VOLVER AL MENÚ...")

def tablero_estrategico(df_m):
    limpiar_pantalla()
    print("🧠 TABLERO DE DECISIÓN EJECUTIVA (VTS v1.7)")
    print("="*85)
    print(f"{'PRODUCTO':20} | {'MARGEN':7} | {'ESTRATEGIA RECOMENDADA'}")
    print("-" * 85)
    df_m_sorted = df_m.sort_values(by='MARGEN REAL (%)', ascending=False)
    for _, r in df_m_sorted.iterrows():
        decision = obtener_decision_ejecutiva(r.get('MARGEN REAL (%)', 0), 
                                           r.get('PRECIO VENTA FINAL (CON IVA)', 0),
                                           r.get('Minimo competencia', 0), 
                                           r.get('Maximo competencia', 0))
        print(f"{r['PRODUCTO'][:20]:20} | {r.get('MARGEN REAL (%)', 0)*100:6.1f}% | {decision}")
    print("="*85)
    input("\nENTER PARA VOLVER...")

def generar_lista_compras(df_i, df_m):
    limpiar_pantalla()
    print("🛒 SUGERENCIA DE REPOSICIÓN (SMART RESTOCK)")
    print("="*60)
    
    # Unimos para saber qué estamos comprando
    df_repo = pd.merge(df_i, df_m[['SKU', 'COSTO (SIN IVA)']], on='SKU', how='left')
    
    # Definimos el criterio de "Falta": Stock <= 1 (ajustable)
    faltantes = df_repo[df_repo['Subtotal'] <= 1].copy()
    
    if not faltantes.empty:
        print(f"{'PRODUCTO':25} | {'STOCK':7} | {'COSTO REF'}")
        print("-" * 60)
        
        total_estimado = 0
        for _, r in faltantes.iterrows():
            costo = r['COSTO (SIN IVA)'] if pd.notnull(r['COSTO (SIN IVA)']) else 0
            print(f"{r['Funcion'][:25]:25} | {r['Subtotal']:7.0f} | ${costo:,.0f}")
            total_estimado += costo * 5  # Sugerimos comprar al menos 5 para stock
            
        print("-" * 60)
        print(f"💰 INVERSIÓN ESTIMADA (Base 5 un. c/u): ${total_estimado:,.0f}")
        print("💡 Nota: El costo es referencial basado en última compra.")
    else:
        print("✅ TODO EN ORDEN: No hay productos con stock crítico.")
        
    input("\nENTER PARA VOLVER...")

# --- REFACTORIZACIÓN DEL MENÚ (EL CORAZÓN DEL PROBLEMA) ---

def menu():
    conectado = verificar_conexion()
    status = "ONLINE (LOCAL DB)" if conectado else "OFFLINE (EMERGENCIA)"
    df_m, df_i = None, None
    
    if conectado:
        try:
            df_m = pd.read_csv(MASTER_FILE)
            df_i = pd.read_csv(INV_FILE)
            # SUBSIDIO DE FORMATO EXCEL:
            # Limpiamos las columnas críticas del Maestro
            df_m['PRECIO VENTA FINAL (CON IVA)'] = df_m['PRECIO VENTA FINAL (CON IVA)'].apply(limpiar_precio)
            df_m['COSTO (SIN IVA)'] = df_m['COSTO (SIN IVA)'].apply(limpiar_precio)
            df_m['MARGEN REAL (%)'] = df_m['MARGEN REAL (%)'].apply(limpiar_precio)
            verificar_integridad_base(df_i, df_m)
            input("\nPresione ENTER para iniciar sistema...") # Pausa opcional para alcanzar a leer el aviso

        except Exception as e:
            status = f"ERROR DE DATOS: {e}"
            conectado = False

    while True:
        limpiar_pantalla()
        print(f"🐮 VTS v1.7.1 🐮 | STATUS: {status}")
        print("==================================================")
        print("1. 🔍 BÚSQUEDA RÁPIDA (STOCK & PRECIO)")
        print("2. 🏠 REGISTRAR APORTE HOGAR")
        print("3. 📑 EXPORTAR REPORTE (TXT)")
        print("4. 💰 VALORIZACIÓN TOTAL (ACTIVOS)")
        print("5. 🧠 TABLERO ESTRATÉGICO (EXCEL EQ)")
        print("6. 🛒 LISTA DE COMPRAS (PEDIDO)")
        print("7. 🚪 SALIR")
        print("==================================================")
        
        op = input("VTS_INPUT > ") 
        
        # Validación de salida inmediata
        if op == "7":
            if conectado:
                # Generamos un backup rápido en TXT antes de irnos
                with open(BACKUP_FILE, "w") as f:
                    f.write(f"RESPALDO DE SEGURIDAD - {datetime.now()}\n")
                    f.write(df_i.to_string(index=False))
            print("Cerrando Terminal VTS 🐮... ¡Buen turno!")
            break
        
        # Validación de Modo Online
        if not conectado and op in ["1", "2", "3", "4", "5", "6"]:
            print("⚠️ Acción no disponible en modo OFFLINE"); input("ENTER...")
            continue

        # Lógica de Ejecución (UN SOLO BLOQUE)
        if op == "1":
            busqueda_rapida(df_i, df_m)
        elif op == "2":
            registrar_aporte_hogar(df_i)
        elif op == "3":
            exportar_datos(df_i)
        elif op == "4":
            valorizar_inventario(df_i, df_m)
        elif op == "5":
            tablero_estrategico(df_m)
        elif op == "6" and conectado:
            generar_lista_compras(df_i, df_m)
        else:
            print("❌ Opción no válida.")
            time.sleep(1)

if __name__ == "__main__":
    menu()