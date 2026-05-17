# views_personal.py — Sección VII de views.py
from datetime import date
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Colaborador
from .sargerite import sargerite_shield
from .akama import AkamaStrategy
from .eremita_engine import EremitaEngine
from .oraculo import OraculoSargerite

@login_required
@sargerite_shield(permiso_requerido='puede_ver_dikbig')
def importar_personal(request):
    if request.method == 'POST' and request.FILES.get('archivo_csv'):
        archivo = request.FILES['archivo_csv']
        resultado = AkamaStrategy.ejecucion_fila_a_fila(archivo)
        if 'HTTP_HX_REQUEST' in request.META:
            return render(request, 'dashboard/partials/resultado_importacion.html', {'res': resultado})
        messages.success(request, f"🛡️ Procesados: {resultado['creados']} nuevos, {resultado['actualizados']} actualizados.")
        return redirect('importar_personal')
    return render(request, 'dashboard/importar_personal.html')

@login_required
@sargerite_shield(permiso_requerido='puede_ver_dikbig')
def ficha_personal(request, rut=None):
    colaborador = None
    if rut:
        rut_clean = AkamaStrategy.normalizar_rut(rut)
        colaborador = get_object_or_404(Colaborador, rut=rut_clean)
    return render(request, 'dashboard/ficha_personal.html', {'paciente': colaborador})

@login_required
@sargerite_shield(permiso_requerido='puede_ver_dikbig')
def guardar_ficha(request, rut):
    if request.method == 'POST':
        rut_clean = AkamaStrategy.normalizar_rut(rut)
        paciente = get_object_or_404(Colaborador, rut=rut_clean)
        try:
            paciente.cargo = request.POST.get('cargo')
            paciente.sueldo_base = AkamaStrategy.limpiar_monto(request.POST.get('sueldo', '0'))
            paciente.afp = request.POST.get('afp')
            paciente.sistema_salud = request.POST.get('sistema_salud')
            plan_raw = request.POST.get('plan_isapre_uf', '0').replace(',', '.')
            paciente.plan_isapre_uf = float(plan_raw)
            paciente.tipo_contrato = request.POST.get('tipo_contrato', 'INDEFINIDO')
            paciente.asignacion_movilizacion = AkamaStrategy.limpiar_monto(request.POST.get('movilizacion', '0'))
            paciente.asignacion_colacion = AkamaStrategy.limpiar_monto(request.POST.get('colacion', '0'))
            paciente.direccion = request.POST.get('direccion')
            paciente.comuna = request.POST.get('comuna')
            paciente.telefono = request.POST.get('telefono')
            paciente.correo_electronico = request.POST.get('correo')
            paciente.fecha_inicio = AkamaStrategy.parsear_fecha(request.POST.get('inicio'))
            paciente.fecha_termino = AkamaStrategy.parsear_fecha(request.POST.get('termino'))
            paciente.save()
            return HttpResponse('<div class="alert alert-success animate__animated animate__headShake">🛡️ Expediente sincronizado correctamente.</div>')
        except Exception as e:
            return HttpResponse(f'<div class="alert alert-danger">❌ Error: {str(e)}</div>', status=500)
    return HttpResponse("Método no permitido", status=405)

@login_required
@sargerite_shield(permiso_requerido='puede_ver_dikbig')
def buscar_colaborador(request):
    rut_raw = request.GET.get('rut', '').strip()
    rut_clean = AkamaStrategy.normalizar_rut(rut_raw)
    try:
        colaborador = Colaborador.objects.get(rut=rut_clean)
        return render(request, 'dashboard/partials/_ficha_parcial.html', {'paciente': colaborador})
    except Colaborador.DoesNotExist:
        return HttpResponse('<div class="alert alert-warning">⚠️ No se encontró registro para el RUT: ' + rut_clean + '</div>')

@login_required
@sargerite_shield(permiso_requerido='puede_ver_dikbig')
def vista_mortaja(request, rut):
    colaborador = get_object_or_404(Colaborador, rut=rut)
    res = EremitaEngine.calcular_mortaja_provisoria(colaborador)
    hoy = date.today()
    inicio = colaborador.fecha_inicio
    total_meses = (hoy.year - inicio.year) * 12 + hoy.month - inicio.month
    context = {
        'colaborador': colaborador,
        'anios': total_meses // 12,
        'meses': total_meses % 12,
        'sueldo_base': colaborador.sueldo_base,
        'provision_anios': res['reserva_total'] - res['detalle']['vacaciones_proporcionales'],
        'vacaciones_monto': res['detalle']['vacaciones_proporcionales'],
        'total_reserva': res['reserva_total'],
    }
    return render(request, 'dashboard/mortaja_modal.html', context)

@login_required
def vista_sabana_digital(request):
    colaboradores = Colaborador.objects.all()
    df = EremitaEngine.procesar_sabana_completa(colaboradores)
    sabana_records = df.to_dict('records') if not df.empty else []
    ind = OraculoSargerite.obtener_indicadores()
    context = {
        'sabana': sabana_records,
        'uf_actual': ind['uf'],
        'utm_actual': ind['utm']
    }
    return render(request, 'dashboard/sabana_digital.html', context)

@require_POST
@login_required
def actualizar_indicadores_view(request):
    ind = OraculoSargerite.obtener_indicadores()
    if 'HTTP_HX_REQUEST' in request.META:
        return HttpResponse(f"""
            <i class="fas fa-microchip"></i>
            Estado del Oráculo: <strong>UF: ${ind['uf']} | UTM: ${ind['utm']}</strong>
        """)
    return redirect('sabana_digital')

@login_required
@sargerite_shield(permiso_requerido='puede_ver_dikbig')
def generar_liquidacion_view(request, rut):
    rut_clean = AkamaStrategy.normalizar_rut(rut)
    colaborador = get_object_or_404(Colaborador, rut=rut_clean)
    ind = OraculoSargerite.obtener_indicadores()
    valor_uf = ind['uf']
    resultados = EremitaEngine.calcular_liquidacion(colaborador, valor_uf)
    context = {
        'colaborador': colaborador,
        'res': resultados,
        'uf_dia': valor_uf,
        'fecha_emision': date.today(),
    }
    from django.shortcuts import render as django_render
    return django_render(request, 'dashboard/liquidacion.html', context)
