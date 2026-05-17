import pandas as pd
import os
from django.core.management.base import BaseCommand
from dashboard.models import AuditoriaVTS
from django.conf import settings
from django.db.models import Q

class Command(BaseCommand):
    help = 'Succiona datos con Costo Inteligente y Limpieza Quirúrgica'

    def handle(self, *args, **options):
        # Localizamos la carpeta CLI (un nivel arriba de PORTAL)
        cli_path = os.path.join(settings.BASE_DIR, '..', 'CLI')
        archivos = [f for f in os.listdir(cli_path) if f.startswith('AUDITORIA_VTS') and f.endswith('.csv')]
        
        if not archivos:
            self.stdout.write(self.style.ERROR('No hay galletas para succionar.'))
            return

        ultimo_archivo = sorted(archivos)[-1]
        ruta_completa = os.path.join(cli_path, ultimo_archivo)
        
        # 🛡️ CARGA Y LIMPIEZA
        df = pd.read_csv(ruta_completa)
        
        # 1. Filtro estricto: SKU debe empezar con 'V-' (Neutraliza la línea 17 con la %)
        df = df[df['sku'].astype(str).str.startswith('V-', na=False)] 
        
        self.stdout.write(self.style.WARNING(f'Procesando: {ultimo_archivo}'))

        for _, row in df.iterrows():
            sku_actual = row['sku']
            
            # 💰 LÓGICA DE COSTO INTELIGENTE
            costo_csv = row['nuevo_costo']
            if pd.isna(costo_csv) or costo_csv == 0:
                ultimo_registro = AuditoriaVTS.objects.filter(sku=sku_actual).exclude(precio_costo=0).order_by('-fecha_auditoria').first()
                costo_final = float(ultimo_registro.precio_costo) if ultimo_registro else 1000.0
            else:
                costo_final = float(costo_csv)

            # 🛡️ LÓGICA DE INVENTARIO A PRUEBA DE MINAS (NaN a 0)
            raw_inv = pd.to_numeric(row['inventario_real'], errors='coerce')
            inventario_final = int(0 if pd.isna(raw_inv) else raw_inv)

            # 🚀 LA GRAN SUCCIÓN
            AuditoriaVTS.objects.update_or_create(
                sku=sku_actual,
                defaults={
                    'producto': row['producto'],
                    'seccion': row['Seccion'],
                    'stock_sistema': row['stock_sistema'],
                    'inventario_real': inventario_final,
                    'precio_costo': costo_final,
                    'precio_venta': costo_final * 1.3,
                    'documento_tipo': 'BOLETA'
                }
            )

        self.stdout.write(self.style.SUCCESS('¡Dashboard Regularizado! Barras de pérdida activas.'))