import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
from datetime import datetime, timedelta

# --- CONFIGURACIÓN SEGURA ---

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')

usuarios_env = os.getenv('LISTA_OBJETIVOS')
if usuarios_env:
    LISTA_USUARIOS = [u.strip() for u in usuarios_env.split(',') if u.strip()]
else:
    print("⚠️ Error: No se encontró la lista de usuarios en los secretos.")
    LISTA_USUARIOS = []

# Configuración Pixwox
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
    if not WEBHOOK_URL: return
    if len(mensaje) > 1900: mensaje = mensaje[:1900] + "... (cortado)"
    data = {"username": "Monitor de Candados", "content": mensaje}
    try: requests.post(WEBHOOK_URL, json=data)
    except: pass

def obtener_hora_mexico():
    utc_now = datetime.utcnow()
    mexico_time = utc_now - timedelta(hours=6)
    return mexico_time.strftime("%I:%M %p")

def chequear_estado(usuario):
    try:
        url = BASE_URL.format(usuario)
        r = requests.get(url, headers=HEADERS, timeout=20)
        
        if r.status_code == 404:
            return "no_existe"
        
        soup = BeautifulSoup(r.text, 'html.parser')
        texto = soup.get_text().lower()

        if "account is private" in texto or "private account" in texto:
            return "privada"
        if "posts" in texto and "followers" in texto:
            return "publica"
        return "error_lectura"
    except Exception as e:
        return "error_red"

# --- EJECUCIÓN ---
print("--- Iniciando Rastreo Seguro ---")
base_datos = cargar_bd()
hora_mx = obtener_hora_mexico()

reporte_novedades = []
reporte_errores = []

for usuario in LISTA_USUARIOS:
    print(f"::add-mask::{usuario}")
    # ---------------------------

    time.sleep(random.randint(5, 10))
    
    print(f"Revisando: {usuario}")
    
    estado_actual = chequear_estado(usuario)

    # 1. Manejo de Errores
    if "error" in estado_actual or "no_existe" in estado_actual:
        reporte_errores.append(f"⚠️ **{usuario}**: {estado_actual}")
        continue

    # 2. Verificar Cambios
    if usuario not in base_datos:
        base_datos[usuario] = estado_actual
        icono = "🔒" if estado_actual == "privada" else "🔓"
        reporte_novedades.append(f"🆕 **{usuario}**: Agregado. Estado: {icono} {estado_actual.upper()}")
    
    else:
        estado_anterior = base_datos[usuario]
        if estado_actual != estado_anterior:
            if estado_actual == "publica":
                reporte_novedades.append(f"🚨🔓 **¡{usuario} AHORA ES PÚBLICA!**\nAntes: {estado_anterior} ➡ Ahora: PÚBLICA\n🔗 [Ver Perfil](https://instagram.com/{usuario})")
            else:
                reporte_novedades.append(f"🔒 **{usuario} puso el candado.** (Ahora es PRIVADA)")
            base_datos[usuario] = estado_actual

guardar_bd(base_datos)

# --- REPORTE ---
mensaje_final = ""
if reporte_novedades:
    mensaje_final += "**📢 NOVEDADES DE PRIVACIDAD:**\n" + "\n".join(reporte_novedades) + "\n\n"
if reporte_errores:
    mensaje_final += "**🛠️ PROBLEMAS DETECTADOS:**\n" + "\n".join(reporte_errores) + "\n\n"

if mensaje_final:
    enviar_discord(f"🕵️ **Reporte de Candados** ({hora_mx})\n\n" + mensaje_final)
else:
    enviar_discord(f"✅ **Chequeo Completo ({hora_mx}):** Sin cambios en las {len(LISTA_USUARIOS)} cuentas.")

print("--- Fin ---")

