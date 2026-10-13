from flask import Flask, jsonify
import platform
import socket
import time
from collections import deque

app = Flask(__name__)

history = deque(maxlen=100)


def check_server(host="google.com", port=443):
    start_time = time.time()

    try:
        connection = socket.create_connection(
            (host, port), timeout=3
        )
        connection.close()

        response_time = round(
            (time.time() - start_time) * 1000, 2
        )

        return {
            "host": host,
            "status": "Online",
            "response_time": response_time
        }

    except OSError:
        return {
            "host": host,
            "status": "Offline",
            "response_time": None
        }


@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloud Network Monitor</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #eef2f7;
            margin: 0;
            padding: 15px;
            color: #222;
        }

        .container {
            max-width: 900px;
            margin: 20px auto;
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        h1 {
            color: #1457a6;
            text-align: center;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
        }

        .card {
            background: #f4f7fb;
            padding: 15px;
            border-radius: 8px;
        }

        .value {
            font-size: 22px;
            font-weight: bold;
        }

        .chart-box {
            margin-top: 25px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }

        th, td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
            text-align: left;
        }

        th {
            background: #1457a6;
            color: white;
        }

        .table-wrap {
            overflow-x: auto;
        }

        .note {
            color: #555;
            font-size: 14px;
        }
    </style>
</head>

<body>
<div class="container">
    <h1>Cloud Network Monitor</h1>

    <p style="text-align:center;">
        Network Performance Monitoring and Analysis
    </p>

    <div class="grid">
        <div class="card">
            <h3>Server</h3>
            <p class="value">google.com</p>
        </div>

        <div class="card">
            <h3>Connection Status</h3>
            <p class="value" id="status">Checking...</p>
        </div>

        <div class="card">
            <h3>Current Response</h3>
            <p class="value" id="current">--</p>
        </div>

        <div class="card">
            <h3>Average Response</h3>
            <p class="value" id="average">--</p>
        </div>

        <div class="card">
            <h3>Fastest Response</h3>
            <p class="value" id="fastest">--</p>
        </div>

        <div class="card">
            <h3>Slowest Response</h3>
            <p class="value" id="slowest">--</p>
        </div>
    </div>

    <div class="chart-box">
        <h3>Network Performance History</h3>
        <p class="note">A new reading is taken every 5 seconds.</p>
        <canvas id="chart"></canvas>
    </div>

    <h3>Recent Network Readings</h3>

    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Status</th>
                    <th>Response Time</th>
                </tr>
            </thead>
            <tbody id="history">
                <tr><td colspan="3">Waiting for readings...</td></tr>
            </tbody>
        </table>
    </div>

    <p class="note">
        History is kept temporarily while this server process runs.
        It may reset after a restart or redeployment.
    </p>
</div>

<script>
const labels = [];
const readings = [];
const tableHistory = [];

const chart = new Chart(document.getElementById("chart"), {
    type: "line",
    data: {
        labels: labels,
        datasets: [{
            label: "Response Time (ms)",
            data: readings,
            borderWidth: 2,
            tension: 0.3,
            spanGaps: true
        }]
    },
    options: {
        responsive: true,
        animation: false,
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: "Milliseconds (ms)"
                }
            }
        }
    }
});

async function updateMonitor() {
    try {
        const response = await fetch("/data");
        if (!response.ok) throw new Error("Request failed");

        const data = await response.json();

        document.getElementById("status").textContent = data.status;
        document.getElementById("status").style.color =
            data.status === "Online" ? "green" : "red";

        document.getElementById("current").textContent =
            data.response_time === null ? "N/A" : data.response_time + " ms";

        document.getElementById("average").textContent =
            data.average === null ? "N/A" : data.average + " ms";

        document.getElementById("fastest").textContent =
            data.fastest === null ? "N/A" : data.fastest + " ms";

        document.getElementById("slowest").textContent =
            data.slowest === null ? "N/A" : data.slowest + " ms";

        const time = new Date().toLocaleTimeString();

        labels.push(time);
        readings.push(data.response_time);

        if (labels.length > 20) {
            labels.shift();
            readings.shift();
        }

        chart.update();

        tableHistory.unshift({
            time: time,
            status: data.status,
            response: data.response_time
        });

        if (tableHistory.length > 10) tableHistory.pop();

        document.getElementById("history").innerHTML =
            tableHistory.map(item => `
                <tr>
                    <td>${item.time}</td>
                    <td>${item.status}</td>
                    <td>${item.response === null ? "N/A" : item.response + " ms"}</td>
                </tr>
            `).join("");

    } catch (error) {
        document.getElementById("status").textContent =
            "Monitoring unavailable";
    }
}

updateMonitor();
setInterval(updateMonitor, 5000);
</script>
</body>
</html>
"""


@app.route("/data")
def data():
    result = check_server()

    if result["response_time"] is not None:
        history.append(result["response_time"])

    result["system"] = platform.system()

    if history:
        result["average"] = round(sum(history) / len(history), 2)
        result["fastest"] = min(history)
        result["slowest"] = max(history)
    else:
        result["average"] = None
        result["fastest"] = None
        result["slowest"] = None

    result["readings_count"] = len(history)

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False)
