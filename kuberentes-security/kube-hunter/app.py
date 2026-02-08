from flask import Flask, render_template_string
import subprocess
import re

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Kube‑Hunter Security Dashboard</title>

    <style>
        body {
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: linear-gradient(120deg,#0b3d91,#1e5ed6);
            color: white;
        }

        header {
            padding: 20px;
            text-align: center;
            background: rgba(0,0,0,0.3);
        }

        .container {
            padding: 30px 60px;
        }

        .card {
            background: linear-gradient(145deg,#0f4cc9,#0b3d91);
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 12px;
            box-shadow: 0 6px 14px rgba(0,0,0,0.25);
        }

        .vuln {
            background: rgba(255,82,82,0.15);
            border-left: 6px solid #ff5252;
            padding: 12px;
            margin: 10px 0;
            font-size: 16px;
        }

        pre {
            background: #000;
            color: #00ff9c;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            max-height: 500px;
        }

        button {
            background: #ffd166;
            border: none;
            padding: 10px 18px;
            font-size: 16px;
            border-radius: 6px;
            cursor: pointer;
        }

        button:hover {
            background: #ffb703;
        }
    </style>
</head>

<body>

<header>
    <h1>Kube‑Hunter Vulnerability Dashboard</h1>
    <p>Kubernetes Penetration Testing Findings</p>
</header>

<div class="container">

    <div class="card">
        <form method="get">
            <button type="submit">Refresh Scan Output</button>
        </form>
    </div>

    <div class="card">
        <h2>Discovered Vulnerabilities</h2>
        {% for v in vulns %}
            <div class="vuln">{{ v }}</div>
        {% endfor %}
    </div>

    <div class="card">
        <h2>Raw kube‑hunter Logs</h2>
        <pre>{{ logs }}</pre>
    </div>

</div>

</body>
</html>
"""


def get_hunter_logs():
    try:
        # Get kube-hunter pod name
        cmd = "kubectl get pods -o name | grep kube-hunter | head -n 1"
        pod = subprocess.check_output(cmd, shell=True).decode().strip()

        if not pod:
            return "No kube-hunter pod found.", []

        # Fetch logs
        logs = subprocess.check_output(f"kubectl logs {pod}", shell=True).decode()

        # Extract vulnerabilities
        vulns = re.findall(r'Found vulnerability "(.*?)"', logs)

        return logs, vulns

    except Exception as e:
        return str(e), []


@app.route("/")
def dashboard():
    logs, vulns = get_hunter_logs()
    return render_template_string(HTML, logs=logs, vulns=vulns)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
