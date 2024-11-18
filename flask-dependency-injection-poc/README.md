



## Journal log
#### `2024-11-18`
* Working on jstasiak's suggestion in: https://github.com/python-injector/flask_injector/issues/83, which involves replacing `get_type_hints()` with `injector.get_bindings()` to detect if we actually have anything to inject.
* I'm ready to submmit a PR for this issue, just need to think about the devX of setting this behavior, as well as the tests.



# Resources
* [Dependency injection in Python](https://snyk.io/blog/dependency-injection-python/)