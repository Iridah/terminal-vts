# dashboard/views_ventas.py
# Módulo Ventas VTS — Wixelandr + Odd
# Importado por views.py (router central)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils.html import escapejs
import json

from .wixelandr import validar_csv_sumup, validar_acceso
from .odd import procesar_ventas, resumen_proceso, construir_mapeo_desde_inventario
from .models import RegistroLogs


# ----------------------------------------------------------------
# ventas/importar/
# ----------------------------------------------------------------
@login_required
@require_http_methods(["GET", "POST"])
def ventas_importar(request):
    if not validar_acceso(request.user):
        messages.error(request, "Acceso denegado. Token Sargerite requerido.")
        return redirect('home')

    if request.method == 'POST':
        confirmar = request.POST.get('confirmar') == '1'

        # ── Confirmación final → procesar ──────────────────────
        if confirmar:
            filas_json = request.POST.get('filas_json', '[]')
            try:
                filas     = json.loads(filas_json)
                resultado = procesar_ventas(filas, request.user)
                resumen   = resumen_proceso(resultado)
                RegistroLogs.objects.create(
                    operador=request.user,
                    tipo_accion='VENTAS_IMPORTAR',
                    sku='SUMUP-CSV',
                    producto=f"Procesadas:{resultado['procesadas']} | SinMatch:{len(resultado['sin_match'])} | Errores:{len(resultado['errores'])}",
                    cantidad=resultado['procesadas'],
                )
                return render(request, 'dashboard/partials/ventas_resultado.html', {
                    'resultado': resultado,
                    'resumen':   resumen,
                })
            except Exception as e:
                return render(request, 'dashboard/partials/ventas_error.html', {
                    'error': str(e)
                })

        # ── Primera carga → validar y mostrar preview ───────────
        archivo = request.FILES.get('csv_ventas')
        if not archivo:
            return render(request, 'dashboard/partials/ventas_error.html', {
                'error': 'No se recibió ningún archivo.'
            })

        validacion = validar_csv_sumup(archivo)

        if not validacion['ok']:
            return render(request, 'dashboard/partials/ventas_error.html', {
                'errores': validacion['errores']
            })

        # Limpiar claves con espacios/paréntesis para el template
        filas_limpias = []
        for f in validacion['filas_validas'][:20]:
            filas_limpias.append({
                'fecha':       f.get('Fecha', ''),
                'descripcion': f.get('Descripción', ''),
                'cantidad':    f.get('Cantidad', '1'),
                'precio':      f.get('Precio (Bruto)', '0'),
                'id_tx':       f.get('ID de transacción', ''),
            })

        filas_json = json.dumps(validacion['filas_validas'], ensure_ascii=False)

        return render(request, 'dashboard/partials/ventas_preview.html', {
            'filas':        filas_limpias,
            'total_filas':  len(validacion['filas_validas']),
            'advertencias': validacion['advertencias'],
            'filas_json':   filas_json,
        })

    return render(request, 'dashboard/ventas_importar.html')


# ----------------------------------------------------------------
# ventas/reporte/
# ----------------------------------------------------------------
@login_required
def ventas_reporte(request):
    if not validar_acceso(request.user):
        messages.error(request, "Acceso denegado.")
        return redirect('home')

    logs = RegistroLogs.objects.filter(
    tipo_accion='VENTAS_IMPORTAR'
    ).order_by('-fecha_exacta')[:50]

    return render(request, 'dashboard/ventas_reporte.html', {
        'logs': logs,
    })


# ----------------------------------------------------------------
# ventas/mapeo/
# ----------------------------------------------------------------
@login_required
@require_http_methods(["GET", "POST"])
def ventas_mapeo(request):
    if not validar_acceso(request.user):
        messages.error(request, "Acceso denegado.")
        return redirect('home')

    mapeo = None

    if request.method == 'POST':
        archivo = request.FILES.get('csv_inventario')
        if archivo:
            validacion = validar_csv_sumup(archivo)
            if validacion['ok'] and validacion['tipo'] == 'inventario':
                mapeo = construir_mapeo_desde_inventario(validacion['filas_validas'])
            else:
                messages.error(request, 'El archivo no es un CSV de inventario SumUp válido.')

    return render(request, 'dashboard/ventas_mapeo.html', {
        'mapeo': mapeo,
    })






