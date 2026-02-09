from flask import Flask, render_template_string, request
import subprocess
import json

app = Flask(__name__)

# -----------------------------------
# Run Kubescape Scan Function
# -----------------------------------

def run_kubescape_scan(framework=None):
    try:
        if framework:
            cmd = ["kubescape", "scan", "framework", framework, "--format", "json"]
        else:
            cmd = ["kubescape", "scan", "--format", "json"]

        print(f"[DEBUG] Running command: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        print(f"[DEBUG] Return code: {result.returncode}")

        if result.returncode != 0:
            return {"error": result.stderr}

        return json.loads(result.stdout)

    except Exception as e:
        return {"error": str(e)}


# -----------------------------------
# Dashboard Route
# -----------------------------------

@app.route("/", methods=["GET", "POST"])
def dashboard():

    framework = request.form.get("framework")

    passed = 0
    failed = 0
    warnings = 0
    controls = []
    error = None

    if request.method == "POST":

        data = run_kubescape_scan(framework)

        if "error" in data:
            error = data["error"]

        else:
            # -------- Summary Parsing --------
            summary = data.get("summary", {})

            passed = summary.get("totalPassed", 0)
            failed = summary.get("totalFailed", 0)
            warnings = summary.get("totalSkipped", 0)

            # -------- Control Parsing --------
            for r in data.get("results", [])[:10]:
                controls.append({
                    "name": r.get("name"),
                    "status": r.get("status"),
                    "severity": r.get("severity", "N/A")
                })

    return render_template_string(
        TEMPLATE,
        passed=passed,
        failed=failed,
        warnings=warnings,
        controls=controls,
        framework=framework or "Full Scan",
        error=error
    )


# -----------------------------------
# HTML Dashboard UI
# -----------------------------------

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubescape Security Dashboard</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg,#020617,#0f172a,#020617);
            color: white;
            padding: 20px;
        }

        h1 {
            color: #38bdf8;
            text-align: center;
        }

        .card {
            background: #1e293b;
            padding: 20px;
            margin: 15px 0;
            border-radius: 12px;
            box-shadow: 0 0 15px black;
        }

        .btn {
            padding: 10px 18px;
            margin: 5px;
            background: #2563eb;
            border: none;
            color: white;
            cursor: pointer;
            border-radius: 8px;
            font-weight: bold;
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

        .summary-box {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }

        .metric {
            background: #020617;
            padding: 15px;
            border-radius: 10px;
            flex: 1;
            text-align: center;
            box-shadow: 0 0 10px black;
        }

        .error {
            color: #f87171;
            font-weight: bold;
        }
    </style>
</head>

<body>

<h1>🛡️ Kubescape Security Dashboard</h1>

<!-- Scan Buttons -->
<div class="card">
    <form method="post">
        <button class="btn" name="framework" value="">Full Scan</button>
        <button class="btn" name="framework" value="nsa">Run NSA</button>
        <button class="btn" name="framework" value="mitre">Run MITRE</button>
        <button class="btn" name="framework" value="cis-v1.23">Run CIS</button>
    </form>
</div>

<!-- Error -->
{% if error %}
<div class="card">
    <p class="error">Error: {{ error }}</p>
</div>
{% endif %}

<!-- Summary -->
<div class="card">
    <h2>Framework: {{ framework }}</h2>

    <div class="summary-box">
        <div class="metric">
            <h3>✅ Passed</h3>
            <p>{{ passed }}</p>
        </div>

        <div class="metric">
            <h3>❌ Failed</h3>
            <p>{{ failed }}</p>
        </div>

        <div class="metric">
            <h3>⚠️ Warnings</h3>
            <p>{{ warnings }}</p>
        </div>
    </div>
</div>

<!-- Controls Table -->
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
            <td>{{ c.name }}</td>
            <td>{{ c.status }}</td>
            <td>{{ c.severity }}</td>
        </tr>
        {% endfor %}
    </table>
</div>

</body>
</html>
"""


# -----------------------------------
# Run Flask App
# -----------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
