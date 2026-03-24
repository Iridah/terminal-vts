# dashboard/vts_config.py
from .models import ConfigVTS

def get_config():
    """Lee los parámetros operativos desde la BD. Retorna dict con decimales."""
    defaults = {
        'sumup_pct':      0.036,
        'internet_pct':   0.046,
        'transporte_pct': 0.056,
        'cmr_pct': 0.046,
        'iva':            0.19,   # IVA real para cálculos de semáforo
        'iva_colchon':    0.21,   # Colchón interno para estimaciones de costo
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
    cmr = precio_costo * cfg['cmr_pct']
    return precio_costo + sumup + internet + transporte + cmr