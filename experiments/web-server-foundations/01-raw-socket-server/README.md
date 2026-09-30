# 01 — Raw socket server

A minimal HTTP server built directly on `socket`: bind, listen, accept, read the raw request bytes, and send back a hand-crafted `HTTP/1.1 200 OK` response.

## Run

```sh
uv run python 01-raw-socket-server/main.py   # from the project root
curl -v http://localhost:8080/hello
```

## Limitations

- Blocking and single-threaded: one client at a time; a slow client blocks everyone else.
- Single `recv(4096)`: no handling of requests larger than the buffer or split across packets.
- The request is printed but never parsed; every path gets the same response.
- No graceful shutdown; the listening socket is never closed.
