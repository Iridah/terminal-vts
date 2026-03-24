# Script para ejecutar en Mardum via manage.py shell
# Crea los SKUs nuevos y la variante de Protex
 
from dashboard.models import AuditoriaVTS, VarianteVTS
 
nuevos = [
    # (sku, producto, seccion, precio_venta)
    ('V-CPE-007', 'ELITE Pañuelos Triple Hoja 10 Un',          'Cuidado Personal', 200),
    ('V-BEB-002', 'EMUBABY Toallitas Húmedas Sin Alcohol 100 Un','Bebe',           1100),
    ('V-LIM-032', 'IGENIX Cloro Gel Lavanda Botella 900 ml',    'Limpieza',        1400),
    ('V-LIM-033', 'MANIAC Set 3 Esponjas Metalicas Doradas',    'Limpieza',        1500),
    ('V-LIB-019', 'PROARTE Cola fria 125 ml',                   'Libreria',        1000),
    ('V-LIM-034', 'SOFT Suavizante Clasic refill 900 mL',       'Limpieza',        1200),
    ('V-LIM-031', 'V-STORE Toallitas Antigrasa 80 u',           'Limpieza',        1250),
]
 
criocongelar = ['Humidificador Ambiental de Escritorio', 'Mochilas Surtidas']
 
for sku, producto, seccion, pventa in nuevos:
    obj, created = AuditoriaVTS.objects.get_or_create(
        sku=sku,
        defaults={
            'producto':       producto,
            'seccion':        seccion,
            'precio_venta':   pventa,
            'inventario_real': 0,
            'stock_sistema':   0,
        }
    )
    print(f"{'CREADO' if created else 'YA EXISTE'}: {sku} | {producto}")
 
# Variante Protex Aloe
protex = AuditoriaVTS.objects.filter(sku='V-CPE-006').first()
if protex:
    var, created = VarianteVTS.objects.get_or_create(
        sku_variante='V-CPE-006-Aloe',
        defaults={
            'producto':        protex,
            'nombre_variante': 'Aloe Vera 125g',
            'precio_venta':    950,
            'inventario_real': 0,
            'stock_sistema':   0,
        }
    )
    print(f"{'CREADO' if created else 'YA EXISTE'}: V-CPE-006-Aloe | Aloe Vera 125g")
 
# Criocongelar productos obsoletos
for nombre in criocongelar:
    p = AuditoriaVTS.objects.filter(producto__icontains=nombre[:20]).first()
    if p and p.estado != 'criocongelado':
        p.estado = 'criocongelado'
        p.save()
        print(f"CRIOCONGELADO: {p.sku} | {p.producto}")
    elif p:
        print(f"YA CRIOCONGELADO: {p.sku} | {p.producto}")
    else:
        print(f"NO ENCONTRADO: {nombre}")
 
print("\nListo.")
 