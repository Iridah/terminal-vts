#dashboard/models.py
from django.db import models

class AuditoriaVTS(models.Model):
    # Identificadores
    sku = models.CharField(max_length=50)
    producto = models.CharField(max_length=200)
    seccion = models.CharField(max_length=100)
    
    # Valores numéricos (Dinero y Unidades)
    stock_sistema = models.IntegerField()
    inventario_real = models.IntegerField()
    precio_costo = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # Usaremos este
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Tipo de documento
    documento_tipo = models.CharField(max_length=20, choices=[('BOLETA', 'Boleta'), ('FACTURA', 'Factura')])
    
    # Metadatos automáticos
    fecha_auditoria = models.DateTimeField(auto_now_add=True)

    @property
    def margen_valor(self):
        """Calcula el porcentaje de margen neto"""
        if self.precio_venta and self.precio_venta > 0:
            return (self.precio_venta - self.precio_costo) / self.precio_venta
        return 0
        
    @property
    def margen_porcentaje_vista(self):
    #"""Devuelve el margen listo para el ancho del CSS"""
        val = self.margen_valor * 100
        if val > 100: return 100
        if val < 5: return 5 # Mínimo para que se vea un poco de color
        return val

    def get_illidari_status(self):
        """Retorna el color y la etiqueta basada en el margen"""
        m = self.margen_valor
        if m < 0.05: return {"color": "#8B4513", "label": "PÉRDIDA", "icon": "🟤"}
        if m < 0.14: return {"color": "#e74c3c", "label": "SOBREVIVENCIA", "icon": "🔴"}
        if m < 0.22: return {"color": "#f1c40f", "label": "NEUTRA", "icon": "🟡"}
        if m < 0.28: return {"color": "#27ae60", "label": "SALUDABLE", "icon": "🟢"}
        return {"color": "#9b59b6", "label": "ILLIDARI", "icon": "🟣"}

    # En tu clase AuditoriaVTS dentro de models.py
    def get_stock_status(self):
        """Calcula el termómetro de stock Skydash."""
        try:
            actual = float(self.inventario_real)
            sistema = float(self.stock_sistema) or 1.0
            pct = (actual / sistema) * 100
            
            if actual <= 0: 
                return {'color': '#714B23', 'texto': 'QUIEBRE'}
            if pct <= 25: 
                return {'color': '#F3797E', 'texto': 'CRÍTICO'}
            if pct <= 60: 
                return {'color': '#7978E9', 'texto': 'REVISAR'}
            return {'color': '#71c016', 'texto': 'ÓPTIMO'}
        except:
            return {'color': '#6C7383', 'texto': 'ERROR'}

    def get_rentabilidad_status(self):
        """Calcula el margen Illidari usando el precio_costo real."""
        try:
            m = float(self.margen_valor) # Usamos la property que ya calcula (Venta - Costo)/Venta
            if m < 0.05: return {'color': '#714B23', 'texto': 'PÉRDIDA', 'icon': 'fa-skull'}
            if m < 0.14: return {'color': '#F3797E', 'texto': 'SOBREVIVENCIA', 'icon': 'fa-triangle-exclamation'}
            if m < 0.22: return {'color': '#7978E9', 'texto': 'NEUTRA', 'icon': 'fa-minus'}
            if m < 0.28: return {'color': '#71c016', 'texto': 'SALUDABLE', 'icon': 'fa-check'}
            return {'color': '#A435F0', 'texto': 'ILLIDARI', 'icon': 'fa-bolt'}
        except:
            return {'color': '#6C7383', 'texto': 'SIN DATOS', 'icon': 'fa-question'}
        
    @property
    def margen_calculado(self):
        """Calcula el margen real para el termómetro."""
        if self.precio_venta > 0:
            return (self.precio_venta - self.costo_neto) / self.precio_venta
        return 0
    
    class Meta:
        verbose_name = "Auditoría VTS"
        verbose_name_plural = "Auditorías VTS"
        ordering = ['-fecha_auditoria'] # Las más recientes primero

class HistorialStock(models.Model):
    sku = models.CharField(max_length=50)
    producto = models.CharField(max_length=200)
    stock_anterior = models.IntegerField()
    stock_nuevo = models.IntegerField()
    fecha_ajuste = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=100, default="Admin_VTS") # Por ahora manual

    class Meta:
        ordering = ['-fecha_ajuste'] # Lo más reciente primero

    def __str__(self):
        return f"{self.sku} - {self.producto}"

# Create your models here.
