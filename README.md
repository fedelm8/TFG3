
# 🛡️ Monitoring_tool

*Secure your data, empower your peace of mind.*

![Last Commit](https://img.shields.io/badge/last%20commit-today-brightgreen)
![Python](https://img.shields.io/badge/python-100%25-blue)
![Platform](https://img.shields.io/badge/platform-Linux-orange)

_Built with the tools and technologies:_

![Python](https://img.shields.io/badge/-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation and Usage](#installation-and-usage)

---

## Overview

**monitoring_tool** is a robust monitoring tool designed to safeguard sensitive files by detecting unauthorized access in real-time.

### Why monitoring_tool?

This project enhances system security by providing continuous oversight of critical files. The core features include:

- 🔐 **Real-time Monitoring**: Instantly detects unauthorized access attempts to sensitive files.
- 🚨 **Alerts**: Automatically alerts administrators and blocks suspicious processes to prevent breaches.
- 🔄 **Continuous Operation**: Runs as a background service, ensuring ongoing surveillance even after system reboots.
- 👤 **User Logging**: Captures user details and IP addresses for accountability and traceability.
- ⚙️ **Systemd Integration**: Simplifies deployment with automatic service management for Linux systems.

---

## Prerequisites

- Python 3.x  
- `pip`  
- `systemd`: to execute the script automatically  
- Gmail (SMTP): for sending alerts  
- `auditd`: for detecting file accesses  

---

## Installation and Usage


### 1. Install `auditd`

```bash
sudo apt update
sudo apt install auditd
sudo systemctl enable auditd
sudo systemctl start auditd
```

### 2. Install Git and Python3

```bash
sudo apt install -y git python3 python3-pip
```

### 3. Clone the Project

```bash
cd ~/Documents
git clone https://github.com/fedelm8/TFG2
```

### 4. Create a Sensitive File to Monitor

```bash
sudo nano tarjetas_bancarias.txt
sudo chmod 644 tarjetas_bancarias.txt
```

### 5. Add Temporary Audit Rule for Testing

```bash
sudo auditctl -w /home/osboxes/Documents/tarjetas_bancarias.txt -p r -k acceso_tarjetas
```

### 6. Make Audit Rule Permanent

```bash
sudo nano /etc/audit/rules.d/monitor.rules
```

**File content:**
```
-w /home/osboxes/Documents/tarjetas_bancarias.txt -p r -k acceso_tarjetas
```

```bash
sudo augenrules --load
sudo systemctl restart auditd
sudo auditctl -l  # Verify rule
```

### 7. Set Up Gmail

- Go to: https://myaccount.google.com/security  
- Create an App Password: https://myaccount.google.com/apppasswords  
- Name: `monitor_tarjetas`  
- Copy the generated key (e.g., `grkyy nyhf uxec iing`)

### 8. Edit Script with App Password

```bash
sudo nano monitor_tarjetas.py
```

### 9. Save Script Securely

```bash
sudo mkdir -p /opt/monitor_archivo
sudo cp monitor_tarjetas.py /opt/monitor_archivo/
sudo chmod 700 /opt/monitor_archivo/monitor_tarjetas.py
sudo chown root:root /opt/monitor_archivo/monitor_tarjetas.py
```

### 10. Turn Script Into a systemd Service

```bash
sudo nano /etc/systemd/system/monitor_tarjetas.service
```

**Service content:**
```ini
[Unit]
Description=Monitor de accesos a archivo sensible
After=network.target auditd.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/monitor_archivo/monitor_tarjetas.py
Restart=on-failure
User=root
Group=root

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable monitor_tarjetas.service
sudo systemctl start monitor_tarjetas.service
```

### 11. Verify Service Status

```bash
sudo systemctl status monitor_tarjetas.service
```

---

