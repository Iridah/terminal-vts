# dashboard/management/commands/importar_historial_ventas.py
# Comando: python manage.py importar_historial_ventas --csv /ruta/al/archivo.csv
# Importa CSV histórico de SumUp a HistorialVentas SIN tocar inventario ni VentaRegistrada
 
import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
 
 
class Command(BaseCommand):
    help = 'Importa CSV histórico de ventas SumUp a HistorialVentas (solo análisis, sin descontar stock)'
 
    def add_arguments(self, parser):
        parser.add_argument('--csv', required=True, help='Ruta al CSV de ventas SumUp')
        parser.add_argument('--dry-run', action='store_true', help='Solo simula, no escribe')
 
    def handle(self, *args, **options):
        from dashboard.models import HistorialVentas
 
        csv_path = options['csv']
        dry_run  = options['dry_run']
 
        self.stdout.write(self.style.WARNING(
            f"\n{'[DRY RUN] ' if dry_run else ''}Importando historial desde {csv_path}\n"
        ))
 
        stats = {
            'creados':    0,
            'duplicados': 0,
            'errores':    0,
            'ignorados':  0,
        }
 
        with open(csv_path, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            filas  = [r for r in reader if r.get('Tipo','').strip() == 'Venta']
 
        self.stdout.write(f"Filas tipo Venta: {len(filas)}")
 
        if not dry_run:
            with transaction.atomic():
                for fila in filas:
                    descripcion  = fila.get('Descripción', '').strip()
                    id_tx        = fila.get('ID de transacción', '').strip()
                    precio_bruto = float(fila.get('Precio (Bruto)', 0) or 0)
                    descuento    = float(fila.get('Descuento', 0) or 0)
                    precio_orig  = float(fila.get('Precio sin descuento', 0) or 0)
                    cantidad     = int(float(fila.get('Cantidad', 1) or 1))
                    fecha_str    = fila.get('Fecha', '').strip()
 
                    if not descripcion or not id_tx:
                        stats['ignorados'] += 1
                        continue
 
                    # Calcular % descuento
                    try:
                        pct_dto = round((descuento / precio_orig) * 100) if precio_orig > 0 else 0
                    except:
                        pct_dto = 0
                    es_ap_hogar = (pct_dto == 40)
 
                    # Parsear fecha
                    try:
                        fecha = datetime.strptime(
                            fecha_str.split(',')[0].strip(), '%d-%m-%Y'
                        ).date()
                    except:
                        from django.utils import timezone
                        fecha = timezone.now().date()
 
                    try:
                        _, created = HistorialVentas.objects.get_or_create(
                            id_transaccion = id_tx,
                            descripcion    = descripcion,
                            defaults={
                                'fecha':        fecha,
                                'cantidad':     cantidad,
                                'precio_bruto': precio_bruto,
                                'descuento':    descuento,
                                'es_ap_hogar':  es_ap_hogar,
                            }
                        )
                        if created:
                            stats['creados'] += 1
                        else:
                            stats['duplicados'] += 1
                    except Exception as e:
                        stats['errores'] += 1
                        self.stdout.write(self.style.ERROR(f"  Error: {id_tx} | {descripcion[:30]} → {e}"))
 
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"{'[DRY RUN] ' if dry_run else ''}RESULTADO:"))
        self.stdout.write(f"  Creados:    {stats['creados']}")
        self.stdout.write(f"  Duplicados: {stats['duplicados']}")
        self.stdout.write(f"  Ignorados:  {stats['ignorados']}")
        self.stdout.write(f"  Errores:    {stats['errores']}")
        self.stdout.write("="*50 + "\n")