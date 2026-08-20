# smee2

This is our own version of [smee.io](https://smee.io), built for SCE CICD.

GitHub can't send webhooks to a computer that's behind a router or firewall, so
it needs something in the middle. That's what this does. GitHub sends a POST
request to `/webhook/{id}` on this server, and anything connected to
`/tunnel/{id}` over a websocket gets that data pushed to it.

```
GitHub  --POST-->  smee2  --websocket-->  your computer
```

## About the IDs

The `{id}` in the URL is just a name you make up, like `asdf`. Think of it like
a channel.

If you POST to `/webhook/asdf`, only the people listening on `/tunnel/asdf` will
get it. Someone listening on a different id won't see anything. This way a bunch
of different projects can use the same server without getting each other's data.

The important part is that the sender and the listener use the same id. If you
don't put an id at all it won't let you connect.

## What you need

- Python 3.9 or newer
- [websocat](https://github.com/vi/websocat) if you want to test it
- Docker, if you'd rather run it that way

## Setup

```bash
git clone https://github.com/chelseamaipham/smee2.git
cd smee2

python3 -m venv .venv
source ./.venv/bin/activate        # windows: .venv\Scripts\activate

python -m pip install -r requirements.txt
```

## Running it

```bash
python tunnel_server.py
```

It runs on port 5000.

Or with Docker:

```bash
docker compose up
```

That way you don't have to install Python stuff, it's all inside the container.
Either way it's on port 5000.

## Testing it

You need two terminal windows. Use the same id in both, I'm using `asdf` here.

First window, this listens for data:

```bash
websocat ws://127.0.0.1:5000/tunnel/asdf
```

It's going to look like nothing happened. That's normal, it's just sitting there
waiting.

Second window, this sends the data:

```bash
curl -X POST http://localhost:5000/webhook/asdf \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -d '{"ref": "refs/heads/main", "repository": {"name": "test-repo"}}'
```

Now the first window should print out the json you just sent, and the second one
should say `{"status":"forwarded","users_notified":1}`.

If it says `users_notified: 0` that means nobody was listening on that id, so
double check you used the same one in both windows.

## The endpoints

- `POST /webhook/{id}` - send json here, it goes to everyone listening on that id
- `WebSocket /tunnel/{id}` - connect here to receive stuff sent to that id
