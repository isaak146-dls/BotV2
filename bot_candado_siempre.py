import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
from datetime import datetime, timedelta # <--- Importamos timedelta

# --- CONFIGURACIÓN ---
LISTA_USUARIOS = ["m0ritaav", "fresaskoncremq", "yazminsitq", "exorcismxq", "jerezanotravis"]
WEBHOOK_URL = "https://discord.com/api/webhooks/1446757512081707071/SKZzU2b3RHs-yz3g6iTOonfIz9SR-ZTd04sjCPeJ4uQ5oTG5SqGMtXv-7s09XoCxwyap" # <--- ¡PON TU WEBHOOK!

# Usamos Pixwox
BASE_URL = "https://www.pixwox.com/profile/{}/"

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

def obtener_hora_mexico():
    # GitHub está en UTC. México (Central) es UTC - 6 horas.
    utc_now = datetime.utcnow()
    mexico_time = utc_now - timedelta(hours=6)
    return mexico_time.strftime("%I:%M %p") # Ejemplo: 01:09 PM

def chequear_estado(usuario):
    print(f"🕵️ Revisando (Pixwox): {usuario}...")
    try:
        url = BASE_URL.format(usuario)
        r = requests.get(url, headers=HEADERS, timeout=20)
        
        if r.status_code == 404:
            return "no_existe"
        
        soup = BeautifulSoup(r.text, 'html.parser')
        texto = soup.get_text().lower()

        # Lógica Pixwox
        if "account is private" in texto or "private account" in texto:
            return "privada"
        
        if "posts" in texto and "followers" in texto:
            return "publica"
            
        return "error_lectura"
            
    except Exception as e:
        return f"error_red"

# --- EJECUCIÓN ---
print("--- Iniciando Rastreo ---")
base_datos = cargar_bd()
hora_mx = obtener_hora_mexico() # <--- Calculamos la hora aquí

for usuario in LISTA_USUARIOS:
    time.sleep(random.randint(5, 10))
    
    estado_actual = chequear_estado(usuario)
    msg = ""

    if "error" in estado_actual or "no_existe" in estado_actual:
        msg = f"⚠️ **{usuario}**: Error ({estado_actual})."
        enviar_discord(msg)
        continue

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
            icono = "🔒" if estado_actual == "privada" else "🔓"
            # Aquí usamos la hora corregida
            msg = f"✅ **{usuario}** ({hora_mx}): Sigue {icono} **{estado_actual.upper()}**"

    enviar_discord(msg)

guardar_bd(base_datos)
print("--- Fin ---")

