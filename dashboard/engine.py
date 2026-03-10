# dashboard/engine.py
import pandas as pd
import numpy as np
from .models import AuditoriaVTS, VarianteVTS

class FelEngine:
    @staticmethod
    def generar_reporte_general():

        # 0.- Productos SIN variantes (directos)
        qs_simples = AuditoriaVTS.objects.exclude(
            seccion__isnull=True).exclude(seccion="").filter(
            variantes__isnull=True).values(
            'seccion', 'producto', 'precio_costo', 'precio_venta', 'inventario_real'
        )

        # 0b.- Productos CON variantes (desde VarianteVTS)
        variantes_data = VarianteVTS.objects.select_related('producto').values_list(
            'producto__seccion',
            'producto__producto',
            'precio_costo',
            'precio_venta',
            'inventario_real',
        )

        df_variantes = pd.DataFrame(
            list(variantes_data),
            columns=['seccion', 'producto', 'precio_costo', 'precio_venta', 'inventario_real']
        ) if variantes_data.exists() else pd.DataFrame()

        df_simples = pd.DataFrame(list(qs_simples)) if qs_simples.exists() else pd.DataFrame()

        # Unir ambos
        df = pd.concat([df_simples, df_variantes], ignore_index=True)

        if df.empty:
            return {'estado': 'vacio'}

        # 2. LIMPIEZA
        for col in ['precio_costo', 'precio_venta']:
            df[col] = df[col].apply(float)
        df['inventario_real'] = df['inventario_real'].astype(int)

        # 3. CÁLCULOS BASE
        df['inversion_total'] = df['precio_costo'] * df['inventario_real']
        df['venta_total'] = df['precio_venta'] * df['inventario_real']
        df['ganancia_potencial'] = df['venta_total'] - df['inversion_total']

        # 4. LÓGICA PRO
        secciones_con_quiebre = df[df['inventario_real'] == 0]['seccion'].unique()
        resumen = df.groupby('seccion').agg({
            'inversion_total': 'sum',
            'ganancia_potencial': 'sum',
            'inventario_real': 'sum',
            'producto': 'count'
        }).rename(columns={'producto': 'total_skus'}).reset_index()

        resumen['roi_nominal'] = np.where(
            resumen['inversion_total'] > 0,
            (resumen['ganancia_potencial'] / resumen['inversion_total']) * 100,
            0
        )

        resumen['roi_pro'] = resumen.apply(
            lambda x: round(x['roi_nominal'] * 1.2, 1) if x['seccion'] in secciones_con_quiebre else round(x['roi_nominal'], 1),
            axis=1
        )

        # 5. RESPUESTA UNIFICADA
        return {
            'total_inversion': round(float(df['inversion_total'].sum()), 2),
            'total_ganancia': round(float(df['ganancia_potencial'].sum()), 2),
            'venta_total_esperada': round(float(df['venta_total'].sum()), 2),
            'secciones': resumen.to_dict('records'),
            'top_illidari': df.nlargest(5, 'ganancia_potencial').to_dict('records'),
            'bottom_illidari': df[df['inventario_real'] > 0].nsmallest(5, 'ganancia_potencial').to_dict('records'),
            'promedio_roi': round(resumen['roi_pro'].mean(), 1) if not resumen.empty else 0,
            'estado': 'ok'
        }

