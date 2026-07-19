from dfs.services.fleet.b5_fleet_rule_catalog import (
    B5_FLEET_CONSTRUCTION_RULES, CatalogStatus, rule_by_id, rule_records,
)


def test_catalog_rule_ids_are_unique_and_stable():
    ids = [record.rule_id for record in B5_FLEET_CONSTRUCTION_RULES]
    assert len(ids) == len(set(ids))
    assert all(rule_id.startswith("B5-") for rule_id in ids)


def test_every_record_is_auditable_and_actionable():
    for record in B5_FLEET_CONSTRUCTION_RULES:
        assert record.fleet
        assert record.rule_family
        assert record.summary
        assert record.remedy_hint
        assert record.source.title
        assert record.source.section
        assert record.source.page is not None and record.source.page > 0


def test_existing_allied_rules_are_marked_implemented():
    assert rule_by_id("B5-ISA-ALL-001").status is CatalogStatus.IMPLEMENTED
    assert rule_by_id("B5-RAID-ALL-001").status is CatalogStatus.IMPLEMENTED


def test_catalog_filters_by_status_and_fleet():
    implemented = rule_records(status=CatalogStatus.IMPLEMENTED)
    assert {record.rule_id for record in implemented} == {"B5-ISA-ALL-001", "B5-RAID-ALL-001", "B5-ANCIENT-UNQ-001"}
    assert all(record.fleet == "Gaim Intelligence" for record in rule_records(fleet="gaim intelligence"))
