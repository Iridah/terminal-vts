# Script para ejecutar en Mardum via manage.py shell
# Documenta el recatálogo de la línea Andina retornable/vidrio (V-ABA-003/004/009)
# ejecutado en vivo el 2026-08-21. Se deja este .py para que el próximo
# correlativo V-ABA no colisione con estos SKUs (idempotente: get_or_create /
# update_or_create en todo).

from dashboard.models import AuditoriaVTS, VarianteVTS

# --- Renombrar padres: de nomenclatura Coca-Cola a nomenclatura Andina ---
renombres = [
    ('V-ABA-003', 'Andina Variedades Retornable 3Lt'),
    ('V-ABA-004', 'Andina Variedades Retornable 2Lt'),
]
for sku, nuevo_nombre in renombres:
    p = AuditoriaVTS.objects.filter(sku=sku).first()
    if p and p.producto != nuevo_nombre:
        p.producto = nuevo_nombre
        p.save()
        print(f"RENOMBRADO: {sku} -> {nuevo_nombre}")
    elif p:
        print(f"YA RENOMBRADO: {sku}")
    else:
        print(f"NO ENCONTRADO: {sku}")

# --- V-ABA-003: unificar costo (precio refill, no cuenta empresa) + variantes nuevas ---
p003 = AuditoriaVTS.objects.filter(sku='V-ABA-003').first()
if p003:
    for sku_variante, nombre_variante in [
        ('V-ABA-003-Orig', 'Coca-Cola Original'),
        ('V-ABA-003-Zero', 'Coca-Cola Zero'),
        ('V-ABA-003-Fant', 'Fanta'),
        ('V-ABA-003-Spri', 'Sprite'),
    ]:
        var, created = VarianteVTS.objects.update_or_create(
            sku_variante=sku_variante,
            defaults={
                'producto': p003,
                'nombre_variante': nombre_variante,
                'precio_costo': 2190,
                'precio_venta': 2650,
            }
        )
        print(f"{'CREADO' if created else 'ACTUALIZADO'}: {sku_variante} | {nombre_variante}")

# --- V-ABA-004: unificar costo + variantes nuevas (chevron de 4 caracteres) ---
p004 = AuditoriaVTS.objects.filter(sku='V-ABA-004').first()
if p004:
    for sku_variante, nombre_variante in [
        ('V-ABA-004-Orig', 'Coca-Cola Original'),
        ('V-ABA-004-Zero', 'Coca-Cola Zero'),
        ('V-ABA-004-Ligh', 'Coca-Cola Light'),
        ('V-ABA-004-FaOr', 'Fanta Original'),
        ('V-ABA-004-FaZe', 'Fanta Zero'),
        ('V-ABA-004-SpOr', 'Sprite Original'),
        ('V-ABA-004-SpZe', 'Sprite Zero'),
        ('V-ABA-004-Inca', 'Inca Kola'),
    ]:
        var, created = VarianteVTS.objects.update_or_create(
            sku_variante=sku_variante,
            defaults={
                'producto': p004,
                'nombre_variante': nombre_variante,
                'precio_costo': 1590,
                'precio_venta': 1750,
            }
        )
        print(f"{'CREADO' if created else 'ACTUALIZADO'}: {sku_variante} | {nombre_variante}")

# --- V-ABA-009: familia nueva, vidrio 1.25Lt (distinta de los retornables 2/3Lt, que son plástico) ---
p009, created = AuditoriaVTS.objects.get_or_create(
    sku='V-ABA-009',
    defaults={
        'producto': 'Andina Variedades Vidrio 1.25Lt',
        'seccion': 'Abarrotes',
        'precio_costo': 1090,
        'precio_venta': 0,  # pendiente: falta precio de venta al público, solo se dio el precio web (costo)
        'documento_tipo': 'FACTURA',
        'inventario_real': 0,
        'stock_sistema': 0,
    }
)
print(f"{'CREADO' if created else 'YA EXISTE'}: V-ABA-009 | Andina Variedades Vidrio 1.25Lt")

if p009 if created else AuditoriaVTS.objects.filter(sku='V-ABA-009').exists():
    p009 = AuditoriaVTS.objects.get(sku='V-ABA-009')
    for sku_variante, nombre_variante in [
        ('V-ABA-009-Orig', 'Coca-Cola Original'),
        ('V-ABA-009-Zero', 'Coca-Cola Zero'),
        ('V-ABA-009-Inca', 'Inca Kola'),
        ('V-ABA-009-Fant', 'Fanta'),
    ]:
        var, created = VarianteVTS.objects.update_or_create(
            sku_variante=sku_variante,
            defaults={
                'producto': p009,
                'nombre_variante': nombre_variante,
                'precio_costo': 1090,
                'precio_venta': 0,  # pendiente, ver nota arriba
                'documento_tipo': 'BOLETA',
            }
        )
        print(f"{'CREADO' if created else 'ACTUALIZADO'}: {sku_variante} | {nombre_variante}")

print("\nListo. Correlativos V-ABA ocupados tras este script: 001-010 sin huecos.")
