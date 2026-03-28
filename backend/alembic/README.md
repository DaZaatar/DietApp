Alembic baseline for DietApp modular monolith.

Generate the first migration after setting `DATABASE_URL`:

- `alembic revision --autogenerate -m "init"`
- `alembic upgrade head`
