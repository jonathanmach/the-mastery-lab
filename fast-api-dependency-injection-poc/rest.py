from typing import Annotated
from fastapi import APIRouter, Depends
from services import AccountService, ProductService

accounts_api = APIRouter()


@accounts_api.post("/accounts", response_model=None)
def create_account(account_service: AccountService = Depends()):
    print("In: create_account")

    # handoff to service
    account_service.create_account("john", "1234")

    return {"message": "Account created successfully"}


products_api = APIRouter()


@products_api.get("/products", response_model=None)
def list_products(product_service: Annotated[ProductService, Depends()]):
    # handoff to service
    products = product_service.get_products()

    return {"data": products}
