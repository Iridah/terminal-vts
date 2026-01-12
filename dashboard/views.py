#dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AuditoriaVTS, Producto
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce

def actualizar_inventario(request, sku):
    if request.method == 'POST':
        # 1. Obtenemos el dato y lo limpiamos
        cantidad_raw = request.POST.get('cantidad')
        
        try:
            # 2. Convertimos a entero (si está vacío, asumimos 0)
            nueva_cantidad = int(cantidad_raw) if cantidad_raw else 0
            
            # 3. Buscamos y actualizamos
            item = AuditoriaVTS.objects.get(sku=sku)
            item.inventario_real = nueva_cantidad
            
            # 4. Forzamos el guardado
            item.save()
            
            # Mensaje de éxito para confirmar en la UI
            messages.success(request, f"Stock de {sku} actualizado a {nueva_cantidad}.")
            
        except Exception as e:
            messages.error(request, f"Error al actualizar {sku}: {str(e)}")
            
    return redirect('home')

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
        # Buscamos por SKU, Nombre o cualquier campo relevante
        resultados = Producto.objects.filter(
            nombre__icontains=query
        ) | Producto.objects.filter(
            sku__icontains=query
        )
    else:
        resultados = []
        
    return render(request, 'resultados_busqueda.html', {
        'resultados': resultados,
        'query': query
    })

def detalle_producto(request, sku):
    # Buscamos el producto por su SKU o ID
    producto = get_object_or_404(AuditoriaVTS, sku=sku) 
    return render(request, 'dashboard/ficha_producto.html', {'item': producto})