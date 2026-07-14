# dashboard/models/inventario.py
# Dominio: Inventario VTS
# Clases: AuditoriaVTS, VarianteVTS, HistorialStock

import os
from django.db import models
from django.core.exceptions import ValidationError
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile


# =================================================================
# I. CLASE MAESTRA: AUDITORÍA VTS (EL CORAZÓN)
# =================================================================
class AuditoriaVTS(models.Model):

    ESTADO_CHOICES = [
        ('activo',        'Activo'),
        ('criocongelado', 'Criocongelado'),
        ('descontinuado', 'Descontinuado'),
    ]

    # --- Campos de Identificación ---
    sku             = models.CharField(max_length=50, primary_key=True)
    codigo_barras   = models.CharField(max_length=100, blank=True, null=True, verbose_name="Código de Barras")
    producto        = models.CharField(max_length=200)
    seccion         = models.CharField(max_length=100)
    variante        = models.CharField(max_length=50, blank=True, null=True, verbose_name="Variante/Color")
    imagen          = models.ImageField(upload_to='productos/', blank=True, null=True, verbose_name="Foto del Producto")
    estado          = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo', verbose_name="Estado")
    sumup_item_id   = models.CharField(max_length=100, blank=True, default='', verbose_name="SumUp Item ID")

    # --- Campos de Inventario ---
    stock_sistema       = models.IntegerField(default=0)
    inventario_real     = models.IntegerField(default=0)
    aporte_hogar_total  = models.IntegerField(default=0)

    # --- Campos Financieros ---
    precio_costo    = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    precio_venta    = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    documento_tipo  = models.CharField(
        max_length=20,
        choices=[('BOLETA', 'Boleta'), ('FACTURA', 'Factura')],
        default='BOLETA'
    )
    fecha_auditoria = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Auditoría VTS"
        verbose_name_plural = "Auditorías VTS"
        ordering            = ['seccion', 'producto']

    # Mapa de secciones a prefijos SKU
    SECCION_PREFIJOS = {
        'Abarrotes':       'ABA',
        'Bebe':            'BEB',
        'Boutique':        'BOU',
        'Colaciones':    'COL',
        'Cuidado Personal':'CPE',
        'Electronica':     'ELE',
        'Ferreteria':      'FER',
        'Libreria':        'LIB',
        'Limpieza':        'LIM',
        'Menaje':          'MEN',
    }

    @classmethod
    def generar_sku(cls, seccion):
        prefijo = cls.SECCION_PREFIJOS.get(seccion)
        if not prefijo:
            prefijo = seccion.upper().replace(' ', '')[:3]
        patron   = f'V-{prefijo}-'
        ultimos  = cls.objects.filter(sku__startswith=patron).values_list('sku', flat=True)
        numeros  = []
        for sku in ultimos:
            try:
                numeros.append(int(sku.replace(patron, '')))
            except ValueError:
                continue
        siguiente = max(numeros) + 1 if numeros else 1
        return f'{patron}{siguiente:03d}'

    # ── Validación ────────────────────────────────────────────────
    def clean(self):
        if self.inventario_real < 0:
            raise ValidationError({'inventario_real': 'El stock no puede ser negativo.'})
        if self.precio_costo < 0 or self.precio_venta < 0:
            raise ValidationError('Los montos financieros deben ser positivos.')

    def save(self, *args, **kwargs):
        if not self.sku and self.seccion:
            self.sku = self.generar_sku(self.seccion)
        self.full_clean()
        if self.imagen and hasattr(self.imagen, 'file'):
            img = Image.open(self.imagen)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((800, 800), Image.LANCZOS)
            buffer = BytesIO()
            img.save(buffer, format="WEBP", quality=80)
            buffer.seek(0)
            nombre_base  = os.path.basename(os.path.splitext(self.imagen.name)[0])
            nuevo_nombre = nombre_base + ".webp"
            self.imagen.save(nuevo_nombre, ContentFile(buffer.read()), save=False)
        super().save(*args, **kwargs)

    # ── KPIs Financieros ──────────────────────────────────────────
    @property
    def margen_valor(self):
        try:
            from .vts_config import get_config
            cfg    = get_config()
            factor = sum(v for k, v in cfg.items() if k.endswith('_pct'))
            costo_real = float(self.precio_costo) * (1 + factor)
            venta      = float(self.precio_venta)
            if venta <= 0:
                return 0
            return (venta - costo_real) / venta
        except:
            return 0

    def get_potencial_ganancia(self):
        try:
            return (self.precio_venta - self.precio_costo) * self.inventario_real
        except:
            return 0

    # ── Semaforización ────────────────────────────────────────────
    def get_stock_status(self):
        if self.inventario_real <= 0:
            return {'color': '#714B23', 'label': 'QUIEBRE'}
        pct = (self.inventario_real / 10) * 100
        if pct <= 25:  return {'color': '#ff4d4d', 'label': 'CRÍTICO'}
        if pct <= 60:  return {'color': '#ffc107', 'label': 'REVISAR'}
        if pct <= 100: return {'color': '#71c016', 'label': 'ÓPTIMO'}
        return {'color': '#4B49AC', 'label': 'SOBRESTOCK'}

    def get_rentabilidad_status(self):
        m = float(self.margen_valor or 0)
        if m < 0.00: return {'color': '#212121', 'simbolo': '⚫', 'texto': 'PÉRDIDA'}
        if m < 0.10: return {'color': '#E53935', 'simbolo': '🔴', 'texto': 'SOBREVIVENCIA'}
        if m < 0.18: return {'color': '#F9A825', 'simbolo': '🟡', 'texto': 'NEUTRO'}
        if m < 0.26: return {'color': '#43A047', 'simbolo': '🟢', 'texto': 'SALUDABLE'}
        if m < 0.36: return {'color': '#FB8C00', 'simbolo': '🔥', 'texto': 'ÓPTIMO'}
        return {'color': '#6A1B9A', 'simbolo': '🟣', 'texto': 'ILLIDARI'}

    def __str__(self):
        estado_tag = ' ❄️' if self.estado == 'criocongelado' else ''
        return f"{self.sku} — {self.producto}{estado_tag}"


# =================================================================
# I.B VARIANTES VTS (TABLA HIJA DE AUDITORÍA)
# =================================================================
class VarianteVTS(models.Model):

    ESTADO_CHOICES = [
        ('activo',        'Activo'),
        ('criocongelado', 'Criocongelado'),
        ('descontinuado', 'Descontinuado'),
    ]

    producto = models.ForeignKey(
        AuditoriaVTS,
        on_delete=models.CASCADE,
        related_name='variantes'
    )
    sku_variante    = models.CharField(max_length=60, primary_key=True)
    nombre_variante = models.CharField(max_length=100, verbose_name="Variante/Color/Fragancia")
    imagen          = models.ImageField(upload_to='productos/variantes/', blank=True, null=True)
    estado          = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo', verbose_name="Estado")

    # --- Inventario por variante ---
    stock_sistema   = models.IntegerField(default=0)
    inventario_real = models.IntegerField(default=0)

    # --- Financiero por variante ---
    precio_costo   = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    precio_venta   = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    documento_tipo = models.CharField(
        max_length=20,
        choices=[('BOLETA', 'Boleta'), ('FACTURA', 'Factura')],
        default='BOLETA'
    )

    class Meta:
        verbose_name        = "Variante VTS"
        verbose_name_plural = "Variantes VTS"
        ordering            = ['producto', 'nombre_variante']

    def __str__(self):
        estado_tag = ' ❄️' if self.estado == 'criocongelado' else ''
        return f"{self.producto.sku} | {self.nombre_variante}{estado_tag}"

    def clean(self):
        if self.inventario_real < 0:
            raise ValidationError({'inventario_real': 'El stock no puede ser negativo.'})
        if self.precio_costo < 0 or self.precio_venta < 0:
            raise ValidationError('Los montos financieros deben ser positivos.')

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.imagen and hasattr(self.imagen, 'file'):
            img = Image.open(self.imagen)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((800, 800), Image.LANCZOS)
            buffer = BytesIO()
            img.save(buffer, format="WEBP", quality=80)
            buffer.seek(0)
            nombre_base  = os.path.basename(os.path.splitext(self.imagen.name)[0])
            nuevo_nombre = nombre_base + ".webp"
            self.imagen.save(nuevo_nombre, ContentFile(buffer.read()), save=False)
        super().save(*args, **kwargs)

    # ── KPIs ──────────────────────────────────────────────────────
    @property
    def margen_valor(self):
        try:
            from .vts_config import get_config
            cfg    = get_config()
            factor = sum(v for k, v in cfg.items() if k.endswith('_pct'))
            costo_real = float(self.precio_costo) * (1 + factor)
            venta      = float(self.precio_venta)
            if venta <= 0:
                return 0
            return (venta - costo_real) / venta
        except:
            return 0

    def get_stock_status(self):
        if self.inventario_real <= 0:
            return {'color': '#714B23', 'label': 'QUIEBRE'}
        pct = (self.inventario_real / 10) * 100
        if pct <= 25:  return {'color': '#ff4d4d', 'label': 'CRÍTICO'}
        if pct <= 60:  return {'color': '#ffc107', 'label': 'REVISAR'}
        if pct <= 100: return {'color': '#71c016', 'label': 'ÓPTIMO'}
        return {'color': '#4B49AC', 'label': 'SOBRESTOCK'}

    def get_rentabilidad_status(self):
        m = float(self.margen_valor or 0)
        if m < 0.05: return {'color': '#212121', 'simbolo': '⚫', 'texto': 'PÉRDIDA'}
        if m < 0.14: return {'color': '#ff4d4d', 'simbolo': '🔴', 'texto': 'SOBREVIVENCIA'}
        if m < 0.22: return {'color': '#ffc107', 'simbolo': '🟡', 'texto': 'NEUTRO'}
        if m < 0.28: return {'color': '#71c016', 'simbolo': '🟢', 'texto': 'SALUDABLE'}
        return {'color': '#38004F', 'simbolo': '🟣', 'texto': 'ILLIDARI'}


# =================================================================
# I.C HISTORIAL DE STOCK
# =================================================================
class HistorialStock(models.Model):
    """Registro de cambios manuales en el stock para auditoría"""
    sku            = models.CharField(max_length=50)
    producto       = models.CharField(max_length=200)
    stock_anterior = models.IntegerField()
    stock_nuevo    = models.IntegerField()
    fecha_ajuste   = models.DateTimeField(auto_now_add=True)
    usuario        = models.CharField(max_length=100, default="Admin_VTS")

    class Meta:
        ordering = ['-fecha_ajuste']

    def __str__(self):
        return f"{self.fecha_ajuste.strftime('%d/%m %H:%M')} | {self.sku} | {self.stock_anterior}→{self.stock_nuevo}"