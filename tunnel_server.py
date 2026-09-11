import hashlib
import hmac
import json
import os

from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect

app = FastAPI()

#keeps track of who is connected to each webhook id
rooms = {}

#secret shared with GitHub, set in the webhook config on GitHub's side too.
#refuse to start without it, otherwise a missing env var would silently turn
#off auth and let anyone who knows the url trigger deploys
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    raise RuntimeError("WEBHOOK_SECRET is not set")


def verify_signature(body: bytes, signature_header: str | None):
    #x-hub-signature-256 is the one that proves the payload really came from
    #github: it's an hmac-sha256 of the raw body keyed with our shared secret,
    #so only someone who knows the secret could have produced it. the older
    #x-hub-signature (sha1) is weaker and only kept for backwards compatibility
    if signature_header is None:
        raise HTTPException(status_code=401, detail="missing x-hub-signature-256 header")

    expected = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

    #compare_digest avoids leaking timing info about how much of the signature matched
    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=401, detail="invalid signature")


#this runs when someone sends data to /webhook
@app.post("/webhook/{webhook_id}")
async def webhook(
    request: Request,
    webhook_id: str,
    x_hub_signature_256: str | None = Header(default=None),
):
    #read the raw bytes first since the signature is computed over the raw
    #body, not the re-serialized json
    body = await request.body()
    verify_signature(body, x_hub_signature_256)

    #grab the data that was sent
    payload = json.loads(body)

    #makes an empty list to store anyone who disconnected
    dead_users = []

    #goes through everyone connected and send them the data
    for user in rooms.get(webhook_id, []):
        try:
            #tries to send the data to user
            await user.send_json(payload)
        except Exception:
            #if it didnt work then add them to the dead list
            dead_users.append(user)

    #removes everyone who disconnected from the main list
    for user in dead_users:
        rooms[webhook_id].remove(user)

    #sends back a message saying how many people got the data
    return {"status": "forwarded", "users_notified": len(rooms.get(webhook_id, []))}


#runs when someone connects to /tunnel
@app.websocket("/tunnel/{webhook_id}")
async def tunnel(websocket: WebSocket, webhook_id: str):
    #says yes to the person trying to connect
    await websocket.accept()

    #adds them to our list of connected people
    rooms.setdefault(webhook_id, []).append(websocket)

    try:
        #keeps the connection open forever until they leave
        while True:
            #waits for any message from them so the connection stays alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        #removes them from our list if they left
        rooms[webhook_id].remove(websocket)


#only starts the server if this file runs directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
