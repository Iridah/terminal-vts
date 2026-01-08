# vts_main
import shutil
import pandas as pd
import os
import sys
from datetime import datetime
import time
from vts_graphics import visualizar_analitica_macro

# IMPORTACIONES PROPIAS (La clave del éxito)
from vts_utils import limpiar_pantalla, pausar, imprimir_separador
from vts_logic import * # Trae todas las funciones saneadas (registrar_entrada, etc.)
from vts_graphics import visualizar_analitica_macro
from database_manager import (
    verificar_conexion, 
    registrar_log, 
    inicializar_db,
    obtener_conexion
)
DB_NAME = "vts_mardum.db"

def realizar_backup_local():
    """Backup inteligente: Sobreescribe el del día para no acumular basura con Gestión de backups: <15 días se mantienen, >30 días se purgan"""
    try:
        import glob
        ahora = time.time()
        segundos_en_dia = 86400
        
        # 1. Crear backup de hoy (Sobreescribe si ya existe hoy)
        timestamp = datetime.now().strftime("%Y%m%d")
        shutil.copy2(DB_NAME, f"vts_backup_{timestamp}.db.bak")
        
        # 2. Purgar archivos viejos
        backups = glob.glob("*.bak")
        for f in backups:
            creacion = os.path.getmtime(f)
            edad_dias = (ahora - creacion) / segundos_en_dia
            
            if edad_dias > 30:
                os.remove(f)
                print(f"🗑️ Purgado automáticamente: {f}")
    except Exception as e:
        print(f"⚠️ Error en backup: {e}")

def pantalla_inicio():
    os.system('cls' if os.name == 'nt' else 'clear')
    if os.name == 'nt':
        os.system('color 0A')
        os.system('mode con: cols=85 lines=45')
    #El Arte de 66 caracteres
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
    time.sleep(4)

def menu():
    # 1. ARRANQUE DEL SISTEMA (Se ejecuta UNA vez)
    pantalla_inicio() # Aquí está Illidan
    inicializar_db()
    conectado = verificar_conexion()
    
    if conectado:
        # Eliminamos el limpiar_pantalla() y el pausar() para que se vea bajo el arte
        verificar_integridad_base() 
        print(f"✅ MOTOR SQL CONECTADO | {datetime.now().strftime('%H:%M')}")
        time.sleep(2) # Pausa breve automática, sin pedir Enter.

    # 2. BUCLE PRINCIPAL
    while True:
        limpiar_pantalla()
        
        # --- LÓGICA DE ALERTA (Ahora vía SQL rápido) ---
        alerta = ""
        try:
            with obtener_conexion() as conn:
                criticos = conn.execute("SELECT COUNT(*) FROM inventario WHERE subtotal <= 1").fetchone()[0]
                if criticos > 0: alerta = f" ⚠️ {criticos} CRÍTICOS"
        except: pass
        
        # --- ENCABEZADO ---
        print(f"        🐮 VTS v2.1.0 🐮 | STATUS: {'ONLINE' if conectado else 'OFFLINE'}{alerta}")
        imprimir_separador()
        print(" [1] 📦 ENTRADA (Ingreso Stock)")
        print(" [2] 📦 EGRESO (Venta / Aporte Hogar)")
        print(" [3] 🔍 BÚSQUEDA RÁPIDA")
        print(" [4] 📦 CALCULADORA DE PACKS")
        print("-" * 50)
        print(" [5] 💰 TABLERO ESTRATÉGICO / VALORIZACIÓN")
        print(" [6] 🛒 SUGERENCIA DE REPOSICIÓN")
        print(" [7] 🛠  ADMINISTRACIÓN (CSV Bridge / Master Editor)")
        print(" [8] 📊 ANALYTICS VISUAL")
        print("-" * 50)
        print(" [0] 🚪 GUARDAR Y SALIR")
        
        op = input("\nVTS_INPUT > ") 

        if op == "0":
            if conectado: realizar_backup_local()
            print("Cerrando Terminal VTS 🐮... ¡Buen turno!"); break

        if not conectado:
            print("⚠️ MODO OFFLINE: Solo se permite SALIR (0)"); pausar(); continue

        # MAPEADO DIRECTO A vts_logic
        if op == "1": registrar_entrada()
        elif op == "2": modulo_egreso()
        elif op == "3": busqueda_rapida()
        elif op == "4": calculadora_packs()
        elif op == "5": 
            # Combinación de vista estratégica
            tablero_estrategico()
            valorizar_inventario()
        elif op == "6": generar_lista_compras()
        elif op == "7": modulo_administracion()
        elif op == "8": visualizar_analitica_macro()
        else:
            print("❌ Opción no válida."); time.sleep(1)    

if __name__ == "__main__":
    menu()