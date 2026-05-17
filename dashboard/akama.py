# Dashboard/akama.py
# Dashboard/akama.py
import csv
from datetime import datetime
from decimal import Decimal
from .models import Colaborador


class AkamaStrategy:
    """
    Estratega para la gestión masiva de personal (Tanque Dikbig).
    Encargado de parsing, normalización de RUT y validación de integridad.
    """

    @staticmethod
    def normalizar_rut(rut_valor):
        if not rut_valor:
            return ""
        limpio = str(rut_valor).replace('.', '').replace('-', '').strip().upper()
        return limpio

    @staticmethod
    def limpiar_monto(monto_raw):
        """Limpia todo y devuelve un entero puro para evitar inflación"""
        if not monto_raw:
            return 0
        solo_numeros = str(monto_raw).split(',')[0]
        solo_numeros = ''.join(filter(str.isdigit, solo_numeros))
        try:
            return int(solo_numeros) if solo_numeros else 0
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def parsear_fecha(fecha_raw):
        """Intenta convertir strings en objetos date de Python"""
        if not fecha_raw or str(fecha_raw).lower() in ['null', 'none', '']:
            return None
        f_str = str(fecha_raw).strip().replace(".0", "")
        if f_str.isdigit():
            f_str = f_str.zfill(8)
        formats = ['%d%m%Y', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
        for fmt in formats:
            try:
                return datetime.strptime(f_str, fmt).date()
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
                # LIMPIEZA ATÓMICA: llaves limpias sin paréntesis ni espacios
                row_clean = {k.split('(')[0].strip(): v for k, v in row.items()}

                rut_clean = cls.normalizar_rut(row_clean.get('rut'))
                if not rut_clean:
                    raise ValueError(f"Fila {fila}: RUT ausente")

                colaborador, created = Colaborador.objects.update_or_create(
                    rut=rut_clean,
                    defaults={
                        'apellido_paterno':       row_clean.get('ap_p', '').strip(),
                        'apellido_materno':       row_clean.get('ap_m', '').strip(),
                        'nombres':                row_clean.get('nombres', '').strip(),
                        'cargo':                  row_clean.get('cargo', '').strip(),
                        'sueldo_base':            cls.limpiar_monto(row_clean.get('sueldo')),
                        'afp':                    row_clean.get('afp', 'MODELO').strip().upper(),
                        'sistema_salud':          row_clean.get('sistema_salud', 'FONASA').strip().upper(),
                        'plan_isapre_uf':         Decimal(str(row_clean.get('plan_uf', 0)).replace(',', '.')),
                        'tipo_contrato':          row_clean.get('tipo_contrato', 'INDEFINIDO').strip().upper(),
                        'asignacion_movilizacion': cls.limpiar_monto(row_clean.get('movilizacion', 0)),
                        'asignacion_colacion':    cls.limpiar_monto(row_clean.get('colacion', 0)),
                        'fecha_inicio':           cls.parsear_fecha(row_clean.get('inicio')),
                        'fecha_termino':          cls.parsear_fecha(row_clean.get('termino')),
                        'direccion':              row_clean.get('direccion', '').strip(),
                        'comuna':                 row_clean.get('comuna', '').strip(),
                        'correo_electronico':     row_clean.get('correo', '').strip(),
                        'telefono':               row_clean.get('telefono', '').strip(),
                    }
                )

                if created:
                    reporte['creados'] += 1
                else:
                    reporte['actualizados'] += 1

            except Exception as e:
                reporte['errores'].append(
                    f"Error en fila {fila} (RUT: {row.get('rut', 'desconocido')}): {str(e)}"
                )

        return reporte