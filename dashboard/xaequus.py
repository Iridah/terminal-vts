# dashboard/xaequus.py
# Xaequus — Guardián de Respaldos VTS
# Responsabilidades: backup BD + media a Backblaze B2, notificación via Lannu (Telegram)
# Dependencias: pip install b2sdk requests
 
import os
import subprocess
import datetime
import requests
from pathlib import Path
 
 
# =================================================================
# I. CONFIGURACIÓN
# =================================================================
 
B2_KEY_ID     = os.environ.get('B2_KEY_ID')
B2_APP_KEY    = os.environ.get('B2_APP_KEY')
B2_BUCKET     = os.environ.get('B2_BUCKET_NAME', 'vacadari-vts-backup')
 
TELEGRAM_TOKEN   = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
 
# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
 
# Directorio temporal para backups
BACKUP_DIR = BASE_DIR / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)
 
 
# =================================================================
# II. LANNU — NOTIFICADOR TELEGRAM
# =================================================================
 
def lannu_notificar(mensaje: str, critico: bool = False) -> bool:
    """
    Envía mensaje via Telegram (Lannu).
    critico=True → agrega 🚨 y menciona urgencia.
    Retorna True si el envío fue exitoso.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠ Lannu: tokens Telegram no configurados.")
        return False
 
    prefijo = "🚨 *CRÍTICO — VTS*\n" if critico else "🛡 *VTS · Xaequus*\n"
    texto   = f"{prefijo}{mensaje}"
 
    try:
        url  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            'chat_id':    TELEGRAM_CHAT_ID,
            'text':       texto,
            'parse_mode': 'Markdown',
        }, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"⚠ Lannu error: {e}")
        return False
 
 
def lannu_recordatorio(mensaje: str) -> bool:
    """Recordatorio de vencimientos y fechas importantes."""
    return lannu_notificar(f"📅 *Recordatorio VTS*\n{mensaje}")
 
 
def lannu_intrusion(ip: str, usuario: str = "desconocido") -> bool:
    """Alerta de intento de acceso sospechoso."""
    return lannu_notificar(
        f"🔴 Intento de login fallido\n"
        f"Usuario: `{usuario}`\n"
        f"IP: `{ip}`\n"
        f"Hora: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        critico=True
    )
 
 
# =================================================================
# III. BACKUP DE BASE DE DATOS
# =================================================================
 
def backup_base_datos() -> Path | None:
    """
    Genera un dump de la BD SQLite (o PostgreSQL si aplica).
    Retorna la ruta del archivo generado o None si falla.
    """
    timestamp   = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre      = f"vts_db_backup_{timestamp}.json"
    ruta_backup = BACKUP_DIR / nombre
 
    try:
        # Django dumpdata — exporta toda la BD en JSON
        resultado = subprocess.run(
            ['python', str(BASE_DIR / 'manage.py'), 'dumpdata',
             '--natural-foreign', '--natural-primary',
             '--exclude', 'auth.permission',
             '--exclude', 'contenttypes',
             '--indent', '2',
             '--output', str(ruta_backup)],
            capture_output=True, text=True, cwd=str(BASE_DIR)
        )
 
        if resultado.returncode != 0:
            print(f"⚠ dumpdata error: {resultado.stderr}")
            return None
 
        print(f"✓ BD exportada: {ruta_backup} ({ruta_backup.stat().st_size // 1024} KB)")
        return ruta_backup
 
    except Exception as e:
        print(f"⚠ backup_base_datos error: {e}")
        return None
 
 
# =================================================================
# IV. SUBIDA A BACKBLAZE B2
# =================================================================
 
def subir_a_b2(ruta_archivo: Path, carpeta: str = 'backups') -> bool:
    """
    Sube un archivo a Backblaze B2.
    Retorna True si fue exitoso.
    """
    if not B2_KEY_ID or not B2_APP_KEY:
        print("⚠ Xaequus: credenciales B2 no configuradas.")
        return False
 
    try:
        from b2sdk.v2 import InMemoryAccountInfo, B2Api
 
        info = InMemoryAccountInfo()
        api  = B2Api(info)
        api.authorize_account("production", B2_KEY_ID, B2_APP_KEY)
 
        bucket      = api.get_bucket_by_name(B2_BUCKET)
        nombre_b2   = f"{carpeta}/{ruta_archivo.name}"
 
        bucket.upload_local_file(
            local_file  = str(ruta_archivo),
            file_name   = nombre_b2,
        )
 
        print(f"✓ Subido a B2: {nombre_b2}")
        return True
 
    except Exception as e:
        print(f"⚠ subir_a_b2 error: {e}")
        return False
 
 
# =================================================================
# V. LIMPIEZA DE BACKUPS LOCALES
# =================================================================
 
def limpiar_backups_locales(dias: int = 7) -> int:
    """
    Elimina backups locales más antiguos que `dias` días.
    Retorna cantidad de archivos eliminados.
    """
    limite     = datetime.datetime.now() - datetime.timedelta(days=dias)
    eliminados = 0
 
    for archivo in BACKUP_DIR.glob('vts_*_backup_*.json'):
        if datetime.datetime.fromtimestamp(archivo.stat().st_mtime) < limite:
            archivo.unlink()
            eliminados += 1
 
    return eliminados
 
 
# =================================================================
# VI. CICLO COMPLETO DE RESPALDO
# =================================================================
 
def ejecutar_respaldo_completo() -> dict:
    """
    Ciclo completo:
      1. Backup BD
      2. Copiar a VacaCapsule (backup local)
      3. Subir a B2 (backup nube)
      4. Limpiar locales antiguos
      5. Notificar via Lannu
    """
    resultado = {
        'ok':              False,
        'archivo':         None,
        'subido_b2':       False,
        'subido_local':    False,
        'eliminados':      0,
        'error':           None,
    }

    VACA_CAPSULE = Path('/mnt/vacaCapsule/vts_backups')
    timestamp = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')

    try:
        # 1. Backup BD
        ruta = backup_base_datos()
        if not ruta:
            raise Exception("Falló la exportación de la BD")

        resultado['archivo'] = str(ruta)
        tam_kb = ruta.stat().st_size // 1024

        # 2. Copiar a VacaCapsule
        try:
            VACA_CAPSULE.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(str(ruta), str(VACA_CAPSULE / ruta.name))
            resultado['subido_local'] = True
        except Exception as e_local:
            print(f"⚠ VacaCapsule no disponible: {e_local}")

        # 3. Subir a B2
        resultado['subido_b2'] = subir_a_b2(ruta)

        # 4. Limpiar locales
        resultado['eliminados'] = limpiar_backups_locales(dias=7)

        resultado['ok'] = True

        # 5. Notificar éxito
        lannu_notificar(
            f"✅ Respaldo completado\n"
            f"📦 Archivo: `{ruta.name}`\n"
            f"💾 Tamaño: {tam_kb} KB\n"
            f"💿 VacaCapsule: {'✓' if resultado['subido_local'] else '✗ no disponible'}\n"
            f"☁️ B2: {'✓' if resultado['subido_b2'] else '✗'}\n"
            f"🗑 Locales eliminados: {resultado['eliminados']}\n"
            f"🕐 {timestamp}"
        )

    except Exception as e:
        resultado['error'] = str(e)
        lannu_notificar(
            f"❌ Respaldo FALLIDO\n"
            f"Error: `{str(e)}`\n"
            f"🕐 {timestamp}",
            critico=True
        )

    return resultado