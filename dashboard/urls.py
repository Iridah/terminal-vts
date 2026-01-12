#dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('inventario/', views.inventario_list, name='inventario'), # La nueva "Forja"
    path('logs/', views.lista_logs, name='lista_logs'),
    path('actualizar/<str:sku>/', views.actualizar_inventario, name='actualizar_inventario'),
    path('producto/<str:sku>/', views.detalle_producto, name='detalle_producto'),
]