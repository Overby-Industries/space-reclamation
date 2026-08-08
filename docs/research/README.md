# Research Registry

Phase 1 of the [roadmap](../../ROADMAP.md) is knowledge consolidation: build
the most open, comprehensive registry of space debris mitigation approaches
before any hardware gets designed. This directory is that registry.

## Structure

- [`sources.md`](sources.md) — bibliography of external research (ESA, NASA,
  JAXA, ISRO, academic), organized by category. Add a citation here before
  citing it anywhere else in the org's repos, so there's one canonical list.
- [`capture-technologies.md`](capture-technologies.md) — comparison of known
  active-debris-removal (ADR) capture approaches (nets, harpoons, tethers,
  magnetic capture, laser ablation), their maturity level, and how each
  would feed Overby's reclaim-and-repurpose model rather than a
  drag-and-deorbit-only model.
- [`2026-state-of-orbital-debris-outline.md`](2026-state-of-orbital-debris-outline.md) —
  outline for the Phase 1 deliverable report. It's an outline, not a
  finished report: the actual data-gathering is the Phase 1 work itself,
  not something to fabricate ahead of it.
- [`../../data/`](../../data/) — the structured (JSON) side of the
  registry: a schema for logging tracked objects/mitigation-approach
  metadata, separate from the narrative research above.

## Contributing a source

- Add the citation to `sources.md` under the right category, in the same
  row format as the existing entries.
- Prefer primary sources (agency reports, peer-reviewed papers) over
  secondary summaries.
- If a claim in any Overby repo needs a citation, it should point here.
