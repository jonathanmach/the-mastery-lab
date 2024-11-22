class DatabaseService:
    def __init__(self):
        pass

    def get_objects(self):
        return [
            {"name": "Object 1", "quantity": 10},
            {"name": "Object 2", "quantity": 20},
        ]


class ProductService:
    def __init__(self, db: DatabaseService):
        self.db = db

    def get_products(self) -> list[dict]:
        # Get products from database
        return self.db.get_objects()
