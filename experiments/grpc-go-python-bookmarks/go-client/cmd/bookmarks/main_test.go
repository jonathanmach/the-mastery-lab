package main

import (
	"context"
	"fmt"
	"net"
	"strings"
	"testing"
	"time"

	cliClient "github.com/jonathanfmach/the-mastery-lab/experiments/grpc-go-python-bookmarks/go-client/internal/client"
	bookmarksv1 "github.com/jonathanfmach/the-mastery-lab/experiments/grpc-go-python-bookmarks/go-client/internal/generated/bookmarks/v1"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"
	"google.golang.org/grpc/test/bufconn"
)

const bufSize = 1024 * 1024

func TestRunCreateRequiresURL(t *testing.T) {
	restore := overrideClientFactory(t, func(addr string) (timeoutClient, error) {
		return cliClient.NewForService(noopBookmarkServiceClient{}), nil
	})
	defer restore()

	stdout := new(strings.Builder)
	stderr := new(strings.Builder)

	code := run([]string{"create"}, stdout, stderr)

	if code != 1 {
		t.Fatalf("expected exit code 1, got %d", code)
	}
	if !strings.Contains(stderr.String(), "create requires --url") {
		t.Fatalf("expected missing url message, got %q", stderr.String())
	}
}

func TestRunTagRequiresAtLeastOneTag(t *testing.T) {
	restore := overrideClientFactory(t, func(addr string) (timeoutClient, error) {
		return cliClient.NewForService(noopBookmarkServiceClient{}), nil
	})
	defer restore()

	stdout := new(strings.Builder)
	stderr := new(strings.Builder)

	code := run([]string{"tag", "--id", "bkm_0001"}, stdout, stderr)

	if code != 1 {
		t.Fatalf("expected exit code 1, got %d", code)
	}
	if !strings.Contains(stderr.String(), "tag requires at least one --tag") {
		t.Fatalf("expected missing tag message, got %q", stderr.String())
	}
}

func TestRunCRUDFlowAgainstBufconnServer(t *testing.T) {
	factory := startBufconnServer(t)
	restore := overrideClientFactory(t, factory)
	defer restore()

	t.Run("create", func(t *testing.T) {
		stdout := new(strings.Builder)
		stderr := new(strings.Builder)

		code := run([]string{"create", "--url", "https://grpc.io/docs/", "--title", "gRPC Docs", "--tag", "grpc", "--tag", "docs"}, stdout, stderr)

		if code != 0 {
			t.Fatalf("expected exit code 0, got %d with stderr %q", code, stderr.String())
		}
		if !strings.Contains(stdout.String(), "created bookmark:") || !strings.Contains(stdout.String(), "id: bkm_0001") {
			t.Fatalf("unexpected create output: %q", stdout.String())
		}
	})

	t.Run("list", func(t *testing.T) {
		stdout := new(strings.Builder)
		stderr := new(strings.Builder)

		code := run([]string{"list"}, stdout, stderr)

		if code != 0 {
			t.Fatalf("expected exit code 0, got %d with stderr %q", code, stderr.String())
		}
		if !strings.Contains(stdout.String(), "1. bkm_0001") {
			t.Fatalf("unexpected list output: %q", stdout.String())
		}
	})

	t.Run("get", func(t *testing.T) {
		stdout := new(strings.Builder)
		stderr := new(strings.Builder)

		code := run([]string{"get", "--id", "bkm_0001"}, stdout, stderr)

		if code != 0 {
			t.Fatalf("expected exit code 0, got %d with stderr %q", code, stderr.String())
		}
		if !strings.Contains(stdout.String(), "url: https://grpc.io/docs/") {
			t.Fatalf("unexpected get output: %q", stdout.String())
		}
	})

	t.Run("tag", func(t *testing.T) {
		stdout := new(strings.Builder)
		stderr := new(strings.Builder)

		code := run([]string{"tag", "--id", "bkm_0001", "--tag", "learning", "--tag", "grpc"}, stdout, stderr)

		if code != 0 {
			t.Fatalf("expected exit code 0, got %d with stderr %q", code, stderr.String())
		}
		if !strings.Contains(stdout.String(), "tags: grpc, docs, learning") {
			t.Fatalf("unexpected tag output: %q", stdout.String())
		}
	})

	t.Run("delete", func(t *testing.T) {
		stdout := new(strings.Builder)
		stderr := new(strings.Builder)

		code := run([]string{"delete", "--id", "bkm_0001"}, stdout, stderr)

		if code != 0 {
			t.Fatalf("expected exit code 0, got %d with stderr %q", code, stderr.String())
		}
		if !strings.Contains(stdout.String(), "deleted bookmark bkm_0001") {
			t.Fatalf("unexpected delete output: %q", stdout.String())
		}
	})

	t.Run("missing", func(t *testing.T) {
		stdout := new(strings.Builder)
		stderr := new(strings.Builder)

		code := run([]string{"get", "--id", "bkm_9999"}, stdout, stderr)

		if code != 1 {
			t.Fatalf("expected exit code 1, got %d", code)
		}
		if !strings.Contains(stderr.String(), "code = NotFound") {
			t.Fatalf("unexpected missing output: %q", stderr.String())
		}
	})
}

func overrideClientFactory(t *testing.T, factory func(addr string) (timeoutClient, error)) func() {
	t.Helper()
	previous := newClient
	newClient = factory
	return func() {
		newClient = previous
	}
}

func startBufconnServer(t *testing.T) func(string) (timeoutClient, error) {
	t.Helper()

	listener := bufconn.Listen(bufSize)
	server := grpc.NewServer()
	bookmarksv1.RegisterBookmarkServiceServer(server, newTestBookmarkServer())

	go func() {
		if err := server.Serve(listener); err != nil {
			t.Logf("bufconn server stopped: %v", err)
		}
	}()

	t.Cleanup(func() {
		server.Stop()
		_ = listener.Close()
	})

	return func(string) (timeoutClient, error) {
		dialer := func(context.Context, string) (net.Conn, error) {
			return listener.Dial()
		}

		return cliClient.NewWithOptions(
			"passthrough:///bufconn",
			grpc.WithContextDialer(dialer),
			grpc.WithTransportCredentials(insecure.NewCredentials()),
		)
	}
}

type testBookmarkServer struct {
	bookmarksv1.UnimplementedBookmarkServiceServer
	nextID    int
	bookmarks map[string]*bookmarksv1.Bookmark
	order     []string
}

func newTestBookmarkServer() *testBookmarkServer {
	return &testBookmarkServer{
		nextID:    1,
		bookmarks: make(map[string]*bookmarksv1.Bookmark),
		order:     []string{},
	}
}

func (s *testBookmarkServer) CreateBookmark(_ context.Context, req *bookmarksv1.CreateBookmarkRequest) (*bookmarksv1.CreateBookmarkResponse, error) {
	if strings.TrimSpace(req.Url) == "" {
		return nil, status.Error(codes.InvalidArgument, "url is required")
	}

	id := fmt.Sprintf("bkm_%04d", s.nextID)
	s.nextID++

	bookmark := &bookmarksv1.Bookmark{
		Id:            id,
		Url:           req.Url,
		Title:         req.Title,
		Description:   req.Description,
		Tags:          dedupe(req.Tags),
		CreatedAtUnix: time.Now().Unix(),
	}
	s.bookmarks[id] = bookmark
	s.order = append(s.order, id)
	return &bookmarksv1.CreateBookmarkResponse{Bookmark: bookmark}, nil
}

func (s *testBookmarkServer) GetBookmark(_ context.Context, req *bookmarksv1.GetBookmarkRequest) (*bookmarksv1.GetBookmarkResponse, error) {
	bookmark, ok := s.bookmarks[req.Id]
	if !ok {
		return nil, status.Errorf(codes.NotFound, "bookmark %s not found", req.Id)
	}
	return &bookmarksv1.GetBookmarkResponse{Bookmark: bookmark}, nil
}

func (s *testBookmarkServer) ListBookmarks(context.Context, *bookmarksv1.ListBookmarksRequest) (*bookmarksv1.ListBookmarksResponse, error) {
	bookmarks := make([]*bookmarksv1.Bookmark, 0, len(s.order))
	for _, id := range s.order {
		bookmarks = append(bookmarks, s.bookmarks[id])
	}
	return &bookmarksv1.ListBookmarksResponse{Bookmarks: bookmarks}, nil
}

func (s *testBookmarkServer) TagBookmark(_ context.Context, req *bookmarksv1.TagBookmarkRequest) (*bookmarksv1.TagBookmarkResponse, error) {
	bookmark, ok := s.bookmarks[req.Id]
	if !ok {
		return nil, status.Errorf(codes.NotFound, "bookmark %s not found", req.Id)
	}
	bookmark.Tags = dedupe(append(bookmark.Tags, req.Tags...))
	return &bookmarksv1.TagBookmarkResponse{Bookmark: bookmark}, nil
}

func (s *testBookmarkServer) DeleteBookmark(_ context.Context, req *bookmarksv1.DeleteBookmarkRequest) (*bookmarksv1.DeleteBookmarkResponse, error) {
	if _, ok := s.bookmarks[req.Id]; !ok {
		return nil, status.Errorf(codes.NotFound, "bookmark %s not found", req.Id)
	}
	delete(s.bookmarks, req.Id)
	filtered := s.order[:0]
	for _, id := range s.order {
		if id != req.Id {
			filtered = append(filtered, id)
		}
	}
	s.order = filtered
	return &bookmarksv1.DeleteBookmarkResponse{Id: req.Id}, nil
}

func dedupe(tags []string) []string {
	seen := make(map[string]struct{}, len(tags))
	out := make([]string, 0, len(tags))
	for _, tag := range tags {
		if _, ok := seen[tag]; ok {
			continue
		}
		seen[tag] = struct{}{}
		out = append(out, tag)
	}
	return out
}

type noopBookmarkServiceClient struct{}

func (noopBookmarkServiceClient) CreateBookmark(context.Context, *bookmarksv1.CreateBookmarkRequest, ...grpc.CallOption) (*bookmarksv1.CreateBookmarkResponse, error) {
	return nil, status.Error(codes.Internal, "unexpected CreateBookmark call")
}

func (noopBookmarkServiceClient) GetBookmark(context.Context, *bookmarksv1.GetBookmarkRequest, ...grpc.CallOption) (*bookmarksv1.GetBookmarkResponse, error) {
	return nil, status.Error(codes.Internal, "unexpected GetBookmark call")
}

func (noopBookmarkServiceClient) ListBookmarks(context.Context, *bookmarksv1.ListBookmarksRequest, ...grpc.CallOption) (*bookmarksv1.ListBookmarksResponse, error) {
	return nil, status.Error(codes.Internal, "unexpected ListBookmarks call")
}

func (noopBookmarkServiceClient) TagBookmark(context.Context, *bookmarksv1.TagBookmarkRequest, ...grpc.CallOption) (*bookmarksv1.TagBookmarkResponse, error) {
	return nil, status.Error(codes.Internal, "unexpected TagBookmark call")
}

func (noopBookmarkServiceClient) DeleteBookmark(context.Context, *bookmarksv1.DeleteBookmarkRequest, ...grpc.CallOption) (*bookmarksv1.DeleteBookmarkResponse, error) {
	return nil, status.Error(codes.Internal, "unexpected DeleteBookmark call")
}
