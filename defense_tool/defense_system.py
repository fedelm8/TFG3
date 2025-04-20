import subprocess
import os
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pwd

CLAVE = "clave_defensa"
INTERVALO = 2  # segundos
RUTAS_PROTEGIDAS = ["/etc/shadow", "/etc/gshadow", "/etc/passwd"]
ARCHIVO_BLOQUEO = "/etc/shadow"  # como referencia para aplicar permisos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "logs", "accesos.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
eventos_detectados = set()

def registrar_log(usuario, ip, ruta, estado):
    mensaje = f"[{datetime.now()}] {estado} | Usuario: {usuario} | IP: {ip} | Ruta: {ruta}\n"
    try:
        with open(LOG_PATH, "a") as log:
            log.write(mensaje)
    except Exception as e:
        print(f"[X] Error al escribir log: {e}")

def enviar_alerta(usuario, ip, ruta, estado):
    remitente = "pruebasfede1111@gmail.com"
    receptor = "pruebasfede1111@gmail.com"
    asunto = f"⚠️ ALERTA DE SEGURIDAD: {estado}"
    mensaje = f"""
Se ha detectado un intento de acceso al sistema.

🔐 Estado: {estado}
👤 Usuario: {usuario}
📍 IP: {ip}
📂 Archivo/Comando: {ruta}
🕒 Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    contrasena = "owbjrlluueabmpbf"

    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = receptor
    msg["Subject"] = asunto
    msg.attach(MIMEText(mensaje, "plain"))

    try:
        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(remitente, contrasena)
        servidor.sendmail(remitente, receptor, msg.as_string())
        servidor.quit()
        print("[EMAIL] Alerta enviada por correo.")
    except Exception as e:
        print(f"[X] Error al enviar correo: {e}")

def bloquear_archivo():
    try:
        os.chmod(ARCHIVO_BLOQUEO, 0o000)
        print("[BLOQUEO] Archivo protegido temporalmente.")
    except Exception as e:
        print(f"[X] Error al bloquear archivo: {e}")

def monitorear():
    print("[*] Defensa activa. Monitorizando accesos peligrosos...\n")
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[*] Ignorando eventos anteriores a {timestamp}\n")

    try:
        while True:
            resultado = subprocess.run(
                ["ausearch", "-k", CLAVE, "-ts", timestamp, "--format", "raw"],
                stdout=subprocess.PIPE
            )
            logs = resultado.stdout.decode().split("\n\n")

            for log in logs:
                if not log or log in eventos_detectados:
                    continue

                ruta_line = next((l for l in log.splitlines() if "name=" in l), None)
                ruta = ruta_line.split("name=")[-1].strip().split()[0] if ruta_line else "desconocido"

                uid_line = next((l for l in log.splitlines() if "uid=" in l and "auid=" in l), "")
                uid = int(uid_line.split("uid=")[1].split()[0]) if "uid=" in uid_line else 0
                usuario = pwd.getpwuid(uid).pw_name if uid else "desconocido"

                ip_line = next((l for l in log.splitlines() if "addr=" in l), "")
                ip = ip_line.split("addr=")[-1].split()[0] if "addr=" in ip_line else "localhost"

                success_line = next((l for l in log.splitlines() if "success=" in l), "")
                estado = "INTENTO EXITOSO" if "success=yes" in success_line else "INTENTO FALLIDO"

                print(f"[{estado}] Usuario: {usuario} | Ruta: {ruta}")
                registrar_log(usuario, ip, ruta, estado)
                enviar_alerta(usuario, ip, ruta, estado)
                bloquear_archivo()
                eventos_detectados.add(log)

            time.sleep(INTERVALO)

    except KeyboardInterrupt:
        print("\n[+] Defensa desactivada. Saliendo...")

if __name__ == "__main__":
    monitorear()
