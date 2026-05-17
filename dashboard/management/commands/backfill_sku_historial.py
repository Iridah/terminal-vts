# dashboard/management/commands/backfill_sku_historial.py
from django.core.management.base import BaseCommand
from dashboard.models import HistorialVentas
from dashboard.odd import buscar_sku_por_nombre

class Command(BaseCommand):
    help = 'Rellena SKU faltante en HistorialVentas usando matching de odd.py'

    def handle(self, *args, **kwargs):
        sin_sku = HistorialVentas.objects.filter(sku__isnull=True)
        self.stdout.write(f"Registros sin SKU: {sin_sku.count()}")
        
        resueltos = 0
        no_match  = set()

        for hv in sin_sku:
            sku = buscar_sku_por_nombre(hv.descripcion)
            if sku:
                hv.sku = sku
                hv.save(update_fields=['sku'])
                resueltos += 1
            else:
                no_match.add(hv.descripcion)

        self.stdout.write(f"Resueltos: {resueltos}")
        self.stdout.write(f"Sin match: {len(no_match)}")
        for desc in sorted(no_match):
            self.stdout.write(f"  · {desc}")