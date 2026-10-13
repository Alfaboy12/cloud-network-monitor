import os
import time
import sqlite3
import csv
import io
from datetime import datetime
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from flask import Flask, request, redirect, url_for, jsonify, Response, render_template_string

app = Flask(__name__)

DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitor.db")
)


def connect_db():
    db = sqlite3.connect(DB_PATH, timeout=15)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with connect_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER,
                server_name TEXT NOT NULL,
                address TEXT NOT NULL,
                status TEXT NOT NULL,
                response_ms REAL,
                checked_at TEXT NOT NULL
            )
        """)

        count = db.execute(
            "SELECT COUNT(*) FROM servers"
        ).fetchone()[0]

        if count == 0:
            db.execute(
                "INSERT INTO servers (name, address) VALUES (?, ?)",
                ("Google", "https://www.google.com")
            )


def list_servers():
    with connect_db() as db:
        return db.execute(
            "SELECT * FROM servers ORDER BY id"
        ).fetchall()


def check_server(address):
    start = time.perf_counter()

    try:
        address = address.strip()
        parsed = urlparse(address)

        if parsed.scheme in ("http", "https") and parsed.hostname:
            req = Request(
                address,
                headers={"User-Agent": "CloudNetworkMonitor/1.0"}
            )

            with urlopen(req, timeout=5) as response:
                response.read(1)

            elapsed = (time.perf_counter() - start) * 1000
            return "Online", round(elapsed, 2)

        host = parsed.hostname if parsed.hostname else address

        if ":" in host and not parsed.hostname:
            host, port_text = host.rsplit(":", 1)
            port = int(port_text)
        else:
            port = parsed.port if parsed.port else 80

        import socket

        with socket.create_connection((host, port), timeout=5):
            elapsed = (time.perf_counter() - start) * 1000
            return "Online", round(elapsed, 2)

    except Exception:
        return "Offline", None


def monitor_servers():
    results = []

    for server in list_servers():
        status, response_ms = check_server(server["address"])
        checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with connect_db() as db:
            db.execute("""
                INSERT INTO readings
                (server_id, server_name, address, status, response_ms, checked_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                server["id"],
                server["name"],
                server["address"],
                status,
                response_ms,
                checked_at
            ))

        results.append({
            "id": server["id"],
            "name": server["name"],
            "address": server["address"],
            "status": status,
            "response_ms": response_ms,
            "checked_at": checked_at
        })

    return results


PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cloud Network Monitoring</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f1f5f9;
    color: #172033;
}

header {
    background: #12304a;
    color: white;
    padding: 24px 16px;
}

header h1 { margin: 0 0 8px; font-size: 25px; }
header p { margin: 0; color: #dbeafe; }

main {
    max-width: 1150px;
    margin: 24px auto;
    padding: 0 15px;
}

.cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 15px;
}

.card, .panel {
    background: white;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 12px;
    box-shadow: 0 3px 12px rgba(0,0,0,.06);
}

.card h3 {
    margin-top: 0;
    font-size: 14px;
    color: #64748b;
}

.number { font-size: 28px; font-weight: bold; }

input {
    display: block;
    width: 100%;
    padding: 12px;
    margin: 8px 0 14px;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    font-size: 15px;
}

button, .button {
    display: inline-block;
    border: none;
    border-radius: 7px;
    background: #1769aa;
    color: white;
    padding: 11px 15px;
    cursor: pointer;
    text-decoration: none;
    font-size: 14px;
}

button:hover, .button:hover { background: #0d4f83; }
.delete { background: #c0392b; }

.table-wrap { overflow-x: auto; }

table {
    width: 100%;
    min-width: 600px;
    border-collapse: collapse;
}

th, td {
    padding: 12px 10px;
    text-align: left;
    border-bottom: 1px solid #e2e8f0;
}

th { background: #f8fafc; }

.online { color: #16803c; font-weight: bold; }
.offline { color: #c0392b; font-weight: bold; }

.muted { color: #64748b; font-size: 13px; }
.message {
    background: #dbeafe;
    padding: 12px;
    border-radius: 7px;
    margin-bottom: 15px;
}

footer {
    text-align: center;
    padding: 25px;
    color: #64748b;
}

@media(max-width: 600px) {
    header h1 { font-size: 21px; }
    .card, .panel { padding: 15px; }
}
</style>
</head>

<body>
<header>
    <h1>Cloud-Based Network Performance Monitoring</h1>
    <p>Monitor server availability and response time.</p>
</header>

<main>
    {% if message %}
    <div class="message">{{ message }}</div>
    {% endif %}

    <div class="cards">
        <div class="card">
            <h3>Total Servers</h3>
            <div class="number" id="total">0</div>
        </div>

        <div class="card">
            <h3>Servers Online</h3>
            <div class="number online" id="online">0</div>
        </div>

        <div class="card">
            <h3>Servers Offline</h3>
            <div class="number offline" id="offline">0</div>
        </div>

        <div class="card">
            <h3>Average Response Time</h3>
            <div class="number" id="average">--</div>
            <p class="muted">Milliseconds</p>
        </div>
    </div>

    <section class="panel">
        <h2>Add a Server or Website</h2>

        <form action="/add" method="POST">
            <label>Server name</label>
            <input name="name" placeholder="Example: My Website" required>

            <label>Website URL</label>
            <input name="address"
                   placeholder="https://example.com"
                   required>

            <button type="submit">Add Server</button>
        </form>
    </section>

    <section class="panel">
        <h2>Server Status</h2>
        <p id="updated" class="muted">Loading monitoring data...</p>

        <div class="table-wrap">
            <table>
                <thead>
                <tr>
                    <th>Name</th>
                    <th>Address</th>
                    <th>Status</th>
                    <th>Response Time</th>
                    <th>Last Checked</th>
                    <th>Action</th>
                </tr>
                </thead>
                <tbody id="serverRows">
                    <tr><td colspan="6">Loading...</td></tr>
                </tbody>
            </table>
        </div>

        <p>
            <button onclick="refreshData()">Check Servers Now</button>
            <a class="button" href="/export">Export CSV</a>
        </p>
    </section>

    <section class="panel">
        <h2>Network Performance History</h2>
        <canvas id="chart"></canvas>
    </section>
</main>

<footer>Cloud-Based Network Performance Monitoring and Analysis</footer>

<script>
let chart;

async function refreshData() {
    document.getElementById("updated").textContent =
        "Checking servers...";

    try {
        const response = await fetch("/api/monitor", {
            cache: "no-store"
        });

        if (!response.ok) throw new Error("Monitoring request failed");

        const data = await response.json();

        document.getElementById("total").textContent = data.summary.total;
        document.getElementById("online").textContent = data.summary.online;
        document.getElementById("offline").textContent = data.summary.offline;

        document.getElementById("average").textContent =
            data.summary.average_ms === null
                ? "--"
                : data.summary.average_ms.toFixed(2);

        const tbody = document.getElementById("serverRows");
        tbody.replaceChildren();

        if (!data.servers.length) {
            const row = tbody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 6;
            cell.textContent = "No servers added.";
        }

        data.servers.forEach(server => {
            const row = tbody.insertRow();

            row.insertCell().textContent = server.name;
            row.insertCell().textContent = server.address;

            const status = row.insertCell();
            status.textContent = server.status;
            status.className =
                server.status === "Online" ? "online" : "offline";

            row.insertCell().textContent =
                server.response_ms === null
                    ? "--"
                    : server.response_ms + " ms";

            row.insertCell().textContent = server.checked_at;

            const action = row.insertCell();
            const form = document.createElement("form");
            form.method = "POST";
            form.action = "/delete/" + server.id;

            const button = document.createElement("button");
            button.className = "delete";
            button.textContent = "Delete";
            button.type = "submit";

            form.appendChild(button);
            action.appendChild(form);
        });

        updateChart(data.history);

        document.getElementById("updated").textContent =
            "Last updated: " + new Date().toLocaleString();

    } catch (error) {
        document.getElementById("updated").textContent =
            "Unable to load data. Please try again.";
    }
}

function updateChart(history) {
    const labels = [...new Set(
        history.map(item => item.checked_at)
    )].slice(-20);

    const names = [...new Set(
        history.map(item => item.server_name)
    )];

    const datasets = names.map(name => ({
        label: name + " (ms)",
        data: labels.map(label => {
            const item = history.find(
                x => x.server_name === name &&
                     x.checked_at === label
            );
            return item ? item.response_ms : null;
        }),
        spanGaps: false
    }));

    if (chart) {
        chart.data.labels = labels;
        chart.data.datasets = datasets;
        chart.update();
    } else {
        chart = new Chart(document.getElementById("chart"), {
            type: "line",
            data: { labels, datasets },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: "Response time (milliseconds)"
                        }
                    }
                }
            }
        });
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
    return render_template_string(
        PAGE,
        message=request.args.get("message", "")
    )


@app.route("/add", methods=["POST"])
def add_server():
    name = request.form.get("name", "").strip()
    address = request.form.get("address", "").strip()

    if not name or not address:
        return redirect(url_for(
            "dashboard", message="Enter the server name and address."
        ))

    if len(name) > 100 or len(address) > 500:
        return redirect(url_for(
            "dashboard", message="The name or address is too long."
        ))

    with connect_db() as db:
        db.execute(
            "INSERT INTO servers (name, address) VALUES (?, ?)",
            (name, address)
        )

    return redirect(url_for(
        "dashboard", message="Server added successfully."
    ))


@app.route("/delete/<int:server_id>", methods=["POST"])
def delete_server(server_id):
    with connect_db() as db:
        db.execute("DELETE FROM servers WHERE id = ?", (server_id,))

    return redirect(url_for(
        "dashboard", message="Server deleted."
    ))


@app.route("/api/monitor")
def api_monitor():
    servers = monitor_servers()

    with connect_db() as db:
        history_rows = db.execute("""
            SELECT server_name, response_ms, checked_at
            FROM readings
            ORDER BY id DESC
            LIMIT 200
        """).fetchall()

    history = [dict(row) for row in reversed(history_rows)]

    online = sum(
        1 for server in servers if server["status"] == "Online"
    )
    offline = sum(
        1 for server in servers if server["status"] == "Offline"
    )

    times = [
        server["response_ms"]
        for server in servers
        if server["response_ms"] is not None
    ]

    average_ms = round(sum(times) / len(times), 2) if times else None

    return jsonify({
        "servers": servers,
        "history": history,
        "summary": {
            "total": len(servers),
            "online": online,
            "offline": offline,
            "average_ms": average_ms
        }
    })


@app.route("/export")
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Server Name", "Address", "Status",
        "Response Time (ms)", "Checked At"
    ])

    with connect_db() as db:
        rows = db.execute("""
            SELECT server_name, address, status, response_ms, checked_at
            FROM readings
            ORDER BY id DESC
        """).fetchall()

    for row in rows:
        writer.writerow([
            row["server_name"],
            row["address"],
            row["status"],
            row["response_ms"],
            row["checked_at"]
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=network_monitor_history.csv"
        }
    )


init_db()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
