from flask import Flask, render_template
import platform
import socket
import time

import os

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
)


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
    server = check_server()

    return f"""
    <h1>Cloud Network Monitor</h1>
    <p>Server: {server['host']}</p>
    <p>Status: {server['status']}</p>
    <p>Response Time: {server['response_time']} ms</p>
    <p>System: {platform.system()}</p>
    """


if __name__ == "__main__":
    app.run(debug=True)
