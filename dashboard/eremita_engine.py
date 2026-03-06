# /dashboard/eremita_engine.py
import pandas as pd
from decimal import Decimal
from datetime import date
from .oraculo import OraculoSargerite
from .models import Colaborador


class EremitaEngine:
    """L'Ermite: Moteur avec le verrou de sécurité du +10%"""

    TARIFA_RED_MAX = Decimal("870")

    @classmethod
    def procesar_sabana_completa(cls, colaboradores_queryset):
        ind = OraculoSargerite.obtener_indicadores()
        df = pd.DataFrame(list(colaboradores_queryset.values()))

        if df.empty:
            return df

        # 1. BLINDAJE SUELDO MÍNIMO
        df['sueldo_base'] = df['sueldo_base'].apply(
            lambda x: max(Decimal(str(x)), ind['sueldo_minimo'])
        )

        # 2. GRATIFICACIÓN LEGAL (Art. 47)
        tope_grat = (ind['sueldo_minimo'] * Decimal("4.75")) / Decimal("12")
        df['gratificacion'] = df['sueldo_base'].apply(
            lambda x: (x * Decimal("0.25")).quantize(Decimal("1"))
            if (x * Decimal("0.25")) < tope_grat
            else tope_grat.quantize(Decimal("1"))
        )

        # 3. MOVILIZACIÓN CON CANDADO PERSONAL (+10%)
        movilizacion_base = (Decimal("22") * Decimal("2") * cls.TARIFA_RED_MAX)
        df['movilizacion_minima'] = (movilizacion_base * Decimal("1.10")).quantize(Decimal("1"))

        return df

    @classmethod
    def calcular_antiguedad(cls, fecha_inicio):
        """Calcula años cumplidos a la fecha actual"""
        hoy = date.today()
        return hoy.year - fecha_inicio.year - (
            (hoy.month, hoy.day) < (fecha_inicio.month, fecha_inicio.day)
        )

    @classmethod
    def calcular_mortaja_provisoria(cls, colaborador):
        """Calcula la provisión de salida (Mes por año + Vacaciones)"""
        ind = OraculoSargerite.obtener_indicadores()

        años = cls.calcular_antiguedad(colaborador.fecha_inicio)
        indemnizacion_años = colaborador.sueldo_base * min(años, 11)

        # Vacaciones: 1.25 días por mes trabajado
        inicio = colaborador.fecha_inicio
        hoy = date.today()
        meses_totales = (hoy.year - inicio.year) * 12 + hoy.month - inicio.month

        dias_vacaciones = Decimal(str(meses_totales)) * Decimal("1.25")
        valor_dia = colaborador.sueldo_base / Decimal("30")
        monto_vacaciones = (dias_vacaciones * valor_dia).quantize(Decimal("1"))

        return {
            'reserva_total': indemnizacion_años + monto_vacaciones,
            'detalle': {
                'años_servicio': años,
                'vacaciones_proporcionales': monto_vacaciones
            }
        }

    @classmethod
    def reporte_mortaja_cli(cls, rut):
        """Genera un resumen atómico para la consola"""
        try:
            colaborador = Colaborador.objects.get(rut=rut)
            res = cls.calcular_mortaja_provisoria(colaborador)

            print(f"\n--- ⚰️ REPORTE DE MORTAJA: {colaborador.nombres} ---")
            print(f"📅 Antigüedad: {res['detalle']['años_servicio']} años")
            print(f"💰 Reserva Mes por Año: ${res['reserva_total'] - res['detalle']['vacaciones_proporcionales']:,}")
            print(f"🏖️ Reserva Vacaciones:  ${res['detalle']['vacaciones_proporcionales']:,}")
            print(f"🛡️ TOTAL BÓVEDA REQUERIDO: ${res['reserva_total']:,}")
            print("-------------------------------------------\n")
        except Colaborador.DoesNotExist:
            print(f"❌ El colaborador con RUT {rut} no existe.")

    @classmethod
    def calcular_liquidacion(cls, colaborador, valor_uf):
        """
        El cerebro del motor.
        Calcula la partida doble: Haberes vs Descuentos Legales.
        """
        ti = Decimal(str(colaborador.sueldo_base))

        # --- 1. CÁLCULO DE SALUD ---
        siete_legal = (ti * Decimal('0.07')).quantize(Decimal("1"))
        adicional_salud = Decimal('0.00')

        if str(colaborador.sistema_salud).upper() == 'ISAPRE':
            costo_plan_pesos = colaborador.plan_isapre_uf * Decimal(str(valor_uf))
            if costo_plan_pesos > siete_legal:
                adicional_salud = (costo_plan_pesos - siete_legal).quantize(Decimal("1"))

        total_salud = siete_legal + adicional_salud

        # --- 2. CÁLCULO DE AFP (Placeholder hasta el Sniffer) ---
        tasa_afp = Decimal('0.1145')
        total_afp = (ti * tasa_afp).quantize(Decimal("1"))

        # --- 3. CÁLCULO DE AFC ---
        total_afc = Decimal('0.00')
        if str(colaborador.tipo_contrato).upper() == 'INDEFINIDO':
            total_afc = (ti * Decimal('0.006')).quantize(Decimal("1"))

        # --- RESUMEN FINAL ---
        total_descuentos = total_salud + total_afp + total_afc
        haberes_no_imponibles = (
            Decimal(str(colaborador.asignacion_movilizacion)) +
            Decimal(str(colaborador.asignacion_colacion))
        )

        liquido = (ti + haberes_no_imponibles) - total_descuentos

        return {
            'ti':                ti,
            'siete_legal':       siete_legal,
            'adicional_salud':   adicional_salud,
            'total_salud':       total_salud,
            'total_afp':         total_afp,
            'total_afc':         total_afc,
            'total_descuentos':  total_descuentos,
            'liquido':           liquido,
        }



