from flask import Flask
import platform
import socket
import time

app = Flask(name)

def check_server(host="google.com", port=443):
start_time = time.time()
try:
connection = socket.create_connection((host, port), timeout=3)
connection.close()
response_time = round((time.time() - start_time) * 1000, 2)
return {"host": host, "status": "Online", "response_time": response_time}
except OSError:
return {"host": host, "status": "Offline", "response_time": None}

@app.route("/")
def home():
    server = check_server()
    response_time = 
    server["response_time"]

    if response_time is None:
        response_time = "N/A"

    status = server["status"]



return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloud Network Monitor</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #eef2f7;
            margin: 0;
            padding: 20px;
            color: #222;
        }}
        .container {{
            max-width: 700px;
            margin: 40px auto;
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #1457a6; text-align: center; }}
        .card {{ background: #f4f7fb; padding: 15px; margin: 12px 0; border-radius: 8px; }}
        .online {{ color: green; font-weight: bold; }}
        .offline {{ color: red; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Cloud Network Monitor</h1>
        <p style="text-align:center;">Network Performance Monitoring and Analysis</p>
        <div class="card">
            <h3>Server Host</h3>
            <p>{server["host"]}</p>
        </div>
        <div class="card">
            <h3>Connection Status</h3>
            <p class="{'online' if status == 'Online' else 'offline'}">{status}</p>
        </div>
        <div class="card">
            <h3>Response Time</h3>
            <p>{response_time} ms</p>
        </div>
        <div class="card">
            <h3>Operating System</h3>
            <p>{platform.system()}</p>
        </div>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=False)
