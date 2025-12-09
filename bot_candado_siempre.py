import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
LISTA_USUARIOS = ["m0ritaav", "fresaskoncremq", "yazminsitq", "exorcismxq", "jerezanotravis"]
WEBHOOK_URL = "https://discord.com/api/webhooks/1446757512081707071/SKZzU2b3RHs-yz3g6iTOonfIz9SR-ZTd04sjCPeJ4uQ5oTG5SqGMtXv-7s09XoCxwyap" 

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
    # Cortar mensaje si es muy largo
    if len(mensaje) > 1900: mensaje = mensaje[:1900] + "... (cortado)"
    
    data = {
        "username": "Monitor de Candados",
        "content": mensaje
    }
    try: requests.post(WEBHOOK_URL, json=data)
    except: pass

def obtener_hora_mexico():
    utc_now = datetime.utcnow()
    # Ajuste manual -6 horas para CDMX
    mexico_time = utc_now - timedelta(hours=6)
    return mexico_time.strftime("%I:%M %p")

def chequear_estado(usuario):
    # print(f"🕵️ Revisando: {usuario}...") # Comentado para limpiar logs
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
        return "error_red"

# --- EJECUCIÓN ---
print("--- Iniciando Rastreo ---")
base_datos = cargar_bd()
hora_mx = obtener_hora_mexico()

# Listas para acumular eventos
reporte_novedades = []
reporte_errores = []

for usuario in LISTA_USUARIOS:
    # Pausa aleatoria
    time.sleep(random.randint(5, 10))
    
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
            # ¡HUBO CAMBIO!
            if estado_actual == "publica":
                reporte_novedades.append(f"🚨🔓 **¡{usuario} AHORA ES PÚBLICA!**\nAntes: {estado_anterior} ➡ Ahora: PÚBLICA\n🔗 [Ver Perfil](https://instagram.com/{usuario})")
            else:
                reporte_novedades.append(f"🔒 **{usuario} puso el candado.** (Ahora es PRIVADA)")
            
            # Guardamos el cambio
            base_datos[usuario] = estado_actual
            
        # Si NO hubo cambio, no hacemos nada, el ciclo sigue.

guardar_bd(base_datos)

# --- GENERAR MENSAJE FINAL ---
mensaje_final = ""

# Agregamos Novedades (Cambios de estado)
if reporte_novedades:
    mensaje_final += "**📢 NOVEDADES DE PRIVACIDAD:**\n" + "\n".join(reporte_novedades) + "\n\n"

# Agregamos Errores
if reporte_errores:
    mensaje_final += "**🛠️ PROBLEMAS DETECTADOS:**\n" + "\n".join(reporte_errores) + "\n\n"

# Decidir qué enviar
if mensaje_final:
    # Si hay texto en mensaje_final, es que pasó algo
    cabecera = f"🕵️ **Reporte de Candados** ({hora_mx})\n\n"
    enviar_discord(cabecera + mensaje_final)
else:
    # Si está vacío, todo está tranquilo
    enviar_discord(f"✅ **Chequeo de Candados Completo ({hora_mx}):** Sin cambios en las {len(LISTA_USUARIOS)} cuentas.")

print("--- Fin ---")
