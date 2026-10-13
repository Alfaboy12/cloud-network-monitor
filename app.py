import os
import csv
import io
import socket
import sqlite3
import time
from functools import wraps
from flask import (
    Flask, request, redirect, url_for,
    session, jsonify, Response, render_template_string
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

DATABASE = os.environ.get("DATABASE_PATH", "monitor.db")
USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")

def get_db():
    connection = sqlite3.connect(DATABASE, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    folder = os.path.dirname(DATABASE)
    if folder:
        os.makedirs(folder, exist_ok=True)

    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL DEFAULT 443
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER,
                server_name TEXT,
                host TEXT,
                status TEXT,
                response_ms REAL,
                checked_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        count = db.execute(
            "SELECT COUNT(*) FROM servers"
        ).fetchone()[0]

        if count == 0:
            db.execute(
                "INSERT INTO servers (name, host, port) VALUES (?, ?, ?)",
                ("Google", "google.com", 443)
            )

init_db()


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return function(*args, **kwargs)
    return wrapper


LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Network Monitor Login</title>
<style>
body{font-family:Arial;background:#101827;color:white;
display:flex;justify-content:center;align-items:center;
min-height:90vh;margin:0}
.box{background:#1e293b;padding:25px;border-radius:12px;
width:85%;max-width:350px}
input,button{box-sizing:border-box;width:100%;padding:12px;
margin:8px 0;border-radius:6px;border:0}
button{background:#16a34a;color:white;font-weight:bold}
</style>
</head>
<body>
<div class="box">
<h2>Network Monitor</h2>
<p>Sign in to access your dashboard.</p>
{% if error %}<p style="color:#f87171">{{ error }}</p>{% endif %}
<form method="post">
<input name="username" placeholder="Username" required>
<input name="password" type="password" placeholder="Password" required>
<button type="submit">Login</button>
</form>
</div>
</body>
</html>
"""


DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cloud Network Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{font-family:Arial;background:#101827;color:#f8fafc;
margin:0;padding:15px}
.container{max-width:1000px;margin:auto}
.card{background:#1e293b;padding:16px;margin:12px 0;
border-radius:10px}
input,button{padding:10px;margin:4px;border-radius:5px;border:0}
button,.btn{background:#16a34a;color:white;padding:10px;
border:0;border-radius:5px;text-decoration:none;cursor:pointer}
.delete{background:#dc2626}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:9px;border-bottom:1px solid #475569;text-align:left}
.tablewrap{overflow-x:auto}
.good{color:#4ade80}.bad{color:#f87171}
.small{color:#cbd5e1;font-size:13px}
</style>
</head>
<body>
<div class="container">
<h1>☁️ Cloud Network Monitor</h1>
<p>Network Performance Monitoring and Analysis</p>
<p>Welcome, {{ username }}!
<a class="btn" href="/logout">Logout</a>
<a class="btn" href="/export">Download CSV Report</a></p>

<div class="card">
<h2>Add a Server</h2>
<form action="/servers/add" method="post">
<input name="name" placeholder="Server name" required>
<input name="host" placeholder="Hostname (e.g. google.com)" required>
<input name="port" type="number" value="443" min="1" max="65535" required>
<button type="submit">Add Server</button>
</form>
<p class="small">Only add servers you own or have permission to monitor.</p>
</div>

<div class="card">
<h2>Server Status</h2>
<p class="small">Monitoring checks run automatically every 15 seconds while this dashboard is open.</p>
<div class="tablewrap">
<table>
<thead><tr><th>Server</th><th>Host</th><th>Status</th>
<th>Response Time</th><th>Action</th></tr></thead>
<tbody id="servers"></tbody>
</table>
</div>
</div>

<div class="card">
<h2>Performance Summary</h2>
<p id="summary">Loading monitoring data...</p>
<canvas id="chart"></canvas>
</div>

<div class="card">
<h2>Recent Monitoring History</h2>
<div class="tablewrap">
<table>
<thead><tr><th>Time</th><th>Server</th><th>Status</th>
<th>Response (ms)</th></tr></thead>
<tbody id="history"></tbody>
</table>
</div>
</div>
</div>

<script>
let chart;

async function refreshData(){
    try {
        const response = await fetch('/api/monitor', {cache:'no-store'});
        if (!response.ok) return;
        const data = await response.json();

        const serverBody = document.getElementById('servers');
        serverBody.innerHTML = '';

        data.servers.forEach(s => {
            const row = document.createElement('tr');
            const statusClass = s.status === 'ONLINE' ? 'good' : 'bad';

            [s.name, s.host, s.status,
             s.response_ms === null ? 'N/A' : s.response_ms + ' ms'
            ].forEach((value, index) => {
                const cell = document.createElement('td');
                cell.textContent = value;
                if (index === 2) cell.className = statusClass;
                row.appendChild(cell);
            });

            const actionCell = document.createElement('td');
            const form = document.createElement('form');
            form.method = 'post';
            form.action = '/servers/delete/' + s.id;

            const button = document.createElement('button');
            button.type = 'submit';
            button.className = 'delete';
            button.textContent = 'Remove';
            button.onclick = (event) => {
                if (!confirm('Remove this server?')) event.preventDefault();
            };

            form.appendChild(button);
            actionCell.appendChild(form);
            row.appendChild(actionCell);
            serverBody.appendChild(row);
        });

        const historyBody = document.getElementById('history');
        historyBody.innerHTML = '';

        data.history.forEach(r => {
            const row = document.createElement('tr');
            [r.checked_at, r.server_name, r.status,
             r.response_ms === null ? 'N/A' : r.response_ms
            ].forEach(value => {
                const cell = document.createElement('td');
                cell.textContent = value ?? '';
                row.appendChild(cell);
            });
            historyBody.appendChild(row);
        });

        document.getElementById('summary').textContent =
            'Servers: ' + data.servers.length +
            ' | Online: ' + data.online +
            ' | Offline: ' + (data.servers.length - data.online) +
            ' | Average response time: ' +
            (data.average_ms === null ? 'N/A' : data.average_ms + ' ms');

        const labels = data.history.slice().reverse().map(r => r.checked_at);
        const values = data.history.slice().reverse().map(r => r.response_ms);

        if (chart) chart.destroy();

        chart = new Chart(document.getElementById('chart'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Response time (ms)',
                    data: values,
                    spanGaps: false,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                scales: {y: {beginAtZero: true}}
            }
        });
    } catch (error) {
        document.getElementById('summary').textContent =
            'Unable to load monitoring data. Please refresh.';
    }
}

refreshData();
setInterval(refreshData, 15000);
</script>
</body>
</html>
"""


@app.route("/")
@login_required
def dashboard():
    return render_template_string(
        DASHBOARD,
        username=session.get("username", USERNAME)
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "")
        password = request.form.get("password", "")

        if user == USERNAME and password == PASSWORD:
            session.clear()
            session["logged_in"] = True
            session["username"] = user
            return redirect(url_for("dashboard"))

        return render_template_string(
            LOGIN_PAGE, error="Incorrect username or password."
        )

    return render_template_string(LOGIN_PAGE, error=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/servers/add", methods=["POST"])
@login_required
def add_server():
    name = request.form.get("name", "").strip()
    host = request.form.get("host", "").strip()
    port_text = request.form.get("port", "443").strip()

    try:
        port = int(port_text)
        if not name or not host or not (1 <= port <= 65535):
            raise ValueError()
        if len(name) > 100 or len(host) > 253:
            raise ValueError()
    except ValueError:
        return "Invalid server name, hostname, or port.", 400

    with get_db() as db:
        db.execute(
            "INSERT INTO servers (name, host, port) VALUES (?, ?, ?)",
            (name, host, port)
        )

    return redirect(url_for("dashboard"))


@app.route("/servers/delete/<int:server_id>", methods=["POST"])
@login_required
def delete_server(server_id):
    with get_db() as db:
        db.execute("DELETE FROM servers WHERE id = ?", (server_id,))
    return redirect(url_for("dashboard"))


def check_server(host, port):
    start = time.perf_counter()

    try:
        with socket.create_connection((host, port), timeout=3):
            elapsed = round((time.perf_counter() - start) * 1000, 2)
        return "ONLINE", elapsed
    except (OSError, ValueError):
        return "OFFLINE", None


@app.route("/api/monitor")
@login_required
def monitor_data():
    with get_db() as db:
        servers = db.execute(
            "SELECT * FROM servers ORDER BY id"
        ).fetchall()

        current_servers = []
        response_times = []

        for server in servers:
            status, response_ms = check_server(
                server["host"], server["port"]
            )

            db.execute("""
                INSERT INTO readings
                (server_id, server_name, host, status, response_ms)
                VALUES (?, ?, ?, ?, ?)
            """, (
                server["id"], server["name"], server["host"],
                status, response_ms
            ))

            current_servers.append({
                "id": server["id"],
                "name": server["name"],
                "host": server["host"],
                "port": server["port"],
                "status": status,
                "response_ms": response_ms
            })

            if response_ms is not None:
                response_times.append(response_ms)

        history = db.execute("""
            SELECT server_name, host, status, response_ms, checked_at
            FROM readings
            ORDER BY id DESC LIMIT 50
        """).fetchall()

    average = (
        round(sum(response_times) / len(response_times), 2)
        if response_times else None
    )

    return jsonify({
        "servers": current_servers,
        "history": [dict(row) for row in history],
        "online": sum(1 for s in current_servers if s["status"] == "ONLINE"),
        "average_ms": average
    })


@app.route("/export")
@login_required
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Time", "Server Name", "Hostname",
        "Status", "Response Time (ms)"
    ])

    with get_db() as db:
        rows = db.execute("""
            SELECT checked_at, server_name, host, status, response_ms
            FROM readings
            ORDER BY id DESC
        """).fetchall()

    for row in rows:
        writer.writerow([
            row["checked_at"], row["server_name"], row["host"],
            row["status"], row["response_ms"]
        ])

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=network_monitor_report.csv"
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
