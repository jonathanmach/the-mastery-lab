from __future__ import annotations

from datetime import datetime, UTC
import logging
from urllib.parse import urlparse

import grpc

from bookmarks.v1 import bookmarks_pb2, bookmarks_pb2_grpc
from app.store import BookmarkRecord, BookmarkStore

LOGGER = logging.getLogger(__name__)


def normalize_tags(raw_tags: list[str]) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for raw_tag in raw_tags:
        tag = raw_tag.strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)
    return tags


def is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


class BookmarkService(bookmarks_pb2_grpc.BookmarkServiceServicer):
    def __init__(self, store: BookmarkStore | None = None) -> None:
        self._store = store or BookmarkStore()

    def CreateBookmark(self, request, context):
        LOGGER.info("CreateBookmark url=%s", request.url)
        if not request.url.strip():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "url is required")
        if not is_valid_url(request.url):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "url must start with http:// or https://")

        record = self._store.create(
            url=request.url.strip(),
            title=request.title.strip(),
            description=request.description.strip(),
            tags=normalize_tags(list(request.tags)),
            created_at_unix=int(datetime.now(tz=UTC).timestamp()),
        )
        return bookmarks_pb2.CreateBookmarkResponse(bookmark=self._to_proto(record))

    def GetBookmark(self, request, context):
        LOGGER.info("GetBookmark id=%s", request.id)
        record = self._store.get(request.id)
        if record is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"bookmark {request.id} not found")
        return bookmarks_pb2.GetBookmarkResponse(bookmark=self._to_proto(record))

    def ListBookmarks(self, request, context):
        LOGGER.info("ListBookmarks")
        del request, context
        bookmarks = [self._to_proto(record) for record in self._store.list()]
        return bookmarks_pb2.ListBookmarksResponse(bookmarks=bookmarks)

    def TagBookmark(self, request, context):
        LOGGER.info("TagBookmark id=%s", request.id)
        record = self._store.get(request.id)
        if record is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"bookmark {request.id} not found")

        merged_tags = normalize_tags([*record.tags, *list(request.tags)])
        updated = self._store.tag(request.id, merged_tags)
        assert updated is not None
        return bookmarks_pb2.TagBookmarkResponse(bookmark=self._to_proto(updated))

    def DeleteBookmark(self, request, context):
        LOGGER.info("DeleteBookmark id=%s", request.id)
        deleted = self._store.delete(request.id)
        if not deleted:
            context.abort(grpc.StatusCode.NOT_FOUND, f"bookmark {request.id} not found")
        return bookmarks_pb2.DeleteBookmarkResponse(id=request.id)

    @staticmethod
    def _to_proto(record: BookmarkRecord) -> bookmarks_pb2.Bookmark:
        return bookmarks_pb2.Bookmark(
            id=record.id,
            url=record.url,
            title=record.title,
            description=record.description,
            tags=record.tags,
            created_at_unix=record.created_at_unix,
        )
