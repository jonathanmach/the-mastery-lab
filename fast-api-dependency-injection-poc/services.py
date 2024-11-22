from abc import ABC

from pydantic import BaseModel


class DatabaseService:
    def __init__(self):
        pass


class EmailProvider(ABC):
    def send_email(self, to: str, subject: str, body: str):
        print(f"Sending email to {to} with subject '{subject}' and body '{body}'")


class EmailService:
    def __init__(self, email_provider: EmailProvider):
        self.email_provider = email_provider

    def send_email(self, to: str, subject: str, body: str):
        self.email_provider.send_email(to, subject, body)


class AccountService:
    def __init__(self, db: DatabaseService, email_service: EmailService):
        self.db = db
        self.email_service = email_service

    def create_account(self, email: str, password_hash: str):
        # Save account to database
        # db...

        self.email_service.send_email(
            to=email,
            subject="Welcome!",
            body="You have successfully created an account.",
        )


class Product(BaseModel):
    name: str
    quantity: int


class ProductService:
    def __init__(self,  db: DatabaseService):
        self.db = db
        ...
    def get_products(self) -> list[Product]:
        # Get products from database
        # db...
        return [
            Product(name="Product 1", quantity=10),
            Product(name="Product 2", quantity=20),
        ]
