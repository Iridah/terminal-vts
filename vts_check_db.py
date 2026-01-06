import sqlite3

def comprobar_datos():
    conn = sqlite3.connect("vts_mardum.db")
    cursor = conn.cursor()
    
    print("📊 RECUENTO DE TABLAS SQL:")
    
    # Verificar Tabla Maestro
    cursor.execute("SELECT COUNT(*) FROM maestro")
    print(f" - Productos en Maestro: {cursor.fetchone()[0]}")
    
    # Verificar Tabla Inventario
    cursor.execute("SELECT COUNT(*) FROM inventario")
    print(f" - Productos en Inventario: {cursor.fetchone()[0]}")
    
    # Mostrar una muestra para ver que no sean ceros o nulos
    print("\n👀 MUESTRA DE DATOS (Primeros 3):")
    cursor.execute("SELECT sku, funcion, subtotal FROM inventario LIMIT 3")
    for fila in cursor.fetchall():
        print(f" SKU: {fila[0]} | NOMBRE: {fila[1]} | STOCK: {fila[2]}")
        
    conn.close()

if __name__ == "__main__":
    comprobar_datos()