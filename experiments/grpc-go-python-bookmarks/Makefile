PROTO_SRC  := ./proto/bookmarks/v1/bookmarks.proto
PROTO_INC  := ./proto

PY_OUT     := ./python-server/src/app/generated
GO_OUT     := ./go-client
GO_DEST    := ./go-client/internal/generated

.PHONY: gen gen-python gen-go

# Regenerate all protobuf stubs (Python + Go)
gen: gen-python gen-go

# Generate Python stubs using grpc_tools bundled with the python-server venv
gen-python:
	cd python-server && uv run python -m grpc_tools.protoc \
		-I ../$(PROTO_INC) \
		--python_out=src/app/generated \
		--grpc_python_out=src/app/generated \
		../$(PROTO_SRC)

# Generate Go stubs then move them into the internal package layout
gen-go:
	protoc \
		-I $(PROTO_INC) \
		--go_out=$(GO_OUT) \
		--go_opt=paths=source_relative \
		--go-grpc_out=$(GO_OUT) \
		--go-grpc_opt=paths=source_relative \
		$(PROTO_SRC)
	mkdir -p $(GO_DEST)/bookmarks/v1
	mv $(GO_OUT)/bookmarks/v1/*.go $(GO_DEST)/bookmarks/v1/
	rmdir $(GO_OUT)/bookmarks/v1
	rmdir $(GO_OUT)/bookmarks
