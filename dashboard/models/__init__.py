from .inventario import AuditoriaVTS, VarianteVTS, HistorialStock
from .logs import RegistroLogs, LogRetirosDeducibles, VentaRegistrada, HistorialVentas
from .config     import ConfigVTS, PerfilVTS
from .personal   import Colaborador

__all__ = [
    'AuditoriaVTS', 'VarianteVTS', 'HistorialStock',
    'RegistroLogs', 'LogRetirosDeducibles',
    'ConfigVTS', 'PerfilVTS',
    'Colaborador', 'VentaRegistrada', 'HistorialVentas'
]