from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import paramiko
import threading

app = Flask(__name__)
app.secret_key = "supersecretkey"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        host = request.form['host']
        username = request.form['username']
        password = request.form.get('password')
        key_file = request.form.get('key_file')

        return render_template('ssh_terminal.html',
                               host=host,
                               username=username,
                               password=password,
                               key_file=key_file)
    return render_template('index.html')

@socketio.on('connect_ssh')
def handle_connect_ssh(data):
    host = data['host']
    username = data['username']
    password = data.get('password')
    key_file = data.get('key_file')

    def ssh_thread():
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if key_file:
                pkey = paramiko.RSAKey.from_private_key_file(key_file)
                ssh.connect(host, username=username, pkey=pkey)
            else:
                ssh.connect(host, username=username, password=password)
            chan = ssh.invoke_shell()
            while True:
                data = chan.recv(1024).decode('utf-8')
                if not data:
                    break
                emit('ssh_output', {'output': data})
        except Exception as e:
            emit('ssh_output', {'output': f"Error: {str(e)}"})

    threading.Thread(target=ssh_thread).start()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
