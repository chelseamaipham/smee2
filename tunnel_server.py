from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect

app = FastAPI()

#keeps track of who is connected to each webhook id
rooms = {}

#this runs when someone sends data to /webhook
@app.post("/webhook/{webhook_id}")
async def webhook(request: Request, webhook_id: str):
    #grab the data that was sent
    payload = await request.json()

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
