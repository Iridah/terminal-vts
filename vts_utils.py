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
    
def entrada_segura(prompt):
    """Captura entrada y detecta si el usuario quiere cancelar"""
    valor = input(f"{prompt} (o 0 para cancelar): ").strip()
    if valor == "0" or valor == "":
        return None  # Señal de que el usuario abortó
    return valor