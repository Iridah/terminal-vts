# dashboard/sargerite.py - El Escudo de Iridah
import requests
import os
import hashlib
from functools import wraps
from django.http import JsonResponse
from django.conf import settings

TOKEN_PATH = "/mnt/vts_key/vts_root.key"

def is_root_key_present():
    """Verifica el hardware físico VTS_CORE"""
    if settings.DEBUG: return True 
    if not os.path.exists(TOKEN_PATH): return False
    try:
        with open(TOKEN_PATH, 'r') as f:
            content = f.read().strip()
            # Compara con el secreto del .env
            return content == settings.SARGERITE_EXPECTED_HASH
    except: return False

def sargerite_shield(permiso_requerido=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            from .models import PerfilVTS
            token = request.headers.get('X-Sargerite-Token')
            ip = request.META.get('REMOTE_ADDR')

            # Print de auditoría SEGURO (dentro de la función)
            print(f"🔍 AUDITORÍA: Token '{token}' desde IP {ip}")

            try:
                perfil = PerfilVTS.objects.get(sargerite_token=token)
                
                # VALIDACIÓN DE BOSS + LLAVE FÍSICA
                if perfil.rol == 'Boss':
                    if not is_root_key_present():
                        alertar_a_lannu(f"Intento de acceso Boss SIN LLAVE FÍSICA desde IP: {ip}")
                        return JsonResponse({'status': 'denied', 'msg': 'Llave física VTS_CORE no detectada.'}, status=403)

                # VALIDACIÓN DE PERMISOS ELÁSTICOS
                if permiso_requerido and not getattr(perfil, permiso_requerido, False):
                    alertar_a_lannu(f"Usuario {perfil.user.username} intentó acceder a {permiso_requerido} sin permiso.")
                    return JsonResponse({'status': 'denied', 'msg': 'Nivel insuficiente'}, status=403)

                perfil.ultima_ip = ip
                perfil.save(update_fields=['ultima_ip'])
                return view_func(request, *args, **kwargs)

            except PerfilVTS.DoesNotExist:
                return JsonResponse({'status': 'error', 'msg': 'Token Inválido'}, status=401)
        return _wrapped_view
    return decorator

# =================================================================
# PROTOCOLO LANNU
# =================================================================
def alertar_a_lannu(mensaje):
    """Protocolo de Alerta vía Telegram"""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={'chat_id': settings.TELEGRAM_CHAT_ID, 'text': f"🚨 Lannu Report: {mensaje}"})
    except: pass