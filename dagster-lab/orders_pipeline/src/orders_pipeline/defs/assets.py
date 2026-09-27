from pathlib import Path

import dagster as dg
import pandas as pd

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


@dg.asset
def products() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "products.csv")


@dg.asset
def orders() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "orders.csv")


@dg.asset
def product_sales(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    sales = orders.merge(products, left_on="product_id", right_on="id")
    sales["revenue"] = sales["quantity"] * sales["unit_price"]
    return sales


@dg.asset
def category_revenue(product_sales: pd.DataFrame) -> pd.DataFrame:
    return product_sales.groupby("category")["revenue"].sum().reset_index()
