# ================================================================
# ARCHIVO 2: dashboard/models/config.py
# ================================================================
 
# dashboard/models/config.py
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
 
 
class ConfigVTS(models.Model):
    clave       = models.CharField(max_length=50, unique=True, verbose_name="Parámetro")
    valor       = models.DecimalField(max_digits=5, decimal_places=4, verbose_name="Valor (decimal)")
    descripcion = models.CharField(max_length=200, blank=True, verbose_name="Descripción")
 
    class Meta:
        verbose_name        = "Configuración VTS"
        verbose_name_plural = "Configuraciones VTS"
        ordering            = ['clave']
 
    def __str__(self):
        return f"{self.clave} = {self.valor}"
 
 
class PerfilVTS(models.Model):
    ROLES_CHOICES = [
        ('Boss',             'Señor de la Legión'),
        ('Jefe-Local',       'Cazador'),
        ('Analista-Bodega',  'Forjador'),
        ('Analista-Personal','Sabana (Dikbig)'),
        ('Analista-IT',      'Escriba (Programación)'),
        ('Vendedor',         'Front-Desk'),
    ]
 
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol             = models.CharField(max_length=20, choices=ROLES_CHOICES, default='Vendedor')
    sargerite_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    ultima_ip       = models.GenericIPAddressField(null=True, blank=True)
 
    puede_ver_fotos      = models.BooleanField(default=False)
    puede_operar_stock   = models.BooleanField(default=False)
    puede_ver_dikbig     = models.BooleanField(default=False)
    puede_ejecutar_ventas = models.BooleanField(default=True)
 
    def save(self, *args, **kwargs):
        mapping = {
            'Boss':              (True,  True,  True,  True),
            'Jefe-Local':        (True,  True,  False, True),
            'Analista-Bodega':   (True,  True,  False, False),
            'Analista-Personal': (False, False, True,  False),
            'Analista-IT':       (False, False, False, False),
            'Vendedor':          (False, False, False, True),
        }
        p_fotos, p_stock, p_dikbig, p_ventas = mapping.get(self.rol, (False, False, False, True))
        self.puede_ver_fotos       = p_fotos
        self.puede_operar_stock    = p_stock
        self.puede_ver_dikbig      = p_dikbig
        self.puede_ejecutar_ventas = p_ventas
        super().save(*args, **kwargs)
 
    def __str__(self):
        return f"[{self.rol}] {self.user.username}"
 
 
@receiver(post_save, sender=User)
def manejar_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        rol_inicial = 'Boss' if instance.is_superuser else 'Vendedor'
        PerfilVTS.objects.create(user=instance, rol=rol_inicial)
    else:
        instance.perfil.save()
 
 
@receiver(user_logged_in)
def inyectar_sargerite_token(sender, request, user, **kwargs):
    if hasattr(user, 'perfil'):
        token_str = str(user.perfil.sargerite_token)
        request.session['sargerite_token'] = token_str
        print(f"🛡️ SARGERITE: Token inyectado para {user.username}")