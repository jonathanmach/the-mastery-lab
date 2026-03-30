from __future__ import annotations

import grpc
import pytest

from bookmarks.v1 import bookmarks_pb2
from app.service import BookmarkService
from app.store import BookmarkStore


class RpcAbort(grpc.RpcError):
    def __init__(self, code: grpc.StatusCode, details: str) -> None:
        super().__init__()
        self._code = code
        self._details = details

    def code(self) -> grpc.StatusCode:
        return self._code

    def details(self) -> str:
        return self._details


class FakeContext:
    def abort(self, code: grpc.StatusCode, details: str):
        raise RpcAbort(code, details)


@pytest.fixture
def service() -> BookmarkService:
    return BookmarkService(BookmarkStore())


@pytest.fixture
def context() -> FakeContext:
    return FakeContext()


def test_create_bookmark_with_valid_url(service: BookmarkService, context: FakeContext) -> None:
    response = service.CreateBookmark(
        bookmarks_pb2.CreateBookmarkRequest(
            url="https://grpc.io/docs/",
            title="Docs",
            description="Official docs",
            tags=["grpc", " docs ", "", "grpc"],
        ),
        context,
    )

    assert response.bookmark.id == "bkm_0001"
    assert response.bookmark.tags == ["grpc", "docs"]


def test_create_bookmark_with_invalid_url_returns_invalid_argument(
    service: BookmarkService, context: FakeContext
) -> None:
    with pytest.raises(RpcAbort) as exc:
        service.CreateBookmark(bookmarks_pb2.CreateBookmarkRequest(url="ftp://grpc.io"), context)

    assert exc.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_get_existing_bookmark(service: BookmarkService, context: FakeContext) -> None:
    created = service.CreateBookmark(bookmarks_pb2.CreateBookmarkRequest(url="https://example.com"), context)

    fetched = service.GetBookmark(bookmarks_pb2.GetBookmarkRequest(id=created.bookmark.id), context)

    assert fetched.bookmark.url == "https://example.com"


def test_get_missing_bookmark_returns_not_found(service: BookmarkService, context: FakeContext) -> None:
    with pytest.raises(RpcAbort) as exc:
        service.GetBookmark(bookmarks_pb2.GetBookmarkRequest(id="missing"), context)

    assert exc.value.code() == grpc.StatusCode.NOT_FOUND


def test_list_preserves_insertion_order(service: BookmarkService, context: FakeContext) -> None:
    first = service.CreateBookmark(bookmarks_pb2.CreateBookmarkRequest(url="https://one.example"), context)
    second = service.CreateBookmark(bookmarks_pb2.CreateBookmarkRequest(url="https://two.example"), context)

    listed = service.ListBookmarks(bookmarks_pb2.ListBookmarksRequest(), context)

    assert [bookmark.id for bookmark in listed.bookmarks] == [first.bookmark.id, second.bookmark.id]


def test_tag_adds_new_tags_and_deduplicates(service: BookmarkService, context: FakeContext) -> None:
    created = service.CreateBookmark(
        bookmarks_pb2.CreateBookmarkRequest(url="https://example.com", tags=["grpc"]),
        context,
    )

    tagged = service.TagBookmark(
        bookmarks_pb2.TagBookmarkRequest(id=created.bookmark.id, tags=["grpc", "proto", " proto "]),
        context,
    )

    assert tagged.bookmark.tags == ["grpc", "proto"]


def test_delete_removes_bookmark(service: BookmarkService, context: FakeContext) -> None:
    created = service.CreateBookmark(bookmarks_pb2.CreateBookmarkRequest(url="https://example.com"), context)

    deleted = service.DeleteBookmark(bookmarks_pb2.DeleteBookmarkRequest(id=created.bookmark.id), context)

    assert deleted.id == created.bookmark.id

    with pytest.raises(RpcAbort) as exc:
        service.GetBookmark(bookmarks_pb2.GetBookmarkRequest(id=created.bookmark.id), context)

    assert exc.value.code() == grpc.StatusCode.NOT_FOUND
