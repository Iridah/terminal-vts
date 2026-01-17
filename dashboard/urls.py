#dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    
    # La Forja (Usamos inventario_view que tiene la lógica de márgenes)
    path('inventario/', views.inventario_view, name='inventario'),
    
    # El Cerebro (Análisis Pro con FelEngine)
    path('analisis-pro/', views.analisis_pro, name='analisis_pro'), 
    
    # Acciones y Logs
    path('actualizar-inventario/<str:sku>/', views.actualizar_inventario, name='actualizar_inventario'),
    path('logs/', views.lista_logs, name='lista_logs'),
    path('producto/<str:sku>/', views.detalle_producto, name='detalle_producto'),
    path('registrar-aporte-hogar/', views.registrar_aporte_hogar, name='registrar_aporte_hogar'),

    # Importaciones masivas
    path('validador/', views.validador_masivo, name='validador_masivo'),
    path('procesar-carga/', views.procesar_carga_masiva, name='procesar_carga_masiva'),
]