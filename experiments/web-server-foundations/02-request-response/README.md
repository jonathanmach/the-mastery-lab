# 02 — Request & Response classes

Builds on [01](../01-raw-socket-server/): the raw bytes are parsed into a `Request` dataclass, and the reply is built as a `Response` dataclass that serialises itself back to bytes.

## Run

```sh
uv run python 02-request-response/main.py   # from the project root
curl -v http://localhost:8080/hello
```

## What changed from 01

- `Request.from_bytes()` parses the request line, headers and body.
- `Response.to_bytes()` builds the status line, headers and `Content-Length`.

## Limitations

- Still blocking and single-threaded.
- Still a single `recv(4096)`.
