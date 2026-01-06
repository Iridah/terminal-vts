import shutil
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
    inicializar_db,
    obtener_conexion  # <--- ESTE ES EL CABLE QUE NECESITABAS
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
    inicializar_db()
    
    conectado = verificar_conexion()
    status = "ONLINE (LOCAL SQL)" if conectado else "OFFLINE (EMERGENCIA)"
    
    if conectado:
        limpiar_pantalla()
        # Llamamos a la integridad sin pasarle DFs, que consulte la DB
        verificar_integridad_base() 
        input("\nSISTEMA SQL LISTO. Presione ENTER para entrar al panel...")

    # 2. BUCLE PRINCIPAL
    while True:
        limpiar_pantalla()
        
        # --- LÓGICA DE ALERTA (Ahora vía SQL rápido) ---
        alerta_compras = "OK"
        if conectado:
            with obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM inventario WHERE subtotal <= 1")
                criticos = cursor.fetchone()[0]
                if criticos > 0: alerta_compras = f"⚠️ {criticos} REVISAR!"
        
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
                try:
                    shutil.copy2("vts_mardum.db", "vts_mardum.db.bak")
                    print("💾 Respaldo local creado (vts_mardum.db.bak)")
                except Exception as e:
                    print(f"⚠️ No se pudo crear el respaldo: {e}")
            
            print("Cerrando Terminal VTS 🐮... ¡Buen turno!")
            break

        if not conectado:
            print("⚠️ MODO OFFLINE: Solo se permite SALIR (9)"); time.sleep(1)
            continue

        # LLAMADAS SIMPLIFICADAS (Pure SQL)
        if op == "1": busqueda_rapida()
        elif op == "2": registrar_aporte_hogar() 
        elif op == "3": exportar_datos()
        elif op == "4": valorizar_inventario()
        elif op == "5": tablero_estrategico()
        elif op == "6": generar_lista_compras()
        elif op == "7": ver_super_ganchos()
        elif op == "8": calculadora_packs()
        else:
            print("❌ Opción no válida."); time.sleep(1)

if __name__ == "__main__":
    menu()