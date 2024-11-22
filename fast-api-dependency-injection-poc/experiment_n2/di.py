from fastapi import Depends
from . import services


def db_service():
    return services.DatabaseService()


def products_service(db=Depends(db_service)):
    return services.ProductService(db=db)
