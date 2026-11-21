import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import otf1_bridge  # noqa: E402

ENTRY = json.loads((ROOT / "data/examples/example-entry.json").read_text())
KW = dict(task_id="T-0042", node="A1", coordinator="fleet-coordinator", seq=95,
          timestamp="2025-02-18T14:05:00Z", accept_by="2025-02-18T14:05:10Z")


def otf1_schema():
    """Locate telemetry-protocol's schema: $OTF1_SCHEMA, else a sibling checkout."""
    candidates = [os.environ.get("OTF1_SCHEMA"),
                  ROOT.parent / "telemetry-protocol" / "schema" / "otf-1.schema.json"]
    for c in candidates:
        if c and Path(c).exists():
            return json.loads(Path(c).read_text(encoding="utf-8"))
    return None


def validate_otf1(pkt):
    schema = otf1_schema()
    if schema is None:
        pytest.skip("telemetry-protocol schema not found (set OTF1_SCHEMA)")
    import jsonschema
    jsonschema.Draft202012Validator(schema).validate(pkt)


def test_assignment_matches_otf1_example_shape():
    pkt = otf1_bridge.entry_to_assignment(ENTRY, **KW)
    assert pkt["task"]["target"] == {"objectType": "fragment", "catalogId": "NORAD-33953", "mass_kg": 5.2}
    assert pkt["task"]["location"] == {"zone": "LEO"}
    assert pkt["task"]["action"] == "capture"


def test_assignment_is_valid_otf1():
    validate_otf1(otf1_bridge.entry_to_assignment(ENTRY, **KW))


def test_entry_without_regime_rejected():
    entry = {k: v for k, v in ENTRY.items() if k != "orbitalRegime"}
    with pytest.raises(ValueError):
        otf1_bridge.entry_to_assignment(entry, **KW)


def event(kg, product, status="stored", odci=0.0):
    return {"version": "OTF-1", "outcome": {"processedKg": kg, "repurposedAs": product, "status": status},
            "certifications": {"SMESSC": True, "ODCI_contribution": odci}}


def test_feedstock_summary_counts_only_finished_material():
    s = otf1_bridge.feedstock_summary([
        event(5.0, "shield_block", odci=5.0),
        event(3.0, "shield_block", "delivered", odci=3.0),
        event(7.0, "ingot", "in-transit"),
        event(2.0, "ingot", "failed"),
    ])
    assert s["events_counted"] == 2
    assert s["kg_by_product"] == {"shield_block": 8.0}
    assert s["odci_contribution_kg"] == 8.0


def test_feedstock_rejects_non_events():
    with pytest.raises(ValueError):
        otf1_bridge.feedstock_summary([{"kind": "status"}])
