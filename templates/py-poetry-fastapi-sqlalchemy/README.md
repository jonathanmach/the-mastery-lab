

## Useful commands

```bash
poetry run alembic init migrations

poetry run alembic revision --autogenerate -m "Initial migration"

poetry run alembic upgrade head

poetry run alembic current  # To check the database schema status
```