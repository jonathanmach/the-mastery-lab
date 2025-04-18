# Development Log

### TODO
- [ ] Docker: Postgres

### 2025-04-18

- Had to add the following to `pyproject.toml` to get the package to build correctly, since I've changed the package name from `py-uv-fastapi-sqla` to `app`:

```toml
      [tool.hatch.build.targets.wheel]
      packages = ["src/app"]

```
