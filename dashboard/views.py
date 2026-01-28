# dashboard/views.py
import json
import csv
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, ExpressionWrapper, FloatField, Q
from django.db.models.functions import Coalesce
from django.db import transaction
from datetime import datetime

# Modelos y Engine
from .models import AuditoriaVTS, HistorialStock, LogRetirosDeducibles, RegistroLogs, Colaborador
from .engine import FelEngine
from .sargerite import sargerite_shield
from .akama import AkamaStrategy

# =================================================================
# I. SECCIÓN CORE: VISTAS PRINCIPALES Y ANÁLISIS
# =================================================================
@login_required
def dashboard_home(request):
    """
    Radar de control principal v2.7.5 unificado.
    Centraliza métricas de AuditoriaVTS y cálculos del FelEngine.
    """
    # 1. Llamada única al Motor Vil (Cálculos financieros Pro)
    reporte = FelEngine.generar_reporte_general()
    
    # 2. Manejo de estado vacío (Blindaje de seguridad)
    if reporte.get('estado') == 'vacio':
        return render(request, 'dashboard/index.html', {'estado': 'vacio', 'quiebres_reales': 0})

    # 3. Métricas directas del ORM (Normalización a INT)
    # Evitamos que el motor de plantillas reciba objetos de consulta complejos
    auditorias = AuditoriaVTS.objects.all()
    quiebres_reales = int(auditorias.filter(inventario_real=0).count())
    alertas_reposicion = int(auditorias.filter(inventario_real__gt=0, inventario_real__lte=3).count())
    
    # 4. Extracción y Limpieza de Datos del Engine
    # Convertimos explícitamente a tipos nativos para matar el bug de las comas decimales
    secciones = reporte.get('secciones', [])

    # NORMALIZACIÓN PILOTO: Forzamos INT nativo [cite: 2026-01-14]
    quiebres_reales = int(auditorias.filter(inventario_real=0).count())

    # 5. Construcción del Contexto para Mardum
    context = {
        # TARJETAS: Valores atómicos (int/float de Python puro)
        'total_productos': int(auditorias.count()),
        'capital_total': int(float(reporte.get('total_inversion', 0))), # Matamos el float64 de Pandas
        'ganancia_potencial': int(float(reporte.get('total_ganancia', 0))),
        'quiebres_reales': int(quiebres_reales),
        'alertas_reposicion': int(alertas_reposicion),
        
        # TABLA DE RIESGOS CRÍTICOS (Top 12 para el dashboard)
        'productos_quiebre': auditorias.filter(inventario_real__lte=3).order_by('inventario_real')[:12],
        
        # JS/GRAFICOS: Listas purificadas (Sincronización Illidari)
        'secciones_labels': [str(s['seccion']) for s in secciones],
        'roi_labels': [str(s['seccion']) for s in secciones],
        'roi_data': [round(float(s['roi_pro']), 1) for s in secciones],
        'total_perdido_data': [int(float(s['inversion_total'])) for s in secciones],# Alimenta "Valor por Sección"
        }
    
    return render(request, 'dashboard/index.html', context)

def analisis_pro(request):
    """Pestaña de análisis avanzado con motor FelEngine"""
    reporte = FelEngine.generar_reporte_general()

    # Si el motor falló o está vacío, salimos rápido
    if reporte.get('estado') == 'vacio':
        return render(request, 'dashboard/analisis_pro.html', {'reporte': reporte})
    
    # EXTRACCIÓN Y LIMPIEZA (El puente entre Python y JS)
    secciones = reporte.get('secciones', [])

    # Sincronización Illidari: Convertimos todo a nativo de una vez
    context = {
        'reporte': reporte,
        # Etiquetas limpias
        'secciones_labels': [str(s['seccion']) for s in secciones],
        'roi_data': [round(float(s.get('roi_pro', 0)), 1) for s in secciones],
        'total_perdido_data': [int(float(s.get('inversion_total', 0))) for s in secciones],
    }
    
    return render(request, 'dashboard/analisis_pro.html', context)

@sargerite_shield(permiso_requerido='puede_ver_fotos')
def subir_foto_producto(request, sku):
    if request.method == 'POST' and request.FILES.get('imagen'):
        producto = get_object_or_404(AuditoriaVTS, sku=sku)
        producto.imagen = request.FILES['imagen']
        producto.save() # Aquí se dispara la conversión a WebP de tu modelo
        messages.success(request, f"✅ Imagen de {sku} actualizada.")
    return redirect('inventario')


# ================================================================= 
# II. SECCIÓN OPERATIVA: LA FORJA (CRUD & BÚSQUEDA)
# =================================================================
@login_required
def inventario_view(request):
    """La Forja: Gestión operativa diaria"""
    auditorias = AuditoriaVTS.objects.annotate(
        venta_neta=ExpressionWrapper(F('precio_venta') / 1.19, output_field=FloatField()),
        margen_db=ExpressionWrapper(
            (F('venta_neta') - F('precio_costo')) / Coalesce(F('venta_neta'), 1.0),
            output_field=FloatField()
        )
    ).order_by('seccion')
    return render(request, 'dashboard/inventario.html', {'auditorias': auditorias})

def detalle_producto(request, sku):
    """Ficha técnica de producto individual"""
    producto = get_object_or_404(AuditoriaVTS, sku=sku) 
    return render(request, 'dashboard/ficha_producto.html', {'item': producto})

@login_required
def actualizar_inventario(request, sku):
    """Acción de Suma Rápida desde la tabla de La Forja"""
    if request.method == 'POST':
        item = get_object_or_404(AuditoriaVTS, sku=sku)
        stock_viejo = item.inventario_real
        
        # Capturamos la cantidad a SUMAR del nuevo input
        try:
            cantidad_a_sumar = int(request.POST.get('cantidad_nueva') or 0)
            
            if cantidad_a_sumar != 0:
                item.inventario_real += cantidad_a_sumar
                item.save()
                
                # Registro en historial para no perder el rastro
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

# =================================================================
# III. SECCIÓN LOGÍSTICA: CARGAS MASIVAS Y VALIDACIÓN
# =================================================================

@login_required
def validador_masivo(request):
    """Formulario y lógica de pre-validación de SKUs"""
    if request.method == 'POST':
        lineas = request.POST.get('bulk_data', '').splitlines()
        resultados = []
        for linea in lineas:
            if not linea.strip(): continue
            partes = linea.split(',') if ',' in linea else linea.split(';')
            sku = partes[0].strip().upper()
            prod_obj = AuditoriaVTS.objects.filter(sku=sku).first()
            resultados.append({
                'sku': sku,
                'existe': prod_obj is not None,
                'nombre': prod_obj.producto if prod_obj else "NO ENCONTRADO",
            })
        return render(request, 'dashboard/validador_check.html', {'resultados': resultados})
    return render(request, 'dashboard/validador_form.html')


@transaction.atomic
def procesar_carga_masiva(request):
    """Ejecución final de carga masiva con seguridad atómica"""
    if request.method == 'POST':
        skus = request.POST.getlist('skus')
        cantidades = request.POST.getlist('cantidades')
        for sku, cant in zip(skus, cantidades):
            if not cant or int(cant) <= 0: continue
            prod = AuditoriaVTS.objects.select_for_update().get(sku=sku)
            stock_prev = prod.inventario_real
            prod.inventario_real += int(cant)
            prod.save()
            HistorialStock.objects.create(sku=sku, producto=prod.producto, stock_anterior=stock_prev, 
                                        stock_nuevo=prod.inventario_real, usuario="Carga_Masiva")
        return render(request, 'dashboard/validador_success.html')


# =================================================================
# IV. SECCIÓN API: ENDPOINTS PARA INTERFAZ JS (LA TRIADA)
# =================================================================

@require_POST
@login_required
def registrar_movimiento_triada(request):
    """API para el modal de La Triada (Venta, Merma, Aporte, Ingreso)"""
    try:
        data = json.loads(request.body)
        prod = get_object_or_404(AuditoriaVTS, sku=data['sku'])
        cantidad = int(data['cantidad'])
        tipo = data['tipo']
        
        if tipo in ['venta', 'merma', 'aporte']: prod.inventario_real -= cantidad
        elif tipo == 'ingreso': prod.inventario_real += cantidad
        prod.save()

        # ARREGLO CLAVE: Eliminamos 'fecha' porque el modelo usa 'fecha_exacta' auto
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
    
# === CONTINUACIÓN DE SECCIÓN IV (API & LOGS) ===

@login_required
def lista_logs(request):
    """Visualización de los últimos movimientos registrados (Historial de Stock)"""
    # Traemos los últimos 50 ajustes de inventario
    logs = HistorialStock.objects.all().order_by('-fecha_ajuste')[:50]
    return render(request, 'dashboard/logs.html', {'logs': logs})

@csrf_exempt
@login_required
def registrar_aporte_hogar(request):
    """API para descontar stock por aporte al hogar (Deducibles)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            with transaction.atomic():
                producto = get_object_or_404(AuditoriaVTS, sku=data['sku'])
                cantidad = int(data['cantidad'])
                
                # Verificación manual antes del save para dar un error amigable
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

# =================================================================
# V. BUSCADOR HTMX (SIN CÓDIGO MUERTO)
# =================================================================

def buscar_productos(request):
    """Motor de búsqueda ultra-rápido para La Forja"""
    query = request.GET.get('q', '').strip()
    
    if query:
        auditorias = AuditoriaVTS.objects.filter(
            Q(producto__icontains=query) | Q(sku__icontains=query)
        ).order_by('seccion')
    else:
        auditorias = AuditoriaVTS.objects.all().order_by('seccion')

    # Retorno único y directo al parcial de la tabla
    return render(request, 'dashboard/partials/forja_items_filas.html', {
        'auditorias': auditorias
    })

# =================================================================
# VI. ACCIONES HTMX Y NOTIFICACIONES
# =================================================================

@require_POST
@login_required
def registrar_movimiento_htmx(request, sku):
    """Procesa movimientos y firma con el Operador Real"""
    producto = get_object_or_404(AuditoriaVTS, sku=sku)
    tipo = request.POST.get('tipo')
    cantidad = int(request.POST.get('cantidad', 1))
    
    if tipo in ['venta', 'merma', 'aporte']: producto.inventario_real -= cantidad
    elif tipo == 'ingreso': producto.inventario_real += cantidad
    producto.save()

    # Registro firmado por el Archimago/Guardián
    RegistroLogs.objects.create(
        sku=sku,
        producto=producto.producto,
        tipo_accion=tipo.upper(),
        cantidad=cantidad,
        operador=request.user # <-- Captura al usuario logueado
    )

    auditorias = AuditoriaVTS.objects.all().order_by('seccion')
    return render(request, 'dashboard/partials/forja_items_filas.html', {'auditorias': auditorias})

def check_logs_notificados(request):
    """Endpoint para el sistema de notificaciones Alt-Tab"""
    # Filtramos por el nuevo campo de fecha para evitar confusiones
    hay_novedad = RegistroLogs.objects.filter(notificado=False).exists()
    if hay_novedad:
        ultimo = RegistroLogs.objects.filter(notificado=False).latest('fecha_exacta')
        ultimo.notificado = True
        ultimo.save()
        return JsonResponse({'alerta': True, 'producto': ultimo.producto, 'stock': ultimo.cantidad})
    return JsonResponse({'alerta': False})

@sargerite_shield(permiso_requerido='puede_ver_dikbig')
def importar_personal_dikbig(request):
    if request.method == 'POST' and request.FILES.get('archivo_csv'):
        try:
            # 1. Lectura robusta con utf-8-sig (para la Ñ y tildes)
            archivo_data = request.FILES['archivo_csv'].read().decode('utf-8-sig').splitlines()
            lector = csv.reader(archivo_data)
            
            # Saltar la cabecera (rut, ap_p, ap_m, etc.)
            next(lector, None) 

            exitos = 0
            with transaction.atomic():
                for fila in lector:
                    # Validación mínima de columnas (tu CSV tiene 15 columnas)
                    if not fila or len(fila) < 11:
                        continue
                    
                    # --- Lógica de Negocio VTS ---
                    rut_limpio = fila[0].strip().replace('.', '')
                    
                    # Manejo de Adicional Salud (Fonasa o #N/A -> 0)
                    adicional = fila[10].strip()
                    if adicional.upper() in ['#N/A', '0', '']:
                        adicional_valor = 0.0
                    else:
                        adicional_valor = float(adicional.replace(',', '.'))

                    # Mapeo Directo al Modelo
                    Colaborador.objects.update_or_create(
                        rut=rut_limpio,
                        defaults={
                            'apellido_paterno': fila[1].strip(),
                            'apellido_materno': fila[2].strip(),
                            'nombres': fila[3].strip(),
                            'cargo': fila[4].strip(),
                            'sueldo_base': float(fila[5].strip() or 0),
                            # Formato Chile: DDMMYYYY
                            'fecha_inicio': datetime.strptime(fila[6].strip(), '%d%m%Y').date(),
                            'fecha_termino': datetime.strptime(fila[7].strip(), '%d%m%Y').date() if (fila[7].strip().isdigit()) else None,
                            'afp': fila[8].strip(),
                            'salud': fila[9].strip(),
                            'adicional_salud': adicional_valor,
                            'direccion': fila[11].strip(),
                            'comuna': fila[12].strip(),
                            'correo_electronico': fila[13].strip(),
                            'telefono': fila[14].strip(),
                        }
                    )
                    exitos += 1

            # SI ES HTMX (USANDO META PARA DJ6)
            if 'HTTP_HX_REQUEST' in request.META:
                return render(request, 'dashboard/partials/resultado_importacion.html', {
                    'exitos': exitos
                })

            # Si por alguna razón no es HTMX, mensaje normal y render completo
            messages.success(request, f"🛡️ Carga Atómica Exitosa: {exitos} registros.")

        except Exception as e:
            if 'HTTP_HX_REQUEST' in request.META:
                return f'<div class="alert alert-danger">🚨 Error: {str(e)}</div>'
            messages.error(request, f"🚨 Error: {str(e)}")

    return render(request, 'dashboard/importar_personal.html')

# =================================================================
# VII. SECCIÓN RRHH: TANQUE DIKBIG
# =================================================================
@login_required
@sargerite_shield(permiso_requerido='puede_ver_dikbig')
def importar_personal(request):
    """
    Punto de entrada para la Carga Atómica de Personal.
    Delega la lógica pesada a AkamaStrategy para mantener views.py limpio.
    """
    if request.method == 'POST' and request.FILES.get('archivo_csv'):
        archivo = request.FILES['archivo_csv']
        
        # Invocamos al estratega Akama
        # Él se encarga del encoding, normalizar RUT y limpiar sueldos
        resultado = AkamaStrategy.ejecucion_fila_a_fila(archivo)
        
        # Si la petición viene de HTMX, enviamos solo el parcial del resultado
        if 'HTTP_HX_REQUEST' in request.META:
            return render(request, 'dashboard/partials/resultado_carga.html', {
                'res': resultado
            })
        
        # Si es una carga tradicional
        messages.success(request, f"🛡️ Procesados: {resultado['creados']} nuevos, {resultado['actualizados']} actualizados.")
        return redirect('importar_personal')

    return render(request, 'dashboard/importar_personal.html')

@login_required
@sargerite_shield(permiso_requerido='puede_ver_dikbig')
def ficha_personal(request, rut=None):
    colaborador = None
    if rut:
        # Usamos Akama para limpiar el RUT de búsqueda
        rut_clean = AkamaStrategy.normalizar_rut(rut)
        colaborador = get_object_or_404(Colaborador, rut=rut_clean)
    
    return render(request, 'dashboard/ficha_personal.html', {'paciente': colaborador})

@login_required
@sargerite_shield(permiso_requerido='puede_ver_dikbig')
def guardar_ficha(request, rut):
    if request.method == 'POST':
        paciente = get_object_or_404(Colaborador, rut=rut)
        # Actualizamos los campos
        paciente.nombres = request.POST.get('nombres')
        paciente.sueldo_base = AkamaStrategy.limpiar_monto(request.POST.get('sueldo'))
        paciente.save()
        
        # Respuesta HTMX: solo un mensaje de éxito
        return HttpResponse('<div class="alert alert-success">🛡️ Expediente Actualizado en la Bóveda.</div>')