Absolutely. A great learning exercise is to build a tiny HTTP/1.1 server directly on top of TCP, without Flask/FastAPI/Node/etc.

At the most basic level, a web server is just:

1. Open a TCP socket.
2. Bind it to an IP address + port.
3. Listen for connections.
4. Accept a connection.
5. Read bytes from that connection.
6. Interpret those bytes according to the HTTP protocol.
7. Write bytes back in HTTP response format.
8. Close or reuse the connection.

The key mental model is:

```text
HTTP is not the network connection itself.

HTTP is a convention for what bytes mean
when sent over a TCP connection.
```

For example, your browser might establish a TCP connection to `localhost:8080` and send these bytes:

```text
GET /hello?name=Jonathan HTTP/1.1\r\n
Host: localhost:8080\r\n
User-Agent: curl/8.7.1\r\n
Accept: */*\r\n
\r\n
```

The `\r\n` parts are real bytes: carriage return + line feed.

Visually:

```text
GET /hello?name=Jonathan HTTP/1.1
Host: localhost:8080
User-Agent: curl/8.7.1
Accept: */*

```

That blank line is important. It means:

```text
headers finished
```

If there were a request body, it would come after that.

For your first experiment, Python is ideal because its socket API stays very close to what's actually happening.

```python
import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind(("127.0.0.1", 8080))
server_socket.listen()

print("Listening on http://127.0.0.1:8080")

while True:
    connection, client_address = server_socket.accept()

    print("Connection from:", client_address)

    data = connection.recv(4096)

    print("Raw bytes:")
    print(repr(data))

    print("\nDecoded:")
    print(data.decode("utf-8"))

    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: 12\r\n"
        "\r\n"
        "Hello world!"
    )

    connection.sendall(response.encode("utf-8"))
    connection.close()
```

Run it:

```bash
python server.py
```

Then, in another terminal:

```bash
curl -v http://localhost:8080/hello
```

You've now built a web server.

There's no HTTP library involved. `curl` thinks it's talking to a perfectly legitimate HTTP server because the bytes you returned follow the HTTP protocol.

The interesting part comes next: stop treating the incoming request as one giant string and actually parse it.

The first line is called the **request line**:

```text
GET /hello?name=Jonathan HTTP/1.1
```

Its shape is:

```text
METHOD SP REQUEST-TARGET SP HTTP-VERSION CRLF
```

So you can parse it:

```python
request = data.decode("utf-8")

lines = request.split("\r\n")

request_line = lines[0]

method, target, http_version = request_line.split(" ")

print(method)
print(target)
print(http_version)
```

That might produce:

```text
GET
/hello?name=Jonathan
HTTP/1.1
```

Then parse the headers.

Given:

```text
Host: localhost:8080
User-Agent: curl/8.7.1
Accept: */*
```

you can build a dictionary:

```python
headers = {}

for line in lines[1:]:
    if line == "":
        break

    name, value = line.split(":", 1)

    headers[name.strip()] = value.strip()

print(headers)
```

Result:

```python
{
    "Host": "localhost:8080",
    "User-Agent": "curl/8.7.1",
    "Accept": "*/*",
}
```

So your tiny server is already starting to look like a framework:

```python
method
path
headers
body
```

You could represent that as:

```python
class Request:
    def __init__(self, method, target, version, headers):
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers
```

And now something interesting has happened.

Your original code:

```text
TCP bytes
```

has become:

```text
Request(
    method="GET",
    target="/hello",
    version="HTTP/1.1",
    headers={...},
)
```

That's essentially one of the jobs a web server/framework does for you.

You can then build crude routing:

```python
if method == "GET" and target == "/":
    body = "Home page"

elif method == "GET" and target == "/hello":
    body = "Hello!"

else:
    body = "Not found"
```

And choose the status code:

```python
if target == "/hello":
    status = "200 OK"
    body = "Hello!"
else:
    status = "404 Not Found"
    body = "Not found"
```

Then serialize the response back into HTTP:

```python
response = (
    f"HTTP/1.1 {status}\r\n"
    "Content-Type: text/plain\r\n"
    f"Content-Length: {len(body.encode('utf-8'))}\r\n"
    "\r\n"
    f"{body}"
)
```

So there are really two transformations:

```text
bytes
 ↓
HTTP parser
 ↓
Request object
 ↓
your application
 ↓
Response object
 ↓
HTTP serializer
 ↓
bytes
```

Conceptually:

```text
Browser / curl
       │
       │ TCP
       ▼
┌───────────────────────┐
│       Socket          │
│ recv() / send()       │
└──────────┬────────────┘
           │ bytes
           ▼
┌───────────────────────┐
│     HTTP parser       │
│                       │
│ GET /users HTTP/1.1   │
│ Host: example.com     │
└──────────┬────────────┘
           │
           ▼
       Request
           │
           ▼
┌───────────────────────┐
│    Your application   │
│                       │
│ if path == "/users"   │
└──────────┬────────────┘
           │
           ▼
       Response
           │
           ▼
┌───────────────────────┐
│ HTTP response encoder │
└──────────┬────────────┘
           │ bytes
           ▼
       TCP socket
```

There's one particularly important trap in that initial implementation:

```python
data = connection.recv(4096)
```

does **not** mean:

> receive one HTTP request.

TCP doesn't know what an HTTP request is.

TCP gives you a **stream of bytes**.

You might receive:

```text
GET / HT
```

in one `recv()`, and:

```text
TP/1.1\r\nHost: localhost...
```

in the next.

Or you might receive the whole request at once.

This is one of the most useful things your experiment can teach you.

Your HTTP parser therefore needs to keep reading until it knows enough bytes have arrived.

For headers, that means:

```python
buffer = b""

while b"\r\n\r\n" not in buffer:
    chunk = connection.recv(1024)

    if not chunk:
        break

    buffer += chunk
```

Now you know you've received at least the complete header section:

```text
\r\n\r\n
```

Then you can separate:

```python
header_bytes, body_start = buffer.split(b"\r\n\r\n", 1)
```

For a request such as:

```text
POST /orders HTTP/1.1
Host: localhost
Content-Length: 18
Content-Type: application/json

{"product_id": 42}
```

you'd parse:

```text
Content-Length: 18
```

and keep reading until you have 18 body bytes.

That leads to a slightly more realistic architecture:

```python
def read_request(connection):
    ...
    return Request(...)


def handle_request(request):
    ...
    return Response(...)


def send_response(connection, response):
    ...
```

And your server loop becomes wonderfully simple:

```python
while True:
    connection, address = server_socket.accept()

    request = read_request(connection)

    response = handle_request(request)

    send_response(connection, response)

    connection.close()
```

That's almost the entire mental model I'd aim for initially.

Don't add concurrency yet.

Your first server should deliberately handle:

```text
connection 1
    ↓
entire request
    ↓
response
    ↓
close
    ↓
connection 2
```

If one client takes 30 seconds to send its HTTP request, everybody else waits.

That's useful because the next question naturally becomes:

> How do real web servers handle multiple connections at the same time?

And that opens up threads, processes, `select`/`poll`/`epoll`, async I/O, Gunicorn, Uvicorn, and eventually ASGI.

But I'd build the **bad single-threaded version first**. It gives you something concrete to improve.

A good progression for your experiment would be:

```text
V1
TCP socket
→ print raw HTTP bytes
→ return hard-coded response

V2
Parse request line
→ method
→ path
→ HTTP version

V3
Parse headers

V4
Parse Content-Length + request body

V5
Introduce Request / Response objects

V6
Add routing
GET /orders
GET /products

V7
Support persistent HTTP/1.1 connections

V8
Explore multiple simultaneous clients

V9
Compare what you've built with Uvicorn
```

By V6, you'll have accidentally created the beginnings of your own tiny web framework.

And you'll have a much stronger intuition for what something like:

```python
@app.get("/orders")
def orders():
    ...
```

is hiding underneath.