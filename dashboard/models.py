from django.db import models

class AuditoriaVTS(models.Model):
    # Identificadores
    sku = models.CharField(max_length=50)
    producto = models.CharField(max_length=200)
    seccion = models.CharField(max_length=100)
    
    # Valores numéricos (Dinero y Unidades)
    stock_sistema = models.IntegerField()
    inventario_real = models.IntegerField()
    precio_costo = models.DecimalField(max_digits=12, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Tipo de documento
    documento_tipo = models.CharField(max_length=20, choices=[('BOLETA', 'Boleta'), ('FACTURA', 'Factura')])
    
    # Metadatos automáticos
    fecha_auditoria = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Auditoría VTS"
        verbose_name_plural = "Auditorías VTS"
        ordering = ['-fecha_auditoria'] # Las más recientes primero

    def __str__(self):
        return f"{self.sku} - {self.producto}"

# Create your models here.
