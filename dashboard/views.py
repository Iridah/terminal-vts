# views.py — Router central v3.0.2
# Toda la lógica vive en los módulos especializados.
# Este archivo solo reexporta para mantener compatibilidad con urls.py
from .wixelandr import validar_csv_sumup, validar_acceso
from .odd import procesar_ventas, resumen_proceso, construir_mapeo_desde_inventario
from .models import RegistroLogs


from dashboard.views_inventario import (
    dashboard_home,
    analisis_pro,
    subir_foto_producto,
    inventario_view,
    detalle_producto,
    actualizar_inventario,
    validador_masivo,
    procesar_carga_masiva,
    buscar_productos,
)

from dashboard.views_movimientos import (
    registrar_movimiento_triada,
    lista_logs,
    registrar_aporte_hogar,
    registrar_movimiento_htmx,
    check_logs_notificados,
)

from dashboard.views_personal import (
    importar_personal,
    ficha_personal,
    guardar_ficha,
    buscar_colaborador,
    vista_mortaja,
    vista_sabana_digital,
    actualizar_indicadores_view,
    generar_liquidacion_view,
)
from .views_inventario import api_config_costos
from dashboard.views_ventas import ventas_importar, ventas_reporte, ventas_mapeo