import os
import csv
import io
import socket
import sqlite3
import time
from flask import Flask, request, redirect, jsonify, Response, render_template_string

app = Flask(__name__)

# Database location
DATABASE = os.environ.get("DATABASE_PATH", "monitor.db")


def get_db():
    db = sqlite3.connect(DATABASE, timeout=10)
    db.row_factory = sqlite3.Row
    return db


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


def check_server(host, port):
    start = time.perf_counter()

    try:
        with socket.create_connection((host, port), timeout=3):
            elapsed = round(
                (time.perf_counter() - start) * 1000, 2
            )
        return "ONLINE", elapsed
    except (OSError, ValueError):
        return "OFFLINE", None


DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cloud Network Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body {
    font-family: Arial, sans-serif;
    background: #101827;
    color: white;
    padding: 15px;
    margin: 0;
}
.container { max-width: 1000px; margin: auto; }
.card {
    background: #1e293b;
    padding: 16px;
    margin: 15px 0;
    border-radius: 10px;
}
input, button {
    padding: 11px;
    margin: 5px 2px;
    border: 0;
    border-radius: 5px;
}
button, .btn {
    background: #16a34a;
    color: white;
    cursor: pointer;
    padding: 10px;
    border-radius: 5px;
    border: 0;
    text-decoration: none;
    display: inline-block;
}
.delete { background: #dc2626; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td {
    padding: 10px;
    border-bottom: 1px solid #475569;
    text-align: left;
}
.tablewrap { overflow-x: auto; }
.good { color: #4ade80; }
.bad { color: #f87171; }
.small { color: #cbd5e1; font-size: 13px; }
</style>
</head>

<body>
<div class="container">

<h1>☁️ Cloud Network Monitor</h1>
<p>Cloud-Based Network Performance Monitoring and Analysis</p>

<div class="card">
<h2>Add a Server</h2>
<form action="/servers/add" method="post">
<input name="name" placeholder="Server name" required>
<input name="host" placeholder="Hostname e.g. google.com" required>
<input name="port" type="number" value="443" min="1" max="65535" required>
<button type="submit">Add Server</button>
</form>
<p class="small">Only monitor servers you own or have permission to test.</p>
</div>

<div class="card">
<h2>Server Status</h2>
<p id="lastcheck" class="small">Loading server information...</p>
<div class="tablewrap">
<table>
<thead>
<tr>
<th>Name</th><th>Host</th><th>Status</th>
<th>Response Time</th><th>Action</th>
</tr>
</thead>
<tbody id="servers"></tbody>
</table>
</div>
</div>

<div class="card">
<h2>Performance Summary</h2>
<p id="summary">Loading...</p>
<canvas id="chart"></canvas>
</div>

<div class="card">
<h2>Recent Monitoring History</h2>
<p><a class="btn" href="/export">Download CSV Report</a></p>
<div class="tablewrap">
<table>
<thead>
<tr>
<th>Time</th><th>Server</th><th>Host</th>
<th>Status</th><th>Response (ms)</th>
</tr>
</thead>
<tbody id="history"></tbody>
</table>
</div>
</div>

</div>

<script>
let chart = null;

async function refreshData() {
    try {
        const response = await fetch('/api/monitor', {cache: 'no-store'});
        if (!response.ok) throw new Error('Request failed');

        const data = await response.json();

        const serverBody = document.getElementById('servers');
        serverBody.innerHTML = '';

        data.servers.forEach(server => {
            const row = document.createElement('tr');

            const values = [
                server.name,
                server.host,
                server.status,
                server.response_ms === null ? 'N/A' : server.response_ms + ' ms'
            ];

            values.forEach((value, index) => {
                const cell = document.createElement('td');
                cell.textContent = value;
                if (index === 2) {
                    cell.className = server.status === 'ONLINE' ? 'good' : 'bad';
                }
                row.appendChild(cell);
            });

            const actionCell = document.createElement('td');
            const form = document.createElement('form');
            form.method = 'post';
            form.action = '/servers/delete/' + server.id;

            const button = document.createElement('button');
            button.className = 'delete';
            button.textContent = 'Remove';
            button.onclick = function(event) {
                if (!confirm('Remove this server?')) event.preventDefault();
            };

            form.appendChild(button);
            actionCell.appendChild(form);
            row.appendChild(actionCell);
            serverBody.appendChild(row);
        });

        const historyBody = document.getElementById('history');
        historyBody.innerHTML = '';

        data.history.forEach(item => {
            const row = document.createElement('tr');
            [
                item.checked_at,
                item.server_name,
                item.host,
                item.status,
                item.response_ms === null ? 'N/A' : item.response_ms
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

        document.getElementById('lastcheck').textContent =
            'Last checked: ' + new Date().toLocaleTimeString() +
            ' | Updates every 15 seconds while this page is open';

        if (chart) chart.destroy();

        chart = new Chart(document.getElementById('chart'), {
            type: 'line',
            data: {
                labels: data.history.slice().reverse().map(x => x.checked_at),
                datasets: [{
                    label: 'Response Time (ms)',
                    data: data.history.slice().reverse().map(x => x.response_ms),
                    spanGaps: false,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                scales: { y: { beginAtZero: true } }
            }
        });

    } catch (error) {
        document.getElementById('summary').textContent =
            'Unable to load monitoring data. Refresh the page.';
    }
}

refreshData();
setInterval(refreshData, 15000);
</script>

</body>
</html>
"""


@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD)


@app.route("/servers/add", methods=["POST"])
def add_server():
    name = request.form.get("name", "").strip()
    host = request.form.get("host", "").strip()
    port_text = request.form.get("port", "443").strip()

    try:
        port = int(port_text)
        if not name or not host or not (1 <= port <= 65535):
            raise ValueError
        if len(name) > 100 or len(host) > 253:
            raise ValueError
    except ValueError:
        return "Please enter a valid name, hostname and port.", 400

    with get_db() as db:
        db.execute(
            "INSERT INTO servers (name, host, port) VALUES (?, ?, ?)",
            (name, host, port)
        )

    return redirect("/")


@app.route("/servers/delete/<int:server_id>", methods=["POST"])
def delete_server(server_id):
    with get_db() as db:
        db.execute("DELETE FROM servers WHERE id = ?", (server_id,))
    return redirect("/")


@app.route("/api/monitor")
def monitor_data():
    current_servers = []
    response_times = []

    with get_db() as db:
        servers = db.execute(
            "SELECT * FROM servers ORDER BY id"
        ).fetchall()

        for server in servers:
            status, response_ms = check_server(
                server["host"], server["port"]
            )

            db.execute("""
                INSERT INTO readings
                (server_name, host, status, response_ms)
                VALUES (?, ?, ?, ?)
            """, (
                server["name"], server["host"], status, response_ms
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
        "online": sum(
            1 for server in current_servers
            if server["status"] == "ONLINE"
        ),
        "average_ms": average
    })


@app.route("/export")
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
            row["checked_at"],
            row["server_name"],
            row["host"],
            row["status"],
            row["response_ms"]
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
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
