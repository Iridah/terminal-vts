import pandas as pd
import os
from datetime import datetime

# CONFIGURACIÓN DE SEGURIDAD (MÁSCARAS)
# Estos nombres van en tu .gitignore
MASTER_FILE = "data_s.csv"
INV_FILE = "data_v.csv"
BACKUP_FILE = "sync_backup.txt"

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def verificar_conexion():
    # Simulador de modo dual
    return os.path.exists(MASTER_FILE)

def busqueda_rapida(df_i, df_m):
    limpiar_pantalla()
    print("🔍 BÚSQUEDA RÁPIDA (TERMINAL VTS)")
    query = input("INGRESE NOMBRE O SKU: ").upper()
    
    # Unimos para tener stock y precio de venta
    df_res = pd.merge(df_i, df_m[['SKU', 'PRECIO VENTA FINAL (CON IVA)']], on='SKU', how='left')
    
    # Filtramos por nombre (Funcion) o SKU
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

def exportar_datos(df_i):
    """Genera un archivo plano de texto para respaldo físico (Estilo RTF/TXT)"""
    limpiar_pantalla()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"VTS_EXPORT_{timestamp}.txt"
    
    with open(filename, "w") as f:
        f.write(f"VTS SYSTEM EXPORT - {timestamp}\n")
        f.write(df_i.to_string())
    
    print(f"✅ ARCHIVO EXPORTADO: {filename}")
    input("ENTER...")

def menu():
    conectado = verificar_conexion()
    status = "ONLINE (LOCAL DB)" if conectado else "OFFLINE (EMERGENCIA)"
    
    df_m = pd.read_csv(MASTER_FILE) if conectado else None
    df_i = pd.read_csv(INV_FILE) if conectado else None

    while True:
        limpiar_pantalla()
        print(f"VTS v1.4 | STATUS: {status}")
        print("==================================================")
        print("1. BÚSQUEDA RÁPIDA (STOCK & PRECIO)")
        print("2. REGISTRAR APORTE HOGAR")
        print("3. EXPORTAR REPORTE (TXT)")
        print("4. IMPORTAR/SINCRONIZAR (PRÓXIMAMENTE)")
        print("5. SALIR")
        print("==================================================")
        
        op = input("VTS_INPUT> ")
        
        if op == "1" and conectado:
            busqueda_rapida(df_i, df_m)
        elif op == "3" and conectado:
            exportar_datos(df_i)
        elif op == "5":
            break

if __name__ == "__main__":
    menu()