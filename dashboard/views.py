#dashboard/views.py
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
# Modifica tu línea 8 actual:
from .models import AuditoriaVTS, HistorialStock, LogRetirosDeducibles # <--- Añade esto
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce

def actualizar_inventario(request, sku):
    if request.method == 'POST':
        try:
            item = get_object_or_404(AuditoriaVTS, sku=sku)
            stock_viejo = item.inventario_real
            
            # 1. Capturar datos (vengan del Modal o de la Tabla)
            # Capturamos datos (usamos .get() para evitar KeyErrors si el campo no viene)
            # 'cantidad' viene del input de la tabla, 'inventario_real' podría venir del modal
            nuevo_stock = request.POST.get('cantidad') or request.POST.get('inventario_real')
            nuevo_costo = request.POST.get('costo')
            nuevo_precio = request.POST.get('precio')
            nuevo_nombre = request.POST.get('nombre')

            # --- INYECCIÓN SEGURA PARA IMÁGENES ---
            if 'imagen' in request.FILES:
                item.imagen = request.FILES['imagen']
            # --------------------------------------

            # 2. Actualizar solo si el dato viene en el POST (evita sobreescribir con None)
            if nuevo_nombre: item.producto = nuevo_nombre
            if nuevo_costo: item.precio_costo = float(nuevo_costo)
            if nuevo_precio: item.precio_venta = float(nuevo_precio)
            if nuevo_stock is not None: item.inventario_real = int(nuevo_stock)

            item.save()
            
            # 3. Registrar Log si hubo cambio de stock
            if nuevo_stock is not None and int(nuevo_stock) != stock_viejo:
                HistorialStock.objects.create(
                    sku=sku,
                    producto=item.producto,
                    stock_anterior=stock_viejo,
                    stock_nuevo=item.inventario_real,
                    usuario=request.user.username if request.user.is_authenticated else "Admin_VTS"
                )
            
            messages.success(request, f"✅ {sku} actualizado.")
        except Exception as e:
            messages.error(request, f"❌ Error: {str(e)}")
            
    return redirect('inventario')

def dashboard_home(request):
    auditorias = AuditoriaVTS.objects.all()
    total_registros = auditorias.count()

# --- MÉTRICAS PARA TARJETAS SKYDASH ---
    capital_total = sum(item.precio_costo * item.stock_sistema for item in auditorias)
    
    # 1. MODIFICACIÓN: Guardamos los objetos en una variable para el Radar
    productos_quiebre = auditorias.filter(inventario_real=0)
    alertas_stock = productos_quiebre.count()

    # --- MÉTRICAS DE AVANCE (Gráfico Torta) ---
    completados = auditorias.exclude(inventario_real=0).count()
    pendientes = total_registros - completados
    
    porc_completado = (completados / total_registros * 100) if total_registros > 0 else 0
    porc_pendiente = 100 - porc_completado

    # --- MÉTRICAS POR SECCIÓN (Gráfico Barras) ---
    capital_por_seccion = auditorias.values('seccion').annotate(
        total_invertido=Sum(F('stock_sistema') * F('precio_costo'))
    ).order_by('-total_invertido')

    context = {
        'total_productos': total_registros,
        'capital_total': capital_total,
        'alertas_stock': alertas_stock,
        'completados': completados,
        'pendientes': pendientes,
        'porcentaje_completado': round(porc_completado, 2),
        'porcentaje_pendiente': round(porc_pendiente, 2),
        'secciones_labels': [p['seccion'] for p in capital_por_seccion],
        'total_perdido_data': [float(p['total_invertido'] or 0) for p in capital_por_seccion],
        # 2. CONEXIÓN: Pasamos la lista al HTML
        'productos_quiebre': productos_quiebre, 
        
        'completados': completados,
        'pendientes': pendientes,
        'porcentaje_completado': round(porc_completado, 2),
        'porcentaje_pendiente': round(porc_pendiente, 2),
        'secciones_labels': [p['seccion'] for p in capital_por_seccion],
        'total_perdido_data': [float(p['total_invertido'] or 0) for p in capital_por_seccion],
    }
    return render(request, 'dashboard/index.html', context)

def inventario_list(request):
    # Aquí va la tabla CRUD con buscadores
    auditorias = AuditoriaVTS.objects.all().order_by('seccion')
    return render(request, 'dashboard/inventario.html', {'auditorias': auditorias})

def buscar_productos(request):
    query = request.GET.get('q', '')
    if query:
        # Filtramos SOLO usando AuditoriaVTS y campos que existen
        resultados = AuditoriaVTS.objects.filter(
            producto__icontains=query
        ) | AuditoriaVTS.objects.filter(
            sku__icontains=query
        )
    else:
        resultados = []
        
    return render(request, 'dashboard/resultados_busqueda.html', {
        'resultados': resultados,
        'query': query
    })

def detalle_producto(request, sku):
    # Buscamos el producto por su SKU o ID
    producto = get_object_or_404(AuditoriaVTS, sku=sku) 
    return render(request, 'dashboard/ficha_producto.html', {'item': producto})

def lista_logs(request):
    logs = HistorialStock.objects.all()[:50] # Últimos 50 movimientos
    return render(request, 'dashboard/logs.html', {'logs': logs})

def inventario_view(request):
    auditorias = AuditoriaVTS.objects.all()
    
    # Contadores de alertas
    alertas = {
        'quiebres': 0,
        'criticos': 0,
        'perdidas': 0,
        'saludables': 0
    }
    
    for item in auditorias:
        # Lógica de Stock
        status_stock = item.get_stock_status()['texto']
        if status_stock == 'QUIEBRE': alertas['quiebres'] += 1
        elif status_stock == 'CRÍTICO': alertas['criticos'] += 1
        
        # Lógica de Rentabilidad (Margen Illidari)
        status_rent = item.get_rentabilidad_status()['texto']
        if status_rent == 'PÉRDIDA': alertas['perdidas'] += 1
        elif status_rent == 'SALUDABLE' or status_rent == 'ILLIDARI': alertas['saludables'] += 1

    return render(request, 'dashboard/inventario.html', {
        'auditorias': auditorias,
        'alertas': alertas
    })

@csrf_exempt
def registrar_aporte_hogar(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            producto = AuditoriaVTS.objects.get(sku=data['sku'])
            cantidad = int(data['cantidad'])
            
            # Creamos el log (el modelo ya descuenta el stock en su .save())
            LogRetirosDeducibles.objects.create(
                sku=producto,
                cantidad=cantidad,
                motivo="Aporte Hogar (Retiro Tablet)"
            )
            
            return JsonResponse({
                'status': 'success', 
                'nuevo_stock': producto.inventario_real
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

def analisis_pro(request):
    secciones = AuditoriaVTS.objects.values_list('seccion', flat=True).distinct()
    analisis_data = {}

    for seccion in secciones:
        # Buscamos los 5 que más han variado o tienen mejor margen
        top_5 = AuditoriaVTS.objects.filter(seccion=seccion).order_by('-precio_venta')[:5]
        analisis_data[seccion] = top_5

    return render(request, 'dashboard/analisis_pro.html', {'analisis_data': analisis_data})
