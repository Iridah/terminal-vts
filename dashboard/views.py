#dashboard/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import AuditoriaVTS
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce

def actualizar_inventario(request, sku):
    if request.method == 'POST':
        nuevo_valor = request.POST.get('cantidad', 0) # El 0 es por si viene vacío
        # Buscamos el registro por SKU
        item = AuditoriaVTS.objects.get(sku=sku)
        item.inventario_real = nuevo_valor
        # Al guardar, la fecha_auditoria se actualizará automáticamente a "ahora" (11-01-2026)
        item.save()
        messages.success(request, f"Inventario de {sku} actualizado correctamente.")
    return redirect('home')

def dashboard_home(request):
    auditorias = AuditoriaVTS.objects.all()
    
    # 🥧 Lógica para el Gráfico de Torta: Estado de Auditoría
    # Consideramos "completado" si inventario_real es > 0, y "pendiente" si es 0
    completados = auditorias.exclude(inventario_real=0).count()
    pendientes = auditorias.filter(inventario_real=0).count()
    total_registros = auditorias.count()

    # Si no hay registros, para evitar divisiones por cero en el dashboard
    porcentaje_completado = (completados / total_registros * 100) if total_registros > 0 else 0
    porcentaje_pendiente = (pendientes / total_registros * 100) if total_registros > 0 else 0

    # 📉 Lógica para el Gráfico de Barras: Pérdidas por Sección
    # Calculamos la diferencia de dinero directamente en la consulta
    # Usamos Coalesce para tratar los casos donde precio_costo pudiera ser nulo (aunque ya lo filtramos a 0 en la succión)
    # y ExpressionWrapper para asegurar el tipo DecimalField en el cálculo.
    perdidazos = auditorias.annotate(
        # Calculamos la diferencia negativa, para que sea un valor absoluto de pérdida
        unidades_perdidas=Coalesce(F('stock_sistema'), 0) - Coalesce(F('inventario_real'), 0),
        # Calculamos la pérdida monetaria solo si unidades_perdidas > 0
        plata_perdida=ExpressionWrapper(
            F('unidades_perdidas') * Coalesce(F('precio_costo'), 0),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    ).filter(
        unidades_perdidas__gt=0 # Solo nos interesan las pérdidas
    ).values('seccion').annotate(
        total_perdido=Sum('plata_perdida')
    ).order_by('-total_perdido') # Ordenamos de mayor a menor pérdida

    # Preparamos los datos para Chart.js
    secciones_labels = [p['seccion'] for p in perdidazos]
    total_perdido_data = [float(p['total_perdido']) for p in perdidazos] # Aseguramos float para JS

    context = {
        'completados': completados,
        'pendientes': pendientes,
        'total_registros': total_registros,
        'porcentaje_completado': round(porcentaje_completado, 2),
        'porcentaje_pendiente': round(porcentaje_pendiente, 2),

        'secciones_labels': secciones_labels,
        'total_perdido_data': total_perdido_data,
    }
    return render(request, 'dashboard/index.html', context)