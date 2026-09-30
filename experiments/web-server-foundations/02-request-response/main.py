import socket
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Request:
    method: str
    path: str
    headers: dict[str, str]  # keys lower-cased when parsing
    body: bytes = b""
    # missing properties: version, cookies, query params, etc.


@dataclass
class Response:
    status: int = 200
    headers: dict[str, str] = field(default_factory=dict[str, str])
    body: bytes = b""
    # missing props: version, cookies, etc.


def parse_request(data: bytes) -> Request:
    # Decode the bytes to a string
    decoded_data = data.decode("utf-8")

    # Split the request into lines
    lines = decoded_data.split("\r\n")

    # Extract the request line (first line)
    request_line = lines[0]
    method, path, _ = request_line.split(" ")

    # Extract headers
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if line == "":
            break  # End of headers
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()

    # Extract body (if any)
    body_index = lines.index("") + 1 if "" in lines else len(lines)
    body = "\r\n".join(lines[body_index:]).encode("utf-8")

    return Request(method=method, path=path, headers=headers, body=body)


def build_response(response: Response) -> bytes:
    # Always send Content-Length (in bytes, not characters) so the client knows
    # where the body ends -- and so the header block is never empty
    headers = {**response.headers, "Content-Length": str(len(response.body))}

    # Build the response headers
    header_lines = [f"{key}: {value}" for key, value in headers.items()]
    header_string = "\r\n".join(header_lines)

    # Build the full response
    full_response = (
        f"HTTP/1.1 {response.status}\r\n"
        f"{header_string}\r\n"
        f"\r\n"
        f"{response.body.decode('utf-8')}"
    )

    return full_response.encode("utf-8")


server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

server_socket.bind(("localhost", 8080))
server_socket.listen()


print("Server is listening on port 8080...")

while True:
    client_socket, (host, port) = server_socket.accept()

    BUFSIZE = 4096
    data = client_socket.recv(BUFSIZE)

    # A client that connects and closes without sending anything makes recv return b"".
    # Browsers and load balancers do this for real, so it needs guarding:
    if not data:
        print(f"{host}:{port} (empty)")
        client_socket.close()
        continue

    # Parse the request
    request = parse_request(data)

    # Build the response
    response = Response(status=200, body=b"Hello, World!")
    raw_response = build_response(response)

    print(f"{host}:{port} {request.method} {request.path} {response.status}")

    # Send the encoded response back to the client
    client_socket.sendall(raw_response)
    client_socket.close()
