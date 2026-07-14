# dashboard/management/commands/exportar_sumup.py
# Contiene toda la mecanica para la generacion del CSV que se cargara posteriormente a Sumup
import csv
import os

from django.core.management.base import BaseCommand
from dashboard.models import AuditoriaVTS, VarianteVTS


COLORES_SECCION = {
    'Abarrotes':        'Yellow',
    'Electronica':      'Light red',
    'Ferreteria':       'Light green',
    'Libreria':         'Orange',
    'Limpieza':         'Pink',
    'Menaje':           'Dark red',
    'Cuidado Personal': 'Dark green',
    'Colaciones':       'Light blue',
    'Boutique':         '',
    'Bebe':             '',
}

COLUMNAS = [
    'Item name', 'Variations', 'Option set 1', 'Option 1',
    'Option set 2', 'Option 2', 'Option set 3', 'Option 3',
    'Option set 4', 'Option 4', 'Is variation visible? (Yes/No)',
    'Price', 'Cost price', 'Variable price? (Yes/No)', 'Tax rate (%)',
    'On sale in Online Store?', 'Regular price (before sale)',
    'Set up different prices and VAT for takeaway', 'Takeaway price',
    'Takeaway tax rate', 'Unit', 'Track inventory? (Yes/No)',
    'Quantity', 'Low stock threshold', 'SKU', 'Barcode', 'Modifiers',
    'Description (Online Store and Invoices only)', 'Category',
    'Display item at Checkout? (Yes/No)',
    'Display colour in POS checkout',
    'Image 1', 'Image 2', 'Image 3', 'Image 4', 'Image 5',
    'Image 6', 'Image 7',
    'Display item in Online Store? (Yes/No)',
    'SEO title (Online Store only)', 'SEO description (Online Store only)',
    'Shipping weight [kg] (Online Store only)',
    'Display service in Bookings? (Yes/No)',
    'Duration [minutes] (Bookings only)',
    'Location [business/customer] (Bookings only)',
    'Item id (Do not change)', 'Variant id (Do not change)',
]


def imagen_valida(url):
    """Solo acepta URLs vivas de SumUp. Filtra las de images-admin (CDN interno, 404)."""
    return isinstance(url, str) and url.startswith('https://images.sumup.com/')


class Command(BaseCommand):
    help = 'Exporta catálogo VTS en formato CSV listo para importar en SumUp'

    def add_arguments(self, parser):
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        parser.add_argument(
            '--csv-base',
            required=False,
            default=None,
            help='Ruta al CSV exportado de SumUp (para preservar IDs e imágenes)'
        )
        parser.add_argument(
            '--output',
            default=f'/mnt/storage/proyectos/VTS/backups/VTSsumup_export_{timestamp}.csv',
            help='Ruta del CSV de salida'
        )

    def handle(self, *args, **options):
        csv_base = options['csv_base']
        output   = options['output']

        # ── 1. Leer CSV base de SumUp ─────────────────────────────────────
        base_por_itemid       = {}  # item_id → fila madre
        base_por_sku_variante = {}  # sku_variante → {variant_id, imágenes}

        if csv_base:
            with open(csv_base, encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for fila in reader:
                    item_id    = fila.get('Item id (Do not change)', '').strip()
                    variant_id = fila.get('Variant id (Do not change)', '').strip()
                    item_name  = fila.get('Item name', '').strip()
                    sku        = fila.get('SKU', '').strip()

                    if item_name and item_id:
                        base_por_itemid[item_id] = fila
                    elif not item_name and sku and variant_id:
                        base_por_sku_variante[sku] = {
                            'variant_id': variant_id,
                            **{f'Image {i}': fila.get(f'Image {i}', '') for i in range(1, 8)}
                        }
            self.stdout.write(
                f"Base SumUp: {len(base_por_itemid)} productos, "
                f"{len(base_por_sku_variante)} variantes"
            )
        else:
            self.stdout.write("Sin CSV base — catálogo limpio")

        # ── 2. Construir filas desde VTS ──────────────────────────────────
        filas_output = []

        for prod in AuditoriaVTS.objects.filter(
            estado__in=['activo', 'criocongelado']
        ).prefetch_related('variantes').order_by('seccion', 'producto'):

            color           = COLORES_SECCION.get(prod.seccion, '')
            variantes       = list(prod.variantes.filter(estado__in=['activo', 'criocongelado']))
            tiene_variantes = len(variantes) > 0

            # Lookup por sumup_item_id (robusto, no depende del nombre)
            item_id_preservado = prod.sumup_item_id or ''
            fila_base          = base_por_itemid.get(item_id_preservado) if item_id_preservado else None

            # Imágenes: solo URLs vivas, filtra CDN interno con 404
            imagenes = [
                fila_base.get(f'Image {i}', '') if imagen_valida(fila_base.get(f'Image {i}', '')) else ''
                for i in range(1, 8)
            ] if fila_base else [''] * 7

            # ── Fila madre ────────────────────────────────────────────────
            fila_madre = {col: '' for col in COLUMNAS}
            fila_madre.update({
                'Item name':                                    prod.producto,
                'Price':                                        '' if tiene_variantes else str(int(prod.precio_venta)),
                'Cost price':                                   '',
                'Variable price? (Yes/No)':                     'No',
                'Tax rate (%)':                                 '19.00',
                'On sale in Online Store?':                     'No',
                'Set up different prices and VAT for takeaway': 'No',
                'Unit':                                         'each.each',
                'Track inventory? (Yes/No)':                    'Yes' if not tiene_variantes else 'No',
                'Quantity':                                     str(prod.inventario_real) if not tiene_variantes else '',
                'Low stock threshold':                          '',
                'SKU':                                          prod.sku if not tiene_variantes else '',
                'Category':                                     prod.seccion,
                'Display item at Checkout? (Yes/No)':           'Yes',
                'Display colour in POS checkout':               color,
                'Display item in Online Store? (Yes/No)':       'Yes',
                'SEO title (Online Store only)':                prod.producto,
                'Item id (Do not change)':                      item_id_preservado,
            })
            for i, img in enumerate(imagenes, 1):
                fila_madre[f'Image {i}'] = img

            filas_output.append(fila_madre)

            # ── Filas variantes ───────────────────────────────────────────
            for var in variantes:
                datos_base            = base_por_sku_variante.get(var.sku_variante, {})
                # En las filas variantes, solo preservar variant_id si el producto madre tiene item_id
                variant_id_preservado = datos_base.get('variant_id', '') if item_id_preservado else ''
                img_var = [
                    datos_base.get(f'Image {i}', '') if imagen_valida(datos_base.get(f'Image {i}', '')) else ''
                    for i in range(1, 8)
                ]

                fila_var = {col: '' for col in COLUMNAS}
                fila_var.update({
                    'Variations':                     var.nombre_variante,
                    'Is variation visible? (Yes/No)': 'Yes',
                    'Price':                          str(int(float(var.precio_venta))) if var.precio_venta else '0',
                    'Cost price':                     '',
                    'Track inventory? (Yes/No)':      'Yes',
                    'Quantity':                       str(var.inventario_real),
                    'SKU':                            var.sku_variante,
                    'Variant id (Do not change)':     variant_id_preservado,
                })
                for i, img in enumerate(img_var, 1):
                    fila_var[f'Image {i}'] = img

                filas_output.append(fila_var)

        # ── 3. Escribir CSV ───────────────────────────────────────────────
        with open(output, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNAS)
            writer.writeheader()
            writer.writerows(filas_output)

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ CSV exportado: {output} ({len(filas_output)} filas)"
        ))
        self.stdout.write(
            f"   Subir en SumUp → Productos → Biblioteca → Carga masiva"
        )

        return output