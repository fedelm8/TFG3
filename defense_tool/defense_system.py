import subprocess
import os
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pwd  # Para traducir UID a nombre de usuario

ARCHIVO = os.path.expanduser("/home/osboxes/Documents/tarjetas_bancarias.txt")
CLAVE = "clave_defensa"
INTERVALO = 2  # Segundos entre chequeos
SITIOS_RESTRINGIDOS = [
    "/etc/shadow", "/etc/passwd", "/etc/sudoers", "/root", "/boot", "/var/log",
    "/bin/bash", "/dev/mem", "/proc/kcore"
]
COMANDOS_PELIGROSOS = ["nmap", "tcpdump", "netstat", "bash", "nc", "rm", "chmod 777", "curl", "wget", "scp"]

# Ruta del log en carpeta 'logs' junto al script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "defense.log")

# Crear carpeta logs si no existe
os.makedirs(LOG_DIR, exist_ok=True)

eventos_defensa = set()

def registrar_log(usuario, ip, rutas_accedidas):
    rutas_txt = "\n".join(f"  - {ruta}" for ruta in rutas_accedidas) if rutas_accedidas else "  - No determinado"
    mensaje = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Usuario: {usuario} | IP: {ip} | Rutas accedidas:\n{rutas_txt}\n"
    try:
        with open(LOG_PATH, "a") as log_file:
            log_file.write(mensaje)
    except Exception as e:
        print(f"[X] Error al escribir en el log: {e}")


def enviar_alerta_gmail(usuario, ip, recurso, rutas_accedidas):
    remitente = "pruebasfede1111@gmail.com"
    receptor = "pruebasfede1111@gmail.com"
    asunto = "🚨 ALERTA DE SEGURIDAD: Acceso sospechoso al sistema"
    
    rutas_txt = "\n".join(f"  - {ruta}" for ruta in rutas_accedidas) if rutas_accedidas else "  - No determinado"
    
    mensaje = f"""
Se ha detectado una posible intrusión o acceso no permitido al sistema operativo.

🔍 Detalles:
- Usuario: {usuario}
- IP: {ip}
- Recurso ejecutado: {recurso}
- Recursos accedidos:
{rutas_txt}
- Hora: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    contrasena = "gdpnbpksefsnuqxh"

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


def monitorear_defensa():
    print(f"[*] Defensa activa. Monitorizando accesos peligrosos...")
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

                    # Revisión de rutas accedidas
                    path_lines = [line for line in log.splitlines() if "name=" in line]
                    paths_accedidos = [line.split("name=")[-1].strip().strip('"') for line in path_lines]
                    accede_sitio_restringido = any(p in SITIOS_RESTRINGIDOS for p in paths_accedidos)

                    if accede_sitio_restringido or any(cmd in recurso for cmd in COMANDOS_PELIGROSOS):
                        print("[DEFENSA] Actividad sospechosa detectada.")
                        print(f"  ➤ Usuario: {usuario}")
                        print(f"  ➤ IP: {ip}")
                        print(f"  ➤ Recurso: {recurso}")
                        print(f"  ➤ Rutas accedidas: {', '.join(paths_accedidos)}")
                        registrar_log(usuario, ip, paths_accedidos)
                        enviar_alerta_gmail(usuario, ip, recurso, paths_accedidos)

                    eventos_defensa.add(log)

            time.sleep(INTERVALO)

    except KeyboardInterrupt:
        print("\n[+] Monitor finalizado por el usuario. Cerrando...")


if __name__ == "__main__":
    monitorear_defensa()
