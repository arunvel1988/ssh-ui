from flask import Flask, render_template_string, request
import subprocess
import json

app = Flask(__name__)

# -----------------------------
# Helper function to run scans
# -----------------------------

def run_kubescape_scan(framework=None):
    try:
        if framework:
            cmd = ["kubescape", "scan", "framework", framework, "--format", "json"]
        else:
            cmd = ["kubescape", "scan", "--format", "json"]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return {"error": result.stderr}

        return json.loads(result.stdout)

    except Exception as e:
        return {"error": str(e)}


# -----------------------------
# Dashboard Route
# -----------------------------

@app.route("/", methods=["GET", "POST"])
def dashboard():
    framework = request.form.get("framework")

    data = run_kubescape_scan(framework)

    summary = {}
    controls = []

    if "error" not in data:
        try:
            summary = data.get("summaryDetails", {})
            controls = data.get("controlDetails", [])[:10]  # show top 10
        except:
            pass

    return render_template_string(TEMPLATE,
                                  summary=summary,
                                  controls=controls,
                                  framework=framework or "All")


# -----------------------------
# HTML Template
# -----------------------------

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubescape Security Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: white;
            padding: 20px;
        }
        h1 {
            color: #38bdf8;
        }
        .card {
            background: #1e293b;
            padding: 20px;
            margin: 10px 0;
            border-radius: 10px;
            box-shadow: 0 0 10px black;
        }
        .btn {
            padding: 10px 15px;
            margin: 5px;
            background: #2563eb;
            border: none;
            color: white;
            cursor: pointer;
            border-radius: 6px;
        }
        .btn:hover {
            background: #1d4ed8;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 10px;
            border-bottom: 1px solid #334155;
            text-align: left;
        }
        th {
            color: #38bdf8;
        }
    </style>
</head>
<body>

<h1>🛡️ Kubescape Security Dashboard</h1>

<form method="post">
    <button class="btn" name="framework" value="">Full Scan</button>
    <button class="btn" name="framework" value="nsa">Run NSA</button>
    <button class="btn" name="framework" value="mitre">Run MITRE</button>
    <button class="btn" name="framework" value="cis-v1.23">Run CIS</button>
</form>

<div class="card">
    <h2>Framework: {{ framework }}</h2>
    <p><b>Passed:</b> {{ summary.get('passed', 'N/A') }}</p>
    <p><b>Failed:</b> {{ summary.get('failed', 'N/A') }}</p>
    <p><b>Warnings:</b> {{ summary.get('warnings', 'N/A') }}</p>
</div>

<div class="card">
    <h2>Top Security Controls</h2>
    <table>
        <tr>
            <th>Control Name</th>
            <th>Status</th>
            <th>Severity</th>
        </tr>
        {% for c in controls %}
        <tr>
            <td>{{ c.get('name') }}</td>
            <td>{{ c.get('status') }}</td>
            <td>{{ c.get('severity') }}</td>
        </tr>
        {% endfor %}
    </table>
</div>

</body>
</html>
"""


# -----------------------------
# Run App
# -----------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
