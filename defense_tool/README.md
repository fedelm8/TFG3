
# 🛡️ Defense_tool

*Guard your files. Secure your system.*

![Last Commit](https://img.shields.io/badge/last%20commit-today-brightgreen)
![Python](https://img.shields.io/badge/python-100%25-blue)
![Languages](https://img.shields.io/badge/languages-1-blue)

_Built with the tools and technologies:_

![Python](https://img.shields.io/badge/-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation and Usage](#installation-and-usage)

---

## Overview

**defense_tool** is a powerful and proactive monitoring solution designed to protect sensitive files by detecting unauthorized access attempts in real-time. It helps ensure system security by immediately alerting administrators and blocking suspicious actions.

### Why defense_tool?

The core features include:

- 🔐 **Real-time Monitoring**: Instantly detects unauthorized access attempts to sensitive files such as /etc/shadow, /etc/passwd, /etc/sudoers.
- 🚨 **Alerts**: Automatically notifies administrators through email when a sensitive file is accessed, providing detailed information about the event, such as the user, IP address and the file path.
- 🔄 **Continuous Operation**: Runs as a background service, ensuring that monitoring continues even after system reboots or restarts, providing uninterrupted protection.
- 👤 **User Logging**: Records detailed logs of the access events, capturing user information and IP addresses for accountability, traceability, and audit purposes.
- ⚙️ **Systemd Integration**: Simplifies deployment and management by seamlessly integrating with systemd for automatic startup and easy service management on Linux systems.

---

## Prerequisites

- Python 3.x  
- `pip`  
- `systemd`: to execute the script automatically  
- Gmail (SMTP): for sending alerts  
- `auditd`: for detecting file accesses  
- `psutil`: for checking the start time

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

### 3. Install psutil

```bash
sudo apt-get install python3-psutil
```



### 4. Clone the Project

```bash
cd ~/Documents
git clone https://github.com/fedelm8/TFG3
```


### 5. Add Temporary Audit Rule for Testing

```bash
sudo auditctl -w /etc/shadow -p r -k clave_defensa
```

### 6. Make Audit Rule Permanent

```bash
sudo nano /etc/audit/rules.d/defense.rules
```

**File content:**
```
 -w /etc/shadow -p r -k clave_defensa
```

```bash
sudo augenrules --load
sudo systemctl restart auditd
sudo auditctl -l  # Verify rule
```

### 7. Set Up Gmail

- Go to: https://myaccount.google.com/security  
- Create an App Password: https://myaccount.google.com/apppasswords  
- Name: `defense_system`  
- Copy the generated key (e.g., `grkyy nyhf uxec iing`)

### 8. Edit Script with App Password

```bash
sudo nano defense_system.py
```

### 9. Save Script Securely

```bash
sudo mkdir -p /opt/defense_archivo
sudo cp defense_system.py /opt/defense_archivo/
sudo chmod 700 /opt/defense_archivo/defense_system.py
sudo chown root:root /opt/defense_archivo/defense_system.py
```

### 10. Turn Script Into a systemd Service

```bash
sudo nano /etc/systemd/system/defense_system.service
```

**Service content:**
```ini
[Unit]
Description=Defensa de archivos sensibles.
After=network.target auditd.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/defense_archivo/defense_system.py
Restart=on-failure
User=root
Group=root

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable defense_system.service
sudo systemctl start defense_system.service
```

### 11. Verify Service Status

```bash
sudo systemctl status defense_system.service
```

---

