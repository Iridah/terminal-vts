# views_movimientos.py — Secciones IV y VI de views.py
import json
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import AuditoriaVTS, HistorialStock, LogRetirosDeducibles, RegistroLogs

@require_POST
@login_required
def registrar_movimiento_triada(request):
    try:
        data = json.loads(request.body)
        prod = get_object_or_404(AuditoriaVTS, sku=data['sku'])
        cantidad = int(data['cantidad'])
        tipo = data['tipo']
        if tipo in ['venta', 'merma', 'aporte']: prod.inventario_real -= cantidad
        elif tipo == 'ingreso': prod.inventario_real += cantidad
        prod.save()
        RegistroLogs.objects.create(
            sku=prod.sku,
            producto=prod.producto,
            tipo_accion=tipo.upper(),
            cantidad=cantidad,
            operador=request.user if request.user.is_authenticated else None
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def lista_logs(request):
    logs = RegistroLogs.objects.all().order_by('-fecha_exacta')[:50]
    return render(request, 'dashboard/logs.html', {'logs': logs})

@login_required
def registrar_aporte_hogar(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            with transaction.atomic():
                producto = get_object_or_404(AuditoriaVTS, sku=data['sku'])
                cantidad = int(data['cantidad'])
                if producto.inventario_real < cantidad:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Stock insuficiente para aporte (Físico: {producto.inventario_real})'
                    }, status=400)
                LogRetirosDeducibles.objects.create(
                    sku=producto,
                    cantidad=cantidad,
                    motivo=f"Aporte Hogar - Op: {request.user.username}"
                )
            return JsonResponse({'status': 'success', 'nuevo_stock': producto.inventario_real})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@login_required
def registrar_movimiento_htmx(request, sku):
    producto = get_object_or_404(AuditoriaVTS, sku=sku)
    tipo = request.POST.get('tipo')
    cantidad = int(request.POST.get('cantidad', 1))
    if tipo in ['venta', 'merma', 'aporte']: producto.inventario_real -= cantidad
    elif tipo == 'ingreso': producto.inventario_real += cantidad
    producto.save()
    RegistroLogs.objects.create(
        sku=sku,
        producto=producto.producto,
        tipo_accion=tipo.upper(),
        cantidad=cantidad,
        operador=request.user
    )
    auditorias = AuditoriaVTS.objects.all().order_by('seccion')
    return render(request, 'dashboard/partials/forja_items_filas.html', {'auditorias': auditorias})

def check_logs_notificados(request):
    hay_novedad = RegistroLogs.objects.filter(notificado=False).exists()
    if hay_novedad:
        ultimo = RegistroLogs.objects.filter(notificado=False).latest('fecha_exacta')
        ultimo.notificado = True
        ultimo.save()
        return JsonResponse({'alerta': True, 'producto': ultimo.producto, 'stock': ultimo.cantidad})
    return JsonResponse({'alerta': False})
