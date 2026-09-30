### Topics

* HTTP Protocol
  * The most bare version of a web server
  * Build a tiny HTTP/1.1 server directly on top of TCP (no framework)




  * 




---
## TODO

- Create tiny web framework prototype (eg: Request class containing method, target, version, headers...

- Understand how modern frameworks handle multiple requests and concepts like processes, threads, thread-safe, etc
- Use gunicorn to run my web framework prototype
- Learn from https://github.com/bottlepy/bottle/blob/main/bottle.py
## Notes

At the most basic level, a web server is just:

1. Open a TCP socket.
2. Bind it to an IP address + port.
3. Listen for connections.
4. Accept a connection.
5. Read bytes from that connection.
6. Interpret those bytes according to the HTTP protocol.
7. Write bytes back in HTTP response format.
8. Close or reuse the connection.



I think it would be nice as well to explore a TCP connection without the HTTP protocol - what does it look like? what can I do with it and what else is it used for beyond http?