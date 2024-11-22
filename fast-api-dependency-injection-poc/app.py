from fastapi import FastAPI
from rest import accounts_api, products_api
from services import AccountService, DatabaseService, EmailProvider, EmailService, ProductService


def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(accounts_api)
    app.include_router(products_api)


    # Manage dependencies
    db_service = DatabaseService()

    email_service = EmailService(email_provider=EmailProvider())
    account_service = AccountService(email_service=email_service, db=db_service)
    product_service = ProductService(db=db_service)

    # Register dependencies
    app.dependency_overrides[AccountService] = lambda: account_service
    app.dependency_overrides[ProductService] = lambda: product_service

    return app

app = create_app()