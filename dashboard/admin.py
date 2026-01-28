#dashboard/admin.py
from django.contrib import admin
from .models import AuditoriaVTS, HistorialStock, LogRetirosDeducibles, RegistroLogs, PerfilVTS

admin.site.site_header = "VTS - MARTILLO VIL"
admin.site.site_title = "Panel de Forja"
admin.site.index_title = "Administración de Inventario" 

@admin.register(AuditoriaVTS)
class AuditoriaAdmin(admin.ModelAdmin):
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
            # Cargamos ambos: style.css (fuentes/vars) + admin_custom.css (tus ajustes específicos)
            'all': ('dashboard/css/style.css', 'dashboard/css/admin_custom.css')
        }

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


