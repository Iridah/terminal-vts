import pandas as pd
import os
from datetime import datetime
import time

# IMPORTACIONES DESDE TUS MÓDULOS (La clave del éxito)
from vts_utils import limpiar_pantalla, pausar, imprimir_separador
from vts_logic import * 
from database_manager import (
    verificar_conexion, 
    registrar_log, 
    registrar_aporte_hogar, 
    MASTER_FILE, 
    INV_FILE
)

# CONFIGURACIÓN DE SEGURIDAD
BACKUP_FILE = "sync_backup.txt"

def pantalla_inicio():
    # 1. Limpieza absoluta de la terminal
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # 2. Configuración estética (Verde Fel para Windows)
    if os.name == 'nt':
        os.system('color 0A')
        os.system('mode con: cols=85 lines=45') # Ventana optimizada para 66px

    # 3. El Arte de 66 caracteres
    illidan_66 = r"""
%@%%%@@@@@@%%*###%%###%%###**##****##***************############%%
%%%@%%#====#*+*###%%##%%#****##*+=+%%%###************#%########%%%
%%%@#+==+%@@%%**###%%%%@%#**#%%%*+==#@@@@@%###********#*#####%%%%%
%%%+=-=+@@@@@@*#####@@%#%*+#@@%#@*=-=*@@@@@%%##*##**********#%%%%#
%%*==+*@@@@@@@*@%#%%@@@%%*=+@@%@@%+===*@@@@#%%%%%####************#
%+=-=*@@@@@@@@*@@#%%%@@@#*+*@@@@@@*=--=@@@@%%%%%%%%%###*########%%
#+==+@@@@@@@@@@@@@%%%#######%##%@@@+===*@@@%@@@@%@%%%%%%%%%%@%%%%%
*+++*@@@@@@@@@@@@@%%########%###*@@*+==+@@@@@@@@@%%%%%@@@@@@%%%%%%
*+++*@@@@@@@@@@%%@#+*%*#*#*#%##%###**+++#%@%@@@@@@@@%%%%@%%#%@%@@%
**++*#@@@@@@@@@@*+*++#######+****%%**+**%@@%@@%%@@@@@@@@%%%#%@@@@@
#****##@@@@@@@#+*+*#%##*****%++***%#+***%@@%#*#%@@@@@@@@@@%%#%@@@@
%##****@@@@@@*+=+#%@%#*++++*#%++******#*%%##***++*#@@@%%%%%%%%%%%%
@%##*#***#+*+++*###%%##########*++**#######*++++*+**%@@%%%%%%%%%%%
@@@%##%#######%#%%%%@%%%*###%%@%###%%%%##****+++*+++**@@%%%%%#%%%%
@@@%#%@@%%%*%%%%#%%%@@%%#####%@@%%%%%%%##%*##*++*+=++*#**#%%%#%%%@
@@@%##@@%######@%%#%%@%@#**##%@@@@@%%%%%#*+**#=****##*##****##%@%@
@@@##%@@@#%%%%%##@@##%@%#**##@@@@@@@@%%#%%%#*+*##**#####*****+%@@@
@@%##@@%@@%@@@@%##%#%%%@@%@@@@@@@@%@@%%%%%#**%%#####%%#******++#@@
@@%#%@@%%%@@@@@%%%%%#%%%%@@@@@@@@@%###+**#####%@@@@%%#*****##*+#**
@@##%##@%%%@@@@%#%%@*#%%%%%%@@@@%%######**#*##%@@@@@%#*##**#**###*
@@###**#%%%@@@@@%%@@@#*%%%##%@@@@@%%#####%%#*#%%@@@@@@%#%####%%*++
@@*#**##%@@@@@@@@@%@%@%#%%%#%@@@@@%%%#%#####%%%@@@@@@@@@@@@@@@@#*+
@*#*###%@@@@@@@@@@@%%%##%%@@%@@@%%%%##%%#*#%@%%@@@@@@@@@@@@@@%%%#+
##*####%@%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%@@@@@@@@@@@@@@@@@@@@%#***
##***%#####@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%@@@@@@@@@@@@@@@%###
#####*#%%@@@@@@@@@@@@@@@@@%%%@@@@@@@@@@@@@@@@@%%%@@@@@@@@@@@@@@@@%
###*#%%@@@@@@@@@@@@@@@@@@@@%%%@@@@@@@@@@@@@@@%@%%@@@@@@@@@@@@@@@@@
***%%%@@@@@@@@@@@@@@@@@%@%%@%%%%@@@@@@@@@@@@%%%@@@@@@@@@@@@@@@@@@@
###%@@@@@@@@@@@@@@@@@@@@@@%%@@@@@@@@%@@%@@@@@@@@@@@@@@@@@@@@@@@@@@
%@@@@@@@@@@@@@@@@@@%#%%@@@@#@@@@%@@@@#@@@@@@@@@@@%%#%@@@@@@@@@@@@@
%%@@@@@@@@@@@@@@@@%##%%%%@%#%%@@%@@@%#%@@@@@@@%@%%%%%%%%@@@@@@@@@@
#%@@@@@@@@@@@@@@@@%%%%%%%@#%%%%@@@@@%#%%@@@@@@%@%%%%@@@%@@@@@@@@@@
#%@@@@@@@@@@@@@@@%%@@@@@%@%#%%%%@@@%%#%@%@@@@@@@@@@%%%%@@@@@@@@@@@
#@@@@@@@@@@@@@%%%%@@@@@@@@*#%@@%%%%%%#@@@@@@@@@@%@@@@%#%%%@@@@@@@@
#@@@@@@@@@@@%#%%%%%@@@@@@@*#%%@%%%%%%#@@@@%@@@@@@@@@@@%##%%@@@@@@@
#@@@@@@@@@%%%%%%%%%%@@@@@@##%%%%%%%%%#@@@@%%%%@@%@@@@@@@%%%%@@@@@@
    """
    print(illidan_66)
    print("\n" + " " * 12 + "¡NO ESTÁN PREPARADOS PARA EL STOCK!")
    print("-" * 66)
    
    # Pausa de 7 segundos para contemplar el arte y cargar librerías
    time.sleep(7)

def menu():
    # 1. ARRANQUE DEL SISTEMA (Se ejecuta UNA vez)
    pantalla_inicio() 
    
    conectado = verificar_conexion()
    status = "ONLINE (LOCAL DB)" if conectado else "OFFLINE (EMERGENCIA)"
    df_m, df_i = None, None
    
    if conectado:
        try:
            df_m = pd.read_csv(MASTER_FILE)
            df_i = pd.read_csv(INV_FILE)
            
            # PARCHE DE TOLERANCIA: Verifica columnas antes de limpiar
            columnas_limpiar = [
                'PRECIO VENTA FINAL (CON IVA)', 
                'COSTO (SIN IVA)', 
                'MARGEN REAL (%)'
            ]
            
            for col in columnas_limpiar:
                if col in df_m.columns:
                    df_m[col] = df_m[col].apply(limpiar_precio)
                else:
                    df_m[col] = 0.0
                    # Usamos un print simple para no ensuciar el splash
                    print(f"⚠️  Columna '{col}' no encontrada en el maestro.")

            limpiar_pantalla()
            verificar_integridad_base(df_i, df_m)
            input("\nSISTEMA LISTO. Presione ENTER para entrar al panel...")
        except Exception as e:
            status = f"ERROR CRÍTICO: {e}"
            conectado = False

    # 2. BUCLE PRINCIPAL
    while True:
        limpiar_pantalla()
        
        # --- LÓGICA DE ESCANEO RÁPIDO ---
        productos_criticos = df_i[df_i['Subtotal'] <= 1].shape[0] if df_i is not None else 0
        alerta_compras = "⚠️ REVISAR!" if productos_criticos > 0 else "OK"
        
        # --- ENCABEZADO ---
        print(f"        🐮 VTS v1.7.6 🐮 | STATUS: {status}")
        print("="*65)
        print(" 1. 🔍 BÚSQUEDA RÁPIDA       2. 🏠 REGISTRAR HOGAR")
        print(" 3. 📑 EXPORTAR TXT          4. 💰 VALORIZACIÓN (KARDEX)")
        print(" 5. 🧠 TABLERO ESTRATÉGICO   6. 🛒 LISTA DE COMPRAS [" + alerta_compras + "]")
        print(" 7. 🔥 SUPERGANCHOS          8. 📦 CALCULAR PACKS")
        print(" 9. 🚪 SALIR")
        print("="*65)
        
        op = input("VTS_INPUT > ") 

        if op == "9":
            if conectado:
                with open(BACKUP_FILE, "w") as f:
                    f.write(f"RESPALDO - {datetime.now()}\n{df_i.to_string(index=False)}")
            print("Cerrando Terminal VTS 🐮... ¡Buen turno!")
            break

        if not conectado:
            print("⚠️ MODO OFFLINE: Solo se permite SALIR (9)"); time.sleep(1)
            continue

        if op == "1": busqueda_rapida(df_i, df_m)
        elif op == "2": registrar_aporte_hogar(df_i)
        elif op == "3": exportar_datos(df_i)
        elif op == "4": valorizar_inventario(df_i, df_m)
        elif op == "5": tablero_estrategico(df_m)
        elif op == "6": generar_lista_compras(df_i, df_m)
        elif op == "7": ver_super_ganchos(df_m)
        elif op == "8": calculadora_packs(df_m)
        else:
            print("❌ Opción no válida.")
            time.sleep(1)

if __name__ == "__main__":
    menu()