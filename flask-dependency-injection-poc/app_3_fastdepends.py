from functools import wraps
from typing import Annotated, Callable
from flask import Blueprint, Flask
from pydantic import BaseModel
from fast_depends import inject, Depends
from fast_depends.library import CustomField

# schemas


class WebhookRequest(BaseModel):
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


# blueprints
webhooks_api = Blueprint("webhooks_api", __name__)


def get_webhook_service():
    return WebhookService()


# ✅ Experiment #1: Ability to inject the service into the view
@webhooks_api.route("/exp1", methods=["GET"])
@inject
def my_webhook(webhook_service=Depends(get_webhook_service)):
    print(webhook_service.process_webhook({"foo": "bar"}))
    return "Webhook processed successfully"


class Validate(CustomField):
    def get_body_dict(self):
        # inspired on flask_pydantic: https://github.com/bauerji/flask-pydantic/blob/8595fa8b5513a336c9c679829f49ddc20f56377d/flask_pydantic/core.py#L87
        from flask import request

        data = request.get_json()
        if data is None:
            return {}
        return data

    def use(self, /, **kwargs):
        if self.param_name == "body":
            kwargs = super().use(**kwargs)
            kwargs["body"] = self.get_body_dict()
            return kwargs


# ✅ Experiment #1.2: Request validation using Pydantic. Based on: https://lancetnik.github.io/FastDepends/#usage
# 💥 Challenge A: `@inject` (see source code) can't see the request body because Flask doesn't pass it to the view (see `flask/app.py/Flask.dispatch_request` source code)
#       and (of course), the library doesn't have Flask as a dependency.
#       ✅ Solved: we need to use a custom field that will extract the request body from Flask.request,
#       implemented through the `Validate` class
@webhooks_api.route("/exp1.2", methods=["POST"])
@inject
def request_validation(body: WebhookRequest = Validate()):
    """
    @inject decorator plays multiple roles at the same time:
    - resolve Depends classes
    - cast types according to Python annotation
    - validate incoming parameters using pydantic
    """
    print(body)
    return "Webhook processed successfully"


# ✅ Experiment #2: DI injection + request validation
#   Discovery A: can use type aliasing to make the code more readable, less verbose, and more maintainable!
#       Eg: WebhooksService = Annotated[WebhookService, Depends(get_webhook_service)]
WebhooksService = Annotated[WebhookService, Depends(get_webhook_service)]


@webhooks_api.route("/exp2", methods=["POST"])
@inject
def my_webhook2(
    # webhooks_service: WebhooksService, # 💥 see Challenge #3/A
    webhooks_service: WebhookService = Depends(get_webhook_service),
    body: WebhookRequest = Validate(),
):
    webhooks_service.process_webhook(body.payload)
    return "Webhook processed successfully"


# Experiment #3: Dependencies Overriding (Testing) - see test_app.py
# 💥 Challenge A: override seems to work with Exp#1, which uses `Depends(get_webhook_service)`, but not
#       with alias: `WebhooksService = Annotated[WebhookService, Depends(get_webhook_service)]`, nor `webhooks_service: WebhookService = Depends(get_webhook_service)`
#
#       Error: pydantic_core._pydantic_core.ValidationError: 1 validation error for my_webhook2
#       webhooks_service
#       Input should be an instance of WebhookService [type=is_instance_of, input_value=<test_app_3_fastdepends.g...bject at 0xffff9bc4eaa0>, input_type=get_fake_webhook_service.<locals>.FakeWebhookService]
#       For further information visit https://errors.pydantic.dev/2.9/v/is_instance_of
#       (The same issue doesn't happen on FastAPI)
#       
#       @2024-11-24: Opened issue: https://github.com/Lancetnik/FastDepends/issues/150
#

def create_app():
    app = Flask(__name__)

    @app.route("/")
    def hello_world():
        return """
        <html>
            <body>
                <form id="myForm">
                    <input type="submit" value="Submit to /exp2">
                </form>
                <script>
                    document.getElementById('myForm').addEventListener('submit', function(event) {
                        event.preventDefault();
                        fetch('/exp2', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({"payload": {"foo": "bar"}})
                        }).then(response => response.json()).then(data => {
                            console.log(data);
                        });
                    });
                </script>
            </body>
        </html>
        """

    app.register_blueprint(webhooks_api)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
