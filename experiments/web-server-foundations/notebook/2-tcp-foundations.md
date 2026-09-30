Yes — I’d actually put this **before HTTP** in your learning path. HTTP becomes much easier to understand once you see that TCP itself doesn’t know anything about requests, headers, URLs, JSON, etc.

### Start with TCP alone

At its core, a TCP connection gives two programs a **reliable, ordered, bidirectional stream of bytes**.

Imagine two programs:

```text
Program A                         Program B

   TCP socket  <===============>  TCP socket

        "hello" ────────────────►

                ◄────────────── "hi!"
```

TCP doesn't know that `"hello"` is a message. As far as TCP is concerned, it's just:

```text
68 65 6c 6c 6f
```

Five bytes.

There's no built-in concept of:

```text
request
response
header
JSON
message
command
URL
```

Those are conventions established by **protocols built on top of TCP**.

---

### Let's build the simplest possible TCP server

```python
import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(("127.0.0.1", 9000))
server.listen()

print("Listening on port 9000...")

connection, address = server.accept()

print("Connected:", address)

while True:
    data = connection.recv(1024)

    if not data:
        break

    print("Received:", data)

    connection.sendall(b"I received your bytes!\n")

connection.close()
```

Notice there's **nothing HTTP-specific here**.

You can connect to it with `nc` (netcat):

```bash
nc localhost 9000
```

Then type:

```text
hello
```

Your server sees something approximately like:

```python
b'hello\n'
```

and responds:

```text
I received your bytes!
```

Congratulations: you've created a network application that has nothing to do with the web.

---

### And the client can also just be Python

Instead of `nc`:

```python
import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(("127.0.0.1", 9000))

client.sendall(b"hello")

response = client.recv(1024)

print(response)

client.close()
```

Now you have:

```text
client.py                         server.py

socket()                           socket()
   │                                  │
connect() ───────────────────────► accept()
   │                                  │
   │────── b"hello" ────────────────► │
   │                                  │
   │ ◄── b"I received..." ─────────── │
   │                                  │
close()                           close()
```

And that's a useful place to ask:

**How does the server know what `"hello"` means?**

It doesn't.

You decide.

---

## Invent your own protocol

Suppose we're building an incredibly sophisticated distributed system called **JonathanDB™**.

Let's say clients can store and retrieve values.

You invent this protocol:

```text
SET <key> <value>
GET <key>
DELETE <key>
```

A conversation could look like:

```text
client → server

SET name Jonathan

server → client

OK

client → server

GET name

server → client

Jonathan
```

You've just invented an application-layer protocol.

Your server might do:

```python
database = {}

while True:
    data = connection.recv(1024)

    if not data:
        break

    command = data.decode().strip()

    parts = command.split()

    if parts[0] == "SET":
        key = parts[1]
        value = parts[2]

        database[key] = value

        connection.sendall(b"OK\n")

    elif parts[0] == "GET":
        key = parts[1]

        value = database.get(key)

        connection.sendall(f"{value}\n".encode())
```

Now you've got something vaguely Redis-like.

And this is the conceptual leap:

```text
TCP
│
│ reliable stream of bytes
│
▼
Your protocol
│
│ "SET name Jonathan\n"
│
▼
Your application
```

HTTP works the same way:

```text
TCP
│
▼
HTTP
│
│ GET /orders HTTP/1.1
│ Host: localhost
│ ...
│
▼
Your web application
```

---

## TCP doesn't even give you messages

This is probably the **most important experiment** to do.

Suppose your client does:

```python
client.sendall(b"HELLO")
client.sendall(b"WORLD")
```

You might expect the server to get:

```python
recv() → b"HELLO"

recv() → b"WORLD"
```

But TCP doesn't promise that.

You could get:

```python
recv() → b"HELLOWORLD"
```

or:

```python
recv() → b"HEL"
recv() → b"LOWO"
recv() → b"RLD"
```

TCP preserves:

```text
HELLOWORLD
```

but **not the boundaries between your calls to `send()`**.

That's why it's called a **byte stream**.

So your invented protocol needs some way to say:

> This message ends here.

You could choose newline:

```text
SET name Jonathan\n
GET name\n
```

Then your parser accumulates bytes until it sees `\n`.

Or you could prefix messages with their length:

```text
17:SET name Jonathan
8:GET name
```

Or use some more sophisticated framing scheme.

And suddenly something in HTTP makes more sense:

```text
GET / HTTP/1.1\r\n
Host: example.com\r\n
Accept: */*\r\n
\r\n
```

That `\r\n\r\n` isn't random formatting.

It's part of HTTP's answer to:

> Given that TCP is just an arbitrary stream of bytes, **how do I know where the HTTP headers end?**

Likewise:

```text
Content-Length: 142
```

helps answer:

> How do I know when I've received the entire body?

---

## So what else uses TCP?

Loads of protocols.

For example:

| Protocol | Typical port | Purpose |
|---|---:|---|
| HTTP | 80 | Web |
| HTTPS | 443 | HTTP over TLS |
| SSH | 22 | Remote shell |
| SMTP | 25 | Email transfer |
| IMAP | 143 | Email retrieval |
| PostgreSQL protocol | 5432 | Database connections |
| MySQL protocol | 3306 | Database connections |
| Redis RESP | 6379 | Redis |
| FTP | 21 | File transfer |

They're conceptually doing the same thing:

```text
             Application protocol
                    │
      ┌─────────────┼─────────────┐
      │             │             │
     HTTP         Redis          SSH
      │             │             │
      └─────────────┼─────────────┘
                    │
                   TCP
                    │
                    ▼
                    IP
```

Obviously the real networking stack has more nuance, but this is a useful mental model.

---

### One particularly fun experiment: talk to a real protocol manually

Once you've played with your custom TCP protocol, use `nc` to connect to an actual HTTP server:

```bash
nc example.com 80
```

Then manually type:

```text
GET / HTTP/1.1
Host: example.com

```

Hit Enter twice.

You'll get something like:

```text
HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: ...

<!doctype html>
...
```

There's something quite illuminating about doing this manually.

You haven't used a browser.

You haven't used `requests`.

You haven't used `curl`.

You've established a TCP connection and **spoken HTTP yourself**.

---

And that gives you a nice progression for the article/experiment you're building:

```text
1. What is a network connection?

2. The bare TCP server
   socket()
   bind()
   listen()
   accept()
   recv()
   send()

3. TCP is just a stream of bytes
   → no messages
   → no requests/responses
   → demonstrate fragmentation/coalescing

4. Invent our own protocol
   SET foo bar
   GET foo

5. We need message framing
   → newline delimiter
   → length prefix

6. HTTP is another application protocol
   → request line
   → headers
   → body

7. Build our bare HTTP server

8. How does it handle multiple clients?
   → blocking
   → threads
   → processes
   → event loops / async

9. What does Uvicorn do for us?
```

In particular, **#3 → #4 → #5 → #6** will make HTTP feel much less magical. HTTP becomes essentially *someone else already designed the rules for what bytes we should send over the connection, so we don't have to invent `JonathanDB™ Protocol v1` ourselves.*