#dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AuditoriaVTS, HistorialStock
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce

def actualizar_inventario(request, sku):
    if request.method == 'POST':
        try:
            item = get_object_or_404(AuditoriaVTS, sku=sku)
            stock_viejo = item.inventario_real
            
            # 1. Captura limpia de datos
            nueva_cantidad = request.POST.get('cantidad', 0)
            nuevo_costo = request.POST.get('costo', item.precio_costo)
            nuevo_precio = request.POST.get('precio', item.precio_venta)

            # 2. Guardado ÚNICO y Blindado
            item.inventario_real = int(nueva_cantidad)
            item.precio_costo = float(nuevo_costo)
            item.precio_venta = float(nuevo_precio)
            item.save()
            
            # 3. CREACIÓN DEL LOG (Una sola vez)
            HistorialStock.objects.create(
                sku=sku,
                producto=item.producto,
                stock_anterior=stock_viejo,
                stock_nuevo=item.inventario_real,
                usuario=request.user.username if request.user.is_authenticated else "Admin_VTS"
            )
            
            messages.success(request, f"✅ {sku} actualizado y registrado en Historial.")
            
        except Exception as e:
            messages.error(request, f"❌ Error crítico al actualizar {sku}: {str(e)}")
            
    return redirect('inventario')

def dashboard_home(request):
    auditorias = AuditoriaVTS.objects.all()
    total_registros = auditorias.count()

    # --- MÉTRICAS PARA TARJETAS SKYDASH ---
    # Capital total basado en lo que el sistema dice que hay
    capital_total = sum(item.precio_costo * item.stock_sistema for item in auditorias)
    # Alertas: productos donde el físico es 0
    alertas_stock = auditorias.filter(inventario_real=0).count()

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

def home(request):
    total = AuditoriaVTS.objects.count()
    # Consideramos 'auditado' si el inventario_real es diferente de -1 (o lo que definas)
    auditados = AuditoriaVTS.objects.filter(inventario_real__gte=0).count()
    pendientes = total - auditados
    
    context = {
        'total': total,
        'auditados': auditados,
        'pendientes': pendientes,
        'capital_total': sum(i.inventario_real * i.costo_neto for i in AuditoriaVTS.objects.all())
    }
    return render(request, 'dashboard/index.html', context)