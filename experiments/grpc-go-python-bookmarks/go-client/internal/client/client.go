package client

import (
	"context"
	"time"

	bookmarksv1 "github.com/jonathanfmach/the-mastery-lab/experiments/grpc-go-python-bookmarks/go-client/internal/generated/bookmarks/v1"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

type Client struct {
	conn    *grpc.ClientConn
	service bookmarksv1.BookmarkServiceClient
}

func New(addr string) (*Client, error) {
	return NewWithOptions(addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
}

func NewWithOptions(addr string, opts ...grpc.DialOption) (*Client, error) {
	conn, err := grpc.NewClient(addr, opts...)
	if err != nil {
		return nil, err
	}

	return &Client{
		conn:    conn,
		service: bookmarksv1.NewBookmarkServiceClient(conn),
	}, nil
}

func NewForService(service bookmarksv1.BookmarkServiceClient) *Client {
	return &Client{service: service}
}

func (c *Client) Close() error {
	if c.conn == nil {
		return nil
	}
	return c.conn.Close()
}

func (c *Client) WithTimeout() (context.Context, context.CancelFunc) {
	return context.WithTimeout(context.Background(), 3*time.Second)
}

func (c *Client) Service() bookmarksv1.BookmarkServiceClient {
	return c.service
}
