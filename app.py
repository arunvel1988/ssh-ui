import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO
import paramiko
import os
import re

app = Flask(__name__)
app.secret_key = "supersecretkey"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

channels = {}
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        connection_type = request.form['connection_type']
        host = request.form['host']
        username = request.form['username']
        password = request.form.get('password', '')
        key_file = request.form.get('key_file', '')

        if connection_type == "ssh":
            return render_template('ssh_terminal.html',
                                   host=host,
                                   username=username,
                                   password=password,
                                   key_file=key_file)
        elif connection_type == "rdp":
            return render_template('rdp_terminal.html',
                                   host=host,
                                   username=username,
                                   password=password)
    return render_template('index.html')


# ===== SSH HANDLING =====
@socketio.on('connect_ssh')
def handle_connect_ssh(data):
    sid = request.sid
    host = data.get('host')
    username = data.get('username')
    password = data.get('password', '')
    key_file = data.get('key_file', '')

    def ssh_worker(sid, host, username, password, key_file):
        ssh = None
        chan = None
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs = dict(hostname=host, username=username, timeout=10)
            if password:
                connect_kwargs.update({
                    'password': password,
                    'allow_agent': False,
                    'look_for_keys': False
                })
            elif key_file:
                if not os.path.exists(key_file):
                    socketio.emit('ssh_output', {'output': f"Error: key file does not exist: {key_file}\r\n"}, to=sid)
                    return
                try:
                    pkey = paramiko.RSAKey.from_private_key_file(key_file)
                except Exception:
                    try:
                        pkey = paramiko.Ed25519Key.from_private_key_file(key_file)
                    except Exception:
                        socketio.emit('ssh_output', {'output': "Error: Failed to load key file\r\n"}, to=sid)
                        return
                connect_kwargs.update({'pkey': pkey, 'allow_agent': False, 'look_for_keys': False})
            else:
                socketio.emit('ssh_output', {'output': 'Error: No authentication provided.\r\n'}, to=sid)
                return

            ssh.connect(**connect_kwargs)

            transport = ssh.get_transport()
            chan = transport.open_session()
            chan.get_pty(term='xterm', width=80, height=24)
            chan.invoke_shell()
            channels[sid] = chan

            socketio.emit('ssh_output', {'output': f"*** Connected to {host} as {username} ***\r\n"}, to=sid)

            while True:
                if chan.recv_ready():
                    data = chan.recv(4096)
                    if not data:
                        break
                    text = data.decode('utf-8', errors='replace')
                    clean_text = ansi_escape.sub('', text)
                    socketio.emit('ssh_output', {'output': clean_text}, to=sid)
                if chan.exit_status_ready() and not chan.recv_ready():
                    break
                eventlet.sleep(0.01)

        except Exception as e:
            socketio.emit('ssh_output', {'output': f"Error: {str(e)}\r\n"}, to=sid)
        finally:
            channels.pop(sid, None)
            try:
                if chan:
                    chan.close()
            except Exception:
                pass
            try:
                if ssh:
                    ssh.close()
            except Exception:
                pass
            socketio.emit('ssh_output', {'output': '*** SSH session closed ***\r\n'}, to=sid)

    socketio.start_background_task(ssh_worker, sid, host, username, password, key_file)


@socketio.on('ssh_input')
def handle_ssh_input(data):
    sid = request.sid
    payload = data.get('input', '')
    chan = channels.get(sid)
    if not chan:
        socketio.emit('ssh_output', {'output': 'Error: No SSH channel.\r\n'}, to=sid)
        return
    try:
        chan.send(payload if isinstance(payload, str) else str(payload))
    except Exception as e:
        socketio.emit('ssh_output', {'output': f"Error sending input: {e}\r\n"}, to=sid)

@socketio.on('resize')
def handle_resize(data):
    sid = request.sid
    cols = int(data.get('cols', 80))
    rows = int(data.get('rows', 24))
    chan = channels.get(sid)
    if chan:
        try:
            chan.resize_pty(width=cols, height=rows)
        except Exception as e:
            socketio.emit('ssh_output', {'output': f"Error resizing pty: {e}\r\n"}, to=sid)

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    chan = channels.pop(sid, None)
    if chan:
        try:
            chan.close()
        except Exception:
            pass

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
