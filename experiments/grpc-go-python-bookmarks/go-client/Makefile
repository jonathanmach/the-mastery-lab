BINARY := bookmarks
CMD    := ./cmd/bookmarks
ADDR  ?= 127.0.0.1:50051

.PHONY: run build clean test

# Run directly without building (pass CLI args with: make run ARGS="list")
run:
	go run $(CMD) --addr $(ADDR) $(ARGS)

# Compile to a binary at ./bookmarks
build:
	go build -o $(BINARY) $(CMD)

# Run the Go unit tests
test:
	go test ./cmd/bookmarks

# Remove compiled binary
clean:
	rm -f $(BINARY)
