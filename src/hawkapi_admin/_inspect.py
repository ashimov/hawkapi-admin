"""SQLAlchemy model introspection helpers."""

from __future__ import annotations

import datetime as _dt
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import DeclarativeBase, Mapper


@dataclass(slots=True)
class FieldSpec:
    name: str
    python_type: type[Any]
    primary_key: bool = False
    nullable: bool = True
    has_default: bool = False
    is_foreign_key: bool = False
    enum_values: tuple[str, ...] | None = None
    max_length: int | None = None
    is_relationship: bool = False
    relationship_target: type[Any] | None = None


def list_fields(model: type[DeclarativeBase]) -> list[FieldSpec]:
    """Return the column-backed fields of ``model`` in declaration order."""
    mapper: Mapper[Any] = sa_inspect(model)  # type: ignore[arg-type]
    out: list[FieldSpec] = []
    for col in mapper.columns:
        py_type: type[Any] = getattr(col.type, "python_type", str)
        try:
            _ = py_type  # validate access (some SQLA types raise on python_type)
        except NotImplementedError:
            py_type = str
        enum_values: tuple[str, ...] | None = None
        if hasattr(col.type, "enums"):
            enum_values = tuple(getattr(col.type, "enums", ()) or ())
        max_length = getattr(col.type, "length", None)
        out.append(
            FieldSpec(
                name=col.key,
                python_type=py_type,
                primary_key=col.primary_key,
                nullable=bool(col.nullable),
                has_default=col.default is not None or col.server_default is not None,
                is_foreign_key=bool(col.foreign_keys),
                enum_values=enum_values,
                max_length=int(max_length) if isinstance(max_length, int) else None,
            )
        )
    return out


def primary_key_column(model: type[DeclarativeBase]) -> str:
    """Return the name of the first primary-key column."""
    mapper: Mapper[Any] = sa_inspect(model)  # type: ignore[arg-type]
    for col in mapper.columns:
        if col.primary_key:
            return col.key
    raise RuntimeError(f"{model.__name__} has no primary key")


def coerce_value(spec: FieldSpec, raw: str | None) -> Any:
    """Convert a string form value into the column's Python type."""
    if raw is None or raw == "":
        if spec.nullable or spec.has_default:
            return None
        return raw
    t = spec.python_type
    try:
        if t is bool:
            return raw.lower() in {"1", "true", "yes", "on"}
        if t is int:
            return int(raw)
        if t is float:
            return float(raw)
        if t is _dt.date:
            return _dt.date.fromisoformat(raw)
        if t is _dt.datetime:
            return _dt.datetime.fromisoformat(raw)
        if t is uuid.UUID:
            return uuid.UUID(raw)
        return raw
    except (ValueError, TypeError):
        return raw


def widget_for(spec: FieldSpec) -> str:
    """Return a short identifier for the template to pick a widget."""
    if spec.enum_values:
        return "enum"
    t = spec.python_type
    if t is bool:
        return "checkbox"
    if t in (int, float):
        return "number"
    if t is _dt.date:
        return "date"
    if t is _dt.datetime:
        return "datetime"
    if spec.max_length is not None and spec.max_length > 500:
        return "textarea"
    return "text"


__all__ = [
    "FieldSpec",
    "coerce_value",
    "list_fields",
    "primary_key_column",
    "widget_for",
]
