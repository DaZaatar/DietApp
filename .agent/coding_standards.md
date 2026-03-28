# Coding Standards

## General
- Keep modules cohesive and explicit
- Favor simple service methods over abstraction-heavy patterns
- Use env vars for all secrets and model/provider config
- Validate AI outputs against strict JSON schemas

## Backend
- Use SQLAlchemy 2.0 style
- Keep routers thin; business logic in services
- Return typed response schemas

## Frontend
- Mobile-first responsive layout
- Feature folders with localized components/hooks
- Avoid coupling UI components to storage/provider details

## Media Handling
- Store attachment metadata in DB
- Use storage abstraction interface for binary persistence