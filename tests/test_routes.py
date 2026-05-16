"""End-to-end smoke tests against the mounted admin routes."""

from __future__ import annotations

from hawkapi import HawkAPI
from hawkapi.testing import TestClient

from hawkapi_admin import Admin


def test_index_lists_resources(app: HawkAPI, admin: Admin) -> None:
    r = TestClient(app).get(admin.url_prefix)
    assert r.status_code == 200
    body = r.text
    assert "Test Admin" in body
    assert "Users" in body


def test_empty_list_page_renders(app: HawkAPI, admin: Admin) -> None:
    r = TestClient(app).get(f"{admin.url_prefix}/user")
    assert r.status_code == 200
    assert "No users yet" in r.text or "users" in r.text.lower()


def test_create_and_list_user(app: HawkAPI, admin: Admin) -> None:
    client = TestClient(app)
    new_form = client.get(f"{admin.url_prefix}/user/new")
    assert new_form.status_code == 200
    assert "Email" in new_form.text or "email" in new_form.text

    r = client.post(
        f"{admin.url_prefix}/user/new",
        body=b"email=a%40b.c&name=Alice",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code in (200, 303)

    listed = client.get(f"{admin.url_prefix}/user")
    assert listed.status_code == 200
    assert "a@b.c" in listed.text


def test_detail_then_edit_then_delete(app: HawkAPI, admin: Admin) -> None:
    client = TestClient(app)
    client.post(
        f"{admin.url_prefix}/user/new",
        body=b"email=x%40y.z&name=Bob",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    listed = client.get(f"{admin.url_prefix}/user")
    assert "x@y.z" in listed.text

    # Detail
    detail = client.get(f"{admin.url_prefix}/user/1")
    assert detail.status_code == 200
    assert "x@y.z" in detail.text

    # Edit form
    edit = client.get(f"{admin.url_prefix}/user/1/edit")
    assert edit.status_code == 200

    # Update
    upd = client.post(
        f"{admin.url_prefix}/user/1/edit",
        body=b"email=x%40y.z&name=BobUpdated",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert upd.status_code in (200, 303)
    detail = client.get(f"{admin.url_prefix}/user/1")
    assert "BobUpdated" in detail.text

    # Delete
    deleted = client.post(f"{admin.url_prefix}/user/1/delete")
    assert deleted.status_code in (200, 303)
    listed = client.get(f"{admin.url_prefix}/user")
    assert "x@y.z" not in listed.text


def test_unknown_resource_returns_404(app: HawkAPI, admin: Admin) -> None:
    r = TestClient(app).get(f"{admin.url_prefix}/nope")
    assert r.status_code == 404


def test_unknown_pk_returns_404(app: HawkAPI, admin: Admin) -> None:
    r = TestClient(app).get(f"{admin.url_prefix}/user/9999")
    assert r.status_code == 404


def test_search_filters_results(app: HawkAPI, admin: Admin) -> None:
    client = TestClient(app)
    client.post(
        f"{admin.url_prefix}/user/new",
        body=b"email=cat%40a.b&name=Cat",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    client.post(
        f"{admin.url_prefix}/user/new",
        body=b"email=dog%40a.b&name=Dog",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    found = client.get(f"{admin.url_prefix}/user?q=cat")
    assert "cat@a.b" in found.text
    assert "dog@a.b" not in found.text
