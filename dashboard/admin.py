#dashboard/admin.py
from django.contrib import admin
from .models import AuditoriaVTS, HistorialStock, LogRetirosDeducibles, RegistroLogs, PerfilVTS, VarianteVTS, ConfigVTS

admin.site.site_header = "VTS - MARTILLO VIL"
admin.site.site_title = "Panel de Forja"
admin.site.index_title = "Administración de Inventario" 

class VarianteInline(admin.TabularInline):
    model = VarianteVTS
    extra = 1
    fields = ('sku_variante', 'nombre_variante', 'inventario_real', 'precio_costo', 'precio_venta', 'documento_tipo', 'imagen')
    
@admin.register(AuditoriaVTS)
class AuditoriaAdmin(admin.ModelAdmin):
    inlines = [VarianteInline]
    # 1. LIST DISPLAY: Conservador + Analítico
    # Mantenemos IDENTIDAD (Barras/Variante) y agregamos MÉTRICAS (Real/Diferencia/Pérdida)
    list_display = (
        'sku', 
        'codigo_barras',  # SE QUEDA (Vital para pistola)
        'producto', 
        'variante',       # SE QUEDA
        'seccion', 
        'inventario_real', # Agregado: Necesitas ver cuánto tienes
        'precio_venta',
        'diferencia_unidades', # Activado (estaba definido abajo pero no aquí)
        'perdida_monetaria'    # Activado (estaba definido abajo pero no aquí)
    )

    # 2. FILTROS Y BÚSQUEDA (Intactos)
    list_filter = ('seccion', 'documento_tipo')
    search_fields = ('sku', 'codigo_barras', 'producto')
    
    # Paginación para no saturar la vista si hay muchos ítems
    list_per_page = 50 

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Protección: Validamos si el campo existe antes de cambiarle el label
        if 'precio_costo' in form.base_fields:
            form.base_fields['precio_costo'].label = "Costo Neto ($)"
        if 'precio_venta' in form.base_fields:
            form.base_fields['precio_venta'].label = "Precio Venta Bruto (IVA Inc.) ($)"
        return form

    # 3. ESTILOS: La Unión hace la fuerza
    class Media:
        css = {
        'all': ('dashboard/css/style.css', 'dashboard/css/admin_custom.css')
        }
        js = ('dashboard/js/admin_calculadora.js',)

    def save_model(self, request, obj, form, change):
        if change and 'inventario_real' in form.changed_data:
            stock_anterior = AuditoriaVTS.objects.get(pk=obj.pk).inventario_real
            super().save_model(request, obj, form, change)
            diferencia = obj.inventario_real - stock_anterior
            tipo = 'INGRESO' if diferencia > 0 else 'MERMA'
            RegistroLogs.objects.create(
                sku=obj.sku,
                producto=obj.producto,
                tipo_accion=f'{tipo} [SUDO]',
                cantidad=abs(diferencia),
                operador=request.user
            )
        else:
            super().save_model(request, obj, form, change)

    # 🧮 CÁLCULO 1: Unidades
    def diferencia_unidades(self, obj):
        # Protección contra None types por si stock_sistema viene vacío
        real = obj.inventario_real or 0
        sistema = obj.stock_sistema or 0
        diff = real - sistema
        return diff
    diferencia_unidades.short_description = "Dif. Stock"

    # 💸 CÁLCULO 2: Dinero
    def perdida_monetaria(self, obj):
        real = obj.inventario_real or 0
        sistema = obj.stock_sistema or 0
        costo = obj.precio_costo or 0
        
        diff = real - sistema
        if diff < 0:
            perdida = abs(diff) * costo
            return f"${perdida:,.0f}" 
        return "-" # Devolvemos guión en vez de $0 para limpiar ruido visual
    perdida_monetaria.short_description = "Pérdida ($)"

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if isinstance(obj, VarianteVTS):
                try:
                    anterior = VarianteVTS.objects.get(pk=obj.pk)
                    if anterior.inventario_real != obj.inventario_real:
                        diferencia = obj.inventario_real - anterior.inventario_real
                        tipo = 'INGRESO' if diferencia > 0 else 'MERMA'
                        obj.save()
                        RegistroLogs.objects.create(
                            sku=obj.sku_variante,
                            producto=obj.producto.producto,
                            tipo_accion=f'{tipo} [SUDO]',
                            cantidad=abs(diferencia),
                            operador=request.user
                        )
                    else:
                        obj.save()
                except VarianteVTS.DoesNotExist:
                    obj.save()
        formset.save_m2m()

# El resto se mantiene IDÉNTICO a tu original
@admin.register(LogRetirosDeducibles)
class LogRetirosAdmin(admin.ModelAdmin):
    list_display = ('sku', 'cantidad', 'fecha', 'motivo')
    list_filter = ('fecha', 'motivo')
    search_fields = ('sku__sku', 'sku__producto')

@admin.register(RegistroLogs)
class RegistroLogsAdmin(admin.ModelAdmin):
    # CAMBIO: 'fecha' -> 'fecha_exacta'
    list_display = ('fecha_exacta', 'sku', 'producto', 'tipo_accion', 'cantidad', 'operador')
    list_filter = ('tipo_accion', 'fecha_exacta', 'operador')
    search_fields = ('sku', 'producto')

# Agregamos HistorialStock que estaba importado pero no registrado en tu snippet original
@admin.register(HistorialStock)
class HistorialStockAdmin(admin.ModelAdmin):
    list_display = ('fecha_ajuste', 'sku', 'producto', 'stock_anterior', 'stock_nuevo', 'usuario')
    list_filter = ('usuario', 'fecha_ajuste')

@admin.register(PerfilVTS)
class PerfilVTSAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'puede_ver_dikbig', 'sargerite_token', 'ultima_ip')
    list_filter = ('rol',)
    # Evitamos que se pueda editar el token a mano para no romper la llave
    readonly_fields = ('sargerite_token', 'ultima_ip')

@admin.register(ConfigVTS)
class ConfigVTSAdmin(admin.ModelAdmin):
    list_display = ('clave', 'valor', 'descripcion')
    ordering = ['clave']

