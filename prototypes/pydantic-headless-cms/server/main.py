import uvicorn


def main() -> None:
    uvicorn.run("api:app", host="0.0.0.0", port=8004, reload=True)


if __name__ == "__main__":
    main()
