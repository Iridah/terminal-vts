# dashboard/odd.py
# Odd — Orquestador de Ventas VTS
# Responsabilidades: mapeo SumUp↔VTS, descuento stock, reportes

import csv
import io
from django.db import transaction
from .models import AuditoriaVTS, VarianteVTS, RegistroLogs

# =================================================================
# I. MODELO DE MAPEO (sin migración — usa ConfigVTS como almacén)
# =================================================================

def _normalizar(texto: str) -> str:
    """Normaliza texto para comparación flexible."""
    return texto.strip().lower()

# =================================================================
# II. GESTIÓN DE MAPEO SumUp ↔ VTS
# =================================================================

def construir_mapeo_desde_inventario(filas: list) -> dict:
    """
    Lee el CSV de inventario SumUp y construye un dict de mapeo:
    {item_id_sumup: {'sku_vts': ..., 'nombre': ..., 'variantes': {variant_id: sku_variante}}}
    Solo registra los que tienen SKU en SumUp.
    """
    mapeo = {}
    item_actual = None

    for fila in filas:
        item_name = fila.get('Item name', '').strip()
        sku_sumup = fila.get('SKU', '').strip()
        item_id = fila.get('Item id', '').strip()
        variant_id = fila.get('Variant id', '').strip()
        variacion = fila.get('Variations', '').strip()

        if item_name:
            item_actual = {
                'item_id': item_id,
                'nombre': item_name,
                'sku_vts': sku_sumup if sku_sumup else None,
                'variantes': {}
            }
            mapeo[item_id] = item_actual
        elif variacion and item_actual:
            item_actual['variantes'][variant_id] = variacion

    return mapeo

def buscar_sku_por_nombre(nombre_sumup: str) -> str | None:
    """
    Intenta encontrar el SKU de VTS buscando por nombre de producto.
    Primero busca en variantes, luego en productos simples.
    """
    nombre_norm = _normalizar(nombre_sumup)

    # Buscar en variantes
    for v in VarianteVTS.objects.select_related('producto').all():
        nombre_completo = _normalizar(f"{v.producto.producto} {v.nombre_variante}")
        if nombre_norm == nombre_completo or nombre_norm in nombre_completo:
            return v.sku_variante

    # Buscar en productos simples
    for p in AuditoriaVTS.objects.filter(variantes__isnull=True):
        if _normalizar(p.producto) in nombre_norm or nombre_norm in _normalizar(p.producto):
            return p.sku

    return None

# =================================================================
# III. PROCESAMIENTO DE VENTAS
# =================================================================

@transaction.atomic
def procesar_ventas(filas_validas: list, operador) -> dict:
    """
    Procesa las filas validadas por Wixelandr.
    Descuenta stock y registra en RegistroLogs.
    Retorna resumen del proceso.
    """
    resultado = {
        'procesadas': 0,
        'sin_match': [],
        'errores': [],
        'total_bruto': 0,
    }

    for fila in filas_validas:
        descripcion = fila.get('Descripción', '').strip()
        cantidad = int(float(fila.get('Cantidad', 1) or 1))
        precio_bruto = float(fila.get('Precio (Bruto)', 0) or 0)
        id_tx = fila.get('ID de transacción', '').strip()

        sku = buscar_sku_por_nombre(descripcion)

        if not sku:
            resultado['sin_match'].append({
                'd