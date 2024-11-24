#### Use case

A backend/admin application used by admins to manage the system. If more than one user is visiting the same page, provide visibility for admins on what other users are visiting/working on that same page.

#### Design

- Server needs to keep state (list of connected users and the page they're visiting)
- Any updates should be broadcasted to users visiting that same page (if any)

#### Overview: Data exchange between client and server

1. Client connects: `client.websocket_connect("/ws") as websocket`
2. Server accepts the connection: `websocket.accept()`
3. Client listens to any response: `websocket.receive_text()`
4. Server sends a message: `websocket.json({"data": ...})`


### Resources
- https://fastapi.tiangolo.com/advanced/websockets/
- https://fastapi.tiangolo.com/advanced/testing-websockets/