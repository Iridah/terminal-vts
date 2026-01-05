import pandas as pd
from vts_utils import limpiar_pantalla, pausar, imprimir_separador

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
    if pd.isnull(valor): return 0.0
    if isinstance(valor, (int, float)): return float(valor)
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
    
    # Supongamos que tu "Meta de Bodega" son $1.000.000 (ajustable)
    meta = 1000000 
    porcentaje = min((total_activos / meta) * 100, 100)
    bloques = int(porcentaje / 5) # 20 bloques representan el 100%
    
    barra = "█" * bloques + "░" * (20 - bloques)
    
    print(f"💰 CAPITAL EN BODEGA")
    print(f"[{barra}] {porcentaje:.1f}%")
    print(f"VALOR NETO: ${total_activos:,.0f}")
    print("-" * 40)

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

def ver_super_ganchos(df_m):
    limpiar_pantalla()
    print("🔥 PRODUCTOS 'SUPER GANCHO' (MÁXIMA ATRACCIÓN)")
    print("="*60)
    
    # Filtramos usando tu lógica de Tablero
    # Un "Super Gancho" es margen >= 28% y precio < competencia_min
    ganchos = []
    for _, r in df_m.iterrows():
        margen = r.get('MARGEN REAL (%)', 0)
        precio = r.get('PRECIO VENTA FINAL (CON IVA)', 0)
        c_min = r.get('Minimo competencia', 0)
        
        if margen >= 0.2801 and (precio < c_min if c_min > 0 else False):
            ganchos.append(r)
            
    if ganchos:
        for g in ganchos:
            print(f"⭐ {g['PRODUCTO'][:30]:30} | P. VENTA: ${g['PRECIO VENTA FINAL (CON IVA)']:,.0f}")
        print("-" * 60)
        print(f"Total: {len(ganchos)} oportunidades encontradas.")
    else:
        print("No hay productos con estatus 'SUPER GANCHO' actualmente.")
    
    input("\nENTER PARA VOLVER...")

def calculadora_packs(df_m):
    limpiar_pantalla()
    print("📦 CREADOR DE COMBOS / PACKS VTS")
    print("="*50)
    skus = input("INGRESE SKUS SEPARADOS POR COMA (EJ: SKU1,SKU2): ").upper().split(',')
    
    total_normal = 0
    productos_en_pack = []
    
    for s in skus:
        s = s.strip()
        prod = df_m[df_m['SKU'] == s]
        if not prod.empty:
            precio = prod.iloc[0]['PRECIO VENTA FINAL (CON IVA)']
            nombre = prod.iloc[0]['PRODUCTO']
            total_normal += precio
            productos_en_pack.append(f"{nombre} (${precio:,.0f})")
    
    if productos_en_pack:
        print("\nCONTENIDO DEL PACK:")
        for p in productos_en_pack: print(f" - {p}")
        print(f"\nPRECIO TOTAL NORMAL: ${total_normal:,.0f}")
        
        # Sugerencia de descuento
        sugerido = total_normal * 0.90 # 10% de descuento
        print(f"🔥 PRECIO COMBO SUGERIDO (-10%): ${sugerido:,.0f}")
    else:
        print("\n❌ NO SE ENCONTRARON LOS SKUS.")
    
    input("\nENTER PARA VOLVER...")
