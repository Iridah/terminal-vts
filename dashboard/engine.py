# dashboard/engine.py
# dashboard/engine.py
import pandas as pd
import numpy as np
from .models import AuditoriaVTS

class FelEngine:
    @staticmethod
    def generar_reporte_general():
        # 1. Extracción de datos
        data = AuditoriaVTS.objects.all().values(
            'seccion', 'producto', 'precio_costo', 'precio_venta', 'inventario_real'
        )
        
        if not data.exists():
            return {'estado': 'vacio'}

        df = pd.DataFrame(list(data))

        # 2. Limpieza y Normalización
        for col in ['precio_costo', 'precio_venta', 'inventario_real']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 3. Cálculos Base
        df['inversion_total'] = df['precio_costo'] * df['inventario_real']
        df['venta_total'] = df['precio_venta'] * df['inventario_real']
        df['ganancia_potencial'] = df['venta_total'] - df['inversion_total']

        # 4. Agrupación y Lógica Pro (Factor de Velocidad)
        # Identificamos secciones con productos en quiebre para el ROI Pro
        secciones_con_quiebre = df[df['inventario_real'] == 0]['seccion'].unique()

        resumen = df.groupby('seccion').agg({
            'inversion_total': 'sum',
            'ganancia_potencial': 'sum',
            'inventario_real': 'sum'
        }).reset_index()

        # ROI Nominal: Lo que ganarás si vendes todo hoy
        resumen['roi_nominal'] = np.where(
            resumen['inversion_total'] > 0, 
            (resumen['ganancia_potencial'] / resumen['inversion_total']) * 100, 
            0
        )

        # ROI Pro: ROI Nominal * Factor de velocidad (1.2 si hay quiebres en la sección)
        # Esto indica que la inversión retorna más rápido por alta demanda
        resumen['roi_pro'] = resumen.apply(
            lambda x: round(x['roi_nominal'] * 1.2, 1) if x['seccion'] in secciones_con_quiebre else round(x['roi_nominal'], 1),
            axis=1
        )

        # 5. Respuesta Unificada
        return {
            'total_inversion': float(df['inversion_total'].sum()),
            'total_ganancia': float(df['ganancia_potencial'].sum()),
            'venta_total_esperada': float(df['venta_total'].sum()),
            'secciones': resumen.to_dict('records'),
            'top_illidari': df.nlargest(5, 'ganancia_potencial').to_dict('records'),
            'estado': 'ok'
        }