#dashboard/models.py
import os
from django.db import models
from django.core.exceptions import ValidationError  
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

# --- CLASE 1: EL MAESTRO (AuditoriaVTS) ---
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

    # Lógica de Validación (La "Prueba" que citaste)
    def clean(self):
        """Verifica que los números sean naturales y lógicos"""
        if self.inventario_real < 0:
            raise ValidationError({'inventario_real': 'El stock no puede ser negativo.'})
        if self.precio_costo < 0 or self.precio_venta < 0:
            raise ValidationError('Los montos deben ser números positivos.')

    def save(self, *args, **kwargs):
        # 1. Forzamos la validación del clean()
        self.full_clean()
        
        # 2. Procesamiento de Imagen (WebP)
        if self.imagen and hasattr(self.imagen, 'file'):
            img = Image.open(self.imagen)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img.thumbnail((800, 800), Image.LANCZOS)
            buffer = BytesIO()
            img.save(buffer, format="WEBP", quality=80)
            buffer.seek(0)
            nuevo_nombre = os.path.splitext(self.imagen.name)[0] + ".webp"
            self.imagen.save(nuevo_nombre, ContentFile(buffer.read()), save=False)

        # 3. Guardado físico en DB
        super().save(*args, **kwargs)

    @property
    def margen_valor(self):
        try:
            v_neta = float(self.precio_venta) / 1.19
            if v_neta > 0:
                return (v_neta - float(self.precio_costo)) / v_neta
            return 0
        except: return 0

    def get_stock_status(self):
    # """Lógica de colores fiel al legado CLI"""
        try:
            # Asumimos máximo de 10 unidades para la visualización del termómetro
            pct = (self.inventario_real / 10) * 100
            if self.inventario_real <= 0:
                return {'color': '#714B23', 'label': 'QUIEBRE'} # 🟤
            if pct <= 25:
                return {'color': '#ff4d4d', 'label': 'CRÍTICO'} # 🔴
            if pct <= 60:
                return {'color': '#ffc107', 'label': 'REVISAR'} # 🟡
            if pct <= 100:
                return {'color': '#71c016', 'label': 'ÓPTIMO'}  # 🟢
            return {'color': '#4B49AC', 'label': 'SOBRESTOCK'}  # 🔵
        except:
            return {'color': '#e0e0e0', 'label': 'ERROR'}
    
    def get_stock_percentage(self):
        """Calcula el llenado del termómetro basado en un stock ideal de 10 unidades"""
        try:
            porcentaje = (self.inventario_real / 10) * 100
            return min(porcentaje, 100) # Máximo 100% para que la barra no se rompa
        except:
            return 0

    def get_rentabilidad_status(self):
        try:
            # Usamos getattr para buscar el alias 'margen_db' inyectado por la vista
            # Si no existe, usamos el campo real 'margen_valor' como respaldo
            m = getattr(self, 'margen_db', self.margen_valor)
            
            if m is None: m = 0
            m = float(m)
            
            # Ajuste de escala (si es 25.0 -> 0.25)
            if m > 1 or m < -1: 
                m = m / 100

            if m < 0.05: return {'color': '#714B23', 'simbolo': '🟤', 'texto': 'ZONA PÉRDIDA'}
            if m < 0.14: return {'color': '#ff4d4d', 'simbolo': '🔴', 'texto': 'SOBREVIVENCIA'}
            if m < 0.22: return {'color': '#ffc107', 'simbolo': '🟡', 'texto': 'ZONA NEUTRA'}
            if m < 0.28: return {'color': '#71c016', 'simbolo': '🟢', 'texto': 'SALUDABLE'}
            return {'color': '#38004F', 'simbolo': '🟣', 'texto': 'ILLIDARI'}
        except Exception:
            return {'color': '#6C7383', 'simbolo': '⚪', 'texto': 'SIN DATOS'}

    class Meta:
        verbose_name_plural = "Auditorías VTS"

# --- CLASE 2: EL TESTIGO (HistorialStock) ---
class HistorialStock(models.Model):
    sku = models.CharField(max_length=50)
    producto = models.CharField(max_length=200)
    stock_anterior = models.IntegerField()
    stock_nuevo = models.IntegerField()
    fecha_ajuste = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=100, default="Admin_VTS")

# --- CLASE 3: EL DEDUCIBLE (LogRetirosDeducibles) ---
class LogRetirosDeducibles(models.Model):
    sku = models.ForeignKey(AuditoriaVTS, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=100, default="Aporte Hogar")

    def save(self, *args, **kwargs):
        # Esta validación evita que descuente stock si solo editamos el motivo
        if not self.pk: 
            self.sku.inventario_real -= self.cantidad
            self.sku.aporte_hogar_total += self.cantidad
            # Guardamos el cambio en el padre
            self.sku.save() 
        super().save(*args, **kwargs)

# Sugerencia de estructura lógica para el Análisis
def get_potencial_ganancia(self):
    """Calcula la utilidad bruta total del stock actual"""
    try:
        margen_unitario = self.precio_venta - self.precio_costo
        return margen_unitario * self.inventario_real
    except:
        return 0
    
class RegistroLogs(models.Model):
    sku = models.CharField(max_length=50)
    producto = models.CharField(max_length=200)
    cantidad = models.IntegerField()
    tipo_accion = models.CharField(max_length=20) # 'ENTRADA' o 'SALIDA'
    fecha = models.DateTimeField(auto_now_add=True)
    operador = models.CharField(max_length=100, default='Sistema')

    def __str__(self):
        return f"{self.tipo_accion} - {self.sku} ({self.fecha})"