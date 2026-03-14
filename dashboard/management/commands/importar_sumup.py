# dashboard/management/commands/importar_sumup.py
# Comando: python manage.py importar_sumup --csv /ruta/al/archivo.csv
# Hace backup, merge inteligente, reporta inconsistencias
 
import csv
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
 
 
SECCION_MAP = {
    'Limpieza':         'Limpieza',
    'Higiene':          'Cuidado Personal',
    'Cuidado Personal': 'Cuidado Personal',
    'Electronica':      'Electronica',
    'Libreria':         'Libreria',
    'Abarrotes':        'Abarrotes',
    'Bebe':             'Bebe',
    'Boutique':         'Boutique',
    'Ferreteria':       'Ferreteria',
    'Menaje':           'Menaje',
}
 
 
class Command(BaseCommand):
    help = 'Importa/actualiza productos VTS desde CSV de inventario SumUp'
 
    def add_arguments(self, parser):
        parser.add_argument('--csv',     required=True, help='Ruta al CSV de SumUp')
        parser.add_argument('--dry-run', action='store_true', help='Solo simula, no escribe en BD')
 
    def handle(self, *args, **options):
        from dashboard.models import AuditoriaVTS, VarianteVTS
 
        csv_path = options['csv']
        dry_run  = options['dry_run']
 
        self.stdout.write(self.style.WARNING(
            f"\n{'[DRY RUN] ' if dry_run else ''}Iniciando importación desde {csv_path}\n"
        ))
 
        # ── 1. BACKUP ────────────────────────────────────────────
        backup_path = f"/tmp/vts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup = []
        for p in AuditoriaVTS.objects.all():
            backup.append({
                'sku': p.sku, 'producto': p.producto, 'seccion': p.seccion,
                'precio_costo': str(p.precio_costo), 'precio_venta': str(p.precio_venta),
                'inventario_real': p.inventario_real, 'estado': p.estado,
            })
        for v in VarianteVTS.objects.all():
            backup.append({
                'sku_variante': v.sku_variante, 'producto_id': v.producto_id,
                'nombre_variante': v.nombre_variante,
                'precio_costo': str(v.precio_costo), 'precio_venta': str(v.precio_venta),
                'inventario_real': v.inventario_real, 'estado': v.estado,
            })
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup, f, ensure_ascii=False, indent=2)
        self.stdout.write(self.style.SUCCESS(f"✓ Backup guardado en {backup_path}"))
 
        # ── 2. LEER CSV ──────────────────────────────────────────
        productos_por_itemid = {}
        variantes_data = []
 
        with open(csv_path, encoding='utf-8-sig') as f:
            reader      = csv.DictReader(f)
            item_actual = None
 
            for fila in reader:
                item_name  = fila.get('Item name',  '').strip()
                sku        = fila.get('SKU',         '').strip()
                item_id    = fila.get('Item id (Do not change)', '').strip()
                variacion  = fila.get('Variations', '').strip()
                precio_str = fila.get('Price', '0').strip()
                categoria  = fila.get('Category', '').strip()
 
                try:
                    precio = float(precio_str) if precio_str else 0.0
                except ValueError:
                    precio = 0.0
 
                seccion = SECCION_MAP.get(categoria, categoria or 'Limpieza')
 
                if item_name:
                    item_actual = {
                        'item_id': item_id,
                        'nombre':  item_name,
                        'sku':     sku,
                        'seccion': seccion,
                        'precio':  precio,
                    }
                    productos_por_itemid[item_id] = item_actual
 
                elif variacion and item_actual:
                    variantes_data.append({
                        'item_id':   item_actual['item_id'],
                        'nombre':    item_actual['nombre'],
                        'seccion':   item_actual['seccion'],
                        'variacion': variacion,
                        'sku':       sku,
                        'precio':    precio,
                    })
 
        self.stdout.write(
            f"\nCSV: {len(productos_por_itemid)} productos madre, {len(variantes_data)} variantes"
        )
 
        # ── 3. MERGE ─────────────────────────────────────────────
        stats = {
            'prod_creados': 0, 'prod_actualizados': 0, 'prod_sin_sku': 0,
            'var_creadas':  0, 'var_actualizadas':  0, 'var_sin_sku':  0,
            'inconsistencias': [],
        }
 
        if not dry_run:
            with transaction.atomic():
 
                # ── Productos madre con SKU propio ───────────────
                for item_id, datos in productos_por_itemid.items():
                    if not datos['sku']:
                        stats['prod_sin_sku'] += 1
                        continue
 
                    try:
                        prod = AuditoriaVTS.objects.get(sku=datos['sku'])
                        prod.producto = datos['nombre']
                        prod.seccion  = datos['seccion']
                        if float(prod.precio_venta) == 0 and datos['precio'] > 0:
                            prod.precio_venta = datos['precio']
                        prod.save()
                        stats['prod_actualizados'] += 1
                    except AuditoriaVTS.DoesNotExist:
                        AuditoriaVTS.objects.create(
                            sku             = datos['sku'],
                            producto        = datos['nombre'],
                            seccion         = datos['seccion'],
                            precio_venta    = datos['precio'],
                            inventario_real = 0,
                            stock_sistema   = 0,
                        )
                        stats['prod_creados'] += 1
 
                # ── Variantes ────────────────────────────────────
                for datos in variantes_data:
                    if not datos['sku']:
                        stats['var_sin_sku'] += 1
                        continue
 
                    # Buscar padre por nombre en VTS
                    padre = AuditoriaVTS.objects.filter(
                        producto=datos['nombre']
                    ).first()
 
                    # Si no existe, inferir SKU madre desde el SKU variante
                    # Ej: V-LIM-017-CoVa → V-LIM-017
                    if not padre:
                        partes    = datos['sku'].split('-')
                        sku_madre = '-'.join(partes[:3]) if len(partes) >= 4 else None
 
                        if sku_madre:
                            padre = AuditoriaVTS.objects.filter(sku=sku_madre).first()
 
                        if not padre and sku_madre:
                            padre = AuditoriaVTS.objects.create(
                                sku             = sku_madre,
                                producto        = datos['nombre'],
                                seccion         = datos['seccion'],
                                inventario_real = 0,
                                stock_sistema   = 0,
                            )
                            stats['prod_creados'] += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  → Padre creado: {sku_madre} ({datos['nombre']})"
                                )
                            )
 
                        if not padre:
                            stats['inconsistencias'].append(
                                f"Variante {datos['sku']} — no se pudo resolver padre"
                            )
                            continue
 
                    # Crear o actualizar variante
                    try:
                        var = VarianteVTS.objects.get(sku_variante=datos['sku'])
                        var.nombre_variante = datos['variacion']
                        var.producto        = padre
                        if float(var.precio_venta) == 0 and datos['precio'] > 0:
                            var.precio_venta = datos['precio']
                        var.save()
                        stats['var_actualizadas'] += 1
                    except VarianteVTS.DoesNotExist:
                        VarianteVTS.objects.create(
                            sku_variante    = datos['sku'],
                            producto        = padre,
                            nombre_variante = datos['variacion'],
                            precio_venta    = datos['precio'],
                            inventario_real = 0,
                            stock_sistema   = 0,
                        )
                        stats['var_creadas'] += 1
 
        # ── 4. REPORTE ───────────────────────────────────────────
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(
            f"{'[SIMULACIÓN] ' if dry_run else ''}RESULTADO:"
        ))
        self.stdout.write(f"  Productos creados:      {stats['prod_creados']}")
        self.stdout.write(f"  Productos actualizados: {stats['prod_actualizados']}")
        self.stdout.write(f"  Productos sin SKU:      {stats['prod_sin_sku']}")
        self.stdout.write(f"  Variantes creadas:      {stats['var_creadas']}")
        self.stdout.write(f"  Variantes actualizadas: {stats['var_actualizadas']}")
        self.stdout.write(f"  Variantes sin SKU:      {stats['var_sin_sku']}")
 
        if stats['inconsistencias']:
            self.stdout.write(self.style.WARNING("\n  Inconsistencias:"))
            for inc in stats['inconsistencias']:
                self.stdout.write(f"    ⚠ {inc}")
        else:
            self.stdout.write(self.style.SUCCESS("  Sin inconsistencias ✓"))
 
        self.stdout.write(f"\n  Backup en: {backup_path}")
        self.stdout.write("="*50 + "\n")