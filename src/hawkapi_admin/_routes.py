"""Route handlers — list / detail / create / edit / delete."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hawkapi import HTTPException, Request
from hawkapi.responses import HTMLResponse, RedirectResponse, Response
from hawkapi_sqlalchemy import resolve_database
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import func, or_, select

from ._inspect import coerce_value, widget_for
from ._resource import ModelResource

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _build_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        enable_async=True,
    )
    env.globals["widget_for"] = widget_for  # type: ignore[assignment]
    return env


_env = _build_env()


def _resource(admin: Any, name: str) -> ModelResource:
    found = admin.resources.get(name)
    if found is None:
        raise HTTPException(404, detail=f"Unknown resource {name!r}")
    return found


def _session_factory(request: Request) -> Any:
    db = resolve_database(request.scope.get("app"))
    if db is None:
        raise HTTPException(
            500, detail="Database not configured — call init_database(app, ...) first"
        )
    return db.session


async def _render(template: str, **context: Any) -> Response:
    tpl = _env.get_template(template)
    body = await tpl.render_async(**context)
    return HTMLResponse(body)


async def index(request: Request, *, admin: Any) -> Response:
    return await _render(
        "index.html",
        admin=admin,
        resources=list(admin.resources.values()),
    )


async def list_resource(request: Request, *, admin: Any) -> Response:
    name = str(request.path_params["resource"])
    res = _resource(admin, name)
    q = request.query_params.get("q", "")
    page = max(1, int(request.query_params.get("page", "1") or 1))
    sessions = _session_factory(request)

    stmt = select(res.model)
    count_stmt = select(func.count()).select_from(res.model)
    if q and res.list_search:
        conditions = []
        for col_name in res.list_search:
            col = getattr(res.model, col_name)
            conditions.append(col.cast(__import__("sqlalchemy").String).ilike(f"%{q}%"))  # type: ignore[no-untyped-call]
        stmt = stmt.where(or_(*conditions))
        count_stmt = count_stmt.where(or_(*conditions))
    stmt = stmt.offset((page - 1) * res.page_size).limit(res.page_size)

    async with sessions(commit=False) as sess:
        rows = (await sess.execute(stmt)).scalars().all()
        total = int((await sess.execute(count_stmt)).scalar() or 0)
    return await _render(
        "list.html",
        admin=admin,
        resource=res,
        rows=rows,
        page=page,
        page_size=res.page_size,
        total=total,
        q=q,
        pages=(total + res.page_size - 1) // res.page_size,
    )


async def detail(request: Request, *, admin: Any) -> Response:
    name = str(request.path_params["resource"])
    res = _resource(admin, name)
    pk = request.path_params["pk"]
    sessions = _session_factory(request)
    async with sessions(commit=False) as sess:
        obj = await sess.get(res.model, pk)
        if obj is None:
            raise HTTPException(404)
    return await _render("detail.html", admin=admin, resource=res, obj=obj)


async def edit_form(request: Request, *, admin: Any) -> Response:
    name = str(request.path_params["resource"])
    res = _resource(admin, name)
    pk = request.path_params.get("pk")
    sessions = _session_factory(request)
    obj = None
    if pk is not None:
        if not res.can_update:
            raise HTTPException(403)
        async with sessions(commit=False) as sess:
            obj = await sess.get(res.model, pk)
            if obj is None:
                raise HTTPException(404)
    else:
        if not res.can_create:
            raise HTTPException(403)
    values: dict[str, Any] = (
        {f.name: getattr(obj, f.name, "") for f in res.editable_fields()} if obj else {}
    )
    return await _render(
        "form.html",
        admin=admin,
        resource=res,
        obj=obj,
        values=values,
        errors={},
    )


async def save(request: Request, *, admin: Any) -> Response:
    name = str(request.path_params["resource"])
    res = _resource(admin, name)
    pk = request.path_params.get("pk")
    sessions = _session_factory(request)
    form = await request.form()
    values: dict[str, Any] = {}
    for fs in res.editable_fields():
        raw = form.get(fs.name)
        coerced = coerce_value(fs, raw if isinstance(raw, str) else None)
        # Skip empty values for columns with DB-side / Python defaults — let the
        # default kick in on insert, and don't clobber the existing value on update.
        if coerced is None and fs.has_default:
            continue
        values[fs.name] = coerced
    async with sessions() as sess:
        if pk is not None:
            if not res.can_update:
                raise HTTPException(403)
            obj = await sess.get(res.model, pk)
            if obj is None:
                raise HTTPException(404)
            for k, v in values.items():
                setattr(obj, k, v)
        else:
            if not res.can_create:
                raise HTTPException(403)
            obj = res.model(**values)
            sess.add(obj)
        await sess.flush()
        new_pk = getattr(obj, res.primary_key)
    return RedirectResponse(f"{admin.url_prefix}/{name}/{new_pk}", status_code=303)


async def delete(request: Request, *, admin: Any) -> Response:
    name = str(request.path_params["resource"])
    res = _resource(admin, name)
    if not res.can_delete:
        raise HTTPException(403)
    pk = request.path_params["pk"]
    sessions = _session_factory(request)
    async with sessions() as sess:
        obj = await sess.get(res.model, pk)
        if obj is None:
            raise HTTPException(404)
        await sess.delete(obj)
    return RedirectResponse(f"{admin.url_prefix}/{name}", status_code=303)


__all__ = ["delete", "detail", "edit_form", "index", "list_resource", "save"]
