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
from .engine import FelEngine

# --- 1. DASHBOARD PRINCIPAL (Con Radar de Quiebres) ---
def dashboard_home(request):
    # 1. Traemos la base de datos con los cálculos de margen inyectados
    auditorias = AuditoriaVTS.objects.all()
    
    # 2. Capital Total Basado en Inventario REAL (No en sistema)
    # Cambiamos stock_sistema por inventario_real para ver la plata de verdad
    capital_total_qs = auditorias.aggregate(
        total=Sum(F('inventario_real') * F('precio_costo'), output_field=FloatField())
    )
    capital_total = capital_total_qs['total'] or 0

    # 3. Radar de Quiebres (Solo lo que está en cero absoluto)
    productos_quiebre = auditorias.filter(inventario_real=0)
    
    # 4. Progreso de la Auditoría
    total_sku = auditorias.count()
    # Consideramos "completado" si el inventario real es distinto al de sistema (ya se tocó)
    auditados = auditorias.exclude(inventario_real=F('stock_sistema')).count()
    porc_completado = (auditados / total_sku * 100) if total_sku > 0 else 0

    # 5. Datos para el Gráfico de Barras (Inversión Real por Sección)
    capital_por_seccion = auditorias.values('seccion').annotate(
        total_invertido=Sum(F('inventario_real') * F('precio_costo'), output_field=FloatField())
    ).order_by('-total_invertido')

    context = {
        'total_productos': total_sku,
        'capital_total': capital_total,
        'alertas_stock': productos_quiebre.count(),
        'porcentaje_completado': round(porc_completado, 1),
        'secciones_labels': [p['seccion'] for p in capital_por_seccion],
        'total_perdido_data': [float(p['total_invertido'] or 0) for p in capital_por_seccion],
        'productos_quiebre': productos_quiebre[:10], # Limitamos para no romper el layout
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
        item = get_object_or_404(AuditoriaVTS, sku=sku)
        stock_viejo = item.inventario_real
        
        # Capturamos la cantidad a SUMAR del nuevo input
        cantidad_a_sumar = int(request.POST.get('cantidad_nueva') or 0)
        
        if cantidad_a_sumar != 0:
            # Operación ciega: Solo sumamos
            item.inventario_real += cantidad_a_sumar
            item.save()
            
            # Registro en historial
            HistorialStock.objects.create(
                sku=sku,
                producto=item.producto,
                stock_anterior=stock_viejo,
                stock_nuevo=item.inventario_real,
                usuario=request.user.username if request.user.is_authenticated else "Admin_VTS"
            )
            messages.success(request, f"✅ Se añadieron {cantidad_a_sumar} unidades a {sku}.")
            
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
    # El motor procesa todo, la vista solo entrega el sobre
    reporte = FelEngine.generar_reporte_general()
    return render(request, 'dashboard/analisis_pro.html', {'reporte': reporte})

# --- 7. APORTE HOGAR (API) ---
@csrf_exempt
def registrar_aporte_hogar(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            producto = get_object_or_404(AuditoriaVTS, sku=data['sku'])
            cantidad = int(data['cantidad'])
            stock_anterior = producto.inventario_real
            
            # 1. Descuento de Stock Real
            producto.inventario_real -= cantidad
            producto.save()

            # 2. Registro en Log de Retiros (Deducibles)
            LogRetirosDeducibles.objects.create(
                sku=producto, 
                cantidad=cantidad, 
                motivo="Aporte Hogar (Manual v2.6)"
            )

            # 3. REGISTRO EN HISTORIAL GENERAL (Para que aparezca en la pestaña Logs)
            HistorialStock.objects.create(
                sku=producto.sku,
                producto=producto.producto,
                stock_anterior=stock_anterior,
                stock_nuevo=producto.inventario_real,
                usuario=request.user.username if request.user.is_authenticated else "SMT700_Admin"
            )

            return JsonResponse({'status': 'success', 'nuevo_stock': producto.inventario_real})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})