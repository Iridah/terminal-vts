# dashboard/odd.py
# Odd — Orquestador de Ventas VTS
# Responsabilidades: mapeo SumUp↔VTS, descuento stock, reportes
 
from django.db import transaction
from .models import AuditoriaVTS, VarianteVTS, RegistroLogs, VentaRegistrada
 
# =================================================================
# I. UTILIDADES
# =================================================================
 
def _norm(texto: str) -> str:
    """Normaliza texto: minúsculas y espacios múltiples colapsados."""
    return ' '.join(texto.strip().lower().split())
 
 
# =================================================================
# II. CONSTRUCCIÓN DE MAPEO SumUp ↔ VTS
# =================================================================
 
def construir_mapeo_desde_inventario(filas: list) -> dict:
    """
    Lee las filas del CSV de inventario SumUp y construye un dict:
    {
        item_id_sumup: {
            'item_id':  str,
            'nombre':   str,
            'sku_vts':  str | None,
            'variantes': {variant_id: nombre_variacion}
        }
    }
    """
    mapeo = {}
    item_actual = None
 
    for fila in filas:
        item_name  = fila.get('Item name',  '').strip()
        sku_sumup  = fila.get('SKU',        '').strip()
        item_id    = fila.get('Item id',    '').strip()
        variant_id = fila.get('Variant id', '').strip()
        variacion  = fila.get('Variations', '').strip()
 
        if item_name:
            item_actual = {
                'item_id':   item_id,
                'nombre':    item_name,
                'sku_vts':   sku_sumup if sku_sumup else None,
                'variantes': {}
            }
            mapeo[item_id] = item_actual
        elif variacion and item_actual:
            item_actual['variantes'][variant_id] = variacion
 
    return mapeo
 
 
# =================================================================
# III. RESOLUCIÓN DE SKU
# =================================================================
 
def buscar_sku_por_nombre(nombre_sumup: str) -> str | None:
    """
    Resuelve el SKU VTS a partir del nombre/descripción de SumUp.
 
    SumUp concatena 'Nombre producto Nombre variante' en la boleta.
    Estrategias en cascada:
      1. Exacto normalizado en variantes activas
      2. Exacto normalizado en productos simples activos
      3. Parcial en variantes activas
      4. Parcial en productos simples activos
    """
    desc = _norm(nombre_sumup)
 
    # ── 1. Exacto en variantes ────────────────────────────────────
    for v in VarianteVTS.objects.select_related('producto').filter(
        producto__estado='activo', estado='activo'
    ):
        if _norm(f"{v.producto.producto} {v.nombre_variante}") == desc:
            return v.sku_variante
 
    # ── 2. Exacto en productos simples ────────────────────────────
    for p in AuditoriaVTS.objects.filter(variantes__isnull=True, estado='activo'):
        if _norm(p.producto) == desc:
            return p.sku
 
    # ── 3. Parcial en variantes ───────────────────────────────────
    for v in VarianteVTS.objects.select_related('producto').filter(
        producto__estado='activo', estado='activo'
    ):
        candidato = _norm(f"{v.producto.producto} {v.nombre_variante}")
        if desc in candidato or candidato in desc:
            return v.sku_variante
 
    # ── 4. Parcial en productos simples ───────────────────────────
    for p in AuditoriaVTS.objects.filter(variantes__isnull=True, estado='activo'):
        norm_p = _norm(p.producto)
        if norm_p in desc or desc in norm_p:
            return p.sku
 
    return None
 
 
# =================================================================
# IV. PROCESAMIENTO DE VENTAS
# =================================================================
 
@transaction.atomic
def procesar_ventas(filas_validas: list, operador) -> dict:
    """
    Procesa las filas ya validadas por Wixelandr:
      - Verifica candado anti-doble descuento (VentaRegistrada)
      - Descuenta stock en VarianteVTS o AuditoriaVTS
      - Registra cada movimiento en RegistroLogs y VentaRegistrada
    Retorna dict con resumen del proceso.
    """
    resultado = {
        'procesadas':   0,
        'duplicadas':   0,
        'sin_match':    [],
        'errores':      [],
        'total_bruto':  0.0,
    }
 
    for fila in filas_validas:
        descripcion  = fila.get('Descripción',      '').strip()
        cantidad     = int(float(fila.get('Cantidad', 1) or 1))
        precio_bruto = float(fila.get('Precio (Bruto)', 0) or 0)
        id_tx        = fila.get('ID de transacción', '').strip()
 
        sku = buscar_sku_por_nombre(descripcion)
 
        if not sku:
            resultado['sin_match'].append({
                'descripcion': descripcion,
                'id_tx':       id_tx,
                'cantidad':    cantidad,
            })
            continue
 
        # ── Candado anti-doble descuento ──────────────────────────
        if VentaRegistrada.objects.filter(id_transaccion=id_tx, sku=sku).exists():
            resultado['duplicadas'] += 1
            continue
 
        try:
            variante = VarianteVTS.objects.filter(sku_variante=sku).first()
 
            if variante:
                variante.inventario_real = max(0, variante.inventario_real - cantidad)
                variante.save()
                producto_nombre = f"{variante.producto.producto} / {variante.nombre_variante}"
            else:
                producto = AuditoriaVTS.objects.get(sku=sku)
                producto.inventario_real = max(0, producto.inventario_real - cantidad)
                producto.save()
                producto_nombre = producto.producto
 
            # Registrar en log
            RegistroLogs.objects.create(
                operador    = operador,
                tipo_accion = 'VENTA_SUMUP',
                sku         = sku,
                producto    = f"TX:{id_tx} | {producto_nombre} | Cant:{cantidad} | Bruto:${precio_bruto:,.0f}",
                cantidad    = cantidad,
            )
 
            # Registrar candado
            VentaRegistrada.objects.create(
                id_transaccion = id_tx,
                sku            = sku,
                operador       = operador,
            )
 
            resultado['procesadas']  += 1
            resultado['total_bruto'] += precio_bruto
 
        except AuditoriaVTS.DoesNotExist:
            resultado['errores'].append({
                'id_tx':       id_tx,
                'sku':         sku,
                'descripcion': descripcion,
                'motivo':      f'SKU {sku} no encontrado en VTS',
            })
        except Exception as e:
            resultado['errores'].append({
                'id_tx':       id_tx,
                'sku':         sku,
                'descripcion': descripcion,
                'motivo':      str(e),
            })
 
    return resultado
 
 
# =================================================================
# V. RESUMEN LEGIBLE
# =================================================================
 
def resumen_proceso(resultado: dict) -> str:
    """Genera texto legible del resultado de procesar_ventas()."""
    lineas = [
        f"✅ Procesadas:    {resultado['procesadas']}",
        f"💰 Total bruto:   ${resultado['total_bruto']:,.0f}",
        f"⚠️  Sin match:     {len(resultado['sin_match'])}",
        f"🔁 Duplicadas:    {resultado['duplicadas']}",
        f"❌ Errores:       {len(resultado['errores'])}",
    ]
 
    if resultado['sin_match']:
        lineas.append("\n— Sin match —")
        for item in resultado['sin_match']:
            lineas.append(
                f"  · {item['descripcion']} (TX:{item['id_tx']}, x{item['cantidad']})"
            )
 
    if resultado['errores']:
        lineas.append("\n— Errores —")
        for err in resultado['errores']:
            lineas.append(
                f"  · SKU:{err['sku']} | {err['descripcion']} → {err['motivo']}"
            )
 
    return "\n".join(lineas)