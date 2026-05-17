# /dashboard/oraculo.py
import requests
from decimal import Decimal
from datetime import datetime

class OraculoSargerite:
    """Le Savant: Gestiona UF (día) y UTM (mes) con precisión quirúrgica"""
    
    SUELDO_MINIMO = Decimal("539000") 
    JORNADA_LABORAL = 40 

    @staticmethod
    def obtener_indicadores() -> dict:
        # Fallback de seguridad
        indicadores = {
            'uf': Decimal("38500.00"), # Valor del día
            'utm': Decimal("67000.00"), # Valor del mes
            'sueldo_minimo': OraculoSargerite.SUELDO_MINIMO,
            'jornada': OraculoSargerite.JORNADA_LABORAL,
            'fecha_consulta': datetime.now().strftime("%d-%m-%Y")
        }
        
        try:
            # Mindicador entrega por defecto la UF de hoy y la UTM del mes actual
            response = requests.get("https://mindicador.cl/api", timeout=5)
            if response.status_code == 200:
                data = response.json()
                indicadores['uf'] = Decimal(str(data['uf']['valor']))
                indicadores['utm'] = Decimal(str(data['utm']['valor']))
        except Exception as e:
            print(f"🚨 ÉCHEC DE L'ORACLE: {e}")
            
        return indicadores