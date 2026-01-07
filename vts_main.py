# vts_main
import shutil
import pandas as pd
import os
import sys
from datetime import datetime
import time
from vts_graphics import visualizar_analitica_macro

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
def realizar_backup_local():
    try:
        shutil.copy2(DB_NAME, f"{DB_NAME}.bak")
        print(f"\n✅ Respaldo creado: {DB_NAME}.bak")
    except Exception as e:
        print(f"⚠️ Error en backup: {e}")

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
        print(f"        🐮 VTS v2.1.0 🐮 | STATUS: {'ONLINE' if conectado else 'OFFLINE'}")
        print(" [1] 📦-> REGISTRAR entrada / ingreso (Carga stock)")
        print(" [2] 📦<- REGISTRAR SALIDA / EGRESO (Ventas/Hogar)")
        print(" [3] 🔍 BÚSQUEDA RÁPIDA (Lazy Search)")
        print(" [4] 📦 CALCULADORA DE COMBOS")
        print("-" * 50)
        print(" [5] 💰 TABLERO ESTRATÉGICO (Márgenes/Ganchos)")
        print(" [6] 🛒 SUGERENCIA DE REPOSICIÓN (Semáforo)")
        print(" [7] 🛠  ADMINISTRACIÓN (Cloud Bridge/Fixes)")
        print(" [8] 📊 VTS ANALYTICS (Estado Macro)")
        print("-" * 50)
        print(" [0] 🚪 GUARDAR Y SALIR")
        
        op = input("VTS_INPUT > ") 

        if op == "0":
            if conectado:
                realizar_backup_local() # Función unificada que usa shutil.copy2
            print("Cerrando Terminal VTS 🐮... ¡Buen turno!"); break

        if not conectado:
            print("⚠️ MODO OFFLINE: Solo se permite SALIR (9)"); time.sleep(1)
            continue

        # LLAMADAS SIMPLIFICADAS (Pure SQL)
        if op == "1": registrar_entrada()   # NUEVA
        elif op == "2": modulo_egreso()     # EXISTENTE
        elif op == "3": busqueda_rapida()
        elif op == "4": calculadora_packs()
        elif op == "5": tablero_estrategico()
        elif op == "6": generar_lista_compras()
        elif op == "7": modulo_administracion()
        elif op == "8": visualizar_analitica_macro() # Movida al 8

if __name__ == "__main__":
    menu()