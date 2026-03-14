# ================================================================
# ARCHIVO 3: dashboard/models/personal.py
# ================================================================
 
# dashboard/models/personal.py
from django.db import models
 
 
class Colaborador(models.Model):
    rut               = models.CharField(max_length=12, primary_key=True)
    apellido_paterno  = models.CharField(max_length=100)
    apellido_materno  = models.CharField(max_length=100)
    nombres           = models.CharField(max_length=200)
    cargo             = models.CharField(max_length=100)
    correo_electronico = models.EmailField(blank=True, null=True)
 
    TIPO_CONTRATO_CHOICES = [
        ('INDEFINIDO', 'Indefinido'),
        ('PLAZO_FIJO', 'Plazo Fijo'),
    ]
    tipo_contrato = models.CharField(max_length=20, choices=TIPO_CONTRATO_CHOICES, default='INDEFINIDO')
    fecha_inicio  = models.DateField()
    fecha_termino = models.DateField(null=True, blank=True)
 
    sueldo_base            = models.DecimalField(max_digits=12, decimal_places=2)
    asignacion_movilizacion = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    asignacion_colacion    = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
 
    AFP_CHOICES = [
        ('CAPITAL','Capital'),('CUPRUM','Cuprum'),('HABITAT','Habitat'),
        ('PLANVITAL','PlanVital'),('PROVIDA','ProVida'),('MODELO','Modelo'),('UNO','Uno')
    ]
    afp = models.CharField(max_length=20, choices=AFP_CHOICES, default='MODELO')
 
    SISTEMA_SALUD_CHOICES = [('FONASA','Fonasa 7%'),('ISAPRE','Isapre (Plan UF)')]
    sistema_salud  = models.CharField(max_length=10, choices=SISTEMA_SALUD_CHOICES, default='FONASA')
    plan_isapre_uf = models.DecimalField(max_digits=6, decimal_places=4, default=0.0000)
 
    direccion = models.CharField(max_length=255, blank=True, null=True)
    comuna    = models.CharField(max_length=100, blank=True, null=True)
    telefono  = models.CharField(max_length=20,  blank=True, null=True)
 
    class Meta:
        verbose_name        = "Colaborador"
        verbose_name_plural = "Personal (Dikbig)"
 
    def __str__(self):
        return f"{self.rut} - {self.apellido_paterno}, {self.nombres}"
 
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}"
 
 
# ================================================================
# ARCHIVO 4: dashboard/models/__init__.py
# ================================================================
 
# dashboard/models/__init__.py
# Reexporta todo para mantener compatibilidad con imports existentes
# Cualquier `from .models import X` o `from dashboard.models import X` sigue funcionando
 
from .inventario import AuditoriaVTS, VarianteVTS, HistorialStock
from .logs       import RegistroLogs, LogRetirosDeducibles
from .config     import ConfigVTS, PerfilVTS
from .personal   import Colaborador
 
__all__ = [
    'AuditoriaVTS', 'VarianteVTS', 'HistorialStock',
    'RegistroLogs', 'LogRetirosDeducibles',
    'ConfigVTS', 'PerfilVTS',
    'Colaborador',
]