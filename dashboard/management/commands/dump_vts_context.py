# dashboard/management/commands/dump_vts_context.py
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from dashboard.models import (
    AuditoriaVTS, VarianteVTS, HistorialVentas, RegistroLogs
)

class Command(BaseCommand):
    help = 'Exporta contexto operacional VTS para IA local (Caspar·3)'

    def handle(self, *args, **kwargs):
        hoy     = timezone.now().date()
        hace_30 = hoy - timedelta(days=30)
        hace_90 = hoy - timedelta(days=90)

        # ── INVENTARIO ────────────────────────────────────────────
        self.stdout.write("=== INVENTARIO ACTIVO ===")
        total_valor_costo = 0
        total_valor_venta = 0

        for p in AuditoriaVTS.objects.filter(estado='activo'):
            vc = float(p.precio_costo) * p.inventario_real
            vv = float(p.precio_venta) * p.inventario_real
            total_valor_costo += vc
            total_valor_venta += vv
            self.stdout.write(
                f"SIMPLE|{p.sku}|{p.producto}|{p.seccion}|"
                f"stock:{p.inventario_real}|"
                f"costo:{p.precio_costo}|"
                f"venta:{p.precio_venta}|"
                f"valor_stock_costo:{vc:.0f}|"
                f"estado:{p.estado}"
            )

        for v in VarianteVTS.objects.select_related('producto').filter(
            estado='activo', producto__estado='activo'
        ):
            vc = float(v.precio_costo) * v.inventario_real
            vv = float(v.precio_venta) * v.inventario_real
            total_valor_costo += vc
            total_valor_venta += vv
            self.stdout.write(
                f"VARIANTE|{v.sku_variante}|"
                f"{v.producto.producto} / {v.nombre_variante}|"
                f"{v.producto.seccion}|"
                f"stock:{v.inventario_real}|"
                f"costo:{v.precio_costo}|"
                f"venta:{v.precio_venta}|"
                f"valor_stock_costo:{vc:.0f}|"
                f"estado:{v.estado}"
            )

        self.stdout.write(f"\nRESUMEN_INVENTARIO|"
                         f"valor_costo_total:{total_valor_costo:.0f}|"
                         f"valor_venta_total:{total_valor_venta:.0f}|"
                         f"margen_potencial:{total_valor_venta - total_valor_costo:.0f}")

        # ── VENTAS 30 DÍAS ────────────────────────────────────────
        self.stdout.write("\n=== VENTAS ÚLTIMOS 30 DÍAS ===")
        r30 = HistorialVentas.objects.filter(fecha__gte=hace_30).aggregate(
            total_bruto        = Sum('precio_bruto'),
            total_descuentos   = Sum('descuento'),
            total_transacciones= Count('id_transaccion', distinct=True),
            total_items        = Count('id'),
            ap_hogar_monto     = Sum('precio_bruto', filter=Q(es_ap_hogar=True)),
            ap_hogar_count     = Count('id', filter=Q(es_ap_hogar=True)),
        )
        self.stdout.write(
            f"VENTAS_30D|"
            f"bruto:{r30['total_bruto'] or 0}|"
            f"descuentos:{r30['total_descuentos'] or 0}|"
            f"transacciones:{r30['total_transacciones'] or 0}|"
            f"items:{r30['total_items'] or 0}|"
            f"ap_hogar_monto:{r30['ap_hogar_monto'] or 0}|"
            f"ap_hogar_count:{r30['ap_hogar_count'] or 0}"
        )

        # ── VENTAS 90 DÍAS ────────────────────────────────────────
        self.stdout.write("\n=== VENTAS ÚLTIMOS 90 DÍAS ===")
        r90 = HistorialVentas.objects.filter(fecha__gte=hace_90).aggregate(
            total_bruto        = Sum('precio_bruto'),
            total_transacciones= Count('id_transaccion', distinct=True),
        )
        self.stdout.write(
            f"VENTAS_90D|"
            f"bruto:{r90['total_bruto'] or 0}|"
            f"transacciones:{r90['total_transacciones'] or 0}"
        )

        # ── TOP 10 PRODUCTOS 30D ──────────────────────────────────
        self.stdout.write("\n=== TOP 10 PRODUCTOS 30D (por ingreso) ===")
        top = (
            HistorialVentas.objects
            .filter(fecha__gte=hace_30)
            .values('descripcion')
            .annotate(
                qty    = Sum('cantidad'),
                ingreso= Sum('precio_bruto')
            )
            .order_by('-ingreso')[:10]
        )
        for item in top:
            self.stdout.write(
                f"TOP|{item['descripcion']}|"
                f"qty:{item['qty']}|"
                f"ingreso:{item['ingreso']}"
            )

        # ── QUIEBRES Y CRÍTICOS ───────────────────────────────────
        self.stdout.write("\n=== ALERTAS DE STOCK ===")
        quiebres = AuditoriaVTS.objects.filter(
            estado='activo', inventario_real=0
        )
        for p in quiebres:
            self.stdout.write(f"QUIEBRE|{p.sku}|{p.producto}")

        criticos = AuditoriaVTS.objects.filter(
            estado='activo', inventario_real__gt=0, inventario_real__lte=3
        )
        for p in criticos:
            self.stdout.write(f"CRITICO|{p.sku}|{p.producto}|stock:{p.inventario_real}")

        # ── PASIVOS CONOCIDOS ─────────────────────────────────────
        self.stdout.write("\n=== PASIVOS CONOCIDOS ===")
        self.stdout.write(
            "CREDITO|Fondo Esperanza SpA|"
            "monto_original:200000|cuota:15944|"
            "periodicidad:semanal|cuotas_pendientes:11|"
            "tasa_anual:40.18%|cae:77.11%|"
            "proxima_cuota:2026-06-03"
        )
        self.stdout.write(
            "SEGURO|Southbridge Negocio+Protegido|"
            "cobertura_uf:20|prima_mensual:1517|"
            "vencimiento:con_credito"
        )

        self.stdout.write(f"\n=== GENERADO: {hoy} ===")