import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ImportStatus(str, enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"
    skipped = "skipped"


class ImportRecord(Base):
    __tablename__ = "import_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_file: Mapped[str] = mapped_column(String, nullable=False, index=True)
    bundle_id: Mapped[str | None] = mapped_column(String, nullable=True)
    resource_type: Mapped[str] = mapped_column(String, nullable=False)
    logical_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    import_status: Mapped[ImportStatus] = mapped_column(SAEnum(ImportStatus), default=ImportStatus.pending)
    validation_errors: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array string
    import_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
