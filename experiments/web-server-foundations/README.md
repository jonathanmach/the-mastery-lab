# Web Server Foundations

Building an HTTP server from first principles, one iteration at a time. Each iteration lives in its own folder and runs on its own, so they can be compared side by side.

## Iterations

| # | Folder | What it covers |
|---|--------|----------------|
| 01 | [01-raw-socket-server](01-raw-socket-server/) | Blocking, single-threaded server on raw `socket` with a hand-crafted response |
| 02 | [02-request-response](02-request-response/) | Parse raw bytes into a `Request` dataclass; build replies with a `Response` dataclass |

### Next steps:

* integrate uvicorn

## Insights



**Processes & threads**

...

## Notes

- [web-servers-fundamentals.md](web-servers-fundamentals.md) — overview
- [notebook/](notebook/) — learning notes, numbered in order
