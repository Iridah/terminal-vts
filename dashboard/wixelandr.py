# dashboard/wixelandr.py
# Wixelandr — Guardián de Datos, Módulo Ventas VTS
# Responsabilidades: validación Sargerite, integridad CSV SumUp
 
import csv
import io
from .models import PerfilVTS
 
# =================================================================
# I. CONSTANTES
# =================================================================
 
# Columnas mínimas requeridas — las extras del CSV se ignoran
COLUMNAS_VENTAS_MIN = {
    'ID de transacción', 'Tipo', 'Descripción', 'Cantidad', 'Precio (Bruto)'
}
 
COLUMNAS_INVENTARIO_MIN = {
    'Item name', 'SKU', 'Item id', 'Variant id'
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
    Acepta columnas extra — solo exige el subconjunto mínimo requerido.
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
 
        # Verificar columnas mínimas requeridas
        cols_min = COLUMNAS_VENTAS_MIN if tipo == 'ventas' else COLUMNAS_INVENTARIO_MIN
        faltantes = cols_min - encabezados
        if faltantes:
            resultado['errores'].append(
                f'Columnas requeridas faltantes: {", ".join(sorted(faltantes))}'
            )
            return resultado
 
        resultado['tipo'] = tipo
        ids_vistos = set()
        filas = list(reader)
 
        if not filas:
            resultado['errores'].append('El archivo está vacío.')
            return resultado
 
        for i, fila in enumerate(filas, start=2):
            if tipo == 'ventas':
                id_tx = fila.get('ID de transacción', '').strip()
                desc  = fila.get('Descripción', '').strip()
                clave = f"{id_tx}_{desc}"
 
                # Duplicados (mismo TX + mismo producto)
                if clave in ids_vistos:
                    resultado['advertencias'].append(
                        f'Fila {i}: transacción duplicada ({id_tx})'
                    )
                    continue
                ids_vistos.add(clave)
 
                # Campos críticos
                if not id_tx:
                    resultado['errores'].append(f'Fila {i}: sin ID de transacción')
                    continue
                if fila.get('Tipo', '').strip() != 'Venta':
                    continue  # Ignorar devoluciones y otros tipos silenciosamente
                if not desc:
                    resultado['advertencias'].append(f'Fila {i}: descripción vacía')
                    continue
 
            resultado['filas_validas'].append(dict(fila))
 
        resultado['ok'] = len(resultado['errores']) == 0
        return resultado
 
    except UnicodeDecodeError:
        resultado['errores'].append('Error de codificación. Guarde el CSV en UTF-8.')
        return resultado
    except Exception as e:
        resultado['errores'].append(f'Error inesperado: {str(e)}')
        return resultado