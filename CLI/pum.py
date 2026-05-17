import sqlite3

def auditar_db_para_django():
    conn = sqlite3.connect("vts_mardum.db")
    cursor = conn.cursor()
    print("🔍 INICIANDO ESCANEO DE INTEGRIDAD...")

    # 1. Buscar SKUs nulos o vacíos
    cursor.execute("SELECT rowid, * FROM inventario WHERE sku IS NULL OR sku = ''")
    huecos = cursor.fetchall()
    
    # 2. Buscar SKUs duplicados
    cursor.execute("SELECT sku, COUNT(sku) FROM inventario GROUP BY sku HAVING COUNT(sku) > 1")
    duplicados = cursor.fetchall()

    # 3. Buscar precios o costos no numéricos
    cursor.execute("SELECT sku FROM maestro WHERE typeof(costo_neto) != 'real' AND typeof(costo_neto) != 'integer'")
    tipos_raros = cursor.fetchall()

    print(f"\n💣 MINAS ENCONTRADAS:")
    print(f"➖ SKUs Vacíos: {len(huecos)}")
    print(f"➖ SKUs Duplicados: {len(duplicados)}")
    print(f"➖ Errores de Formato de Precio: {len(tipos_raros)}")
    
    if duplicados:
        print("\n⚠️  DUPLICADOS CRÍTICOS (Django los odia):")
        for d in duplicados: print(f"   -> {d[0]} aparece {d[1]} veces")
    
    conn.close()

if __name__ == "__main__":
    auditar_db_para_django()