import json
import pytest
from fastapi.testclient import TestClient
from main import app
from starlette.testclient import WebSocketTestSession
import asyncio
from threading import Thread
from websockets import connect
from uvicorn import Config, Server


@pytest.fixture
def client():
    return TestClient(app)


def test_websocket_basic(client: TestClient):
    """
    ✅ Experiment #1: Simple WebSocket endpoint accepting and sending text messages

    Resources:
    - https://fastapi.tiangolo.com/advanced/testing-websockets/
    """
    websocket: WebSocketTestSession
    with client.websocket_connect("/ws/exp1") as websocket:
        websocket.send_json({"greeting": "Hi!", "name": "John"})

        # Receive a response from the WebSocket server
        response = websocket.receive_text()
        assert response == "Hello, John, I'm the server"


@pytest.fixture(scope="module")
def run_server():
    """Run FastAPI app in a separate thread."""
    config = Config(app=app, host="localhost", port=5000, log_level="info")
    server = Server(config)

    thread = Thread(target=server.run, daemon=True)
    thread.start()

    yield  # Tests will run while the server is active

    server.should_exit = True
    thread.join()


@pytest.mark.asyncio
async def test_websocket_endpoint(run_server):
    """
    ✅ Experiment #2: Keep track of active connections and broadcast messages to relevant users

    This test validates a WebSocket server’s ability to handle multiple client connections and broadcast messages between them.
    Two asynchronous WebSocket clients connect to the server running on a separate thread.
    The first client (jonathan) sends user data and waits a notification when another user joins.
    The second client (victor) sends its own data.

    The test uses asyncio.gather to run both connections concurrently and verifies that the server broadcasts a “user joined”
    notification containing the correct payload to the first client.
    """
    uri = "ws://localhost:5000/ws/exp2"

    # Wait for the server to start # TODO: Find a better way to handle this
    await asyncio.sleep(1)

    # Connection #1
    async def ws_client_1():
        header = {"username": "jonathan"}
        async with connect(uri, additional_headers=header) as websocket:
            # Send first user's data
            json_dump = json.dumps({"username": "jonathan", "location": "home"})
            await websocket.send(json_dump)

            # Wait for notification from server about the second user joining
            response = await websocket.recv()
            json_res = json.loads(response)
            assert json_res == {
                "type": "user_joined",
                "payload": {"username": "victor", "location": "home"},
            }

    # Connection #2
    async def ws_client_2():
        header = {"username": "victor"}
        async with connect(uri, additional_headers=header) as websocket:
            # Send second user's data
            json_dump = json.dumps({"username": "victor", "location": "home"})
            await websocket.send(json_dump)

    # Set timeout for the combined tasks
    await asyncio.gather(ws_client_1(), ws_client_2())
