#martillo_vil/pollofrito.py - Martillo Vil - Modo D
import requests
import time
import subprocess
import os

TOKEN_PATH = "/mnt/VTSCORE/vts_root.key"
GRACE_PERIOD = 1800
RESTORE_THRESHOLD = 300
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def alertar_a_lannu(mensaje):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje}
        try:
            requests.post(url, data=data, timeout=10)
        except Exception as e:
            print(f"Error al enviar mensaje a Telegram: {e}")
    else:
        print(mensaje)

def token_presente():
    try:
        with open(TOKEN_PATH, "r") as f:
            content = f.read().strip()
            return content != ""
    except FileNotFoundError:
        return False
    except Exception as e:
        alertar_a_lannu(f"⚠️ ERROR LECTURA TOKEN: {e} — tick omitido")
        raise

def abort_autorizado():
    override_hash = os.environ.get("GIGA_SLAVE_OVERRIDE")
    abort_signal = os.environ.get("GIGA_SLAVE_ABORT")
    return bool(override_hash and abort_signal and abort_signal == override_hash)

def activar_giga_slave():
    """VTS siempre se detiene (niega acceso ante amenaza activa). El shred
    —irreversible, sobrescribe 3 veces, sin recuperación posible ni a nivel
    de filesystem— solo procede si el backup de emergencia se confirmó
    exitoso. Antes esto shredeaba igual aunque el backup fallara: un
    problema no adversarial en backup_cron.sh (disco lleno, red caída,
    permisos) bastaba para perder la base de datos completa de Vaca's
    Store sin ninguna copia de respaldo."""
    alertar_a_lannu("🔴 GIGA SLAVE ACTIVADO - Iniciando protocolo")
    try:
        subprocess.run(["systemctl", "stop", "vts"], check=True)
    except subprocess.CalledProcessError as e:
        alertar_a_lannu(f"⚠️ FALLO al detener vts: {e} — continuando protocolo")

    backup_ok = False
    try:
        subprocess.run(["/mnt/storage/proyectos/backup_cron.sh", "--emergency"], check=True)
        backup_ok = True
    except subprocess.CalledProcessError as e:
        alertar_a_lannu(f"⚠️ FALLO en backup de emergencia: {e} — NO se hará shred sin respaldo válido")

    if not backup_ok:
        alertar_a_lannu(
            "🔴 GIGA SLAVE DETENIDO ANTES DEL SHRED — respaldo de emergencia no confirmado. "
            "VTS caído (acceso denegado), base de datos intacta. Revisar backup_cron.sh a mano "
            "y decidir el shred manualmente si corresponde."
        )
        return

    try:
        subprocess.run(["shred", "-vfz", "-n", "3",
                        "/mnt/storage/proyectos/VTS/db.sqlite3"], check=True)
        alertar_a_lannu("✅ GIGA SLAVE COMPLETADO - VTS neutralizado")
    except subprocess.CalledProcessError as e:
        alertar_a_lannu(f"🔴 FALLO CRÍTICO en shred: {e} — DB puede estar intacta")

def watchdog_loop():
    ausencia_detectada = None
    token_restaurado = None

    while True:
        if abort_autorizado():
            alertar_a_lannu("🟡 ABORT MANUAL - Giga Slave detenido por iridah")
            break

        try:
            presente = token_presente()
        except Exception:
            time.sleep(60)
            continue

        if not presente:
            token_restaurado = None
            if ausencia_detectada is None:
                ausencia_detectada = time.time()
                alertar_a_lannu(f"⚠️ TOKEN AUSENTE - Giga Slave en {GRACE_PERIOD//60} minutos")

            elapsed = time.time() - ausencia_detectada
            if elapsed >= GRACE_PERIOD:
                activar_giga_slave()
                break
        else:
            if ausencia_detectada is not None:
                if token_restaurado is None:
                    token_restaurado = time.time()
                elif time.time() - token_restaurado >= RESTORE_THRESHOLD:
                    alertar_a_lannu("✅ Token restaurado - Giga Slave abortado")
                    ausencia_detectada = None
                    token_restaurado = None

        time.sleep(60)

if __name__ == "__main__":
    watchdog_loop()
