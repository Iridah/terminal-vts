# dashboard/engine.py
import pandas as pd
import numpy as np
from .models import AuditoriaVTS

class FelEngine:
    @staticmethod
    def generar_reporte_general():
        # Traemos los datos crudos
        data = AuditoriaVTS.objects.all().values(
            'seccion', 'producto', 'precio_costo', 'precio_venta', 'inventario_real'
        )
        
        if not data.exists():
            return {'estado': 'vacio'}

        df = pd.DataFrame(list(data))

        # 1. Limpieza inicial: Convertir a numérico y manejar nulos
        # Esto soluciona el TypeError de "dtype object"
        for col in ['precio_costo', 'precio_venta', 'inventario_real']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 2. Cálculos de Negocio
        df['inversion_total'] = df['precio_costo'] * df['inventario_real']
        df['ganancia_potencial'] = (df['precio_venta'] - df['precio_costo']) * df['inventario_real']
        
        # 3. Forzamos que la ganancia sea float explícitamente antes del ranking
        df['ganancia_potencial'] = df['ganancia_potencial'].astype(float)

        # 4. Agrupación por Sección
        resumen = df.groupby('seccion').agg({
            'inversion_total': 'sum',
            'ganancia_potencial': 'sum',
            'inventario_real': 'sum'
        }).reset_index()

        # ROI por sección (evitando división por cero)
        resumen['roi'] = np.where(
            resumen['inversion_total'] > 0, 
            (resumen['ganancia_potencial'] / resumen['inversion_total']) * 100, 
            0
        )

        return {
            'total_inversion': df['inversion_total'].sum(),
            'total_ganancia': df['ganancia_potencial'].sum(),
            # NUEVO: La suma de lo invertido más la ganancia esperada
            'venta_total_esperada': df['inversion_total'].sum() + df['ganancia_potencial'].sum(),
            'secciones': resumen.to_dict('records'),
            'top_illidari': df.nlargest(5, 'ganancia_potencial').to_dict('records'),
            'estado': 'ok'
        }