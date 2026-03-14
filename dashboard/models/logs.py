# ================================================================
# ARCHIVO 1: dashboard/models/logs.py
# ================================================================
 
# dashboard/models/logs.py
from django.db import models
 
 
class LogRetirosDeducibles(models.Model):
    """Específico para Aporte Hogar — impacta directamente en el padre"""
    sku      = models.ForeignKey('dashboard.AuditoriaVTS', on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    fecha    = models.DateTimeField(auto_now_add=True)
    motivo   = models.CharField(max_length=100, default="Aporte Hogar")
 
    def save(self, *args, **kwargs):
        if not self.pk:
            self.sku.inventario_real     -= self.cantidad
            self.sku.aporte_hogar_total  += self.cantidad
            self.sku.save()
        super().save(*args, **kwargs)
 
    def __str__(self):
        return f"{self.fecha.strftime('%d/%m %H:%M')} | Aporte | {self.sku_id} | x{self.cantidad}"
 
 
class RegistroLogs(models.Model):
    """Logs generales del sistema (La Triada y movimientos automáticos)"""
    sku        = models.CharField(max_length=50)
    producto   = models.CharField(max_length=255)
    cantidad   = models.IntegerField()
    tipo_accion = models.CharField(max_length=20)  # VENTA, INGRESO, MERMA, VENTAS_IMPORTAR
    fecha_exacta = models.DateTimeField(auto_now_add=True)
    operador   = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    notificado = models.BooleanField(default=False)
 
    class Meta:
        ordering = ['-fecha_exacta']
 
    def __str__(self):
        return f"{self.fecha_exacta.strftime('%d/%m %H:%M')} | {self.tipo_accion} | {self.sku}"