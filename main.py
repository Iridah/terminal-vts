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
            print(f"PRECIO:   ${r['PRECIO VENTA FINAL (CON IVA)']:,.0f}")
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

def menu():
    conectado = verificar_conexion()
    status = "ONLINE (LOCAL DB)" if conectado else "OFFLINE (EMERGENCIA)"
    
    # Carga inicial de datos
    df_m = pd.read_csv(MASTER_FILE) if conectado else None
    df_i = pd.read_csv(INV_FILE) if conectado else None

    while True:
        limpiar_pantalla()
        print(f"VTS v1.5 | STATUS: {status}")
        print("==================================================")
        print("1. BÚSQUEDA RÁPIDA (STOCK & PRECIO)")
        print("2. REGISTRAR APORTE HOGAR")
        print("3. EXPORTAR REPORTE (TXT)")
        print("4. SINCRONIZAR (PRÓXIMAMENTE)")
        print("5. SALIR")
        print("==================================================")
        
        op = input("VTS_INPUT> ")
        
        if op == "1" and conectado:
            busqueda_rapida(df_i, df_m)
        elif op == "2" and conectado:
            registrar_aporte_hogar(df_i)
        elif op == "3" and conectado:
            exportar_datos(df_i)
        elif op == "5":
            print("Cerrando Terminal VTS...")
            break

if __name__ == "__main__":
    menu()