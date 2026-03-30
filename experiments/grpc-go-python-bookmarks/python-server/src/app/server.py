from __future__ import annotations

import argparse
from concurrent import futures
import logging

import grpc

from bookmarks.v1 import bookmarks_pb2_grpc
from app.service import BookmarkService

LOGGER = logging.getLogger(__name__)


def serve(host: str = "127.0.0.1", port: int = 50051) -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    bookmarks_pb2_grpc.add_BookmarkServiceServicer_to_server(BookmarkService(), server)
    bind_addr = f"{host}:{port}"
    server.add_insecure_port(bind_addr)
    LOGGER.info("starting bookmark gRPC server on %s", bind_addr)
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        LOGGER.info("stopping bookmark gRPC server")
        server.stop(grace=0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the bookmark gRPC server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50051)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    serve(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
