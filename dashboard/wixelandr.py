# dashboard/wixelandr.py
# Wixelandr — Guardián de Datos, Módulo Ventas VTS
# Responsabilidades: validación Sargerite, integridad CSV SumUp

import csv
import io
from .models import PerfilVTS

# =================================================================
# I. CONSTANTES
# =================================================================

COLUMNAS_VENTAS = {
    'Fecha', 'Tipo', 'ID de transacción', 'Forma de pago',
    'Cantidad', 'Descripción', 'Moneda', 'Precio (Bruto)',
    'Precio (Neto)', 'IVA'
}

COLUMNAS_INVENTARIO = {
    'Item name', 'Variations', 'SKU', 'Price',
    'Category', 'Item id', 'Variant id'
}

# =================================================================
# II. VALIDACIÓN SARGERITE
# =================================================================

def validar_acceso(user):
    """Verifica que el usuario tenga token Sargerite activo."""
    try:
        perfil = PerfilVTS.objects.get(user=user)
        return bool(perfil.sargerite_token)
    except PerfilVTS.DoesNotExist:
        return False

# =================================================================
# III. VALIDACIÓN CSV
# =================================================================

def detectar_tipo_csv(encabezados: set) -> str:
    """Detecta si el CSV es de ventas o de inventario SumUp."""
    if 'ID de transacción' in encabezados:
        return 'ventas'
    if 'Item id' in encabezados:
        return 'inventario'
    return 'desconocido'

def validar_csv_sumup(archivo) -> dict:
    """
    Valida un CSV de SumUp antes de procesarlo.
    Retorna dict con: tipo, filas_validas, errores, advertencias
    """
    resultado = {
        'tipo': None,
        'filas_validas': [],
        'errores': [],
        'advertencias': [],
        'ok': False
    }

    try:
        contenido = archivo.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(contenido))
        encabezados = set(reader.fieldnames or [])
        tipo = detectar_tipo_csv(encabezados)

        if tipo == 'desconocido':
            resultado['errores'].append('Formato no reconocido. ¿Es un CSV de SumUp?')
            return resultado

        resultado['tipo'] = tipo
        ids_vistos = set()
        filas = list(reader)

        if not filas:
            resultado['errores'].append('El archivo está vacío.')
            return resultado

        for i, fila in enumerate(filas, start=2):
            # Duplicados
            if tipo == 'ventas':
                id_tx = fila.get('ID de transacción', '').strip()
                desc = fila.get('Descripción', '').strip()
                clave = f"{id_tx}_{desc}"
                if clave in ids_vistos:
                    resultado['advertencias'].append(f'Fila {i}: transacción duplicada ({id_tx})')
                    continue
                ids_vistos.add(clave)

                # Validar campos críticos
                if not id_tx:
                    resultado['errores'].append(f'Fila {i}: sin ID de transacción')
                    continue
                if fila.get('Tipo', '').strip() != 'Venta':
                    continue  # Ignorar devoluciones y otros tipos
                if not desc:
                    resultado['advertencias'].append(f'Fila {i}: descripción vacía')
                    continue

            resultado['filas_validas'].append(fila)

        resultado['ok'] = len(resultado['errores']) == 0
        return resultado

    except UnicodeDecodeError:
        resultado['errores'].append('Error de codificación. Guarde el CSV en UTF-8.')
        return resultado
    except Exception as e:
        resultado['errores'].append(f'Error inesperado: {str(e)}')
        return resultado