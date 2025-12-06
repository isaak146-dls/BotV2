import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
from datetime import datetime

# --- CONFIGURACIÓN ---
LISTA_USUARIOS = ["m0ritaav", "fresaskoncremq", "yazminsitq", "exorcismxq", "jerezanotravis"]
WEBHOOK_URL = "TU_WEBHOOK_AQUI" # <--- ¡PON TU WEBHOOK!

# CAMBIO: Usamos Pixwox, suele ser más fiable para ver el estado "Private"
BASE_URL = "https://www.pixwox.com/profile/{}/"

# Headers más completos para parecer un navegador Chrome real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

DB_FILE = "estado_privacidad.json"

def cargar_bd():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def guardar_bd(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

def enviar_discord(mensaje):
    if "TU_WEBHOOK" in WEBHOOK_URL: return
    
    data = {
        "username": "Monitor de Candados",
        "content": mensaje
    }
    try: requests.post(WEBHOOK_URL, json=data)
    except: pass

def chequear_estado(usuario):
    print(f"🕵️ Revisando (Pixwox): {usuario}...")
    try:
        url = BASE_URL.format(usuario)
        r = requests.get(url, headers=HEADERS, timeout=20)
        
        if r.status_code == 404:
            return "no_existe"
        
        soup = BeautifulSoup(r.text, 'html.parser')
        texto = soup.get_text().lower()

        # --- LÓGICA DE DETECCIÓN PIXWOX ---
        
        # Pixwox suele poner "This Account is Private" claramente
        if "account is private" in texto or "private account" in texto:
            return "privada"
        
        # Si vemos contadores de posts/seguidores y NO dice privada, es pública
        # Buscamos clases específicas o palabras clave de un perfil abierto
        if "posts" in texto and "followers" in texto:
            return "publica"
            
        # Si llegamos aquí, algo raro pasó (quizás Cloudflare o página vacía)
        # Imprimimos un trozo del texto para depurar si lo corres en local
        # print(f"DEBUG: {texto[:200]}") 
        return "error_lectura"
            
    except Exception as e:
        print(f"Error de conexión: {e}")
        return f"error_red"

# --- EJECUCIÓN ---
print("--- Iniciando Rastreo ---")
base_datos = cargar_bd()
hora = datetime.now().strftime("%H:%M")

for usuario in LISTA_USUARIOS:
    # Pausa aleatoria un poco más larga para Pixwox
    time.sleep(random.randint(5, 10))
    
    estado_actual = chequear_estado(usuario)
    msg = ""

    # 1. Manejo de Errores
    if "error" in estado_actual or "no_existe" in estado_actual:
        # Si falla, avisamos a Discord para que sepas que el bot está vivo pero bloqueado
        msg = f"⚠️ **{usuario}**: Error al leer ({estado_actual}). Posible bloqueo."
        enviar_discord(msg)
        continue

    # 2. Verificar Cambios
    if usuario not in base_datos:
        base_datos[usuario] = estado_actual
        icono = "🔒" if estado_actual == "privada" else "🔓"
        msg = f"🆕 **{usuario}** agregado.\nEstado: {icono} {estado_actual.upper()}"
    
    else:
        estado_anterior = base_datos[usuario]
        
        if estado_actual != estado_anterior:
            if estado_actual == "publica":
                msg = f"🚨🔓 **¡{usuario} AHORA ES PÚBLICA!**\nAntes: {estado_anterior} ➡ Ahora: PÚBLICA\n[Ver Perfil](https://instagram.com/{usuario})"
            else:
                msg = f"🚨🔒 **{usuario} puso el candado.**\nAntes: {estado_anterior} ➡ Ahora: PRIVADA"
            base_datos[usuario] = estado_actual
            
        else:
            # SIN CAMBIOS
            icono = "🔒" if estado_actual == "privada" else "🔓"
            msg = f"✅ **{usuario}** ({hora}): Sigue {icono} **{estado_actual.upper()}**"

    enviar_discord(msg)

guardar_bd(base_datos)
print("--- Fin ---")
