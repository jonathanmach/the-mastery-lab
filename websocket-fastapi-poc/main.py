from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Any, Dict

from pydantic import BaseModel

app = FastAPI()


class EventPayload(BaseModel):
    # event: str # "user_joined" or "user_left"
    username: str
    location: str


class Event(BaseModel):
    type: str  # eg: "user_joined"
    payload: EventPayload


class PresenceState(BaseModel):
    location: str
    conn: Any  # Using WebSocket type raises a type error: Unable to generate pydantic-core schema for <class 'starlette.websockets.WebSocket'>. Set `arbitrary_types_allowed=True` in the model_config to ignore this error or implement `__get_pydantic_core_schema__` on your type to fully support it.


class ConnectionManager:
    active_sessions: Dict[str, PresenceState]

    def __init__(self):
        self.active_sessions = {}

    async def connect(self, websocket: WebSocket):
        # TODO: authenticate user
        await websocket.accept()

    async def disconnect(self, websocket: WebSocket):
        username = websocket.headers["username"]
        del self.active_sessions[username]
        # TODO: Notify other users about the user leaving
        await websocket.close()

    async def handle_event(self, payload: EventPayload, websocket: WebSocket):
        # Update the user's location
        self.active_sessions[payload.username] = PresenceState(
            location=payload.location, conn=websocket
        )

        # Notify all users on the same location except the sender
        for user_id, presence in self.active_sessions.items():
            if user_id != payload.username and presence.location == payload.location:
                event = Event(type="user_joined", payload=payload)
                event_json = event.model_dump()
                await presence.conn.send_json(event_json)


@app.websocket("/ws/exp1")
async def ws_hello_world(websocket: WebSocket):
    """
    ✅ Experiment #1: Simple WebSocket endpoint accepting and sending text messages
    """
    await websocket.accept()
    try:
        while True:
            # payload = {"greeting": "Hi!", "name": "John"}
            payload = await websocket.receive_json()
            await websocket.send_text(f"Hello, {payload["name"]}, I'm the server")
    except WebSocketDisconnect:
        await websocket.close()


manager = ConnectionManager()


@app.websocket("/ws/exp2")
async def websocket_endpoint(websocket: WebSocket):
    """
    ✅ Experiment #2: Keep track of active connections and broadcast messages to relevant users
    """
    await manager.connect(websocket)
    try:
        while True:
            payload = await websocket.receive_json()
            payload = EventPayload.model_validate(payload)
            await manager.handle_event(payload, websocket)

    except WebSocketDisconnect as e:
        print(f"WebSocket connection closed: {e}")
        await manager.disconnect(websocket)
