from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('actualizar/<str:sku>/', views.actualizar_inventario, name='actualizar_inventario'),
]