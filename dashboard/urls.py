# dashboard/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from . import views

urlpatterns = [
    # =================================================================
    # PASILLO 1: CORE Y NAVEGACIÓN (Vistas Maestras)
    # =================================================================
    path('', views.dashboard_home, name='home'),
    path('analisis-pro/', views.analisis_pro, name='analisis_pro'), 
    path('logs/', views.lista_logs, name='lista_logs'),
    #path('admin/', admin.site.norma_nombre_aqui), # Tu ruta de admin
    
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

    # =================================================================
    # PASILLO 5: HTMX
    # =================================================================
    path('', views.dashboard_home, name='home'),
    path('buscar-productos/', views.buscar_productos, name='buscar_productos'), # EL NUEVO TAG
    path('registrar-movimiento/<str:sku>/', 
         views.registrar_movimiento_htmx, 
         name='registrar_movimiento_htmx'),
    path('login/', auth_views.LoginView.as_view(template_name='dashboard/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/check-logs/', views.check_logs_notificados, name='check_logs'),
    path('personal/importar/', views.importar_personal, name='importar_personal'),
    # FICHA DE PERSONAL
    # Vista principal (el contenedor blanco hueso)
    path('personal/ficha/', views.ficha_personal, name='ficha_personal'),
    
    # Búsqueda y carga del parcial (lo que HTMX inyecta)
    path('personal/buscar/', views.buscar_colaborador, name='buscar_colaborador'),
    
    # Guardado de cambios
    path('personal/guardar/<str:rut>/', views.guardar_ficha, name='guardar_ficha'),

    # Esta es la que te está pidiendo el error:
    path('sabana-digital/', views.vista_sabana_digital, name='sabana_digital'), 
    
    # Y esta es la del modal que ya tenías:
    path('mortaja/<str:rut>/', views.vista_mortaja, name='ver_mortaja'),
    path('actualizar-indicadores/', views.actualizar_indicadores_view, name='actualizar_indicadores'),
    
    # =================================================================
    # PASILLO 6: IMAGENES
    # =================================================================
    path('subir-foto/<str:sku>/', views.subir_foto_producto, name='subir_foto'),



]

# ESTO ES LO QUE FALTA: Solo para desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)