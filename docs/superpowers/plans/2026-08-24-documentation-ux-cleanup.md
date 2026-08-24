# Documentation UX Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the public-facing Metaphysics Lab documentation so a general Traditional-Chinese user can understand installation, chart-source options, and release contents without learning internal engineering terminology, while preserving all technical contracts in developer-facing documents.

**Architecture:** Keep runtime/schema/capability behavior unchanged. Simplify README, quick start, installation, data preparation, changelog/release-facing summaries, and terminology tests; keep exact Subject Identity / Case Schema / capability details in technical documents. Astralium remains an optional External chart source and cross-check path, never a runtime dependency.

**Tech Stack:** Markdown, Python 3.9+ unittest documentation contract tests, GitHub Release metadata (where connector support allows).

**Spec:** Approved conversation requirements on 2026-08-24: README/release white-language cleanup, Astralium option restoration, example anonymization, download wording simplification, platform-neutral reasoning wording, and no distribution filename migration in this PR.

## Global Constraints

- Base commit: `df814567a8e21a5a75b4d575a2fd17b50cfb4298`.
- Work only on `docs/documentation-ux-cleanup`; do not edit `main` directly.
- Preserve formal release identity `v1.3.0 | 2026-08-23`.
- Do not change runtime logic, Case Schema behavior, Project Contract behavior, capability implementation/maturity/routing, release tag, or calculation rules.
- Keep `metaphysics_lab.py`, `METAPHYSICS_CORE.md`, and `PROJECT_INSTRUCTIONS.md` as the actual v1.3.0 distribution filenames in this cleanup.
- Present those files to users with Traditional-Chinese purpose labels rather than engineering jargon.
- Do not use `Kai` or any real-looking private birth combination in public user-facing examples; use explicitly fictional names/data such as Alex / Mina.
- Astralium is optional: support birth-data-only, birth-data + Astralium cross-check, and third-party-chart-only input paths.
- Do not describe Astralium as required or as a runtime dependency.
- README must not hard-code transient branch/PR status such as Draft PR #160.
- Replace product-UI-specific `High reasoning` wording with platform-neutral wording such as higher reasoning / deep reasoning mode where available.
- Use `下載區（GitHub 顯示為 Assets）` when the GitHub label must be referenced; do not require users to understand the term `Assets`.
- General-user docs should avoid `artifact`, `runtime`, `deterministic`, `materialize`, `canonical slot`, `implementation / maturity / routing` unless a short plain-language explanation is necessary.

---

### Task 1: Lock the new user-facing documentation contract in tests

**Files:**
- Modify: `tests/test_ai_distribution_docs.py`
- Modify: `tests/test_document_contract_consistency.py`

**Interfaces:**
- Consumes: public README / quick-start / install / data-preparation documentation.
- Produces: tests that require plain-language download guidance, fictional examples, Astralium optional-source paths, and platform-neutral reasoning wording while leaving technical contracts in technical docs.

- [ ] Replace assertions that force `Assets`, `High`, or `Kai` in user-facing docs.
- [ ] Require the README/quick start to explain `下載區`, no source-code ZIP requirement, and the three files with Traditional-Chinese purpose labels.
- [ ] Require public examples to use fictional aliases such as `Alex` / `Mina` and reject `Kai` in README, quick start, installation, and data-preparation guides.
- [ ] Require three chart-source modes: birth data only; birth data + Astralium/third-party cross-check; third-party chart only.
- [ ] Keep exact subject-aware filename/schema assertions in technical/advanced docs, but remove the requirement that README itself teach canonical-slot syntax.
- [ ] Run the focused doc tests and verify RED against the old documents.

### Task 2: Rewrite README as a general-user landing page

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: current v1.3.0 release identity and stable installation surface.
- Produces: a short landing page answering what the project is, what to download, how to start, what chart data can be supplied, privacy basics, and where advanced technical docs live.

- [ ] Keep the opening concept `Python 負責計算，AI 負責解讀` but explain it without engineering vocabulary.
- [ ] State formal version `v1.3.0（2026-08-23）` in plain language.
- [ ] Replace `Latest Release → Assets` with `Release 頁面下方的下載區（GitHub 顯示為 Assets）` and explicitly say not to download/unzip Source code.
- [ ] Present the files as: `命理計算程式 — metaphysics_lab.py`, `命理分析核心規則 — METAPHYSICS_CORE.md`, `Project 設定指令 — PROJECT_INSTRUCTIONS.md`.
- [ ] Replace fixed `High reasoning` instructions with platform-neutral higher-reasoning wording.
- [ ] Add the three input/source choices, including Astralium as optional External cross-check.
- [ ] Explain unknown birth time in one plain-language paragraph; link to advanced data-preparation docs instead of teaching Candidate Envelope internals on the landing page.
- [ ] Remove Draft PR #160 / feature branch status and deep Unreleased contract exposition from README.
- [ ] Use fictional examples only.

### Task 3: Rewrite quick start and installation guides for first-time users

**Files:**
- Modify: `docs/快速開始.md`
- Modify: `docs/安裝到ChatGPT-Project.md`

**Interfaces:**
- Consumes: the three stable distribution files and Project installation workflow.
- Produces: step-by-step Traditional-Chinese instructions that remain usable on ChatGPT or Claude without requiring repo knowledge.

- [ ] Put download/install steps first and explain the three file roles in plain Traditional Chinese.
- [ ] Keep the actual filenames unchanged.
- [ ] Add an explicit note that all names, dates, and IDs in examples are fictional.
- [ ] Replace all `Kai` examples with `Alex`, `Mina`, or placeholders.
- [ ] Replace the private-looking 1984-03-13 19:20 Taipei example with clearly synthetic example data.
- [ ] Introduce the three chart-source paths before advanced identity/schema details.
- [ ] Keep advanced Subject Identity / partial-birth-time behavior, but move it after the basic setup and explain technical terms on first use.
- [ ] Replace platform-specific High/Medium/Instant recommendations with a neutral statement about higher-reasoning modes if available.
- [ ] Keep the no-Python fallback and privacy warnings.

### Task 4: Make data preparation explicitly support Astralium as an optional path

**Files:**
- Modify: `docs/命盤資料準備指南.md`
- Review: `docs/Astralium資料取得指南.md`

**Interfaces:**
- Consumes: External / Project / Resolved data model.
- Produces: a user-visible source-choice section that treats Astralium as one optional third-party source for both Bazi and Ziwei.

- [ ] Add a top-level `三種準備方式` section: birth data only; birth data + Astralium/third-party chart; third-party chart only.
- [ ] State that Astralium Bazi and Ziwei outputs can both be supplied when available.
- [ ] Preserve External / Project / Resolved separation and `MATCH / EQUIVALENT / CONFLICT / NOT_COMPARABLE` semantics.
- [ ] State clearly that third-party-only data does not prove a Project-native calculation was performed.
- [ ] Replace user-facing `Kai` examples with fictional aliases.
- [ ] Preserve `runtime_info` as technical execution truth without putting implementation/maturity/routing jargon in the opening paragraphs.

### Task 5: Reframe version/changelog/release-facing copy

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `VERSION.md` only for navigation/reader guidance, not historical capability state.
- Create: `docs/發布說明-v1.3.0.md` as the canonical plain-language release-note source if direct GitHub Release-body editing is unavailable.

**Interfaces:**
- Consumes: immutable v1.3.0 technical release facts.
- Produces: a plain-language release summary plus preserved technical acceptance history.

- [ ] Add a short `一般使用者摘要` before detailed v1.3.0 engineering evidence.
- [ ] Summarize native Bazi/Ziwei natal creation, optional Astralium/third-party cross-check, fine-cycle/flowing-star support, and the three-file Project installation surface.
- [ ] Keep qualification counts, pinned revisions, maturity, and phase history in the technical section rather than deleting them.
- [ ] Add a note at the top of VERSION.md that general usage belongs in README/quick start while VERSION is the technical version/capability ledger.
- [ ] Create `docs/發布說明-v1.3.0.md` with user-facing download/install/source-mode wording suitable for GitHub Release body.
- [ ] If a connector action for editing the existing GitHub Release body is available, update it from this source without changing the tag or release identity; otherwise report that only the canonical repo source could be updated.

### Task 6: Verify consistency and distribution non-regression

**Files:**
- Test: `tests/test_ai_distribution_docs.py`
- Test: `tests/test_document_contract_consistency.py`
- Test: `tests/test_ai_distribution_acceptance.py`
- Verify: `tools/build_ai_distribution.py --check`

**Interfaces:**
- Consumes: all documentation edits.
- Produces: proof that documentation UX changed without altering runtime/distribution contracts.

- [ ] Run focused documentation tests.
- [ ] Run AI distribution acceptance tests to prove the actual three filenames did not change.
- [ ] Run `python tools/build_ai_distribution.py --check`.
- [ ] Run full `python -m unittest discover -s tests -p 'test_*.py' -v`.
- [ ] Run `python -m compileall engine tests tools`.
- [ ] Run `git diff --check` and confirm branch-only changed files are documentation/tests/plan unless deterministic generated markdown is intentionally affected.
- [ ] Confirm `VERSION.md` still says v1.3.0, release tag is untouched, and Experimental capabilities remain unpromoted.
