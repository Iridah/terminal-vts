# views_inventario.py — Secciones I, II, III de views.py
import json
import csv
import datetime
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, ExpressionWrapper, FloatField, Q
from django.db.models.functions import Coalesce
from django.db import transaction
from .models import AuditoriaVTS, VarianteVTS, HistorialStock, RegistroLogs, HistorialVentas
from .engine import FelEngine
from .sargerite import sargerite_shield
from .vts_config import get_config
 
 
# =================================================================
# UTILIDAD: historial ventas últimos 13 meses
# =================================================================
def _ventas_historial():
    hoy    = datetime.date.today()
    inicio = hoy.replace(day=1) - datetime.timedelta(days=365)
    ventas_hist = (
        HistorialVentas.objects
        .filter(fecha__gte=inicio)
        .values('fecha__year', 'fecha__month')
        .annotate(total=Sum('precio_bruto'))
        .order_by('fecha__year', 'fecha__month')
    )
    labels, data = [], []
    for r in ventas_hist:
        labels.append(f"{r['fecha__month']:02d}/{str(r['fecha__year'])[2:]}")
        data.append(float(r['total']))
    return labels, data
 
 
@login_required
def dashboard_home(request):
    reporte = FelEngine.generar_reporte_general()
    if reporte.get('estado') == 'vacio':
        return render(request, 'dashboard/index.html', {'estado': 'vacio', 'quiebres_reales': 0})
    auditorias = AuditoriaVTS.objects.filter(estado='activo')
    quiebres_reales    = int(auditorias.filter(inventario_real=0, variantes__isnull=True).count())
    alertas_reposicion = int(auditorias.filter(inventario_real__gt=0, inventario_real__lte=3, variantes__isnull=True).count())
    secciones = reporte.get('secciones', [])
    context = {
        'total_productos':    int(auditorias.count()),
        'capital_total':      int(float(reporte.get('total_inversion', 0))),
        'ganancia_potencial': int(float(reporte.get('total_ganancia', 0))),
        'quiebres_reales':    int(quiebres_reales),
        'alertas_reposicion': int(alertas_reposicion),
        'sin_costo':          int(auditorias.filter(precio_costo=0, variantes__isnull=True).count()),
        'productos_quiebre':  auditorias.filter(inventario_real__lte=3, variantes__isnull=True).order_by('inventario_real')[:15],
        'secciones_labels':   [str(s['seccion']) for s in secciones],
        'roi_labels':         [str(s['seccion']) for s in secciones],
        'roi_data':           [round(float(s['roi_pro']), 1) for s in secciones],
        'total_perdido_data': [int(float(s['inversion_total'])) for s in secciones],
    }
    return render(request, 'dashboard/index.html', context)
 
 
@login_required
def analisis_pro(request):
    reporte = FelEngine.generar_reporte_general()
    if reporte.get('estado') == 'vacio':
        return render(request, 'dashboard/analisis_pro.html', {'reporte': reporte})
 
    secciones = reporte.get('secciones', [])
    cfg    = get_config()
    factor = sum(v for k, v in cfg.items() if k.endswith('_pct'))
 
    perdida       = []
    sobrevivencia = []
    neutro        = []
    saludable     = []
    optimo        = []
    illidari      = []
 
    # Productos simples activos
    for p in AuditoriaVTS.objects.filter(estado='activo', variantes__isnull=True):
        costo = float(p.precio_costo)
        venta = float(p.precio_venta)
        if venta <= 0:
            continue
        costo_real = costo * (1 + factor)
        m          = (venta - costo_real) / venta
        entrada = {
            'sku':        p.sku,
            'producto':   p.producto,
            'seccion':    p.seccion,
            'margen':     round(m * 100, 1),
            'psp':        int(venta),
            'psp_neutro': int(costo_real / (1 - 0.18)) + 1,
        }
        if   m < 0.00: perdida.append(entrada)
        elif m < 0.10: sobrevivencia.append(entrada)
        elif m < 0.18: neutro.append(1)
        elif m < 0.26: saludable.append(1)
        elif m < 0.36: optimo.append(1)
        else:          illidari.append(1)
 
    # Variantes activas
    for v in VarianteVTS.objects.filter(estado='activo', producto__estado='activo').select_related('producto'):
        costo = float(v.precio_costo)
        venta = float(v.precio_venta)
        if venta <= 0:
            continue
        costo_real = costo * (1 + factor)
        m          = (venta - costo_real) / venta
        entrada = {
            'sku':        v.sku_variante,
            'producto':   f"{v.producto.producto} / {v.nombre_variante}",
            'seccion':    v.producto.seccion,
            'margen':     round(m * 100, 1),
            'psp':        int(venta),
            'psp_neutro': int(costo_real / (1 - 0.18)) + 1,
        }
        if   m < 0.00: perdida.append(entrada)
        elif m < 0.10: sobrevivencia.append(entrada)
        elif m < 0.18: neutro.append(1)
        elif m < 0.26: saludable.append(1)
        elif m < 0.36: optimo.append(1)
        else:          illidari.append(1)
 
    perdida.sort(key=lambda x: x['margen'])
    sobrevivencia.sort(key=lambda x: x['margen'])
 
    meses_labels, meses_data = _ventas_historial()
 
    context = {
        'reporte':            reporte,
        'secciones_labels':   [str(s['seccion']) for s in secciones],
        'roi_data':           [round(float(s.get('roi_pro', 0)), 1) for s in secciones],
        'total_perdido_data': [int(float(s.get('inversion_total', 0))) for s in secciones],
        'sin_costo_lista':    AuditoriaVTS.objects.filter(precio_costo=0, variantes__isnull=True, estado='activo').order_by('seccion'),
        'perdida_lista':      perdida,
        'sobrevivencia_lista': sobrevivencia,
        'semaforo_labels':    ['⚫ Pérdida', '🔴 Sobrevivencia', '🟡 Neutro', '🟢 Saludable', '🔥 Óptimo', '🟣 Illidari'],
        'semaforo_data':      [len(perdida), len(sobrevivencia), len(neutro), len(saludable), len(optimo), len(illidari)],
        'ventas_hist_labels': meses_labels,
        'ventas_hist_data':   meses_data,
    }
    return render(request, 'dashboard/analisis_pro.html', context)
 
 
@sargerite_shield(permiso_requerido='puede_ver_fotos')
def subir_foto_producto(request, sku):
    if request.method == 'POST' and request.FILES.get('imagen'):
        producto = get_object_or_404(AuditoriaVTS, sku=sku)
        producto.imagen = request.FILES['imagen']
        producto.save()
        messages.success(request, f"✅ Imagen de {sku} actualizada.")
    return redirect('inventario')
 
 
@login_required
def inventario_view(request):
    auditorias = AuditoriaVTS.objects.annotate(
        venta_neta=ExpressionWrapper(F('precio_venta') / 1.19, output_field=FloatField()),
        margen_db=ExpressionWrapper(
            (F('venta_neta') - F('precio_costo')) / Coalesce(F('venta_neta'), 1.0),
            output_field=FloatField()
        )
    ).prefetch_related('variantes').order_by('seccion')
    return render(request, 'dashboard/inventario.html', {'auditorias': auditorias})
 
 
def detalle_producto(request, sku):
    producto = get_object_or_404(AuditoriaVTS, sku=sku)
    return render(request, 'dashboard/ficha_producto.html', {'item': producto})
 
 
@login_required
def actualizar_inventario(request, sku):
    if request.method == 'POST':
        item = get_object_or_404(AuditoriaVTS, sku=sku)
        stock_viejo = item.inventario_real
        try:
            cantidad_a_sumar = int(request.POST.get('cantidad_nueva') or 0)
            if cantidad_a_sumar != 0:
                item.inventario_real += cantidad_a_sumar
                item.save()
                HistorialStock.objects.create(
                    sku=sku,
                    producto=item.producto,
                    stock_anterior=stock_viejo,
                    stock_nuevo=item.inventario_real,
                    usuario=request.user.username if request.user.is_authenticated else "Admin_VTS"
                )
                messages.success(request, f"✅ Se añadieron {cantidad_a_sumar} unidades a {sku}.")
        except ValueError:
            messages.error(request, "❌ Cantidad inválida.")
    return redirect('inventario')
 
 
@login_required
def validador_masivo(request):
    if request.method == 'POST':
        lineas = request.POST.get('bulk_data', '').splitlines()
        resultados = []
        for linea in lineas:
            if not linea.strip(): continue
            partes = linea.split(',') if ',' in linea else linea.split(';')
            sku = partes[0].strip().upper()
            prod_obj = AuditoriaVTS.objects.filter(sku=sku).first()
            resultados.append({
                'sku':    sku,
                'existe': prod_obj is not None,
                'nombre': prod_obj.producto if prod_obj else "NO ENCONTRADO",
            })
        return render(request, 'dashboard/validador_check.html', {'resultados': resultados})
    return render(request, 'dashboard/validador_form.html')
 
 
@transaction.atomic
def procesar_carga_masiva(request):
    if request.method == 'POST':
        skus      = request.POST.getlist('skus')
        cantidades = request.POST.getlist('cantidades')
        for sku, cant in zip(skus, cantidades):
            if not cant or int(cant) <= 0: continue
            prod = AuditoriaVTS.objects.select_for_update().get(sku=sku)
            stock_prev = prod.inventario_real
            prod.inventario_real += int(cant)
            prod.save()
            HistorialStock.objects.create(
                sku=sku, producto=prod.producto,
                stock_anterior=stock_prev, stock_nuevo=prod.inventario_real,
                usuario="Carga_Masiva"
            )
        return render(request, 'dashboard/validador_success.html')
 
 
def buscar_productos(request):
    query = request.GET.get('q', '').strip()
    if query:
        auditorias = AuditoriaVTS.objects.filter(
            Q(producto__icontains=query) | Q(sku__icontains=query)
        ).order_by('seccion')
    else:
        auditorias = AuditoriaVTS.objects.all().order_by('seccion')
    return render(request, 'dashboard/partials/forja_items_filas.html', {'auditorias': auditorias})
 
 
def api_config_costos(request):
    """Endpoint interno — devuelve porcentajes operativos para el JS del admin."""
    return JsonResponse(get_config())
 
 
@login_required
def inventario_pdf_view(request):
    import subprocess
    from datetime import datetime as dt
    timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
    ruta_pdf  = f"/home/asilvaq/Programacion/VTS/backups/inventario_{timestamp}.pdf"
    subprocess.run([
        '/home/asilvaq/Programacion/VTS/venv/bin/python',
        'manage.py', 'generar_inventario_pdf',
        '--output', ruta_pdf
    ], cwd='/home/asilvaq/Programacion/VTS')
    return FileResponse(
        open(ruta_pdf, 'rb'),
        as_attachment=True,
        filename=f'inventario_{timestamp}.pdf'
    )
 