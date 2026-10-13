from flask import Flask, jsonify
import platform
import socket
import time

app = Flask(__name__)


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
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">
    <title>Cloud Network Monitor</title>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #eef2f7;
            margin: 0;
            padding: 20px;
            color: #222;
        }

        .container {
            max-width: 800px;
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

        .card {
            background: #f4f7fb;
            padding: 15px;
            margin: 12px 0;
            border-radius: 8px;
        }

        .value {
            font-size: 22px;
            font-weight: bold;
        }

        #status {
            color: green;
        }

        .chart-box {
            margin-top: 25px;
        }
    </style>
</head>

<body>
<div class="container">

    <h1>Cloud Network Monitor</h1>

    <p style="text-align:center;">
        Network Performance Monitoring and Analysis
    </p>

    <div class="card">
        <h3>Server Host</h3>
        <p class="value">google.com</p>
    </div>

    <div class="card">
        <h3>Connection Status</h3>
        <p class="value" id="status">Checking...</p>
    </div>

    <div class="card">
        <h3>Response Time</h3>
        <p class="value" id="response">Checking...</p>
    </div>

    <div class="card">
        <h3>Operating System</h3>
        <p class="value" id="system">Loading...</p>
    </div>

    <div class="chart-box">
        <h3>Live Network Response Time</h3>
        <p>New reading every 5 seconds</p>
        <canvas id="performanceChart"></canvas>
    </div>

</div>

<script>
const labels = [];
const readings = [];

const chart = new Chart(
    document.getElementById("performanceChart"),
    {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Response Time (ms)",
                data: readings,
                borderWidth: 2,
                tension: 0.3
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
    }
);

async function updateMonitor() {
    try {
        const response = await fetch("/data");
        const data = await response.json();

        document.getElementById("status").textContent =
            data.status;

        document.getElementById("status").style.color =
            data.status === "Online" ? "green" : "red";

        document.getElementById("response").textContent =
            data.response_time === null
                ? "N/A"
                : data.response_time + " ms";

        document.getElementById("system").textContent =
            data.system;

        labels.push(new Date().toLocaleTimeString());

        readings.push(data.response_time);

        if (labels.length > 20) {
            labels.shift();
            readings.shift();
        }

        chart.update();

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
    result["system"] = platform.system()
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False)
