# hawkapi-admin

Auto-generated admin UI for [HawkAPI](https://github.com/Hawk-API/HawkAPI) + [hawkapi-sqlalchemy](https://pypi.org/project/hawkapi-sqlalchemy/) models. Drop your model classes in and get list / detail / create / edit / delete views mounted under `/admin` — no boilerplate, no React, no JSON-schema duplication.

## Install

```bash
pip install hawkapi-admin
```

## Quickstart

```python
from hawkapi import HawkAPI
from hawkapi_sqlalchemy import Base, TimestampMixin, init_database
from sqlalchemy.orm import Mapped, mapped_column

from hawkapi_admin import Admin, ModelResource, init_admin


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(default="")


app = HawkAPI()
init_database(app, url="postgresql+asyncpg://…/myapp")

admin = init_admin(app, title="My App")
admin.register(User)                            # simplest form
```

Visit `/admin` — you get the index page, `/admin/user` (list), `/admin/user/new` (create form), `/admin/user/{id}` (detail), `/admin/user/{id}/edit`, and `POST /admin/user/{id}/delete`. All with sane widgets picked from each column's SQLAlchemy type.

## Customizing a resource

```python
from hawkapi_admin import ModelResource

admin.register(ModelResource(
    model=User,
    label="Account",
    label_plural="Accounts",
    icon="👤",
    list_display=("id", "email", "created_at"),
    list_search=("email", "name"),
    form_fields=("email", "name"),
    readonly_fields=("created_at",),
    page_size=25,
    can_delete=False,
))
```

| Option              | Default                         | Effect                                                        |
|---------------------|---------------------------------|---------------------------------------------------------------|
| `name`              | lowercased class name           | URL slug (`/admin/<name>`)                                    |
| `label`             | class name                      | Heading on detail / form                                      |
| `label_plural`      | `label + "s"`                   | Nav label & list-page heading                                 |
| `icon`              | `""`                            | Prepended to nav label                                        |
| `list_display`      | every column                    | Columns shown on the list page                                |
| `list_search`       | `()`                            | Columns searched by `?q=...` (LIKE)                           |
| `form_fields`       | every non-PK column             | Columns shown in the form                                     |
| `readonly_fields`   | `()`                            | Columns rendered but not editable                             |
| `page_size`         | `50`                            | Rows per list page                                            |
| `can_create / can_update / can_delete` | `True`                | Toggles the corresponding routes off                          |

## Widgets

`hawkapi-admin` picks an input widget per column type, automatically:

- `bool` → checkbox
- `int` / `float` → `<input type="number">`
- `date` / `datetime` → matching native input
- `String(length > 500)` → textarea
- `Enum` → `<select>` with the declared choices
- everything else → `<input type="text">`

## Authentication

The plugin doesn't ship its own auth — it picks up whatever middleware you already attached. Combine with [hawkapi-auth](https://pypi.org/project/hawkapi-auth/) and gate the admin prefix:

```python
from hawkapi_auth import requires_scopes


admin = Admin(title="Admin", url_prefix="/admin")
admin.register(User)
admin.attach(app)


@app.middleware("http")
async def gate_admin(request, call_next):
    if request.url.path.startswith("/admin"):
        # raises 401/403 if the JWT is missing / lacks the scope
        await requires_scopes("admin:read")(request)
    return await call_next(request)
```

## Theming

The bundled CSS is roughly 60 lines, prefers system colors (light + dark mode), and lives inline in `_base.html` — copy that template into your own `templates/` directory if you want to restyle. Jinja `extends "_base.html"` keeps working as long as the same blocks (`title`, `content`) are defined.

## Development

```bash
git clone https://github.com/Hawk-API/hawkapi-admin.git
cd hawkapi-admin
uv sync --extra dev
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
uv run pyright src/
```

## License

MIT.
