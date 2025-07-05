from project_a.dependency import my_value


def hello() -> None:
    print(f"Hello from project-a! Value: {my_value}")


if __name__ == "__main__":
    hello()
