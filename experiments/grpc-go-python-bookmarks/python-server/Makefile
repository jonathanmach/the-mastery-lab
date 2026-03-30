PORT ?= 50051

.PHONY: install run test

# Install all dependencies (including dev)
install:
	uv sync --dev

# Start the gRPC server (override port with: make run PORT=50055)
run:
	uv run python -m app.server --port $(PORT)

# Run pytest
test:
	uv run pytest
