from collections import defaultdict

import pytest
from jmespath import search
from jsonpointer import resolve_pointer

from spoonbill.common import JOINABLE_SEPARATOR
from spoonbill.flatten import Flattener, FlattenOptions

ID_ITEMS = {
    "tenders": [
        {"/tender/id": "ocds-213czf-000-00001-01-planning"},
        {"/tender/id": "ocds-213czf-000-00001-01-tender"},
        {"/tender/id": "ocds-213czf-000-00001-01-tender"},
        {"/tender/id": "ocds-213czf-000-00001-01-tender"},
    ],
    "parties": [
        {"/parties/id": "GB-LAC-E09000003"},
        {"/parties/id": "GB-LAC-E09000003"},
        {"/parties/id": "GB-LAC-E09000003"},
        {"/parties/id": "GB-COH-22222222"},
        {"/parties/id": "GB-COH-11111111"},
        {"/parties/id": "GB-LAC-E09000003"},
        {"/parties/id": "GB-LAC-E09000003"},
        {"/parties/id": "GB-LAC-E09000003"},
    ],
}


def test_flatten(spec_analyzed, releases):
    options = FlattenOptions(
        **{
            "selection": {"tenders": {"split": True}, "parties": {"split": False}},
        }
    )
    flattener = Flattener(options, spec_analyzed.tables)
    count = {"tenders": 0, "parties": 0}
    for _count, flat in flattener.flatten(releases):
        for name, rows in flat.items():
            for row in rows:
                assert "id" in row
                assert "ocid" in row
                assert "rowID" in row
                if name in ID_ITEMS:
                    key = "tender" if name == "tenders" else "parties"
                    path = f"/{key}/id"
                    assert ID_ITEMS[name][count[name]][path] == row.get(path)
                    count[name] += 1


def test_flattener_generate_count_columns(spec, releases):
    releases[0]["tender"]["items"] = releases[0]["tender"]["items"] * 6
    for _ in spec.process_items(releases):
        pass
    options = FlattenOptions(**{"selection": {"tenders": {"split": False}}, "count": True})
    flattener = Flattener(options, spec.tables)
    tenders = flattener.tables["tenders"]
    assert "/tender/itemsCount" not in tenders
    for index in range(tenders.arrays["/tender/items/additionalClassifications"]):
        assert f"/tender/items/{index}/additionalClassificationsCount" not in tenders

    options = FlattenOptions(
        **{"selection": {"tenders": {"split": True}, "tenders_items": {"split": False}}, "count": True}
    )
    flattener = Flattener(options, spec.tables)
    tenders = flattener.tables["tenders"]
    tenders_items = flattener.tables["tenders_items"]
    assert "/tender/itemsCount" in tenders
    for index in range(tenders.arrays["/tender/items/additionalClassifications"]):
        assert f"/tender/items/{index}/additionalClassificationsCount" not in tenders
    assert "/tender/items/additionalClassificationsCount" in tenders_items


def test_flatten_with_counters(spec, releases):
    releases[0]["tender"]["items"] = releases[0]["tender"]["items"] * 6
    releases[0]["tender"]["items"][0]["additionalClassifications"] = (
        releases[0]["tender"]["items"][0]["additionalClassifications"] * 6
    )
    for _ in spec.process_items(releases):
        pass
    options = FlattenOptions(**{"selection": {"tenders": {"split": True}}, "count": True})
    flattener = Flattener(options, spec.tables)
    for count, flat in flattener.flatten(releases):
        for name, rows in flat.items():
            if name == "tenders":
                for row in rows:
                    items = search(f"[{count}].tender.items", releases)
                    if items:
                        assert "/tender/itemsCount" in row
                        assert len(items) == row["/tender/itemsCount"]
            elif name == "tenders_items":
                for index, row in enumerate(rows):
                    additional = search(
                        f"[{count}].tender.items[{index}].additionalClassifications",
                        releases,
                    )
                    if additional:
                        assert "/tender/items/additionalClassificationsCount" in row
                        assert len(additional) == row["/tender/items/additionalClassificationsCount"]


def test_flatten_with_repeat(spec_analyzed, releases):
    options = FlattenOptions(
        **{
            "selection": {"tenders": {"split": True, "repeat": ["/tender/id"]}},
        }
    )
    flattener = Flattener(options, spec_analyzed.tables)
    for count, flat in flattener.flatten(releases):
        for name, rows in flat.items():
            if name == "tenders":
                continue
            for row in rows:
                assert "id" in row
                assert "ocid" in row
                assert "rowID" in row
                assert "/tender/id" in row
                assert row["/tender/id"] == search(f"[{count}].tender.id", releases)


def test_flatten_with_unnest(spec_analyzed, releases):
    field = "/tender/items/0/id"
    options = FlattenOptions(
        **{
            "selection": {"tenders": {"split": True, "unnest": [field]}},
        }
    )
    flattener = Flattener(options, spec_analyzed.tables)
    for count, flat in flattener.flatten(releases):
        for name, rows in flat.items():
            for row in rows:
                if name != "tenders":
                    assert field not in row
                    continue
                item_id = search(f"[{count}].tender.items[0].id", releases)
                if item_id:
                    assert field in row
                    assert search(f"[{count}].tender.items[0].id", releases) == row[field]


def test_flatten_with_exclude(spec, releases):
    releases[0]["tender"]["items"] = releases[0]["tender"]["items"] * 6
    for _ in spec.process_items(releases):
        pass
    options = FlattenOptions(**{"selection": {"tenders": {"split": True}}, "exclude": ["tenders_items"]})
    flattener = Flattener(options, spec.tables)
    all_rows = defaultdict(list)
    for count, flat in flattener.flatten(releases):
        for name, rows in flat.items():
            all_rows[name].extend(rows)
    assert "tenders" in all_rows
    assert "tenders_items" not in all_rows

    options = FlattenOptions(**{"selection": {"tenders": {"split": True}}})
    flattener = Flattener(options, spec.tables)
    all_rows = defaultdict(list)
    for count, flat in flattener.flatten(releases):
        for name, rows in flat.items():
            all_rows[name].extend(rows)
    assert "tenders" in all_rows
    assert "tenders_items" in all_rows


def test_flatten_with_only(spec_analyzed, releases):
    options = FlattenOptions(
        **{"selection": {"tenders": {"split": True, "only": ["/tender/id"]}, "parties": {"split": False}}}
    )
    flattener = Flattener(options, spec_analyzed.tables)
    all_rows = defaultdict(list)
    for count, flat in flattener.flatten(releases):
        for name, rows in flat.items():
            all_rows[name].extend(rows)
    assert all_rows["tenders"]
    for row in all_rows["tenders"]:
        assert not set(row).difference(["/tender/id", "rowID", "ocid", "parentID", "id"])

    options = FlattenOptions(**{"selection": {"tenders": {"split": False, "only": ["/tender/id"]}}})
    flattener = Flattener(options, spec_analyzed.tables)
    all_rows = defaultdict(list)
    for count, flat in flattener.flatten(releases):
        for name, rows in flat.items():
            all_rows[name].extend(rows)

    assert all_rows["tenders"]
    for row in all_rows["tenders"]:
        assert not set(row).difference(["/tender/id", "rowID", "ocid", "parentID", "id"])


def test_flatten_should_not_split(spec_analyzed, releases):
    options = FlattenOptions(**{"selection": {"tenders": {"split": False}}})
    flattener = Flattener(options, spec_analyzed.tables)
    all_rows = defaultdict(list)
    for count, flat in flattener.flatten(releases):
        for name, rows in flat.items():
            all_rows[name].extend(rows)
    assert "tender_items" not in all_rows
    assert "tenders_items_addit" not in all_rows
    tenders = all_rows["tenders"]

    for tender, release in zip(tenders, releases):
        items = release.get("tender", {}).get("items")
        if release.get("tender", {}).get("items"):
            assert "/tender/items/0/id" in tender
            assert "/tender/items/0/description" in tender
            if len(items) > 1:
                assert "/tender/items/1/id" in tender
                assert "/tender/items/1/description" in tender


def test_flatten_should_not_split_with_split(spec_analyzed, releases):
    options = FlattenOptions(**{"selection": {"tenders": {"split": True}}})
    flattener = Flattener(options, spec_analyzed.tables)
    all_rows = defaultdict(list)
    for count, flat in flattener.flatten(releases):
        for name, rows in flat.items():
            all_rows[name].extend(rows)
    assert "tender_items" not in all_rows
    assert "tenders_items_addit" not in all_rows
    tenders = all_rows["tenders"]

    for tender, release in zip(tenders, releases):
        items = release.get("tender", {}).get("items")
        if items:
            assert "/tender/items/0/id" in tender
            assert "/tender/items/0/description" in tender
            assert "/tender/items/0/additionalClassifications/0/description"
            if len(items) > 1:
                assert "/tender/items/1/id" in tender
                assert "/tender/items/1/description" in tender


@pytest.mark.parametrize(
    "options",
    [
        FlattenOptions(**{"selection": {"tenders": {"split": True}, "tenders_items": {"split": False}}}),
        FlattenOptions(**{"selection": {"tenders": {"split": True}}}),
    ],
)
def test_flatten_should_split_with_child(spec, releases, options):
    releases[0]["tender"]["items"] = releases[0]["tender"]["items"] * 6
    for _ in spec.process_items(releases):
        pass
    flattener = Flattener(options, spec.tables)
    all_rows = defaultdict(list)
    for count, flat in flattener.flatten(releases):
        for name, rows in flat.items():
            all_rows[name].extend(rows)

    assert "tenders_items" in all_rows
    assert "tenders_items_addit" not in all_rows
    tenders = all_rows["tenders"]

    for tender, release in zip(tenders, releases):
        if release.get("tender", {}).get("items"):
            assert "/tender/items/0/id" not in tender
            assert "/tender/items/0/description" not in tender
            assert "/tender/items/1/id" not in tender
            assert "/tender/items/1/description" not in tender

    items = all_rows["tenders_items"]
    for item in items:
        assert "/tender/items/id" in item
        assert "/tender/items/description" in item


def test_flatten_fields_compare(spec_analyzed, releases):
    options = FlattenOptions(
        **{
            "selection": {"tenders": {"split": True}, "parties": {"split": False}},
        }
    )
    flattener = Flattener(options, spec_analyzed.tables)
    fields = ["submissionMethod", "roles"]
    for count, flat in flattener.flatten(releases):
        for name, rows in flat.items():
            counters = defaultdict(int)
            for row in reversed(rows):
                for key, value in row.items():
                    if "/" in key:
                        if "parties" in key:
                            key = key.replace("parties", f"parties/{counters['parties']}")
                        expected = resolve_pointer(releases[count], key)
                        if any(key.endswith(field) for field in fields):
                            expected = JOINABLE_SEPARATOR.join(expected)
                        assert expected == value
                counters[name] += 1
