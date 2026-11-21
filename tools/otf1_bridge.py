#!/usr/bin/env python3
"""Bridge between the debris registry and OTF-1 (telemetry-protocol).

Two directions, so a registry entry and the fleet's packets stay consistent:

  registry entry  -> OTF-1 `assignment`  (what a coordinator offers a reclaimer)
  OTF-1 `event`s  -> feedstock summary   (what captured debris became, in kg,
                                          plus the ODCI contribution)

The feedstock summary is the handoff to processing: a depot (outpost-core)
or refinery (miner-automation) ingests the same events and ends up with the
same totals.

Usage:
    python tools/otf1_bridge.py assign ENTRY.json --task-id T-1 --node A1 \\
        --coordinator fleet-coordinator --seq 1 --timestamp 2026-11-21T12:00:00Z \\
        --accept-by 2026-11-21T12:00:10Z
    python tools/otf1_bridge.py feedstock EVENT.json [EVENT.json ...]
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def entry_to_assignment(entry, *, task_id, node, coordinator, seq, timestamp, accept_by):
    """Build an OTF-1 capture assignment from a registry entry."""
    regime = entry.get("orbitalRegime")
    if regime is None:
        raise ValueError("entry has no orbitalRegime; cannot place the task (OTF-1 location.zone is required)")
    target = {"objectType": entry["objectType"]}
    if "catalogId" in entry:
        target["catalogId"] = entry["catalogId"]
    if "estimatedMass_kg" in entry:
        target["mass_kg"] = entry["estimatedMass_kg"]
    return {
        "version": "OTF-1",
        "kind": "assignment",
        "timestamp": timestamp,
        "source": {"id": coordinator, "role": "coordinator"},
        "destination": node,
        "seq": seq,
        "task": {
            "id": task_id,
            "action": "capture",
            "location": {"zone": regime},
            "target": target,
        },
        "acceptBy": accept_by,
    }


def feedstock_summary(events):
    """Total processed mass by product, and total ODCI, over OTF-1 event packets.

    Only events whose outcome status is stored or delivered count: material
    that is failed or still in transit is not yet feedstock.
    """
    by_product = defaultdict(float)
    odci = 0.0
    counted = 0
    for ev in events:
        if ev.get("kind", "event") != "event":
            raise ValueError("feedstock_summary expects OTF-1 event packets only")
        out = ev["outcome"]
        if out["status"] not in ("stored", "delivered"):
            continue
        by_product[out.get("repurposedAs", "none")] += float(out.get("processedKg", 0.0))
        odci += float(ev["certifications"].get("ODCI_contribution", 0.0))
        counted += 1
    return {
        "events_counted": counted,
        "kg_by_product": dict(sorted(by_product.items())),
        "total_kg": sum(by_product.values()),
        "odci_contribution_kg": odci,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("assign")
    a.add_argument("entry")
    for name in ("task-id", "node", "coordinator", "timestamp", "accept-by"):
        a.add_argument("--" + name, required=True)
    a.add_argument("--seq", type=int, required=True)
    f = sub.add_parser("feedstock")
    f.add_argument("events", nargs="+")
    args = ap.parse_args(argv)

    if args.cmd == "assign":
        entry = json.loads(Path(args.entry).read_text(encoding="utf-8"))
        pkt = entry_to_assignment(entry, task_id=args.task_id, node=args.node,
                                  coordinator=args.coordinator, seq=args.seq,
                                  timestamp=args.timestamp, accept_by=args.accept_by)
        print(json.dumps(pkt, indent=2))
    else:
        events = [json.loads(Path(p).read_text(encoding="utf-8")) for p in args.events]
        print(json.dumps(feedstock_summary(events), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
