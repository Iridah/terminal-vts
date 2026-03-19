# dashboard/vts_config.py
from .models import ConfigVTS

def get_config():
    """Lee los parámetros operativos desde la BD. Retorna dict con decimales."""
    defaults = {
        'sumup_pct':      0.031,
        'internet_pct':   0.041,
        'transporte_pct': 0.051,
        'iva':            0.19,   # IVA real para cálculos de semáforo
        'iva_colchon':    0.20,   # Colchón interno para estimaciones de costo
    }
    for obj in ConfigVTS.objects.all():
        defaults[obj.clave] = float(obj.valor)
    return defaults

def calcular_costo_operativo(precio_costo: float) -> float:
    """Aplica los porcentajes operativos sobre el costo neto."""
    cfg = get_config()
    sumup      = precio_costo * cfg['sumup_pct']
    internet   = precio_costo * cfg['internet_pct']
    transporte = precio_costo * cfg['transporte_pct']
    return precio_costo + sumup + internet + transporte