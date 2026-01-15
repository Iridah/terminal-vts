from django.contrib import admin
from .models import AuditoriaVTS, HistorialStock, LogRetirosDeducibles

admin.site.site_header = "VTS - MARTILLO VIL"
admin.site.site_title = "Panel de Forja"
admin.site.index_title = "Administración de Inventario" 

@admin.register(AuditoriaVTS)
class AuditoriaAdmin(admin.ModelAdmin):
    # Columnas que veremos en la lista
    list_display = ('sku', 'codigo_barras', 'producto', 'variante', 'seccion', 'precio_venta')
    # Filtros laterales (Exprimiendo el limón)
    list_filter = ('seccion', 'documento_tipo')
    # Buscador
    search_fields = ('sku', 'codigo_barras', 'producto')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['precio_costo'].label = "Costo Neto ($)"
        form.base_fields['precio_venta'].label = "Precio Venta Bruto (IVA Inc.) ($)"
        return form
    # CSS Inyectado para cambiar colores (Dark/Purple)
    class Media:
        css = {
            'all': ('dashboard/css/admin_custom.css',)
        }

    # 🧮 Cálculo de unidades faltantes
    def diferencia_unidades(self, obj):
        diff = obj.inventario_real - obj.stock_sistema
        return diff
    diferencia_unidades.short_description = "Dif. Unidades"

    # 💸 Cálculo de pérdida en dinero (Precio Costo)
    def perdida_monetaria(self, obj):
        diff = obj.inventario_real - obj.stock_sistema
        if diff < 0:
            perdida = abs(diff) * obj.precio_costo
            return f"${perdida:,.0f}" # Formato de dinero
        return "$0"
    perdida_monetaria.short_description = "Pérdida ($)"

@admin.register(LogRetirosDeducibles)
class LogRetirosAdmin(admin.ModelAdmin):
    list_display = ('sku', 'cantidad', 'fecha', 'motivo')
    list_filter = ('fecha', 'motivo')
    search_fields = ('sku__sku', 'sku__producto')