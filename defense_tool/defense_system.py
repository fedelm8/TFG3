import subprocess
import os
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pwd

ARCHIVOS_PELIGROSOS = ["/etc/shadow", "/etc/passwd", "/etc/sudoers"]
CLAVE = "clave_defensa"
INTERVALO = 2

PROCESOS_PERMITIDOS = {
    "gdm-session-worker",
    "login",
    "sudo",
    "sshd",
    "polkitd",
    "systemd",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "accesos.log")

os.makedirs(LOG_DIR, exist_ok=True)

eventos_detectados = set()

timestamp_inicio = datetime.now().strftime("%H:%M:%S")
print(f"[*] Ignorando eventos anteriores a {timestamp_inicio}\n")

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

    contrasena = "owbjrlluueabmpbf"  # <- contraseña de aplicación

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

def monitorear():
    print("[*] Defensa activa. Monitorizando accesos peligrosos...\n")

    print("[*] Esperando a que el sistema se estabilice...")
    time.sleep(10)

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
                    proceso = "desconocido"

                    if f"audit({timestamp_inicio}" not in log:
                        continue

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

                        if "comm=" in line:
                            proceso = line.split("comm=")[-1].strip().strip('"')

                    # Verificar si es un proceso permitido
                    if proceso in PROCESOS_PERMITIDOS:
                        print(f"[IGNORADO] Proceso seguro: {proceso} | Usuario: {usuario} | Ruta: \"{ruta}\"")
                        continue

                    #if usuario == "root" and ruta == "/etc/shadow":
                     #   print(f"[IGNORADO] Acceso esperado de root a /etc/shadow durante el arranque: {usuario} | Ruta: \"{ruta}\"")
                      #  continue

                    print(f"[{estado}] Usuario: {usuario} | Ruta: \"{ruta}\"")
                    registrar_log(usuario, ip, ruta, estado)
                    proteger_archivo(ruta)
                    enviar_alerta_gmail(usuario, ip, ruta, estado)
                    eventos_detectados.add(log)

            time.sleep(INTERVALO)

    except KeyboardInterrupt:
        print("\n[+] Monitor finalizado por el usuario. Cerrando...")

if __name__ == "__main__":
    monitorear()
