# smee2

A webhook delivery service. This is our own version of [smee.io](https://smee.io).

GitHub can't send webhooks straight to a machine running behind a home router or
firewall. smee2 sits in the middle at a public address. GitHub sends an HTTP POST
to `/webhook`, and any client with an open WebSocket connection to `/tunnel` gets
that payload pushed down to it.

```
GitHub  --HTTP POST-->  smee2  --WebSocket push-->  local machine
```

Built for [SCE](https://sce.sjsu.edu) CICD.

## Requirements

- Python 3.9 or newer
- [websocat](https://github.com/vi/websocat), only needed for testing

## Install

```bash
git clone https://github.com/chelseamaipham/smee2.git
cd smee2

python3 -m venv .venv
source ./.venv/bin/activate        # on Windows: .venv\Scripts\activate

python -m pip install -r requirements.txt
```

## Run

```bash
python tunnel_server.py
```

The server runs on port 5000.

## Test

Open two terminals.

In the first one, listen for forwarded payloads:

```bash
websocat ws://127.0.0.1:5000/tunnel
```

In the second one, send a payload:

```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -d '{"ref": "refs/heads/main", "repository": {"name": "test-repo"}}'
```

The first terminal should print the JSON body. The second one should print a
message saying how many clients got it.

## Endpoints

| Method | Path | What it does |
| --- | --- | --- |
| POST | `/webhook` | Takes a JSON payload and forwards it to every connected client |
| WebSocket | `/tunnel` | Clients connect here to receive forwarded payloads |
