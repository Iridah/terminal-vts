#dashboard/models.py
from django.db import models

class AuditoriaVTS(models.Model):
    sku = models.CharField(max_length=40, primary_key=True)
    codigo_barras = models.CharField(max_length=100, blank=True, null=True, verbose_name="Código de Barras")
    producto = models.CharField(max_length=200)
    seccion = models.CharField(max_length=100)
    variante = models.CharField(max_length=10, blank=True, null=True)
    
    stock_sistema = models.IntegerField(default=0)
    # ELIMINADA LA DUPLICACIÓN: Dejamos solo uno con default
    inventario_real = models.IntegerField(default=0)
    
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    documento_tipo = models.CharField(max_length=20, choices=[('BOLETA', 'Boleta'), ('FACTURA', 'Factura')], default='BOLETA')
    fecha_auditoria = models.DateTimeField(auto_now_add=True)

    @property
    def margen_valor(self):
        """Calcula margen: (Venta Neta - Costo Neto) / Venta Neta"""
        try:
            # 1. Traemos los valores de la base de datos
            v_bruta = float(self.precio_venta)
            costo_neto = float(self.precio_costo)
            
            # 2. El tercer operador: Convertimos venta bruta a neta
            v_neta = v_bruta / 1.19
            
            # 3. Cálculo final protegido contra división por cero
            if v_neta > 0:
                return (v_neta - costo_neto) / v_neta
            return 0
        except (ValueError, TypeError, ZeroDivisionError):
            # Si algo falla (valores nulos o letras), devolvemos 0 para no romper la web
            return 0

    def get_stock_status(self):
        try:
            actual = float(self.inventario_real)
            sistema = float(self.stock_sistema) or 1.0
            pct = (actual / sistema) * 100
            if actual <= 0: return {'color': '#714B23', 'texto': 'QUIEBRE'}
            if pct <= 25: return {'color': '#F3797E', 'texto': 'CRÍTICO'}
            if pct <= 60: return {'color': '#7978E9', 'texto': 'REVISAR'}
            return {'color': '#71c016', 'texto': 'ÓPTIMO'}
        except:
            return {'color': '#6C7383', 'texto': 'ERROR'}
        
    def get_rentabilidad_status(self):
        try:
            m = self.margen_valor  # Este ya descuenta el IVA (Venta / 1.19)
            
            # PÉRDIDA: Menos del 5%
            if m < 0.05: return {'color': '#714B23', 'texto': 'PÉRDIDA', 'icon': 'fa-skull'}
            
            # SOBREVIVENCIA: Entre 5% y 14.9%
            if m < 0.15: return {'color': '#F3797E', 'texto': 'SOBREVIVENCIA', 'icon': 'fa-triangle-exclamation'}
            
            # NEUTRA / ESTÁNDAR: Entre 15% y 21.9%
            if m < 0.22: return {'color': '#7978E9', 'texto': 'NEUTRA', 'icon': 'fa-minus'}
                
            # SALUDABLE: Entre 22% y 27.9%
            if m < 0.28: return {'color': '#71c016', 'texto': 'SALUDABLE', 'icon': 'fa-check'}
                
            # ILLIDARI: 28% o más
            return {'color': '#A435F0', 'texto': 'ILLIDARI', 'icon': 'fa-bolt'}
        except:
            return {'color': '#6C7383', 'texto': 'SIN DATOS', 'icon': 'fa-question'}





        
    def get_full_sku(self):
        """Devuelve el SKU completo: V-BEB-001-G"""
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