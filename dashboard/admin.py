#dashboard/admin.py
from django.contrib import admin
from django import forms
from .models import AuditoriaVTS, HistorialStock, LogRetirosDeducibles, RegistroLogs, PerfilVTS, VarianteVTS, ConfigVTS
 
admin.site.site_header = "VTS - MARTILLO VIL"
admin.site.site_title = "Panel de Forja"
admin.site.index_title = "Administración de Inventario"
 
 
# =================================================================
# FORMULARIO PERSONALIZADO — Select cerrado para Sección
# =================================================================
class AuditoriaVTSForm(forms.ModelForm):
    SECCIONES = [
        ('Abarrotes',       'Abarrotes'),
        ('Bebe',            'Bebé'),
        ('Boutique',        'Boutique'),
        ('Cuidado Personal','Cuidado Personal'),
        ('Electronica',     'Electrónica'),
        ('Ferreteria',      'Ferretería'),
        ('Libreria',        'Librería'),
        ('Limpieza',        'Limpieza'),
        ('Menaje',          'Menaje'),
    ]
 
    ESTADOS = [
        ('activo',        'Activo'),
        ('criocongelado', '❄️ Criocongelado'),
        ('descontinuado', 'Descontinuado'),
    ]
 
    seccion = forms.ChoiceField(
        choices=SECCIONES,
        label='Sección',
        widget=forms.Select(attrs={'style': 'width:220px;'})
    )
    estado = forms.ChoiceField(
        choices=ESTADOS,
        label='Estado',
        widget=forms.Select(attrs={'style': 'width:220px;'})
    )
 
    class Meta:
        model  = AuditoriaVTS
        fields = '__all__'
 
 
# =================================================================
# INLINE DE VARIANTES
# =================================================================
class VarianteInline(admin.TabularInline):
    model  = VarianteVTS
    extra  = 1
    fields = (
        'sku_variante', 'nombre_variante', 'estado',
        'inventario_real', 'precio_costo', 'precio_venta',
        'documento_tipo', 'imagen'
    )
 
 
# =================================================================
# ADMIN AUDITORÍA VTS
# =================================================================
@admin.register(AuditoriaVTS)
class AuditoriaAdmin(admin.ModelAdmin):
    form    = AuditoriaVTSForm
    inlines = [VarianteInline]
 
    list_display = (
        'sku',
        'codigo_barras',
        'producto',
        'variante',
        'seccion',
        'estado',
        'inventario_real',
        'precio_venta',
    )
 
    list_filter   = ('seccion', 'estado', 'documento_tipo')
    search_fields = ('sku', 'codigo_barras', 'producto')
    list_per_page = 50
    readonly_fields = ('costo_neto_calculado', 'iva_calculado')

 
    # ── Fieldsets: Sección y Estado al frente ────────────────────
    fieldsets = (
        ('📦 Clasificación', {
            'fields': ('seccion', 'estado', 'sku', 'codigo_barras')
        }),
        ('🏷 Identificación', {
            'fields': ('producto', 'variante', 'imagen')
        }),
        ('📊 Inventario', {
            'fields': ('stock_sistema', 'inventario_real', 'aporte_hogar_total')
        }),
        ('💰 Precios', {
            'fields': ('precio_costo', 'costo_neto_calculado', 'iva_calculado', 'precio_venta', 'documento_tipo')
        }),
    )
 
    def costo_neto_calculado(self, obj):
        if obj.precio_costo:
            neto = float(obj.precio_costo) / 1.19
            return f"${neto:,.0f}"
        return "—"
    costo_neto_calculado.short_description = "Costo Neto (sin IVA)"

    def iva_calculado(self, obj):
        if obj.precio_costo:
            iva = float(obj.precio_costo) - (float(obj.precio_costo) / 1.19)
            return f"${iva:,.0f}"
        return "—"
    iva_calculado.short_description = "IVA (19%)"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'precio_costo' in form.base_fields:
            form.base_fields['precio_costo'].label = "Costo de Compra ($) bruto"
        if 'precio_venta' in form.base_fields:
            form.base_fields['precio_venta'].label = "Precio Sugerido al Público (PSP) ($)"
        return form
 
    class Media:
        css = {'all': ('dashboard/css/style.css', 'dashboard/css/admin_custom.css')}
        js  = ('dashboard/js/admin_calculadora.js',)
 
    def save_model(self, request, obj, form, change):
        if change and 'inventario_real' in form.changed_data:
            stock_anterior = AuditoriaVTS.objects.get(pk=obj.pk).inventario_real
            super().save_model(request, obj, form, change)
            diferencia = obj.inventario_real - stock_anterior
            tipo = 'INGRESO' if diferencia > 0 else 'MERMA'
            RegistroLogs.objects.create(
                sku        = obj.sku,
                producto   = obj.producto,
                tipo_accion= f'{tipo} [SUDO]',
                cantidad   = abs(diferencia),
                operador   = request.user
            )
        else:
            super().save_model(request, obj, form, change)
 
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
                            sku        = obj.sku_variante,
                            producto   = obj.producto.producto,
                            tipo_accion= f'{tipo} [SUDO]',
                            cantidad   = abs(diferencia),
                            operador   = request.user
                        )
                    else:
                        obj.save()
                except VarianteVTS.DoesNotExist:
                    obj.save()
        formset.save_m2m()
 
 
# =================================================================
# RESTO DE ADMINS
# =================================================================
@admin.register(LogRetirosDeducibles)
class LogRetirosAdmin(admin.ModelAdmin):
    list_display  = ('sku', 'cantidad', 'fecha', 'motivo')
    list_filter   = ('fecha', 'motivo')
    search_fields = ('sku__sku', 'sku__producto')
 
 
@admin.register(RegistroLogs)
class RegistroLogsAdmin(admin.ModelAdmin):
    list_display  = ('fecha_exacta', 'sku', 'producto', 'tipo_accion', 'cantidad', 'operador')
    list_filter   = ('tipo_accion', 'fecha_exacta', 'operador')
    search_fields = ('sku', 'producto')
 
 
@admin.register(HistorialStock)
class HistorialStockAdmin(admin.ModelAdmin):
    list_display = ('fecha_ajuste', 'sku', 'producto', 'stock_anterior', 'stock_nuevo', 'usuario')
    list_filter  = ('usuario', 'fecha_ajuste')
 
 
@admin.register(PerfilVTS)
class PerfilVTSAdmin(admin.ModelAdmin):
    list_display    = ('user', 'rol', 'puede_ver_dikbig', 'sargerite_token', 'ultima_ip')
    list_filter     = ('rol',)
    readonly_fields = ('sargerite_token', 'ultima_ip')
 
 
@admin.register(ConfigVTS)
class ConfigVTSAdmin(admin.ModelAdmin):
    list_display = ('clave', 'valor', 'descripcion')
    ordering     = ['clave']