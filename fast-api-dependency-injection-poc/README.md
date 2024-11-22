# FastAPI dependency injection

Experimenting with dependency injection in FastAPI. Exploring complex use cases, nested dependecies, dev experience and potential pitfalls.

The goal is to find a clean and maintainable way to set-up dependencies in FastAPI.

## Experimentation log

#### `@2024-11-22`: Dedicated module for setting up dependencies

![Custom Badge](https://img.shields.io/badge/Outcome-✅_Success-brightgreen)

Decided to stop fighting the `Depends(get_dependency)` approach and
create a `di` module where all dependencies are set-up, which is then imported in the main app module. This makes the main app module cleaner and more readable.

See [experiment_n3/main.py](./experiment_n3/main.py) for more details.

---

#### `@2024-11-22`: Empty `Depends()` in FastAPI

![Custom Badge](https://img.shields.io/badge/Outcome-❌_Failed-red)

I was hoping to keep `Depends()` empty, instead of having to tight-couple it to a real callable. The rationale is to keep the dependency injection as abstract as possible.

```python
@products_api.get("/products")
def list_products(product_service: ProductService = Depends()):
    return product_service.get_products()
```

See [app_issue_1.py](app_issue_1.py) for more details.
