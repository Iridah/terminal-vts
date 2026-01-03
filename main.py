import pandas as pd
import os
from datetime import datetime

# CONFIGURACIÓN DE SEGURIDAD (MÁSCARAS)
MASTER_FILE = "data_s.csv"
INV_FILE = "data_v.csv"
BACKUP_FILE = "sync_backup.txt"

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def verificar_conexion():
    return os.path.exists(MASTER_FILE) and os.path.exists(INV_FILE)

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
            actual_hogar = df_i.at[idx, 'Aporte Hogar'] if pd.notnull(df_i.at[idx, 'Aporte Hogar']) else 0
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

def menu():
    conectado = verificar_conexion()
    status = "ONLINE (LOCAL DB)" if conectado else "OFFLINE (EMERGENCIA)"
    
    df_m, df_i = None, None
    
    if conectado:
        try:
            df_m = pd.read_csv(MASTER_FILE)
            df_i = pd.read_csv(INV_FILE)
        except Exception as e:
            print(f"❌ ERROR CRÍTICO AL LEER CSV: {e}")
            status = "ERROR DE DATOS"
            conectado = False

    while True:
        limpiar_pantalla()
        print(f"VTS v1.5.1 | STATUS: {status}")
        print("==================================================")
        print("1. BÚSQUEDA RÁPIDA (STOCK & PRECIO)")
        print("2. REGISTRAR APORTE HOGAR")
        print("3. EXPORTAR REPORTE (TXT)")
        print("4. SINCRONIZAR (PRÓXIMAMENTE)")
        print("5. SALIR")
        print("==================================================")
        
        op = input("VTS_INPUT > ") # Asegúrate de que el cursor se quede aquí
        
        if op == "1":
            if conectado: busqueda_rapida(df_i, df_m)
            else: print("⚠️ Acción no disponible en modo OFFLINE"); input("ENTER...")
        elif op == "2":
            if conectado: registrar_aporte_hogar(df_i)
            else: print("⚠️ Acción no disponible en modo OFFLINE"); input("ENTER...")
        elif op == "3":
            if conectado: exportar_datos(df_i)
            else: print("⚠️ Acción no disponible en modo OFFLINE"); input("ENTER...")
        elif op == "5":
            print("Cerrando Terminal VTS... ¡Buen fin de semana!")
            break
        else:
            print("❌ Opción no válida.")
            import time; time.sleep(1) # Pausa breve para ver el error

if __name__ == "__main__":
    menu()