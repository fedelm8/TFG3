import subprocess
import os
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pwd  # Para traducir UID a nombre de usuario

ARCHIVO = os.path.expanduser("/home/osboxes/Documents/tarjetas_bancarias.txt")
CLAVE = "acceso_tarjetas"
CLAVE_DEFENSA = "clave_defensa"
INTERVALO = 2  # Segundos entre chequeos
SITIOS_RESTRINGIDOS = [
    "/etc/shadow", "/etc/passwd", "/etc/sudoers", "/root", "/boot", "/var/log",
    "/bin/bash", "/dev/mem", "/proc/kcore"
]
COMANDOS_PELIGROSOS = ["nmap", "tcpdump", "netstat", "bash", "nc", "rm", "chmod 777", "curl", "wget", "scp"]


# Ruta del log en carpeta 'logs' junto al script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "accesos.log")
LOG_PATH2 = os.path.join(LOG_DIR, "defense.log")

# Crear carpeta logs si no existe
os.makedirs(LOG_DIR, exist_ok=True)

eventos_accesos = set()
eventos_defensa = set()

def registrar_log(usuario, ip):
    mensaje = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Usuario: {usuario} | IP: {ip}\n"
    try:
        with open(LOG_PATH, "a") as log_file:
            log_file.write(mensaje)
    except Exception as e:
        print(f"[X] Error al escribir en el log: {e}")

def registrar_log2(usuario, ip, recurso):
    mensaje = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Usuario: {usuario} | IP: {ip} | Acceso: {recurso}\n"
    try:
        with open(LOG_PATH2, "a") as log_file:
            log_file.write(mensaje)
    except Exception as e:
        print(f"[X] Error al escribir en el log: {e}")

def enviar_alerta_gmail(usuario, ip):
    remitente = "pruebasfede1111@gmail.com"
    receptor = "pruebasfede1111@gmail.com"
    asunto = "ALERTA: Acceso al archivo sensible"
    mensaje = f"""
Se ha detectado un intento de lectura en tarjetas_bancarias.txt

🔍 Detalles:
- Usuario: {usuario}
- IP: {ip}
- Hora: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    ##contrasena = "grkyynyhfuxecing"  #contraseña de aplicación
    contrasena = "gsxacdvzlnelgitx"

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

def enviar_alerta_gmail2(usuario, ip, recurso):
    remitente = "pruebasfede1111@gmail.com"
    receptor = "pruebasfede1111@gmail.com"
    asunto = "🚨 ALERTA DE SEGURIDAD: Acceso sospechoso al sistema"
    mensaje = f"""
Se ha detectado una posible intrusión o acceso no permitido al sistema operativo.

🔍 Detalles:
- Usuario: {usuario}
- IP: {ip}
- Recurso/Acción: {recurso}
- Hora: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    contrasena = "gsxacdvzlnelgitx"

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
        os.chmod(ARCHIVO, 0o000)
        print("[BLOQUEO] Permisos eliminados del archivo para impedir lectura.")
    except Exception as e:
        print(f"[X] Error al bloquear el archivo: {e}")

def monitorear_accesos():
    print(f"[*] Monitoreando accesos de lectura al archivo:\n{ARCHIVO}\n")

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
                if log and log not in eventos_accesos:
                    # Extraer UID
                    uid_line = next((line for line in log.splitlines() if "uid=" in line and "auid=" in line), None)
                    uid = "desconocido"
                    usuario = "desconocido"
                    ip = "localhost"

                    if uid_line:
                        try:
                            partes = uid_line.split()
                            for parte in partes:
                                if parte.startswith("uid="):
                                    uid = int(parte.split("=")[1])
                                    usuario = pwd.getpwuid(uid).pw_name
                        except:
                            pass

                    # Extraer IP 
                    addr_line = next((line for line in log.splitlines() if "addr=" in line), None)
                    if addr_line and "addr=" in addr_line:
                        ip = addr_line.split("addr=")[-1].strip().split()[0]

                    print("[ALERTA] ¡Intento de ACCESO DETECTADO al archivo sensible!")
                    print(f"  ➤ Usuario: {usuario}")
                    print(f"  ➤ IP: {ip}")
                    registrar_log(usuario, ip)
                    bloquear_archivo()
                    enviar_alerta_gmail(usuario, ip)
                    eventos_accesos.add(log)

            time.sleep(INTERVALO)

    except KeyboardInterrupt:
        print("\n[+] Monitor finalizado por el usuario. Cerrando...")

# ===================== MONITOREO =====================
def monitorear_defensa():
    print(f"[*] Defensa activa. Monitorizando accesos peligrosos...")
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[*] Ignorando eventos anteriores a {timestamp}\n")

    try:
        while True:
            resultado = subprocess.run(
                ["ausearch", "-k", CLAVE_DEFENSA, "-ts", timestamp, "--format", "raw"],
                stdout=subprocess.PIPE
            )
            logs = resultado.stdout.decode().split("\n\n")

            for log in logs:
                if log and log not in eventos_defensa:
                    uid_line = next((line for line in log.splitlines() if "uid=" in line and "auid=" in line), None)
                    uid = "desconocido"
                    usuario = "desconocido"
                    ip = "localhost"
                    recurso = "indeterminado"

                    if uid_line:
                        try:
                            partes = uid_line.split()
                            for parte in partes:
                                if parte.startswith("uid="):
                                    uid = int(parte.split("=")[1])
                                    usuario = pwd.getpwuid(uid).pw_name
                        except:
                            pass

                    exe_line = next((line for line in log.splitlines() if "exe=" in line), None)
                    if exe_line:
                        recurso = exe_line.split("exe=")[-1].strip().split()[0]

                    addr_line = next((line for line in log.splitlines() if "addr=" in line), None)
                    if addr_line and "addr=" in addr_line:
                        ip = addr_line.split("addr=")[-1].strip().split()[0]

                    if any(recurso.startswith(path) for path in SITIOS_RESTRINGIDOS) or any(cmd in recurso for cmd in COMANDOS_PELIGROSOS):
                        print("[DEFENSA] Actividad sospechosa detectada.")
                        print(f"  ➤ Usuario: {usuario}")
                        print(f"  ➤ IP: {ip}")
                        print(f"  ➤ Recurso: {recurso}")
                        registrar_log2(usuario, ip, recurso)
                        enviar_alerta_gmail2(usuario, ip, recurso)

                    eventos_defensa.add(log)

            time.sleep(INTERVALO)

    except KeyboardInterrupt:
        print("\n[+] Monitor finalizado por el usuario. Cerrando...")

if __name__ == "__main__":
    monitorear_accesos()
    monitorear_defensa()

