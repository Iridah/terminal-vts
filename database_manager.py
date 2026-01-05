import pandas as pd
import os
from datetime import datetime
from vts_utils import limpiar_pantalla

# Configuraciones
MASTER_FILE = "data_s.csv"
INV_FILE = "data_v.csv"

def verificar_conexion():
    return os.path.exists(MASTER_FILE) and os.path.exists(INV_FILE)

def registrar_log(sku, producto, cantidad, motivo="APORTE HOGAR"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] SKU: {sku} | CANT: {cantidad} | MOTIVO: {motivo} | PROD: {producto}\n"
    try:
        with open("vts_movimientos.log", "a", encoding="utf-8") as f:
            f.write(log_line)
    except:
        pass

def registrar_aporte_hogar(df_i):
    limpiar_pantalla()
    print("🏠 REGISTRO DE APORTE HOGAR")
    sku = input("INGRESE SKU DEL PRODUCTO: ").upper()
    
    if sku in df_i['SKU'].values:
        try:
            cantidad = int(input(f"CANTIDAD PARA CONSUMO INTERNO: "))
            idx = df_i.index[df_i['SKU'] == sku].tolist()[0]
            
            actual_hogar = float(df_i.at[idx, 'Aporte Hogar']) if pd.notnull(df_i.at[idx, 'Aporte Hogar']) else 0.0
            df_i.at[idx, 'Aporte Hogar'] = actual_hogar + cantidad
            df_i.at[idx, 'Subtotal'] = df_i.at[idx, 'Inventario actual'] - df_i.at[idx, 'Aporte Hogar']
            
            df_i.to_csv(INV_FILE, index=False)
            nombre_prod = df_i.at[idx, 'Funcion']
            registrar_log(sku, nombre_prod, cantidad)

            print("\n✅ BASE DE DATOS LOCAL ACTUALIZADA.")
        except ValueError:
            print("\n❌ ERROR: INGRESE UN NÚMERO VÁLIDO.")
    else:
        print("\n❌ SKU NO ENCONTRADO.")
    input("\nENTER PARA CONTINUAR...")