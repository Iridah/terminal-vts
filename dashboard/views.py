#dashboard/views.py
import json
import os
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AuditoriaVTS, HistorialStock, LogRetirosDeducibles
from django.db.models import Sum, F, ExpressionWrapper, FloatField
from django.db.models.functions import Coalesce

# --- 1. DASHBOARD PRINCIPAL (Con Radar de Quiebres) ---
def dashboard_home(request):
    # Optimización Dj6: Cálculo de margen en SQLite
    auditorias = AuditoriaVTS.objects.annotate(
        venta_neta=ExpressionWrapper(F('precio_venta') / 1.19, output_field=FloatField()),
        margen_db=ExpressionWrapper(
            (F('venta_neta') - F('precio_costo')) / Coalesce(F('venta_neta'), 1.0),
            output_field=FloatField()
        )
    )
    total_registros = auditorias.count()
    capital_total = sum(item.precio_costo * item.stock_sistema for item in auditorias)
    productos_quiebre = auditorias.filter(inventario_real=0)
    
    completados = auditorias.exclude(inventario_real=0).count()
    pendientes = total_registros - completados
    porc_completado = (completados / total_registros * 100) if total_registros > 0 else 0

    capital_por_seccion = auditorias.values('seccion').annotate(
        total_invertido=Sum(F('stock_sistema') * F('precio_costo'))
    ).order_by('-total_invertido')

    context = {
        'total_productos': total_registros,
        'capital_total': capital_total,
        'alertas_stock': productos_quiebre.count(),
        'completados': completados,
        'pendientes': pendientes,
        'porcentaje_completado': round(porc_completado, 2),
        'porcentaje_pendiente': round(100 - porc_completado, 2),
        'secciones_labels': [p['seccion'] for p in capital_por_seccion],
        'total_perdido_data': [float(p['total_invertido'] or 0) for p in capital_por_seccion],
        'productos_quiebre': productos_quiebre,
    }
    return render(request, 'dashboard/index.html', context)

# --- 2. LA FORJA (Inventario Operativo) ---
def inventario_view(request):
    auditorias = AuditoriaVTS.objects.annotate(
        venta_neta=ExpressionWrapper(F('precio_venta') / 1.19, output_field=FloatField()),
        margen_db=ExpressionWrapper(
            (F('venta_neta') - F('precio_costo')) / Coalesce(F('venta_neta'), 1.0),
            output_field=FloatField()
        )
    ).order_by('seccion')
    
    alertas = {
        'quiebres': auditorias.filter(inventario_real=0).count(),
        'criticos': auditorias.filter(inventario_real=1).count(),
        'perdidas': 0,
        'saludables': 0
    }
    for item in auditorias:
        if item.margen_db < 0.05: alertas['perdidas'] += 1
        elif item.margen_db >= 0.22: alertas['saludables'] += 1

    return render(request, 'dashboard/inventario.html', {'auditorias': auditorias, 'alertas': alertas})

# --- 3. LISTADO CRUD (Para Análisis Pro) ---
def inventario_list(request):
    """Mantenida por requerimiento para pestaña de análisis"""
    auditorias = AuditoriaVTS.objects.all().order_by('seccion')
    return render(request, 'dashboard/inventario.html', {'auditorias': auditorias})

# --- 4. ACCIÓN: ACTUALIZAR PRODUCTO ---
def actualizar_inventario(request, sku):
    if request.method == 'POST':
        try:
            item = get_object_or_404(AuditoriaVTS, sku=sku)
            stock_viejo = item.inventario_real
            
            nuevo_stock = request.POST.get('cantidad') or request.POST.get('inventario_real')
            nuevo_costo = request.POST.get('costo')
            nuevo_precio = request.POST.get('precio')
            nuevo_nombre = request.POST.get('nombre')

            if 'imagen' in request.FILES: item.imagen = request.FILES['imagen']
            if nuevo_nombre: item.producto = nuevo_nombre
            if nuevo_costo: item.precio_costo = float(nuevo_costo)
            if nuevo_precio: item.precio_venta = float(nuevo_precio)
            if nuevo_stock is not None: item.inventario_real = int(nuevo_stock)

            item.save()
            
            if nuevo_stock is not None and int(nuevo_stock) != stock_viejo:
                HistorialStock.objects.create(
                    sku=sku, producto=item.producto, stock_anterior=stock_viejo,
                    stock_nuevo=item.inventario_real,
                    usuario=request.user.username if request.user.is_authenticated else "Admin_VTS"
                )
            messages.success(request, f"✅ {sku} actualizado.")
        except Exception as e:
            messages.error(request, f"❌ Error: {str(e)}")
    return redirect('inventario')

# --- 5. BÚSQUEDA Y DETALLE ---
def buscar_productos(request):
    query = request.GET.get('q', '')
    resultados = AuditoriaVTS.objects.filter(producto__icontains=query) | AuditoriaVTS.objects.filter(sku__icontains=query) if query else []
    return render(request, 'dashboard/resultados_busqueda.html', {'resultados': resultados, 'query': query})

def detalle_producto(request, sku):
    producto = get_object_or_404(AuditoriaVTS, sku=sku) 
    return render(request, 'dashboard/ficha_producto.html', {'item': producto})

# --- 6. LOGS Y ANÁLISIS ---
def lista_logs(request):
    logs = HistorialStock.objects.all().order_by('-fecha_ajuste')[:50]
    return render(request, 'dashboard/logs.html', {'logs': logs})

def analisis_pro(request):
    secciones = AuditoriaVTS.objects.values_list('seccion', flat=True).distinct()
    analisis_data = {seccion: AuditoriaVTS.objects.filter(seccion=seccion).order_by('-precio_venta')[:5] for seccion in secciones}
    return render(request, 'dashboard/analisis_pro.html', {'analisis_data': analisis_data})

# --- 7. APORTE HOGAR (API) ---
@csrf_exempt
def registrar_aporte_hogar(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            producto = get_object_or_404(AuditoriaVTS, sku=data['sku'])
            LogRetirosDeducibles.objects.create(
                sku=producto, 
                cantidad=int(data['cantidad']), 
                motivo="Aporte Hogar (Tablet SMT700)"
            )
            producto.refresh_from_db()
            return JsonResponse({'status': 'success', 'nuevo_stock': producto.inventario_real})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})