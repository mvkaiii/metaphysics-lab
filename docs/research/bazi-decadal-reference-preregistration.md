# 大運reference預註冊準備紀錄

Methodology：`APPROVED WITH CONSTRAINTS`。Comparator contract：`ENGINEERING_READY`。Pre-oracle v1：`SEALED_AND_PRESERVED`。Oracle v1：`HALTED_BEFORE_ORACLE`。v2 handoff：`HALTED_BEFORE_ORACLE_DUE_TO_HANDOFF_CONTAMINATION`。Pre-oracle v2.1：`SEALED`。v2.1 clean handoff：`READY_FOR_INDEPENDENT_ORACLE_EXECUTOR`。Independent comparison：`NOT_STARTED`。Task3：`NEEDS_EVIDENCE`。

依據：[人工決策](../superpowers/phase-gates/2026-09-27-review-decisions.md)、
`bazi-decadal-domain-review-decision.v1.json`及
`bazi-decadal-nonindependent-dryrun-receipt.v1.json`。

v1 pre-oracle seal 不回寫、不修補、不放寬 tolerance。它保留為完整治理歷史。

## v1 pre-oracle封存

- approved spec SHA256：`0757d1275e55b84e2424d6131e9dbdc73e029e1b619f900147be928cc7e5e01d`
- case bundle SHA256：`ab7ebd72671c3020d67444f720c6f3645111005348efd56efe91ffd2ee699d3f`
- HKO 2015 SHA256：`60a45ab889ef436936571a04a49387c6f9ce8d43243fb21c64e3fcb0331c8320`
- HKO 2016 SHA256：`84beb01553646b807a7c15d6efebdd7550af1ac6d7f06e07bfdd124dab9e443b`
- pre-oracle seal SHA256：`db32a95bc41a54531907e7e059655c094b1b1234a533770a88f2e3a52712874e`
- independent oracle expected values：0
- independent oracle execution：未開始

## 2026-09-29 non-independent dry-run

在production repository context內，以明確標示的
`NON_INDEPENDENT_DRY_RUN / SAME_CONTEXT_DIAGNOSTIC_REPRODUCTION`
執行12個sealed cases。此結果不可作independent qualification evidence。

Workflow run：`36590426371`  
Artifact：`11044145236`  
Artifact digest：`sha256:6575986c533b6be5701fa2d2fe777a0c8b082513e039cdc5d78ef1381b054fb4`

結果：

- total fields：60
- MATCH：12
- MISMATCH：36
- MISSING_REFERENCE：12
- `/decadal_direction`：12 MATCH，但方向答案已存在sealed coverage tags，不具獨立性
- `/periods/0/pillar`：12 MISSING_REFERENCE；approved spec未定義natal month pillar推導
- `/periods/0/start_age_years`：12 MISMATCH
- `/periods/0/start_datetime`：12 MISMATCH
- `/periods/1/end_datetime`：12 MISMATCH

Strict clean-room executability：`FAIL_UNDER_SPECIFIED`。

原因至少包括：

1. spec以natal year stem決定順逆，但未把birth datetime → natal year stem算法寫入clean-room規格；
2. spec以natal month pillar推第一段大運，但未把birth datetime → natal month pillar算法寫入clean-room規格；
3. coverage tags直接包含forward/reverse expected direction，削弱該欄位的獨立性。

## Timing mismatch

已封存HKO source與目前production `solar_term_time()` 在本12-case實際使用的同名Jie上，
production相對HKO約早121～412秒，全部超過已封存的±60秒來源精度tolerance。

2015清明最具materiality：

- HKO：`2015-04-05T10:39:00+08:00`
- production：`2015-04-05T10:33:09+08:00`
- difference：-351秒
- sealed before-case：`2015-04-05T10:34:00+08:00`

因此10:34案例在HKO仍屬清明前，但production已屬清明後；順／逆不同方向會直接選到不同Jie，
導致約10年量級的起運差，而不是可用presentation rounding吸收的小誤差。

## Current gate

v1 independent oracle handoff：`HALTED_BEFORE_ORACLE`。

不得：

- 回頭修改v1 seal；
- 看到結果後放寬v1 tolerance；
- 把non-independent dry-run冒充Task3 PASS；
- 以coverage tags的方向答案當獨立oracle輸出。

下一輪必須走v2：

1. 補齊self-contained year-pillar算法；
2. 補齊self-contained month-pillar算法；
3. clean-room case bundle移除expected-direction leakage；
4. 先以更廣泛public astronomical evidence改善／重新qualification production solar-term calculation；
5. 凍結新candidate後建立v2 pre-oracle seal；
6. 再交給真正未接觸production/output的獨立oracle executor。

Task3持續為`NEEDS_EVIDENCE`，不做maturity promotion。


## 2026-09-30 v2 engineering correction checkpoint

Solar-term provider engineering correction is complete and separately recorded in
`bazi-solar-term-provider-change-receipt.v1.json`.

General benchmark evidence:

- pre-change current engine: 3/48 within ±60 seconds;
- pre-change mean absolute error: 279.458333 seconds;
- pre-change max absolute error: 767 seconds;
- qualified candidate `lunar-python==1.4.8`: 48/48 within ±60 seconds;
- candidate mean absolute error: 18.395833 seconds;
- candidate max absolute error: 30 seconds.

After production switched to the Project-private bundled lunar-python authority:

- post-change general benchmark: 48/48 within ±60 seconds;
- post-change current engine mean absolute error: 18.395833 seconds;
- post-change max absolute error: 30 seconds;
- post-change non-independent Task3 diagnostic:
  `48 MATCH / 0 MISMATCH / 12 MISSING_REFERENCE`.

The 36 timing mismatches observed in v1 disappeared. The remaining 12
`MISSING_REFERENCE` rows are the already-identified v1 written-spec omission
for natal month-pillar derivation.

Historical `synthetic-engine-view.v1.json` remains unchanged and continues to
reproduce through the preserved legacy solar-term solver. Current production is
not required to equal that historical baseline timing.

Hosted verification at `e7940882a0f04eed9afe12af9c9f271f6b1a9f57`:

- v1.5 run `36650906997`: SUCCESS
- v1.6 run `36650907033`: SUCCESS
- v1.7 run `36650906966`: SUCCESS
- v1.7 Plan 3 Focused run `36650907013`: SUCCESS

## v2 approved seal and handoff gate

Human/domain decisions V2-D1 through V2-D5 were approved on
`2026-09-30T09:51:00+08:00`.

V2-D1 wording is intentionally precise: HKO is accepted as an
**official public astronomical reference source for this qualification cycle**.
This does not claim HKO is the unique or universal Bazi industry standard.

Frozen production candidate:

`6280c29b0a493e4b27379948c8cc82ba94bfa04f`

Approved v2 written specification:

- path: `bazi-decadal-independent-profile-spec.v2.md`
- SHA256:
  `24825b1c2c850873f54e117c53c13932a8a730dc3a245a1c5e7e2599259c3305`

V2 case bundle:

- exactly the same 12 birth/sex inputs selected before v1 result exposure;
- post-result additions: 0;
- removals: 0;
- replacements: 0;
- opaque IDs `bdv2-001..012`;
- no Yin/Yang-year or expected forward/reverse metadata;
- canonical SHA256:
  `939f8e29123acabfc16366b05622d1d3598b6aa72c4cc54cf96db3ce6e35128e`.

V2 pre-oracle seal:

- status: `PRE_ORACLE_SEALED`;
- canonical SHA256:
  `56f63fbe9561a9216e2f6e597d0f76ca4006af0ffd09a775f4da0d980e13ae0c`;
- expected values present: false;
- oracle execution started: false;
- comparison started: false.

Independent-oracle handoff:

- status: `READY_FOR_INDEPENDENT_ORACLE_EXECUTOR`;
- inner ZIP:
  `Bazi-Decadal-Independent-Oracle-Handoff-v2-20260930.zip`;
- inner ZIP SHA256:
  `6a1a92e79b1fa26c5527874c86feecc0436ac7cdd825e51b6b5d3e696a5c0be7`;
- packaging workflow run: `36659028255`;
- artifact id: `11073676130`;
- outer artifact digest:
  `sha256:3a154796e9cf2239c9d6b1423bf8bc90c2c24984692bb6c11de85fa61946d664`.

The handoff contains no production implementation, production output,
non-independent dry-run output, comparison output or expected values.

The current Project context remains ineligible to execute the independent
oracle. The next gate is execution in a genuinely isolated environment that
receives only the sealed v2 handoff boundary.

Task3 remains `NEEDS_EVIDENCE`. No qualification decision or maturity
promotion is implied by the v2 seal.


## 2026-09-30 v2 handoff contamination and v2.1 clean replacement

A fresh isolated executor correctly failed closed on the v2 handoff before
oracle execution because the v2 written specification included non-normative
prior engineering and diagnostic results.

No oracle source, expected values or production comparison were produced in
that attempt.

The v2 historical seal and handoff are preserved and must not be repaired in
place.

A sanitization-only v2.1 execution contract was created. It preserves the
approved domain rules and exact same 12-case census, removes prior-result
history, and explicitly maps the HKO English labels to the 12 Jie.

v2.1 bindings:

- clean execution contract SHA256:
  `b47de7809cadb82159c272b2d2d7fb3bbc7ffc99d9e8ed6c1fa60a1bf3c900e4`
- unchanged case-bundle canonical SHA256:
  `939f8e29123acabfc16366b05622d1d3598b6aa72c4cc54cf96db3ce6e35128e`
- v2.1 pre-oracle seal canonical SHA256:
  `53f4e249f4f6e13fd26e9859101cceeaac31a1f186c155653a24e79f02dd4a27`

Clean handoff:

- file:
  `Bazi-Decadal-Independent-Oracle-Cleanroom-v2.1-20260930.zip`
- inner ZIP SHA256:
  `5674a7d943e14e841d17d3ae9d0bab650912524ac93a9b1b334c92381d135304`
- workflow run:
  `36665923915`
- artifact id:
  `11076158110`
- outer artifact digest:
  `sha256:5383e599cf16d2cea9d10fa7a575b9030629047471e97f467876707476589b26`

The packaging workflow passed exact-SHA validation, the existing pre-oracle
seal validator, exact HKO source-byte checks, case census checks, and an
explicit prior-result leakage scan.

After download, the inner ZIP was reopened and all 9 files plus SHA256SUMS were
verified again. The leakage scan returned zero hits.

v2.1 oracle execution remains `NOT_STARTED`. The next gate is a new fresh
isolated executor context receiving only the v2.1 clean handoff.
