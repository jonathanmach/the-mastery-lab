from flask import Flask

from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware


flask_app = Flask(__name__)


@flask_app.route('/')
def hello_world():
    return 'Hello, World!'



app = FastAPI()


@app.get("/v2")
def read_main():
    return {"message": "Hello World"}


app.mount("/", WSGIMiddleware(flask_app))
