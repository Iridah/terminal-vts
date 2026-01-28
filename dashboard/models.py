# dashboard/models.py
import os
from django.db import models
from django.core.exceptions import ValidationError  
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import uuid
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# =================================================================
# I. CLASE MAESTRA: AUDITORÍA VTS (EL CORAZÓN)
# =================================================================
class AuditoriaVTS(models.Model):
    # --- Campos de Identificación ---
    sku = models.CharField(max_length=50, primary_key=True)
    codigo_barras = models.CharField(max_length=100, blank=True, null=True, verbose_name="Código de Barras")
    producto = models.CharField(max_length=200)
    seccion = models.CharField(max_length=100)
    variante = models.CharField(max_length=50, blank=True, null=True, verbose_name="Variante/Color")
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True, verbose_name="Foto del Producto")
    
    # --- Campos de Inventario ---
    stock_sistema = models.IntegerField(default=0)
    inventario_real = models.IntegerField(default=0)
    aporte_hogar_total = models.IntegerField(default=0)
    
    # --- Campos Financieros ---
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    documento_tipo = models.CharField(max_length=20, choices=[('BOLETA', 'Boleta'), ('FACTURA', 'Factura')], default='BOLETA')
    fecha_auditoria = models.DateTimeField(auto_now_add=True)

    # --- CONFIGURACIÓN META ---
    class Meta:
        verbose_name = "Auditoría VTS"
        verbose_name_plural = "Auditorías VTS"
        ordering = ['seccion', 'producto'] # Calcetines ordenados por sección al consultar

    # --- 1. MÉTODOS DE INTEGRIDAD (VALIDACIÓN Y GUARDADO) ---
    def clean(self):
        """Asegura que no entren datos imposibles a Mardum"""
        if self.inventario_real < 0:
            raise ValidationError({'inventario_real': 'El stock no puede ser negativo.'})
        if self.precio_costo < 0 or self.precio_venta < 0:
            raise ValidationError('Los montos financieros deben ser positivos.')

    def save(self, *args, **kwargs):
        # Validación forzada
        self.full_clean()
        
        # Procesamiento de Imagen: Conversión a WebP para optimizar carga
        if self.imagen and hasattr(self.imagen, 'file'):
            img = Image.open(self.imagen)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img.thumbnail((800, 800), Image.LANCZOS)
            buffer = BytesIO()
            img.save(buffer, format="WEBP", quality=80)
            buffer.seek(0)
            nuevo_nombre = os.path.splitext(self.imagen.name)[0] + ".webp"
            self.imagen.save(nuevo_nombre, ContentFile(buffer.read()), save=False)

        super().save(*args, **kwargs)

    # --- 2. MÉTODOS DE LÓGICA FINANCIERA (KPIs) ---
    @property
    def margen_valor(self):
        """Calcula el margen de utilidad neta aproximado (Neta vs Costo)"""
        try:
            v_neta = float(self.precio_venta) / 1.19
            if v_neta > 0:
                return (v_neta - float(self.precio_costo)) / v_neta
            return 0
        except: return 0

    def get_potencial_ganancia(self):
        """Utilidad bruta total del stock actual"""
        try:
            return (self.precio_venta - self.precio_costo) * self.inventario_real
        except: return 0

    # --- 3. MÉTODOS DE VISUALIZACIÓN (Semaforización) ---
    def get_stock_status(self):
        """Retorna color y etiqueta según el 'termómetro' de stock"""
        if self.inventario_real <= 0:
            return {'color': '#714B23', 'label': 'QUIEBRE'}
        pct = (self.inventario_real / 10) * 100
        if pct <= 25: return {'color': '#ff4d4d', 'label': 'CRÍTICO'}
        if pct <= 60: return {'color': '#ffc107', 'label': 'REVISAR'}
        if pct <= 100: return {'color': '#71c016', 'label': 'ÓPTIMO'}
        return {'color': '#4B49AC', 'label': 'SOBRESTOCK'}

    def get_rentabilidad_status(self):
        """Clasificación de salud financiera del producto"""
        m = float(getattr(self, 'margen_db', self.margen_valor) or 0)
        if m < 0.05: return {'color': '#714B23', 'simbolo': '🟤', 'texto': 'PÉRDIDA'}
        if m < 0.14: return {'color': '#ff4d4d', 'simbolo': '🔴', 'texto': 'SOBREVIVENCIA'}
        if m < 0.22: return {'color': '#ffc107', 'simbolo': '🟡', 'texto': 'NEUTRO'}
        if m < 0.28: return {'color': '#71c016', 'simbolo': '🟢', 'texto': 'SALUDABLE'}
        return {'color': '#38004F', 'simbolo': '🟣', 'texto': 'ILLIDARI'}

# =================================================================
# II. CLASES DE REGISTRO (HISTORIAL Y LOGS)
# =================================================================

class HistorialStock(models.Model):
    """Registro de cambios manuales en el stock para auditoría"""
    sku = models.CharField(max_length=50)
    producto = models.CharField(max_length=200)
    stock_anterior = models.IntegerField()
    stock_nuevo = models.IntegerField()
    fecha_ajuste = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=100, default="Admin_VTS")

class LogRetirosDeducibles(models.Model):
    """Específico para Aporte Hogar, impacta directamente en el padre"""
    sku = models.ForeignKey(AuditoriaVTS, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=100, default="Aporte Hogar")

    def save(self, *args, **kwargs):
        if not self.pk: # Solo al crear, descontamos
            self.sku.inventario_real -= self.cantidad
            self.sku.aporte_hogar_total += self.cantidad
            self.sku.save() 
        super().save(*args, **kwargs)

class RegistroLogs(models.Model):
    """Logs generales del sistema (La Triada y movimientos automáticos)"""
    # Identificadores básicos
    sku = models.CharField(max_length=50)
    producto = models.CharField(max_length=255)

    # La Trinidad: VENTA, MERMA, INGRESO, APORTE
    cantidad = models.IntegerField()
    tipo_accion = models.CharField(max_length=20) # 'VENTA', 'INGRESO', 'MERMA'
    
    # Auditoría de Seguridad (Fase V)
    fecha_exacta = models.DateTimeField(auto_now_add=True)
    operador = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    # Campo extra para el "Alt-Tab" (Notificaciones)
    notificado = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha_exacta']

    def __str__(self):
        # Cambiar self.fecha por self.fecha_exacta
        return f"{self.fecha_exacta.strftime('%d/%m %H:%M')} | {self.tipo_accion} | {self.sku}"
    
# =================================================================
# III. SEGURIDAD ADICIONAL
# =================================================================
class PerfilVTS(models.Model):
    ROLES_CHOICES = [
        ('Boss', 'Señor de la Legión'),
        ('Jefe-Local', 'Cazador'),
        ('Analista-Bodega', 'Forjador'),
        ('Analista-Personal', 'Sabana (Dikbig)'),
        ('Analista-IT', 'Escriba (Programación)'),
        ('Vendedor', 'Front-Desk'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES_CHOICES, default='Vendedor')
    sargerite_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    ultima_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Capacidades Elásticas
    puede_ver_fotos = models.BooleanField(default=False)
    puede_operar_stock = models.BooleanField(default=False)
    puede_ver_dikbig = models.BooleanField(default=False)
    puede_ejecutar_ventas = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Auto-asignación de poder por Rol
        mapping = {
            'Boss': (True, True, True, True),
            'Jefe-Local': (True, True, False, True),
            'Analista-Bodega': (True, True, False, False),
            'Analista-Personal': (False, False, True, False),
            'Analista-IT': (False, False, False, False),
            'Vendedor': (False, False, False, True),
        }
        p_fotos, p_stock, p_dikbig, p_ventas = mapping.get(self.rol, (False, False, False, True))
        self.puede_ver_fotos, self.puede_operar_stock = p_fotos, p_stock
        self.puede_ver_dikbig, self.puede_ejecutar_ventas = p_dikbig, p_ventas
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.rol}] {self.user.username}"

@receiver(post_save, sender=User)
def crear_perfil_automatico(sender, instance, created, **kwargs):
    if created:
        PerfilVTS.objects.create(user=instance)

class Colaborador(models.Model):
    """Tanque Dikbig: Gestión de Personal Cifrada"""
    rut = models.CharField(max_length=12, primary_key=True)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    nombres = models.CharField(max_length=200)
    cargo = models.CharField(max_length=100)
    
    # Datos Sensibles
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=2)
    afp = models.CharField(max_length=50)
    salud = models.CharField(max_length=50) 
    adicional_salud = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # --- CAMPOS RESCATADOS PARA LA IMPORTACIÓN ---
    direccion = models.CharField(max_length=255, blank=True, null=True)
    comuna = models.CharField(max_length=100, blank=True, null=True)
    correo_electronico = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    
    # Fechas de Contrato
    fecha_inicio = models.DateField()
    fecha_termino = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Colaborador"
        verbose_name_plural = "Personal (Dikbig)"

    def __str__(self):
        return f"{self.rut} - {self.apellido_paterno}, {self.nombres}"
    
# @login_required
# @sargerite_shield(permiso_requerido='puede_ver_dikbig')
def importar_personal(request):
    # Akama entra en acción solo si el escudo lo permite
    if request.method == 'POST':
        archivo = request.FILES.get('archivo_csv')
        res = AkamaStrategy.ejecucion_fila_a_fila(archivo)
        return render(request, 'dashboard/partials/resultado_carga.html', {'res': res})