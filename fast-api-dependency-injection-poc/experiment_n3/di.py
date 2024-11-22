from fastapi import Depends
from . import services
import logging
from typing import Generator


def logger() -> logging.Logger:
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)


def db_service(
    logger=Depends(logger),
) -> Generator[services.DatabaseService, None, None]:
    """
    📝 You can declare a request-bound dependency by defining a function or class without
    specifying any special scope. By default, FastAPI dependencies are request-scoped.
    """
    # db = create_db_connection()
    try:
        logger.info("Borrowing an available connection from the pool...")
        yield services.DatabaseService()
    finally:
        # db.close()
        ...


def products_service(
    db=Depends(db_service), logger=Depends(logger)
) -> services.ProductService:
    logger.info("Instantiating ProductService...")
    return services.ProductService(db=db)
