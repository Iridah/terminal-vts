import sqlite3
from vts_utils import limpiar_pantalla

def asignar_precios_faltantes():
    conn = sqlite3.connect("vts_mardum.db")
    cursor = conn.cursor()
    
    # Buscamos productos con precio 0 o nulo
    cursor.execute("SELECT sku, producto, costo_neto FROM maestro WHERE precio_venta IS NULL OR precio_venta = 0")
    faltantes = cursor.fetchall()
    
    if not faltantes:
        print("✅ No hay productos con precio $0. ¡Todo en orden!")
        return

    print(f"💰 ASIGNADOR DE PRECIOS VTS - {len(faltantes)} pendientes")
    print("="*50)
    
    for sku, nombre, costo in faltantes:
        print(f"\nSKU: {sku} | {nombre}")
        print(f"Costo Neto: ${costo:,.0f}")
        
        nuevo_p = input(f"Ingrese Precio de Venta para {sku} (0 para saltar): ")
        if nuevo_p and nuevo_p != "0":
            precio = float(nuevo_p)
            # Calculamos el margen automáticamente para que la Opción 5 funcione
            margen = (precio - costo) / precio if precio > 0 else 0
            
            cursor.execute("""
                UPDATE maestro 
                SET precio_venta = ?, margen = ? 
                WHERE sku = ?""", (precio, margen, sku))
            print(f"✔ Guardado: {sku} a ${precio:,.0f} (Margen: {margen*100:.1f}%)")
    
    conn.commit()
    conn.close()
    print("\n🚀 Proceso terminado. Ahora el Tablero Estratégico mostrará datos reales.")

if __name__ == "__main__":
    asignar_precios_faltantes()