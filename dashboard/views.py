# dashboard/views.py
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, F, ExpressionWrapper, FloatField
from django.db.models.functions import Coalesce
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

# Modelos y Engine
from .models import AuditoriaVTS, HistorialStock, LogRetirosDeducibles, RegistroLogs
from .engine import FelEngine

# =================================================================
# I. SECCIÓN CORE: VISTAS PRINCIPALES Y ANÁLISIS
# =================================================================

def dashboard_home(request):
    """Radar de control principal v2.7.5"""
    auditorias = AuditoriaVTS.objects.all()
    
    # Métricas de Inventario
    quiebres_reales = auditorias.filter(inventario_real=0).count()
    alertas_reposicion = auditorias.filter(inventario_real__gt=0, inventario_real__lte=3).count()
    
    # Capitalización
    capital_total = auditorias.aggregate(
        total=Sum(F('inventario_real') * F('precio_costo'), output_field=FloatField())
    )['total'] or 0
    
    # ROI por Sección
    roi_por_seccion = auditorias.values('seccion').annotate(
        inversion=Sum(F('inventario_real') * F('precio_costo'), output_field=FloatField()),
        venta_proyectada=Sum(F('inventario_real') * F('precio_venta'), output_field=FloatField())
    )
    
    roi_data, roi_labels = [], []
    for item in roi_por_seccion:
        if item['inversion'] > 0:
            margen = ((item['venta_proyectada'] - item['inversion']) / item['inversion']) * 100
            roi_data.append(round(margen, 1))
            roi_labels.append(item['seccion'])

    context = {
        'total_productos': auditorias.count(),
        'capital_total': capital_total,
        'quiebres_reales': quiebres_reales,
        'alertas_reposicion': alertas_reposicion,
        'productos_quiebre': auditorias.filter(inventario_real__lte=3).order_by('inventario_real'),
        'roi_labels': roi_labels,
        'roi_data': roi_data,
        'secciones_labels': [p['seccion'] for p in roi_por_seccion],
    }
    return render(request, 'dashboard/index.html', context)

def analisis_pro(request):
    """Pestaña de análisis avanzado con motor FelEngine"""
    reporte = FelEngine.generar_reporte_general()
    # Reutilizamos lógica de ROI para consistencia visual
    return render(request, 'dashboard/analisis_pro.html', {'reporte': reporte})


# =================================================================
# II. SECCIÓN OPERATIVA: LA FORJA (CRUD & BÚSQUEDA)
# =================================================================

def inventario_view(request):
    """La Forja: Gestión operativa diaria"""
    auditorias = AuditoriaVTS.objects.annotate(
        venta_neta=ExpressionWrapper(F('precio_venta') / 1.19, output_field=FloatField()),
        margen_db=ExpressionWrapper(
            (F('venta_neta') - F('precio_costo')) / Coalesce(F('venta_neta'), 1.0),
            output_field=FloatField()
        )
    ).order_by('seccion')
    return render(request, 'dashboard/inventario.html', {'auditorias': auditorias})

def detalle_producto(request, sku):
    """Ficha técnica de producto individual"""
    producto = get_object_or_404(AuditoriaVTS, sku=sku) 
    return render(request, 'dashboard/ficha_producto.html', {'item': producto})


# =================================================================
# III. SECCIÓN LOGÍSTICA: CARGAS MASIVAS Y VALIDACIÓN
# =================================================================

def validador_masivo(request):
    """Formulario y lógica de pre-validación de SKUs"""
    if request.method == 'POST':
        lineas = request.POST.get('bulk_data', '').splitlines()
        resultados = []
        for linea in lineas:
            if not linea.strip(): continue
            partes = linea.split(',') if ',' in linea else linea.split(';')
            sku = partes[0].strip().upper()
            prod_obj = AuditoriaVTS.objects.filter(sku=sku).first()
            resultados.append({
                'sku': sku,
                'existe': prod_obj is not None,
                'nombre': prod_obj.producto if prod_obj else "NO ENCONTRADO",
            })
        return render(request, 'dashboard/validador_check.html', {'resultados': resultados})
    return render(request, 'dashboard/validador_form.html')

@transaction.atomic
def procesar_carga_masiva(request):
    """Ejecución final de carga masiva con seguridad atómica"""
    if request.method == 'POST':
        skus = request.POST.getlist('skus')
        cantidades = request.POST.getlist('cantidades')
        for sku, cant in zip(skus, cantidades):
            if not cant or int(cant) <= 0: continue
            prod = AuditoriaVTS.objects.select_for_update().get(sku=sku)
            stock_prev = prod.inventario_real
            prod.inventario_real += int(cant)
            prod.save()
            HistorialStock.objects.create(sku=sku, producto=prod.producto, stock_anterior=stock_prev, 
                                        stock_nuevo=prod.inventario_real, usuario="Carga_Masiva")
        return render(request, 'dashboard/validador_success.html')


# =================================================================
# IV. SECCIÓN API: ENDPOINTS PARA INTERFAZ JS (LA TRIADA)
# =================================================================

@require_POST
def registrar_movimiento_triada(request):
    """API para el modal de La Triada (Venta, Merma, Aporte, Ingreso)"""
    try:
        data = json.loads(request.body)
        prod = get_object_or_404(AuditoriaVTS, sku=data['sku'])
        cantidad = int(data['cantidad'])
        tipo = data['tipo']
        
        stock_anterior = prod.inventario_real
        if tipo in ['venta', 'merma', 'aporte']: prod.inventario_real -= cantidad
        elif tipo == 'ingreso': prod.inventario_real += cantidad
        prod.save()

        # Registro en Logs del Sistema
        RegistroLogs.objects.create(
            sku=prod.sku,
            producto=prod.producto,
            tipo_accion=tipo.upper(),
            cantidad=cantidad,
            fecha=timezone.now()
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def lista_logs(request):
    """Visualización de los últimos movimientos registrados"""
    logs = HistorialStock.objects.all().order_by('-fecha_ajuste')[:50]
    return render(request, 'dashboard/logs.html', {'logs': logs})