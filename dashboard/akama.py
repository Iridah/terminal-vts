# Dashboard/akama.py
import csv
import io
from datetime import datetime
from decimal import Decimal
from django.db import transaction
from .models import Colaborador

class AkamaStrategy:
    """
    Estratega para la gestión masiva de personal (Tanque Dikbig).
    Encargado de parsing, normalización de RUT y validación de integridad.
    """

    @staticmethod
    def normalizar_rut(rut_raw):
        """Limpia RUTs: '12.345.678-k' -> '12345678K'"""
        if not rut_raw: return None
        return str(rut_raw).upper().replace(".", "").replace("-", "").strip()

    @staticmethod
    def limpiar_monto(monto_raw):
        """Limpia signos de peso y puntos de miles: '$1.200.000' -> 1200000.00"""
        if not monto_raw: return Decimal("0.00")
        clean = str(monto_raw).replace("$", "").replace(".", "").replace(",", ".").strip()
        try:
            return Decimal(clean)
        except:
            return Decimal("0.00")

    @staticmethod
    def parsear_fecha(fecha_raw):
        """Intenta convertir strings en objetos date de Python"""
        if not fecha_raw or str(fecha_raw).lower() in ['null', 'none', '']:
            return None
                # Convertimos a string y aseguramos 8 dígitos (ej: 1012025 -> 01012025)
        f_str = str(fecha_raw).strip().replace(".0", "") # Limpieza por si viene de float de Excel
        if f_str.isdigit():
            f_str = f_str.zfill(8)
        # Añadimos %d%m%Y al principio de la lista de intentos
        formats = ['%d%m%Y', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
        for fmt in formats:
            try:
                return datetime.strptime(str(fecha_raw).strip(), fmt).date()
            except ValueError:
                continue
        return None

    @classmethod
    def ejecucion_fila_a_fila(cls, file_obj):
        """
        Procesa el manifiesto CSV. Si una fila falla, se registra el error
        pero el proceso continúa con la siguiente.
        """
        decoded_file = file_obj.read().decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded_file)
        
        reporte = {'creados': 0, 'actualizados': 0, 'errores': []}

        for fila, row in enumerate(reader, start=1):
            try:
                rut_clean = cls.normalizar_rut(row.get('rut'))
                if not rut_clean:
                    raise ValueError(f"Fila {fila}: RUT ausente")

                # Actualizar o Crear (Upsert)
                colaborador, created = Colaborador.objects.update_or_create(
                    rut=rut_clean,
                    defaults={
                        'apellido_paterno': row.get('ap_p', '').strip(),
                        'apellido_materno': row.get('ap_m', '').strip(),
                        'nombres': row.get('nombres', '').strip(),
                        'cargo': row.get('cargo', '').strip(),
                        'sueldo_base': cls.limpiar_monto(row.get('sueldo')),
                        'afp': row.get('afp', '').strip(),
                        'salud': row.get('salud', '').strip(),
                        'adicional_salud': cls.limpiar_monto(row.get('adicional', 0)),
                        'fecha_inicio': cls.parsear_fecha(row.get('inicio')),
                        'fecha_termino': cls.parsear_fecha(row.get('termino')),
                        'direccion': row.get('direccion', '').strip(),
                        'comuna': row.get('comuna', '').strip(),
                        'correo_electronico': row.get('correo', '').strip(),
                        'telefono': row.get('telefono', '').strip(),
                    }
                )
                
                if created: reporte['creados'] += 1
                else: reporte['actualizados'] += 1

            except Exception as e:
            # El error se guarda, pero Akama no se detiene
                reporte['errores'].append(f"Error en fila {fila} (RUT: {row.get('rut')}): {str(e)}")

        return reporte