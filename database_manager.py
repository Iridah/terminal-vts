import sqlite3
import pandas as pd
import os
from datetime import datetime
from vts_utils import limpiar_pantalla, pausar

DB_NAME = "vts_mardum.db"

def inicializar_db():
    """Asegura la existencia de las tablas (Punto Ciego 1)"""
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS maestro 
            (sku TEXT PRIMARY KEY, producto TEXT, costo_neto REAL, precio_venta REAL, 
             margen REAL, comp_min REAL, comp_max REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS inventario 
            (sku TEXT PRIMARY KEY, funcion TEXT, stock_actual INTEGER, 
             aporte_hogar INTEGER, subtotal INTEGER)''')
        conn.commit()

def registrar_aporte_hogar(df_ignorado=None):
    """Actualiza el consumo interno usando SQL puro."""
    limpiar_pantalla()
    print("🏠 REGISTRO DE APORTE HOGAR (SQL ENGINE)")
    sku = input("INGRESE SKU (o 0 para cancelar): ").upper()
    
    if sku == "0" or sku == "": 
        return

    try:
        with obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT funcion, aporte_hogar, stock_actual FROM inventario WHERE sku = ?", (sku,))
            fila = cursor.fetchone()

            if fila:
                nombre, hogar_actual, stock = fila
                try:
                    cantidad = int(input(f"CANTIDAD PARA {nombre}: "))
                    nuevo_hogar = hogar_actual + cantidad
                    nuevo_subtotal = stock - nuevo_hogar

                    cursor.execute('''UPDATE inventario SET aporte_hogar = ?, subtotal = ? WHERE sku = ?''', 
                                 (nuevo_hogar, nuevo_subtotal, sku))
                    conn.commit()
                    
                    registrar_log(sku, nombre, cantidad)
                    print(f"\n✅ SQL UPDATE EXITOSO: {nombre}")
                    print(f"📊 NUEVO SUBTOTAL: {nuevo_subtotal}")
                except ValueError:
                    print("❌ ERROR: Ingrese un número entero.")
            else:
                print("❌ SKU no encontrado en la base de datos.")
    except Exception as e:
        print(f"❌ ERROR DE CONEXIÓN: {e}")
    
    pausar()

def obtener_conexion():
    """Conexión robusta al motor SQL"""
    return sqlite3.connect(DB_NAME)

def verificar_conexion():
    """El nuevo sensor de estado para el main.py"""
    return os.path.exists(DB_NAME)

# Mantenemos registrar_log igual ya que escribe en un .log externo
def registrar_log(sku, producto, cantidad, motivo="APORTE HOGAR"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] SKU: {sku} | CANT: {cantidad} | MOTIVO: {motivo} | PROD: {producto}\n"
    try:
        with open("vts_movimientos.log", "a", encoding="utf-8") as f:
            f.write(log_line)
    except:
        pass