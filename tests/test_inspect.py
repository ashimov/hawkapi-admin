"""Model introspection helpers."""

from __future__ import annotations

import datetime as _dt

from hawkapi_admin import FieldSpec, coerce_value, list_fields, primary_key_column, widget_for

from .conftest import User


def test_list_fields_returns_all_columns() -> None:
    fields = list_fields(User)
    names = [f.name for f in fields]
    assert "id" in names
    assert "email" in names
    assert "name" in names


def test_primary_key_column() -> None:
    assert primary_key_column(User) == "id"


def test_widget_for_text() -> None:
    f = FieldSpec(name="x", python_type=str, max_length=255)
    assert widget_for(f) == "text"


def test_widget_for_textarea_when_long() -> None:
    f = FieldSpec(name="x", python_type=str, max_length=2000)
    assert widget_for(f) == "textarea"


def test_widget_for_bool() -> None:
    f = FieldSpec(name="x", python_type=bool)
    assert widget_for(f) == "checkbox"


def test_widget_for_number() -> None:
    f = FieldSpec(name="x", python_type=int)
    assert widget_for(f) == "number"


def test_widget_for_date() -> None:
    f = FieldSpec(name="x", python_type=_dt.date)
    assert widget_for(f) == "date"


def test_widget_for_enum() -> None:
    f = FieldSpec(name="status", python_type=str, enum_values=("draft", "active"))
    assert widget_for(f) == "enum"


def test_coerce_int_value() -> None:
    f = FieldSpec(name="x", python_type=int, nullable=False)
    assert coerce_value(f, "42") == 42


def test_coerce_bool_value() -> None:
    f = FieldSpec(name="x", python_type=bool, nullable=False)
    assert coerce_value(f, "1") is True
    assert coerce_value(f, "0") is False


def test_coerce_empty_to_none_when_nullable() -> None:
    f = FieldSpec(name="x", python_type=str, nullable=True)
    assert coerce_value(f, "") is None


def test_coerce_date_value() -> None:
    f = FieldSpec(name="d", python_type=_dt.date)
    assert coerce_value(f, "2026-01-15") == _dt.date(2026, 1, 15)


def test_coerce_bad_int_returns_raw() -> None:
    f = FieldSpec(name="x", python_type=int)
    # Best-effort: invalid input is returned as-is so the caller / DB can object.
    assert coerce_value(f, "not-int") == "not-int"
