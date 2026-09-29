# 大運reference預註冊準備紀錄

Methodology：`APPROVED WITH CONSTRAINTS`。Comparator contract：`ENGINEERING_READY`。Pre-oracle v1：`SEALED_AND_PRESERVED`。Oracle v1：`HALTED_BEFORE_ORACLE`。Independent comparison：`NOT_STARTED`。Task3：`NEEDS_EVIDENCE`。

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
