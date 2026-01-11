from django.contrib import admin
from .models import AuditoriaVTS

@admin.register(AuditoriaVTS)
class AuditoriaAdmin(admin.ModelAdmin):
    # Columnas que veremos en la lista
    list_display = ('sku', 'producto', 'seccion', 'diferencia_unidades', 'perdida_monetaria', 'fecha_auditoria')
    # Filtros laterales (Exprimiendo el limón)
    list_filter = ('seccion', 'fecha_auditoria')
    # Buscador
    search_fields = ('sku', 'producto')

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