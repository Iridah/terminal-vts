#dashboard/models.py
import os
from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

class AuditoriaVTS(models.Model):
    sku = models.CharField(max_length=50, primary_key=True)
    codigo_barras = models.CharField(max_length=100, blank=True, null=True, verbose_name="Código de Barras")
    producto = models.CharField(max_length=200)
    seccion = models.CharField(max_length=100)
    variante = models.CharField(max_length=50, blank=True, null=True, verbose_name="Variante/Color")
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True, verbose_name="Foto del Producto")

    stock_sistema = models.IntegerField(default=0)
    inventario_real = models.IntegerField(default=0)
    aporte_hogar_total = models.IntegerField(default=0)

    precio_costo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    documento_tipo = models.CharField(max_length=20, choices=[('BOLETA', 'Boleta'), ('FACTURA', 'Factura')], default='BOLETA')
    fecha_auditoria = models.DateTimeField(auto_now_add=True)

    @property
    def margen_valor(self):
        try:
            v_bruta = float(self.precio_venta)
            costo_neto = float(self.precio_costo)
            v_neta = v_bruta / 1.19
            if v_neta > 0:
                return (v_neta - costo_neto) / v_neta
            return 0
        except (ValueError, TypeError, ZeroDivisionError):
            return 0

    def get_stock_status(self):
        try:
            actual = int(self.inventario_real)
            if actual <= 0: return {'color': '#714B23', 'texto': 'QUIEBRE'}
            if actual == 1: return {'color': '#F3797E', 'texto': 'ÚLTIMA UNIDAD'}
            if actual <= 3: return {'color': '#FF9900', 'texto': 'STOCK BAJO'}
            if actual < 5: return {'color': '#7978E9', 'texto': 'REVISAR'}
            return {'color': '#71c016', 'texto': 'ÓPTIMO'}
        except:
            return {'color': '#6C7383', 'texto': 'ERROR'}
        
    def get_rentabilidad_status(self):
        try:
            m = self.margen_valor
            if m < 0.05: return {'color': '#714B23', 'texto': 'PÉRDIDA', 'icon': 'fa-skull'}
            if m < 0.15: return {'color': '#F3797E', 'texto': 'SOBREVIVENCIA', 'icon': 'fa-triangle-exclamation'}
            if m < 0.22: return {'color': '#7978E9', 'texto': 'NEUTRA', 'icon': 'fa-minus'}
            if m < 0.28: return {'color': '#71c016', 'texto': 'SALUDABLE', 'icon': 'fa-check'}
            return {'color': '#A435F0', 'texto': 'ILLIDARI', 'icon': 'fa-bolt'}
        except:
            return {'color': '#6C7383', 'texto': 'SIN DATOS', 'icon': 'fa-question'}

    def save(self, *args, **kwargs):
        if self.imagen and hasattr(self.imagen, 'file'):
            img = Image.open(self.imagen)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            img.thumbnail((800, 800), Image.LANCZOS)
            
            buffer = BytesIO()
            img.save(buffer, format="WEBP", quality=80)
            buffer.seek(0)
            
            nuevo_nombre = os.path.splitext(self.imagen.name)[0] + ".webp"
            self.imagen.save(nuevo_nombre, ContentFile(buffer.read()), save=False)

        super().save(*args, **kwargs)

    def get_full_sku(self):
        return f"{self.sku}-{self.variante}" if self.variante else self.sku

    class Meta:
        verbose_name = "Auditoría VTS"
        verbose_name_plural = "Auditorías VTS"
        ordering = ['-fecha_auditoria']

class HistorialStock(models.Model):
    sku = models.CharField(max_length=50)
    producto = models.CharField(max_length=200)
    stock_anterior = models.IntegerField()
    stock_nuevo = models.IntegerField()
    fecha_ajuste = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=100, default="Admin_VTS")

class LogRetirosDeducibles(models.Model):
    sku = models.ForeignKey(AuditoriaVTS, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=100, default="Aporte Hogar")

    def save(self, *args, **kwargs):
        if not self.pk:  # Solo descontar si es un registro nuevo
            self.sku.inventario_real -= self.cantidad
            self.sku.aporte_hogar_total += self.cantidad
            self.sku.save()
        super().save(*args, **kwargs)