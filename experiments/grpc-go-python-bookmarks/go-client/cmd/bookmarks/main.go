package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"os"
	"strings"

	cliClient "github.com/jonathanfmach/the-mastery-lab/experiments/grpc-go-python-bookmarks/go-client/internal/client"
	bookmarksv1 "github.com/jonathanfmach/the-mastery-lab/experiments/grpc-go-python-bookmarks/go-client/internal/generated/bookmarks/v1"
)

type bookmarkClient interface {
	Close() error
	WithTimeout() (context.Context, context.CancelFunc)
	Service() bookmarksv1.BookmarkServiceClient
}

type timeoutClient interface {
	Close() error
	WithTimeout() (context.Context, context.CancelFunc)
	Service() bookmarksv1.BookmarkServiceClient
}

var newClient = func(addr string) (timeoutClient, error) {
	return cliClient.New(addr)
}

type multiFlag []string

func (m *multiFlag) String() string {
	return strings.Join(*m, ",")
}

func (m *multiFlag) Set(value string) error {
	*m = append(*m, value)
	return nil
}

func main() {
	os.Exit(run(os.Args[1:], os.Stdout, os.Stderr))
}

func run(args []string, stdout io.Writer, stderr io.Writer) int {
	root := flag.NewFlagSet("bookmarks", flag.ExitOnError)
	root.SetOutput(stderr)
	addr := root.String("addr", "127.0.0.1:50051", "gRPC server address")
	root.Usage = func() {
		fmt.Fprintln(stderr, "Usage: bookmarks [--addr host:port] <create|get|list|tag|delete> [flags]")
	}

	if err := root.Parse(args); err != nil {
		return exitErr(stderr, err)
	}

	remaining := root.Args()
	if len(remaining) == 0 {
		root.Usage()
		return 1
	}

	client, err := newClient(*addr)
	if err != nil {
		return exitErr(stderr, err)
	}
	defer client.Close()

	var runErr error
	switch remaining[0] {
	case "create":
		runErr = runCreate(client, remaining[1:], stdout, stderr)
	case "get":
		runErr = runGet(client, remaining[1:], stdout, stderr)
	case "list":
		runErr = runList(client, remaining[1:], stdout, stderr)
	case "tag":
		runErr = runTag(client, remaining[1:], stdout, stderr)
	case "delete":
		runErr = runDelete(client, remaining[1:], stdout, stderr)
	default:
		root.Usage()
		return 1
	}

	if runErr != nil {
		return exitErr(stderr, runErr)
	}

	return 0
}

func runCreate(client timeoutClient, args []string, stdout io.Writer, stderr io.Writer) error {
	fs := flag.NewFlagSet("create", flag.ExitOnError)
	fs.SetOutput(stderr)
	url := fs.String("url", "", "bookmark URL")
	title := fs.String("title", "", "bookmark title")
	description := fs.String("description", "", "bookmark description")
	var tags multiFlag
	fs.Var(&tags, "tag", "bookmark tag (repeatable)")
	if err := parse(fs, args); err != nil {
		return err
	}

	if strings.TrimSpace(*url) == "" {
		return fmt.Errorf("create requires --url")
	}

	ctx, cancel := client.WithTimeout()
	defer cancel()

	response, err := client.Service().CreateBookmark(ctx, &bookmarksv1.CreateBookmarkRequest{
		Url:         *url,
		Title:       *title,
		Description: *description,
		Tags:        tags,
	})
	if err != nil {
		return err
	}

	fmt.Fprintln(stdout, "created bookmark:")
	printBookmark(stdout, response.Bookmark)
	return nil
}

func runGet(client timeoutClient, args []string, stdout io.Writer, stderr io.Writer) error {
	fs := flag.NewFlagSet("get", flag.ExitOnError)
	fs.SetOutput(stderr)
	id := fs.String("id", "", "bookmark ID")
	if err := parse(fs, args); err != nil {
		return err
	}

	if strings.TrimSpace(*id) == "" {
		return fmt.Errorf("get requires --id")
	}

	ctx, cancel := client.WithTimeout()
	defer cancel()

	response, err := client.Service().GetBookmark(ctx, &bookmarksv1.GetBookmarkRequest{Id: *id})
	if err != nil {
		return err
	}

	printBookmark(stdout, response.Bookmark)
	return nil
}

func runList(client timeoutClient, args []string, stdout io.Writer, stderr io.Writer) error {
	fs := flag.NewFlagSet("list", flag.ExitOnError)
	fs.SetOutput(stderr)
	if err := parse(fs, args); err != nil {
		return err
	}

	ctx, cancel := client.WithTimeout()
	defer cancel()

	response, err := client.Service().ListBookmarks(ctx, &bookmarksv1.ListBookmarksRequest{})
	if err != nil {
		return err
	}

	if len(response.Bookmarks) == 0 {
		fmt.Fprintln(stdout, "no bookmarks found")
		return nil
	}

	for index, bookmark := range response.Bookmarks {
		fmt.Fprintf(stdout, "%d. %s\n", index+1, bookmark.Id)
		printBookmark(stdout, bookmark)
	}
	return nil
}

func runTag(client timeoutClient, args []string, stdout io.Writer, stderr io.Writer) error {
	fs := flag.NewFlagSet("tag", flag.ExitOnError)
	fs.SetOutput(stderr)
	id := fs.String("id", "", "bookmark ID")
	var tags multiFlag
	fs.Var(&tags, "tag", "tag to add (repeatable)")
	if err := parse(fs, args); err != nil {
		return err
	}

	if strings.TrimSpace(*id) == "" {
		return fmt.Errorf("tag requires --id")
	}
	if len(tags) == 0 {
		return fmt.Errorf("tag requires at least one --tag")
	}

	ctx, cancel := client.WithTimeout()
	defer cancel()

	response, err := client.Service().TagBookmark(ctx, &bookmarksv1.TagBookmarkRequest{
		Id:   *id,
		Tags: tags,
	})
	if err != nil {
		return err
	}

	fmt.Fprintln(stdout, "updated bookmark:")
	printBookmark(stdout, response.Bookmark)
	return nil
}

func runDelete(client timeoutClient, args []string, stdout io.Writer, stderr io.Writer) error {
	fs := flag.NewFlagSet("delete", flag.ExitOnError)
	fs.SetOutput(stderr)
	id := fs.String("id", "", "bookmark ID")
	if err := parse(fs, args); err != nil {
		return err
	}

	if strings.TrimSpace(*id) == "" {
		return fmt.Errorf("delete requires --id")
	}

	ctx, cancel := client.WithTimeout()
	defer cancel()

	response, err := client.Service().DeleteBookmark(ctx, &bookmarksv1.DeleteBookmarkRequest{Id: *id})
	if err != nil {
		return err
	}

	fmt.Fprintf(stdout, "deleted bookmark %s\n", response.Id)
	return nil
}

func parse(fs *flag.FlagSet, args []string) error {
	return fs.Parse(args)
}

func printBookmark(stdout io.Writer, bookmark *bookmarksv1.Bookmark) {
	if bookmark == nil {
		fmt.Fprintln(stdout, "bookmark: <nil>")
		return
	}

	fmt.Fprintf(stdout, "  id: %s\n", bookmark.Id)
	fmt.Fprintf(stdout, "  url: %s\n", bookmark.Url)
	if bookmark.Title != "" {
		fmt.Fprintf(stdout, "  title: %s\n", bookmark.Title)
	}
	if bookmark.Description != "" {
		fmt.Fprintf(stdout, "  description: %s\n", bookmark.Description)
	}
	if len(bookmark.Tags) > 0 {
		fmt.Fprintf(stdout, "  tags: %s\n", strings.Join(bookmark.Tags, ", "))
	}
	fmt.Fprintf(stdout, "  created_at_unix: %d\n", bookmark.CreatedAtUnix)
}

func exitErr(stderr io.Writer, err error) int {
	fmt.Fprintln(stderr, err)
	return 1
}
