
# Goals
Experiment with alternative approaches to inject dependencies in a Flask application.




## Journal log
#### `2024-11-19`  Challenge #2: Flask-Pydantic conflict with Flask-Injector
Problem: Flask-Pydantic tries to validate the type of injected dependecy.
...

Testing **flask_openapi3** with **flask_injector**.
injector: `call_with_injection()` L1050: `return callable(*full_args, **dependencies)`
scaffold.APIScaffold.create_view_func.view_func() L104 `_validate_request()`, the injected dependency is considered a `path_kwargs`, which gets validated and the dependency is stripped from kwargs 🫠


#### `2024-11-18`  Challenge #1: flask_injector trying to inject dependencies for every type hint
* Working on jstasiak's suggestion in: https://github.com/python-injector/flask_injector/issues/83, which involves replacing `get_type_hints()` with `injector.get_bindings()` to detect if we actually have anything to inject.
* I'm ready to submmit a PR for this issue, just need to think about the devX of setting this behavior, as well as the tests.
* Raised a PR for this issue: https://github.com/python-injector/flask_injector/pull/85

# Resources
* [Dependency injection in Python](https://snyk.io/blog/dependency-injection-python/)