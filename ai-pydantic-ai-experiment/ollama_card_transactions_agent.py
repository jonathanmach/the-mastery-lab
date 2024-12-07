import csv
from typing import List
from uuid import uuid4
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIModel


class BaseTransaction(BaseModel):
    id: str
    description: str = Field(description="The description of the transaction.")


class CategorizedTransaction(BaseModel):
    merchant: str
    category: str = Field(
        description="The category of the transaction (e.g., groceries, entertainment, etc).",
        min_length=1,
    )
    subcategory: str = Field(
        description="The subcategory of the transaction (e.g., supermarket, streaming, etc)."
    )
    confidence: float = Field(description="The confidence of the categorization.")


client = AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="-")
model = OpenAIModel(model_name="llama3.2:latest", openai_client=client)


def categorize_transactions(transactions: List[BaseTransaction]):
    categorized_transactions = []
    agent = Agent(
        model, result_type=CategorizedTransaction, retries=6, result_retries=6
    )
    for transaction in transactions:
        print(f"\nProcessing transaction: {transaction.description}")

        # Format the query for categorization
        tx_json = transaction.model_dump_json(include={"description", "amount"})
        query = "Categorize the following transaction:\n" + f"{tx_json}"

        # Run the agent synchronously for each transaction
        try:
            result = agent.run_sync(query)
        except Exception as e:
            print(f"❌ Error processing transaction: {transaction.description} \n {e}")
            continue

        categorized_tx = result.data
        print(
            f"✅ Categorized as: {categorized_tx.category}. Confidence: {categorized_tx.confidence}"
        )
        categorized_transactions.append(categorized_tx)

    return categorized_transactions


class AmexTransaction(BaseTransaction):
    id: str = Field(default_factory=lambda: str(uuid4()))
    date: str
    description: str
    card_member: str
    account_number: str
    amount: float


def get_amex_transactions(file_path: str):
    transactions = []
    with open(file_path, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip the header row

        for row in reader:
            # Date,Description,Card Member,Account #,Amount
            transaction = AmexTransaction(
                date=row[0],
                description=row[1],
                card_member=row[2],
                account_number=row[3],
                amount=float(row[4]),
            )
            transactions.append(transaction)
    return transactions


FILE_PATH = "/Users/jonathan/Downloads/activity.csv"


def run_transaction_categorization():
    transactions = get_amex_transactions(FILE_PATH)
    categorized_transactions = categorize_transactions(transactions)
    print(categorized_transactions)


if __name__ == "__main__":
    run_transaction_categorization()
