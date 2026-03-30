# Go + Python gRPC Bookmark Experiment

This experiment explores a small cross-language gRPC setup where a Go CLI talks to a Python service using a shared protobuf contract.

## Learning goal

Understand the core mechanics of gRPC across languages:

- define a shared `.proto` contract
- generate language-specific stubs
- implement a Python gRPC server
- call it from a Go client with deadlines and typed request/response messages

## Architecture

- `proto/bookmarks/v1/bookmarks.proto` is the source of truth
- `python-server/` hosts the gRPC `BookmarkService` and stores bookmarks in memory
- `go-client/` contains a small CLI for create/get/list/tag/delete operations

The transport is local and insecure on `127.0.0.1:50051` because the experiment is intended for one-machine development.

## Prerequisites

- Go
- Python 3.12+
- `uv`
- `protoc`
- `protoc-gen-go`
- `protoc-gen-go-grpc`

Install the Go plugins if needed:

```bash
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
```

Ensure `$GOPATH/bin` is on your `PATH`.

## Generate protobuf code

From the experiment root:

```bash
make gen
```

To regenerate stubs for one language only:

```bash
make gen-python
make gen-go
```

## Install Python dependencies

```bash
cd python-server
make install
```

## Run the Python server

```bash
cd python-server
make run
```

The server binds to `127.0.0.1:50051`. Override the port with:

```bash
make run PORT=50055
```

## Run the Go CLI

```bash
cd go-client
make run ARGS="list"
```

Example flow:

```bash
make run ARGS="create --url https://grpc.io/docs/ --title 'gRPC Docs' --description 'Official docs' --tag grpc --tag docs"
make run ARGS="list"
make run ARGS="get --id bkm_0001"
make run ARGS="tag --id bkm_0001 --tag learning --tag grpc"
make run ARGS="delete --id bkm_0001"
```

To compile a binary instead of using `go run`:

```bash
make build    # produces ./bookmarks
make clean    # removes it
```

## Expected error examples

- `create` with a missing URL fails locally in the Go CLI
- `create` with `ftp://...` reaches the server and returns `INVALID_ARGUMENT`
- `get`, `tag`, or `delete` with an unknown bookmark ID return `NOT_FOUND`
- if the server is not running, the Go CLI exits non-zero with the connection error

## Tests

Run Python tests:

```bash
cd python-server
make test
```

Run Go tests:

```bash
cd go-client
make test
```

Manual Go acceptance flow:

1. Start the Python server.
2. Create a bookmark from the Go CLI.
3. Get the created bookmark by ID.
4. List bookmarks.
5. Add tags and verify duplicates are removed.
6. Delete the bookmark and verify later `get` fails.

## Follow-up ideas

- add `ListByTag`
- add server streaming for live bookmark updates
- back the service with SQLite
- add metadata-based auth
