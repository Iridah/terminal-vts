# dashboard/engine.py
import pandas as pd
import numpy as np
from .models import AuditoriaVTS

class FelEngine:
    @staticmethod
    def generar_reporte_general():
        
        # 0.- Candado (si no tiene seccion, no entra)
        qs = AuditoriaVTS.objects.exclude(seccion__isnull=True).exclude(seccion="").values(
            'seccion', 'producto', 'precio_costo', 'precio_venta', 'inventario_real'
        )
        
        if not qs.exists():
            return {'estado': 'vacio'}

        # 1. EXTRACCIÓN (Uso de select_related si hubiera, pero aquí values es eficiente)
        df = pd.DataFrame(list(qs))

        # 2. LIMPIEZA (Aseguramos floats para evitar errores de Decimal vs Float en cálculos)
        for col in ['precio_costo', 'precio_venta']:
            df[col] = df[col].apply(float)
        df['inventario_real'] = df['inventario_real'].astype(int)

        # 3. CÁLCULOS BASE (Cimientos financieros)
        df['inversion_total'] = df['precio_costo'] * df['inventario_real']
        df['venta_total'] = df['precio_venta'] * df['inventario_real']
        df['ganancia_potencial'] = df['venta_total'] - df['inversion_total']

        # 4. LÓGICA PRO (Factor de Velocidad y Salud)
        # Identificamos quiebres para castigar o premiar la sección
        secciones_con_quiebre = df[df['inventario_real'] == 0]['seccion'].unique()

        resumen = df.groupby('seccion').agg({
            'inversion_total': 'sum',
            'ganancia_potencial': 'sum',
            'inventario_real': 'sum',
            'producto': 'count' # Cantidad de SKUs por sección
        }).rename(columns={'producto': 'total_skus'}).reset_index()

        # ROI Nominal: Lo que ganarás si vendes todo hoy
        resumen['roi_nominal'] = np.where(
            resumen['inversion_total'] > 0, 
            (resumen['ganancia_potencial'] / resumen['inversion_total']) * 100, 
            0
        )

        # ROI Pro: Factor de velocidad 1.2 si hay quiebres (alta rotación implícita)
        resumen['roi_pro'] = resumen.apply(
            lambda x: round(x['roi_nominal'] * 1.2, 1) if x['seccion'] in secciones_con_quiebre else round(x['roi_nominal'], 1),
            axis=1
        )

        # 5. RESPUESTA UNIFICADA (Formateada para el Dashboard)
        return {
            'total_inversion': round(float(df['inversion_total'].sum()), 2),
            'total_ganancia': round(float(df['ganancia_potencial'].sum()), 2),
            'venta_total_esperada': round(float(df['venta_total'].sum()), 2),
            'secciones': resumen.to_dict('records'), # Esta es la variable real
            'top_illidari': df.nlargest(5, 'ganancia_potencial').to_dict('records'),
            'promedio_roi': round(resumen['roi_pro'].mean(), 1) if not resumen.empty else 0,
            'estado': 'ok'
        }