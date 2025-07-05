import os
import sys


path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../project_a/src"))
if not os.path.exists(path):
    error = f"Path {path} does not exist. Ensure the project_a/src directory is correct."
    raise ImportError(error)

sys.path.append(path)
from project_a import main


def main_b() -> None:
    print("Hello from project-b!")
    main.hello()


if __name__ == "__main__":
    main_b()
