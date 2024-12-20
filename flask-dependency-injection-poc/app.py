from functools import wraps
from typing import Callable
from flask import Blueprint, Flask
from flask_injector import FlaskInjector
from flask_pydantic import validate
from injector import Binder, Inject, singleton
from pydantic import BaseModel
from flask_openapi3 import OpenAPI, APIBlueprint



# schemas

class WebhookContract(BaseModel):
    payload: dict

# services
class WebhookService:
    def process_webhook(self, payload):
        print("Processing webhook:", payload)

# decorator that injects user_id into the view
def include_user_id():
    def decorator(f: Callable) -> Callable:
        """
        When you decorate a function with @wraps(original_function), it ensures that:
        1.	The wrapped function (wrapper) retains the metadata (such as the name, docstring, and attributes) of the original function (f).
        2.	The wrapped function looks like the original function in tools and frameworks that inspect function metadata, such as Flask’s app.view_functions.
        """
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_id = "123"
            return f(user_id, *args, **kwargs)
        return wrapper
    return decorator



def create_app():
    app = Flask(__name__)

    @app.route("/")
    def hello_world():
        return "Hello, World!"
        
    # blueprints
    webhooks_api = Blueprint("webhooks_api", __name__)

    @webhooks_api.route("/my-webhook", methods=["POST"])
    @include_user_id()
    def my_webhook(user_id: str, webhook_service: Inject[WebhookService]):
        print(f"user_id={user_id}")
        print(webhook_service.process_webhook({"foo": "bar"}))
        return "Webhook processed successfully"

    @webhooks_api.route("/my-webhook2", methods=["POST"])
    @validate() # Flask-Pydantic
    def my_webhook2(body: WebhookContract, webhook_service: Inject[WebhookService]):
        print(webhook_service.process_webhook(body.payload))
        return "Webhook processed successfully"

    @webhooks_api.route("/my-webhook3", methods=["POST"])
    @validate()
    def my_webhook3(body: WebhookContract):
        # print(webhook_service.process_webhook(body.payload))
        return "Webhook processed successfully"

    flask_openapi3 = APIBlueprint('book', __name__, url_prefix='/api/book')

    @flask_openapi3.post("/flask-openapi3")
    @validate()
    def my_webhook3(body: WebhookContract):
        # print(webhook_service.process_webhook(body.payload))
        return "Webhook processed successfully"

    app.register_blueprint(webhooks_api)
    
    
    
    FlaskInjector(app=app, modules=[setup_di], inject_explicit_only=True)  # Needs to be called *after* all views, signal handlers, template globals and context processors are registered.
    return app

def create_flask_openapi3_app():
    app = OpenAPI(__name__)

    flask_openapi3 = APIBlueprint('book', __name__)

    @flask_openapi3.post("/flask-openapi3")
    def openapi3_endpoint(webhook_service: Inject[WebhookService]):
        # print(webhook_service.process_webhook(body.payload))
        return "Webhook processed successfully"

    app.register_blueprint(flask_openapi3)
    
    
    FlaskInjector(app=app, modules=[setup_di], inject_explicit_only=True)  # Needs to be called *after* all views, signal handlers, template globals and context processors are registered.
    return app


# Dependency configurations
def setup_di(binder: Binder):
    binder.bind(WebhookService, to=WebhookService(), scope=singleton)


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)