import subprocess
import os
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pwd
import psutil  # Necesitamos psutil para obtener el tiempo de arranque

ARCHIVOS_PELIGROSOS = ["/etc/shadow", "/etc/passwd", "/etc/sudoers"]
CLAVE = "clave_defensa"
INTERVALO = 2
ARRANQUE_TEMPRANO_SEGUNDOS = 30  # Tiempo en segundos para ignorar eventos de arranque

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "accesos.log")

os.makedirs(LOG_DIR, exist_ok=True)

eventos_detectados = set()

def registrar_log(usuario, ip, ruta, estado):
    mensaje = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {estado} | Usuario: {usuario} | IP: {ip} | Ruta: \"{ruta}\"\n"
    try:
        with open(LOG_PATH, "a") as log_file:
            log_file.write(mensaje)
    except Exception as e:
        print(f"[X] Error al escribir en el log: {e}")

def enviar_alerta_gmail(usuario, ip, ruta, estado):
    remitente = "pruebasfede1111@gmail.com"
    receptor = "pruebasfede1111@gmail.com"
    asunto = f"ALERTA: {estado} a archivo sensible"

    mensaje = f"""
Se ha detectado un {estado.lower()} de acceso a un archivo sensible.

🔍 Detalles:
- Usuario: {usuario}
- IP: {ip}
- Ruta: {ruta}
- Hora: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    contrasena = "pddcqheuxehilvay"  # <- contraseña de aplicación

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

def proteger_archivo(ruta):
    try:
        os.chmod(ruta, 0o000)
        print(f"[BLOQUEO] Archivo protegido temporalmente: {ruta}")
    except Exception as e:
        print(f"[X] Error al bloquear el archivo: {e}")

def obtener_tiempo_arranque():
    """Obtiene el tiempo de arranque del sistema en segundos."""
    boot_time = psutil.boot_time()
    return boot_time

def monitorear():
    print("[*] Defensa activa. Monitorizando accesos peligrosos...\n")

    print("[*] Esperando a que el sistema se estabilice...")
    time.sleep(10)

    # Obtener el tiempo de arranque del sistema
    tiempo_arranque = obtener_tiempo_arranque()

    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[*] Ignorando eventos anteriores a {timestamp}\n")

    time.sleep(1.2)

    try:
        while True:
            resultado = subprocess.run(
                ["ausearch", "-k", CLAVE, "-ts", timestamp, "--format", "raw"],
                stdout=subprocess.PIPE
            )
            logs = resultado.stdout.decode().split("\n\n")

            for log in logs:
                if log and log not in eventos_detectados:
                    ruta = "desconocida"
                    uid = "desconocido"
                    usuario = "desconocido"
                    ip = "localhost"
                    estado = "DESCONOCIDO"

                    for line in log.splitlines():
                        if "name=" in line:
                            for archivo in ARCHIVOS_PELIGROSOS:
                                if f'name="{archivo}"' in line:
                                    ruta = archivo
                                    break

                        if "type=SYSCALL" in line and "success=" in line:
                            partes = line.split()
                            success_val = next((p for p in partes if p.startswith("success=")), "")
                            estado = "INTENTO EXITOSO" if success_val == "success=yes" else "INTENTO FALLIDO"

                        if "uid=" in line and "auid=" in line:
                            try:
                                partes = line.split()
                                for parte in partes:
                                    if parte.startswith("uid="):
                                        uid = int(parte.split("=")[1])
                                        usuario = pwd.getpwuid(uid).pw_name
                            except:
                                pass

                        if "addr=" in line:
                            ip = line.split("addr=")[-1].split()[0]

                    # Comprobar si el evento ocurrió durante el tiempo de arranque
                    tiempo_actual = time.time()
                    if tiempo_actual - tiempo_arranque < ARRANQUE_TEMPRANO_SEGUNDOS:
                        print(f"[IGNORADO] Acceso durante el arranque: {usuario} | Ruta: \"{ruta}\"")
                        continue

                    # Verificar si el evento ya ha sido registrado
                    timestamp_evento = datetime.now().strftime("%Y%m%d%H%M%S")
                    evento_id = f"{usuario}-{ruta}-{ip}-{timestamp_evento}"

                    if evento_id in eventos_detectados:
                        continue

                    print(f"[{estado}] Usuario: {usuario} | Ruta: \"{ruta}\"")
                    registrar_log(usuario, ip, ruta, estado)
                    proteger_archivo(ruta)
                    enviar_alerta_gmail(usuario, ip, ruta, estado)
                    eventos_detectados.add(evento_id)

            time.sleep(INTERVALO)

    except KeyboardInterrupt:
        print("\n[+] Monitor finalizado por el usuario. Cerrando...")

if __name__ == "__main__":
    monitorear()
