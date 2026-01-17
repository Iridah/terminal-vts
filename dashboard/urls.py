# dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # =================================================================
    # PASILLO 1: CORE Y NAVEGACIÓN (Vistas Maestras)
    # =================================================================
    path('', views.dashboard_home, name='home'),
    path('analisis-pro/', views.analisis_pro, name='analisis_pro'), 
    path('logs/', views.lista_logs, name='lista_logs'),
    
    # =================================================================
    # PASILLO 2: LA FORJA (Gestión de Inventario y Fichas)
    # =================================================================
    path('inventario/', views.inventario_view, name='inventario'),
    path('producto/<str:sku>/', views.detalle_producto, name='detalle_producto'),

    # =================================================================
    # PASILLO 3: ACCIONES OPERATIVAS (Lógica de Movimientos)
    # =================================================================
    path('actualizar-inventario/<str:sku>/', views.actualizar_inventario, name='actualizar_inventario'),
    path('registrar-aporte-hogar/', views.registrar_aporte_hogar, name='registrar_aporte_hogar'),
    path('registrar-movimiento-triada/', views.registrar_movimiento_triada, name='triada_movimiento'),

    # =================================================================
    # PASILLO 4: LOGÍSTICA MASIVA (Validadores e Importación)
    # =================================================================
    path('validador/', views.validador_masivo, name='validador_masivo'),
    path('procesar-carga/', views.procesar_carga_masiva, name='procesar_carga_masiva'),
]