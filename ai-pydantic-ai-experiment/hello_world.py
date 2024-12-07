from pydantic_ai import Agent
from pydantic import BaseModel
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIModel

# from devtools import debug


class CityLocation(BaseModel):
    city: str
    country: str


client = AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="-")
model = OpenAIModel(model_name="llama3.2:latest", openai_client=client)


def run_hello_world():
    agent = Agent(model, result_type=CityLocation)
    result = agent.run_sync("Where the olympics held in 2012?")
    print(result.data)
    print(result._cost)


if __name__ == "__main__":
    run_hello_world()
