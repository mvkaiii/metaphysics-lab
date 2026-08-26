# Bazi Flow Day / Hour Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen the existing Project Bazi flow-day / flow-hour algorithm with reproducible public-oracle, boundary, matrix, timezone-boundary, and generated-runtime qualification without changing the metaphysical formulas unless a failing qualification proves a defect.

**Architecture:** Keep `engine/bazi/calendar.py` as the sole algorithm implementation. Add a deterministic qualification builder that compares the Project implementation with pinned `lunar-python==1.4.8` using EightChar sect 1 (晚子時日柱按明天), commits a machine-readable public evidence snapshot, and exposes `--check` for drift detection. Unit tests verify the builder contract, properties, DST responsibility boundary, and modular/generated runtime parity through the existing forecast runtime action.

**Tech Stack:** Python 3.9, `unittest`, `lunar-python==1.4.8`, `zoneinfo`, existing Metaphysics Lab distribution/runtime APIs.

**Spec:** `core/命理推導計算規則.md` sections 2.3–2.4 and the approved 2026-08-26 qualification scope.

## Global Constraints

- Do not change the Bazi day formula `offset = JDN - 11` unless qualification proves it wrong.
- Do not change the 23:00 early-Zi rule unless qualification proves it wrong.
- Do not change the Five Rat formula unless qualification proves it wrong.
- Oracle is pinned `lunar-python==1.4.8`, EightChar sect 1 for the Project early-Zi convention.
- Calendar Resolver retains DST ambiguity/nonexistent-time authority; Bazi flow-time does not invent a second timezone resolver.
- No capability maturity promotion is part of this work.
- Generated distribution must remain deterministic and clean.

---

### Task 1: Qualification contract and RED gate

**Files:**
- Create: `tests/test_bazi_flow_time_qualification.py`
- Create later: `tools/build_bazi_flow_time_qualification.py`
- Create later: `qualification/bazi/flow_time/public-lunar-python-1.4.8.json`

**Interfaces:**
- Consumes: `engine.bazi.calendar.day_pillar`, `time_pillar`; `lunar_python.Solar`.
- Produces: `build_report()` and CLI `python tools/build_bazi_flow_time_qualification.py [--check]`.

- [ ] Write tests requiring the qualification builder and committed evidence snapshot.
- [ ] Open a PR / run CI and verify RED is caused by the missing qualification deliverable, not by syntax or unrelated regressions.

### Task 2: Public oracle and matrix qualification

**Files:**
- Create: `tools/build_bazi_flow_time_qualification.py`
- Create: `qualification/bazi/flow_time/public-lunar-python-1.4.8.json`
- Modify: `tests/test_bazi_flow_time_qualification.py`

**Coverage:**
- deterministic day samples from 1980-01-01 through 2050-12-31 at a fixed interval, compared with lunar-python sect 1;
- 22:59 / 23:00 / 23:59 / 00:00 boundary vectors in Taipei, Tokyo, New York, and London;
- year/month/leap-day transitions;
- complete 10 day stems × 12 hour branches = 120 Five Rat combinations, compared with the oracle;
- consecutive-day sexagenary +1 property and 12-branch time progression property.

- [ ] Implement the smallest builder needed for the tests.
- [ ] Run focused tests and `--check` until GREEN.
- [ ] If any oracle mismatch appears, stop and use systematic debugging before changing production formulas.

### Task 3: DST responsibility and generated-runtime parity

**Files:**
- Modify: `tests/test_bazi_flow_time_qualification.py`

**Coverage:**
- Calendar Resolver rejects New York spring-forward nonexistent local time;
- Calendar Resolver reports both fall-back candidates and accepts explicit offset hints;
- resolved valid local civil time produces the same Bazi day/hour result regardless of UTC-offset candidate when the local civil fields are identical;
- modular `resolve_forecast_context` and generated `dist/ai/metaphysics_lab.py` return byte-equivalent daily forecast context for representative ordinary and 23:xx inputs.

- [ ] Add tests first.
- [ ] Verify any new failing behavior before implementation changes.
- [ ] Rebuild generated distribution only if source/document inputs require it.

### Task 4: Record qualification evidence

**Files:**
- Modify: `core/命理推導計算規則.md`
- Modify: `CHANGELOG.md` only if repository convention requires an unreleased qualification note.
- Regenerate: `dist/ai/*` if required by the distribution builder.

- [ ] Record exact oracle version, convention, vector counts, PASS/FAIL state, and DST responsibility boundary.
- [ ] Explicitly state that qualification strengthens evidence and does not itself promote maturity.
- [ ] Run `python tools/build_ai_distribution.py` then `--check` and commit only deterministic generated differences.

### Task 5: Final verification and PR

- [ ] Run `python tools/build_bazi_flow_time_qualification.py --check`.
- [ ] Run focused flow-time qualification tests.
- [ ] Run full `python -m unittest discover -s tests -p 'test_*.py' -v`.
- [ ] Run `python -m compileall engine tests tools`.
- [ ] Run AI distribution `--check` and verify clean tree in CI.
- [ ] Update PR with exact counts, CI run/job IDs, oracle convention, and any discovered limitations.
- [ ] Do not merge without a separate explicit authorization.
