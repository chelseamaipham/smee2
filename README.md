# smee2

Our own version of [smee.io](https://smee.io) for SCE CICD.

GitHub can't send webhooks to a computer behind a router or firewall, so it
needs something in the middle. GitHub sends a POST to `/webhook/{id}` here, and
anything connected to `/tunnel/{id}` over a websocket gets that data pushed to
it.

```
GitHub  --POST-->  smee2  --websocket-->  your computer
```

## About the ids

The `{id}` is just a name you make up, like `asdf`. It works like a channel.

If you POST to `/webhook/asdf`, only people listening on `/tunnel/asdf` get it.
Someone on a different id gets nothing. That way a bunch of projects can share
one server without mixing up each other's data.

The sender and the listener have to use the same id. If you don't put an id at
all, it won't let you connect.

## What you need

- Python 3.10 or newer
- [websocat](https://github.com/vi/websocat) for testing
- Docker if you want to run it that way instead

## Setup

```bash
git clone https://github.com/chelseamaipham/smee2.git
cd smee2

python3 -m venv .venv
source ./.venv/bin/activate

python -m pip install -r requirements.txt
```

## Running it

```bash
python tunnel_server.py
```

It runs on port 5000.

With Docker instead:

```bash
docker compose up
```

Also port 5000, and you don't need to install anything Python related.

## Testing it

Open two terminals. Use the same id in both, I used `asdf`.

First one listens:

```bash
websocat ws://127.0.0.1:5000/tunnel/asdf
```

It'll look like nothing happened. That's normal, it's just waiting.

Second one sends:

```bash
curl -X POST http://localhost:5000/webhook/asdf \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -d '{"ref": "refs/heads/main", "repository": {"name": "test-repo"}}'
```

The first terminal should print out the json, and the second one should say
`{"status":"forwarded","users_notified":1}`.

If it says `users_notified: 0` nobody was listening on that id, so check you
used the same one in both.

## Endpoints

- `POST /webhook/{id}` sends json to everyone listening on that id
- `WebSocket /tunnel/{id}` connect here to get stuff sent to that id
