"""Windows desktop launcher for the offline Flux application."""

from __future__ import annotations

import socket
import threading
import time

import uvicorn
import webview

from app.main import app

HOST = "127.0.0.1"
PORT = 8765


def wait_for_server(timeout: float = 15.0) -> None:
    """Wait until Uvicorn accepts connections before opening the window."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
            connection.settimeout(0.5)
            if connection.connect_ex((HOST, PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Flux backend gagal dimulai pada port lokal.")


def run_server(server: uvicorn.Server) -> None:
    server.run()


def main() -> None:
    """Start the local API and show it inside a native desktop window."""
    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    server_thread = threading.Thread(target=run_server, args=(server,), daemon=True)
    server_thread.start()
    wait_for_server()

    try:
        webview.create_window(
            "Flux — All-in-One File Toolkit",
            f"http://{HOST}:{PORT}/",
            width=1200,
            height=820,
            min_size=(420, 640),
            confirm_close=True,
        )
        webview.start()
    finally:
        server.should_exit = True
        server_thread.join(timeout=5)


if __name__ == "__main__":
    main()
