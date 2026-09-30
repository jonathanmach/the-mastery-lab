import socket

server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

server_socket.bind(("localhost", 8080))
server_socket.listen()


print("Server is listening on port 8080...")

while True:
    """
    Example of a raw HTTP request sent by a client (e.g., curl):

    GET /hello?name=John HTTP/1.1\r\n
    Host: localhost:8080\r\n
    User-Agent: curl/8.7.1\r\n
    Accept: */*\r\n
    \r\n
    """

    client_socket, address = server_socket.accept()
    print(f"Connection from {address} has been established!")

    BUFSIZE = 4096
    data = client_socket.recv(BUFSIZE)

    print("Raw bytes:", repr(data))

    # Decode the bytes to a string
    decoded_data = data.decode("utf-8")
    print("Decoded string:", decoded_data)

    # Hand-crafted HTTP response
    # HTTP specification requires CRLF (\r\n) line endings and
    # a blank line separating headers from the body
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: 12\r\n"
        "\r\n"
        "Hello world!"
    )

    # Send the encoded response back to the client
    client_socket.sendall(response.encode("utf-8"))

    """Close the client socket
    
    If ommitted, (1) client hangs, (2) file descriptor / socket leak
    # MORE ../notebook/code-comments#client_socket_close
    # TODO: Not sure how to properly tag the above comment yet... need to find a solution
    """
    client_socket.close()
