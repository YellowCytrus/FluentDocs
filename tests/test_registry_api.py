"""GET /registry/options: схема для универсальной страницы «Правила»."""

from __future__ import annotations


async def test_registry_api_exposes_option_contract(client):
    response = await client.get("/registry/options")
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == 1
    assert body["groups"]
    options = {option["id"]: option for option in body["options"]}
    assert "page.margin_left" in options
    assert "outline.indent_mode" in options

    margin = options["page.margin_left"]
    assert margin["type"] == "number"
    assert margin["unit"] == "mm"
    assert margin["min"] == 0
    assert margin["max"] == 100
    assert margin["ui"]["control"] == "number"
    assert margin["ui"]["label"] == "Поле слева"
    assert margin["group_label"] == "Страница"

    indent_mode = options["outline.indent_mode"]
    assert indent_mode["type"] == "select"
    assert {item["value"] for item in indent_mode["ui"]["options"]} == {
        "step",
        "per_level",
    }
