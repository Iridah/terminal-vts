#!/usr/bin/env python
"""
exportar_vts.py
Exporta la mercaderia de AuditoriaVTS al CSV del ecommerce.

CORRER EN MARDUM dentro de VTS:

    cd ~/Programacion/VTS
    source venv/bin/activate
    python exportar_vts.py

Genera vts_export.csv en el mismo directorio.
Luego:
    cp ~/Programacion/VTS/vts_export.csv \
       ~/Programacion/ecommerce_vacadari/vts_export.csv

CAMPOS USADOS DE AuditoriaVTS
    producto        → nombre
    seccion         → categoria
    precio_venta    → precio (precio de venta al publico)
    inventario_real → stock  (stock fisico real, no el de sistema)
    imagen          → imagen (ya en WEBP, upload_to='productos/')
    variante        → descripcion (color/fragancia si aplica)
    estado          → filtro: solo 'activo' (excluye criocongelado/descontinuado)
    sku             → codigo de referencia
"""

import os
import csv
import sys
import django
from pathlib import Path

# ── Setup Django de VTS ───────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'martillo_vil.settings')
django.setup()

from dashboard.models.inventario import AuditoriaVTS  # noqa: E402

# ── Queryset: solo productos activos con precio_venta > 0 ─────────────────────
qs = (
    AuditoriaVTS.objects
    .filter(estado='activo', precio_venta__gt=0)
    .order_by('seccion', 'producto')
)

total = qs.count()
print(f'Productos activos con precio: {total}')

if total == 0:
    print('\nNo hay productos para exportar.')
    print('Verificar: estado="activo" y precio_venta > 0 en la BD.')
    sys.exit(0)

# ── Exportar ──────────────────────────────────────────────────────────────────
OUTPUT = BASE_DIR / 'vts_export.csv'

exportados = 0
sin_imagen = 0
sin_stock  = 0

with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    # Cabecera — seed_vts.py espera exactamente estos nombres
    writer.writerow([
        'nombre',
        'categoria',
        'precio',
        'stock',
        'descripcion',
        'imagen',
        'sku_vts',
    ])

    for obj in qs:
        # Nombre del archivo de imagen (solo el basename, sin prefijo 'productos/')
        imagen_nombre = ''
        if obj.imagen and obj.imagen.name:
            imagen_nombre = Path(obj.imagen.name).name   # ej: IMG_2770-Photoroom.webp

        # Descripcion: variante si existe, string vacio si no
        descripcion = (obj.variante or '').strip()

        writer.writerow([
            obj.producto,                   # nombre
            obj.seccion,                    # categoria → seccion
            int(obj.precio_venta),          # precio como entero CLP
            obj.inventario_real,            # stock real
            descripcion,                    # variante como descripcion
            imagen_nombre,                  # solo el nombre del archivo
            obj.sku,                        # referencia VTS
        ])

        exportados += 1
        if not imagen_nombre:
            sin_imagen += 1
        if obj.inventario_real <= 0:
            sin_stock += 1

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f'\nCSV generado: {OUTPUT}')
print(f'  exportados   : {exportados}')
print(f'  sin imagen   : {sin_imagen}')
print(f'  sin stock    : {sin_stock}  (se cargan igual, disponible=False)')
print(f'\nDetalle por seccion:')

from django.db.models import Count
for row in (
    AuditoriaVTS.objects
    .filter(estado='activo', precio_venta__gt=0)
    .values('seccion')
    .annotate(n=Count('sku'))
    .order_by('seccion')
):
    print(f'  {row["seccion"]:<20} {row["n"]:>4} productos')

print(f'\nSiguiente paso:')
print(f'  cp {OUTPUT}')
print(f'     ~/Programacion/ecommerce_vacadari/vts_export.csv')
