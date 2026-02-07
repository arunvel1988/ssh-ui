from flask import Flask, render_template_string
import subprocess

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubernetes Audit Dashboard</title>

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
            border-radius: 12px;
            box-shadow: 0 6px 14px rgba(0,0,0,0.25);
        }

        pre {
            background: #000;
            color: #00ff9c;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            max-height: 600px;
        }

        button {
            background: #ffd166;
            border: none;
            padding: 10px 18px;
            font-size: 16px;
            border-radius: 6px;
            cursor: pointer;
            margin-bottom: 15px;
        }

        button:hover {
            background: #ffb703;
        }
    </style>
</head>

<body>

<header>
    <h1>Kube‑Bench Audit Dashboard</h1>
    <p>Control Plane Security Benchmark Output</p>
</header>

<div class="container">

    <div class="card">
        <form method="get">
            <button type="submit">Run kube-bench</button>
        </form>

        <h3>Audit Output</h3>

        <pre>{{ output }}</pre>
    </div>

</div>

</body>
</html>
"""


def get_kube_bench_output():
    try:
        # Get kube-bench pod name
        pod_cmd = "kubectl get pods -o name | grep kube-bench | head -n 1"
        pod_name = subprocess.check_output(pod_cmd, shell=True).decode().strip()

        if not pod_name:
            return "No kube-bench pod found. Run the job first."

        # Fetch logs
        log_cmd = f"kubectl logs {pod_name}"
        logs = subprocess.check_output(log_cmd, shell=True).decode()

        return logs

    except subprocess.CalledProcessError as e:
        return f"Error fetching kube-bench logs: {str(e)}"


@app.route("/", methods=["GET"])
def dashboard():
    output = get_kube_bench_output()
    return render_template_string(HTML_TEMPLATE, output=output)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
