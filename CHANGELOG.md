# Changelog

## 0.1.0 — 2026-05-16

Initial release.

- `Admin` orchestrator + `init_admin(app)` — mounts index / list / detail / create / edit / delete routes under `/admin`.
- `ModelResource` — declarative wrapper over a SQLAlchemy model with knobs for `list_display`, `list_search`, `form_fields`, `readonly_fields`, `page_size`, `can_create/update/delete`, custom `label`, `icon`.
- Type-driven widget picker (checkbox / number / date / datetime / textarea / enum / text), automatic from each column's SQLAlchemy type.
- Search on the list page (`?q=`) backed by ILIKE against the configured columns.
- Pagination.
- Light + dark mode CSS, ~60 lines inline in `_base.html`.
- Built on top of hawkapi-sqlalchemy — picks up the session factory from `init_database(app, ...)`.
