#dashboard/views.py
import json
import os
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AuditoriaVTS, HistorialStock, LogRetirosDeducibles, RegistroLogs
from django.db.models import Sum, F, ExpressionWrapper, FloatField
from django.db.models.functions import Coalesce
from .engine import FelEngine
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

# --- 1. DASHBOARD PRINCIPAL (Con Radar y ROI Unificados) ---
def dashboard_home(request):
    auditorias = AuditoriaVTS.objects.all()

    # 1. Semáforo y Alertas Críticas
    quiebres_reales = auditorias.filter(inventario_real=0).count()
    alertas_reposicion = auditorias.filter(inventario_real__gt=0, inventario_real__lte=3).count()
    alertas_criticas = auditorias.filter(inventario_real__lte=3).order_by('inventario_real')

    # 2. Capital y Progreso
    capital_total = auditorias.aggregate(
        total=Sum(F('inventario_real') * F('precio_costo'), output_field=FloatField())
    )['total'] or 0
    
    total_sku = auditorias.count()
    auditados = auditorias.exclude(inventario_real=F('stock_sistema')).count()
    porc_completado = (auditados / total_sku * 100) if total_sku > 0 else 0

    # 3. Datos para ROI (Mini-gráfico y General)
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

    # 4. Lógica Predictiva (El Corazón del Punto 2.7)
    hace_una_semana = timezone.now() - timedelta(days=7)
    alertas_quiebre = []
    utiles = AuditoriaVTS.objects.filter(seccion='Libreria', inventario_real__lt=20)
    
    for util in utiles:
        consumo_semanal = RegistroLogs.objects.filter(
            sku=util.sku, tipo_accion='SALIDA', fecha__gte=hace_una_semana
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        consumo_diario = consumo_semanal / 7
        if consumo_diario > 0:
            dias_restantes = util.inventario_real / consumo_diario
            if dias_restantes <= 3:
                alertas_quiebre.append({
                    'producto': util.producto,
                    'dias': round(dias_restantes, 1),
                    'stock': util.inventario_real
                })

    # 5. EL ÚNICO CONTEXTO
    context = {
        'total_productos': total_sku,
        'capital_total': capital_total,
        'porcentaje_completado': round(porc_completado, 1),
        'secciones_labels': [p['seccion'] for p in auditorias.values('seccion').annotate(t=Sum('inventario_real')).order_by('-t')],
        'quiebres_reales': quiebres_reales,
        'alertas_reposicion': alertas_reposicion,
        'productos_quiebre': alertas_criticas, 
        'roi_labels': roi_labels,
        'roi_data': roi_data,
        'alertas_quiebre': alertas_quiebre, # Inyectamos la predicción aquí
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
    reporte = FelEngine.generar_reporte_general()
    auditorias = AuditoriaVTS.objects.all()

    # Reutilizamos la lógica del ROI para el gráfico de esta pestaña
    roi_por_seccion = auditorias.values('seccion').annotate(
        inversion=Sum(F('inventario_real') * F('precio_costo'), output_field=FloatField()),
        venta_proyectada=Sum(F('inventario_real') * F('precio_venta'), output_field=FloatField())
    )

    roi_data = []
    roi_labels = []
    for item in roi_por_seccion:
        if item['inversion'] > 0:
            margen = ((item['venta_proyectada'] - item['inversion']) / item['inversion']) * 100
            roi_data.append(round(margen, 1))
            roi_labels.append(item['seccion'])

    context = {
        'reporte': reporte,
        'roi_labels': roi_labels,
        'roi_data': roi_data,
    }
    return render(request, 'dashboard/analisis_pro.html', context)

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
        
# --- 8. VALIDADOR MASIVO ---
def validador_masivo(request):
    if request.method == 'POST':
        raw_data = request.POST.get('bulk_data', '')
        
        # USO DE SPLITLINES: Maneja saltos de línea de Windows (\r\n) y Unix (\n) automáticamente
        lineas = raw_data.splitlines() 
        resultados = []
        
        for linea in lineas:
            # Limpiamos espacios al inicio y final
            linea_limpia = linea.strip()
            
            # Si la línea está vacía después de limpiar, la saltamos
            if not linea_limpia: 
                continue
            
            # Intentamos separar por coma, si falla, probamos punto y coma (por si acaso)
            if ',' in linea_limpia:
                partes = linea_limpia.split(',')
            elif ';' in linea_limpia:
                partes = linea_limpia.split(';')
            else:
                # Si no hay separador, asumimos que es solo SKU y cantidad 0 o error
                partes = [linea_limpia]

            sku = partes[0].strip().upper() # Forzamos mayúsculas para evitar errores
            
            # Manejo robusto de la cantidad (Si no es número, asumimos 0)
            try:
                cantidad = int(partes[1].strip()) if len(partes) > 1 else 0
            except ValueError:
                cantidad = 0
            
            producto = AuditoriaVTS.objects.filter(sku=sku).first()
            
            resultados.append({
                'sku': sku,
                'cantidad': cantidad,
                'existe': producto is not None,
                'nombre': producto.producto if producto else "NUEVO (No se sumará)",
                'status_class': "table-success" if producto else "table-warning"
            })
            
        return render(request, 'dashboard/validador_check.html', {'resultados': resultados})
    
    return render(request, 'dashboard/validador_form.html')

# --- 9. IMPORTADOR MASIVO ---
def procesar_carga_masiva(request):
    if request.method == 'POST':
        skus = request.POST.getlist('skus')
        cantidades = request.POST.getlist('cantidades')
        
        # Usamos una transacción para que, si falla uno, no se rompa nada
        with transaction.atomic():
            for sku, cantidad in zip(skus, cantidades):
                if not cantidad or int(cantidad) <= 0: continue
                
                # 1. Buscamos el producto para tener su nombre y stock actual para el log
                producto = AuditoriaVTS.objects.filter(sku=sku).first()
                
                if producto:
                    stock_anterior = producto.inventario_real
                    nueva_cantidad = int(cantidad)
                    
                    # 2. Actualización atómica (Evita errores de concurrencia)
                    AuditoriaVTS.objects.filter(sku=sku).update(
                        inventario_real=F('inventario_real') + nueva_cantidad
                    )
                    
                    # 3. Registro en Historial (Log)
                    HistorialStock.objects.create(
                        sku=sku,
                        producto=producto.producto,
                        stock_anterior=stock_anterior,
                        stock_nuevo=stock_anterior + nueva_cantidad,
                        usuario=request.user.username if request.user.is_authenticated else "Carga_Masiva_VTS",
                        fecha_ajuste=timezone.now()
                    )

        messages.success(request, f"✅ Se procesaron {len(skus)} referencias correctamente.")
        return render(request, 'dashboard/validador_success.html', {
            'total_items': len(skus),
            'fecha_completa': timezone.now(), # Esto lleva fecha y hora
            'operador': request.user.username if request.user.is_authenticated else "Admin_VTS"
        })
    return redirect('validador_masivo')