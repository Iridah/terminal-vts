import os
import time

def limpiar_pantalla():
    """Limpia la terminal según el sistema operativo"""
    os.system('cls' if os.name == 'nt' else 'clear')

def pausar():
    """Pausa estética para que el usuario lea antes de continuar"""
    input("\nPresione ENTER para continuar...")

def imprimir_separador(caracter="=", largo=65):
    """Genera líneas divisorias uniformes"""
    print(caracter * largo)

def formatear_moneda(valor):
    """Transforma un número en formato de moneda legible $XX.XXX"""
    try:
        return f"${int(valor):,}".replace(",", ".")
    except:
        return "$0"