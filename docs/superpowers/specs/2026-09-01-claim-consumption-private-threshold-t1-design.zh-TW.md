# Claim Consumption Private Threshold Governance T1 設計規格

## 狀態與來源追溯

- 研究週期：`v1.6 Claim Consumption Private Threshold Governance T1`。
- 上游 O1 frozen candidate：GitHub `c810136936c4804560218c2cb03e86734afda37f`，tree `74f044bf7ad7616dba4cc2280021d6334ada1f6f`。
- 上游 Q1 frozen candidate：GitHub `4c5df745554b1d14a08b58aae45f4212b0162132`。
- 上游 C1 production policy、Q1 scoring semantics、O1 sealing/join semantics、Coordination、Phase 3、Interpretation ranking、Hybrid render authority 均為唯讀。
- T1 的 threshold 選擇只能來自 general / prospective governance rationale；既有 private candidate output、private metrics、舊 private aggregate PASS/FAIL 不得作為 threshold-selection input。
- 已在 T1 policy freeze 前暴露 private candidate output 的 oracle/candidate pair，不得回頭套用 T1 作 release 判定。

## 問題定義

Q1 已建立 claim-level qualification measurement authority，能輸出 aggregate metrics，例如：

- `over_render_count`；
- `under_render_count`；
- `caveat_omission_count`；
- `unnecessary_caveat_count`；
- `specificity_overreach_count`；
- `specificity_excessive_downgrade_count`；
- `decision_alignment.partial`；
- `decision_alignment.missed`；
- `cutoff_contamination_count`。

但 Q1 明確設定 `promotion_allowed=false`，它只量測，不負責判定 private release gate。

目前 Project 缺少一個獨立、事前 freeze、可重現的 threshold authority。若在看到 private Q1 結果後才決定允許多少錯誤，會產生 outcome-informed threshold tuning，破壞 prospective validation。

因此 T1 的責任是：在任何 eligible private oracle seal 與 private candidate scoring **之前**，先固定 strict-zero threshold policy；之後只接受符合 prospective sequencing、sampling eligibility 與 identity checks 的 aggregate Q1 report，輸出 deterministic 的 private gate `PASS / FAIL / INELIGIBLE`。

## 目標

建立一套 deterministic、aggregate-only 的 Private Threshold Governance subsystem，使 Project 可以：

1. 固定一份不依賴 private outcome 的 strict-zero threshold policy；
2. 以 policy digest 與 freeze timestamp 證明 threshold 在 oracle seal 前已固定；
3. 接受一份外部、事前封存的 sampling eligibility receipt，而不在 T1 內自行發明最低 case/claim 數；
4. 驗證 oracle seal receipt 與 Q1 aggregate report 的 case/claim identity 一致；
5. 對符合 prospective sequencing 的 Q1 aggregate metrics 執行 strict-zero gate；
6. 對不符合 sequencing、sampling、identity 或 schema 的輸入 fail closed 為 `INELIGIBLE`；
7. 產生不含 case/claim/private text 的 deterministic aggregate gate report；
8. 保留「private gate PASS」與「最終 release/promotion」的治理分離。

## 非目標

T1 不得：

- 修改 Q1 evaluator 的 scoring semantics；
- 修改 O1 oracle seal / join semantics；
- 修改 C1 production policy；
- 修改 Coordination、Phase 3、Interpretation 或 Hybrid；
- 自行產生 private oracle expectations；
- 自行決定 sampling protocol 或最低樣本數；
- 從既有 private outcome 推導 threshold；
- 使用百分比 tolerance；
- 在 strict-zero 第一版允許任何非零 error count；
- 對 policy freeze 前已暴露 private candidate output 的 pair 作 retrospective release 判定；
- 把 `PASS` 解讀為可以直接 merge、default switch、tag 或 release；
- 將 private case id、claim id、事件內容、生日、姓名或 adjudication prose 寫入 gate report。

## 設計原則

### 1. Measurement 與 release threshold 分離

```text
Q1 aggregate report
      +
Frozen T1 policy
      +
Sampling eligibility receipt
      +
Oracle seal receipt
      ↓
T1 private release gate
      ↓
PASS / FAIL / INELIGIBLE
```

Q1 繼續只負責量測。T1 不重新計算 claim-level alignment，也不讀 raw Q1 input。

### 2. Strict-zero 是第一版唯一合法門檻

在沒有 general prospective evidence 支持非零 tolerance 前，T1 v1 不允許任意比例或數量容忍。

所有下列欄位的 threshold 固定為 `0`：

```text
cutoff_contamination_count
over_render_count
under_render_count
caveat_omission_count
unnecessary_caveat_count
specificity_overreach_count
specificity_excessive_downgrade_count
decision_alignment.partial
decision_alignment.missed
```

Identity、schema 或 sequencing mismatch 不轉譯成自造的 scoring metric；它們直接使 evidence `INELIGIBLE` 或 validation rejection。T1 的 threshold 只比較 Q1 真正輸出的 aggregate metrics。

### 3. Sampling eligibility 是外部 authority

T1 不定義「至少幾個 cases / claims 才夠」。它只接受一份已在 private evaluation 前封存的 sampling eligibility receipt。

正式 evaluator API 需要 sampling receipt；CLI 未提供必要檔案屬 usage error。若 receipt 本身合法但 `status=INELIGIBLE`，或其 case/claim counts 與其他 aggregate artifacts 不一致，T1 結果必須是 `INELIGIBLE`，不是 PASS，也不是 FAIL。

### 4. Evaluation identity 必須 aggregate-only 綁定 candidate / oracle / Q1 input

T1 不能只知道「某份 Q1 report 的 metrics」；它還必須能稽核這份 report 對應哪個 frozen candidate 與哪個 sealed oracle。

因此 T1 需要一份外部建立、aggregate-only 的 `evaluation identity receipt`，至少綁定：

```text
candidate_sha
oracle_seal_digest
qualification_input_set_digest
case_count
claim_count
```

T1 不負責從 raw private joined input 產生這份 receipt；它只嚴格驗證 receipt，並要求：

```text
identity.oracle_seal_digest == oracle.seal_digest
identity.qualification_input_set_digest == q1.input_set_digest
identity.case_count == oracle.case_count == q1.case_count
identity.claim_count == oracle.claim_count == q1.claim_count
oracle.sealed_at <= identity.bound_at
```

這讓 final gate report 可以保留 candidate SHA 與 aggregate digests，同時不暴露任何 case/claim answer。

### 5. Prospective sequencing 必須可機械驗證

T1 policy 必須在 oracle seal 前 freeze：

```text
policy_frozen_at < oracle_sealed_at
```

若：

```text
policy_frozen_at >= oracle_sealed_at
```

該 pair 一律 `INELIGIBLE`。

這條規則故意排除任何在 threshold policy freeze 前已建立的 oracle seal，包括先前已暴露 candidate output 的 pair。T1 不需要讀該 pair 的 private metrics，就能判斷其不具 prospective eligibility。

Sampling eligibility receipt 也必須在 oracle seal 前 freeze：

```text
sampling_receipt_sealed_at <= oracle_sealed_at
```

T1 不要求 sampling receipt 早於 policy freeze；兩者都是 pre-oracle governance artifacts，但都必須在 oracle seal 前存在。

### 6. Private gate PASS 不是最終 promotion

T1 report 中：

```text
promotion_allowed = false
```

即使 `private_gate_status=PASS`，仍只表示「這個 prospective private qualification gate 通過」。Merge、default switch、tag、release 必須由 Project 其他 release gates 與明確治理決策處理。

## 架構

T1 有五個互相隔離的責任。

### 1. Frozen policy contract

建立：

`engine/distribution/claim_consumption_private_threshold.py`

負責：

- strict policy schema validation；
- strict-zero threshold validation；
- policy digest 計算；
- policy freeze timestamp validation；
- deterministic gate evaluation；
- aggregate-only report digest。

module 不得 import private fixtures、raw oracle、C1 policy 或 Q1 scoring internals。

### 2. Frozen policy artifact

建立 public general artifact：

`qualification/claim_consumption/v1.6/private-release-policy.strict-zero.v1.json`

這份 artifact 是 general governance policy，不含 private data，可進 git。

### 3. Evaluation identity receipt input

T1 定義並驗證 aggregate-only evaluation identity receipt contract，但不從 raw private data 自行產生它。未來 private orchestration 必須在 Q1 gate 前提供此 receipt，用來綁定 frozen candidate、sealed oracle 與 qualification input identity。

### 4. Thin CLI

建立：

`tools/evaluate_v16_claim_consumption_private_threshold.py`

CLI 只負責：

- 讀取 policy；
- 讀取 sampling eligibility receipt；
- 讀取 O1 public seal receipt；
- 讀取 evaluation identity receipt；
- 讀取 Q1 aggregate report；
- 呼叫 T1 evaluator；
- 輸出 canonical aggregate JSON。

CLI 不讀 raw oracle、不讀 joined Q1 private input、不讀 case-level candidate output。

### 5. Synthetic-only tests

建立 synthetic fixtures 與 tests，覆蓋：

- valid strict-zero PASS；
- 每一個 strict-zero metric 單獨非零都 FAIL；
- sampling missing / invalid → INELIGIBLE；
- policy frozen after oracle seal → INELIGIBLE；
- sampling receipt sealed after oracle → INELIGIBLE；
- case/claim count mismatch → INELIGIBLE；
- evaluation identity / oracle / Q1 input-set binding mismatch → INELIGIBLE；
- Q1 report digest tamper → fail closed；
- oracle receipt digest tamper → fail closed；
- unknown/private fields → reject；
- canonical determinism；
- CLI parity；
- current/previous private artifacts cannot be imported or referenced by tests。

## Policy schema

Schema version：

`v1.6-claim-consumption-private-release-policy.v1`

Fields 必須且只能是：

```text
schema_version
policy_profile
policy_frozen_at
thresholds
policy_digest
promotion_allowed
```

固定值：

```text
policy_profile = lin_tianji_claim_consumption_private_strict_zero_v1
promotion_allowed = false
```

`policy_frozen_at` 必須是 UTC RFC3339 `Z` timestamp。

`thresholds` 必須且只能包含：

```text
cutoff_contamination_count
over_render_count
under_render_count
caveat_omission_count
unnecessary_caveat_count
specificity_overreach_count
specificity_excessive_downgrade_count
partial_alignment_count
missed_alignment_count
```

T1 v1 中，全部值必須等於 `0`。任何非零 threshold 都是 schema-validity failure，而不是「另一個 profile」。若未來研究非零 tolerance，必須建立新的 policy profile/schema cycle，不得偷偷修改 v1。

`policy_digest` 是 canonical policy payload（排除 `policy_digest`）的 SHA-256。

## Sampling eligibility receipt schema

T1 只驗證 receipt，不負責產生 receipt。

Schema version：

`v1.6-claim-consumption-sampling-eligibility-receipt.v1`

Fields 必須且只能是：

```text
schema_version
sampling_profile
status
case_count
claim_count
sampling_protocol_digest
sealed_at
receipt_digest
promotion_allowed
```

允許值：

```text
status = ELIGIBLE | INELIGIBLE
promotion_allowed = false
```

規則：

- `case_count`、`claim_count` 必須是 non-negative integer；
- 若 `status=ELIGIBLE`，則 `case_count >= 1` 且 `claim_count >= 1`；
- `sampling_protocol_digest` 必須是 lowercase SHA-256；
- `sealed_at` 必須是 UTC RFC3339 `Z` timestamp；
- `receipt_digest` 是 receipt payload（排除自身）的 SHA-256。

T1 不解讀 `sampling_protocol_digest` 內容，也不自行判斷 sampling 方法是否合理；那是另一個事前 governance authority。

## Evaluation identity receipt schema

T1 只驗證 receipt，不負責從 raw private joined input 產生 receipt。

Schema version：

`v1.6-claim-consumption-private-evaluation-identity-receipt.v1`

Fields 必須且只能是：

```text
schema_version
candidate_sha
oracle_seal_digest
qualification_input_set_digest
case_count
claim_count
bound_at
receipt_digest
promotion_allowed
```

規則：

- `candidate_sha` 必須是 40 字元 lowercase Git SHA；
- `oracle_seal_digest`、`qualification_input_set_digest` 必須是 lowercase SHA-256；
- `case_count >= 1`、`claim_count >= 1`；
- `bound_at` 必須是 UTC RFC3339 `Z` timestamp；
- `promotion_allowed=false`；
- `receipt_digest` 為 receipt payload（排除自身）的 SHA-256。

這份 receipt 不得包含 case id、claim id、decision、expectation、event text 或任何 private prose。

Project governance 必須在 Q1 evaluator invocation 前 freeze 這份 receipt；T1 可驗證 `bound_at >= oracle.sealed_at` 與 digest binding，但無法從 aggregate report 單獨證明 evaluator 的實際 invocation timestamp，因此「receipt 先於 evaluator」仍是外部執行順序 hard gate。

## O1 public seal receipt input

T1 只接受 frozen O1 schema：

`v1.6-claim-consumption-oracle-seal-receipt.v1`

必要條件：

```text
status = SEALED
promotion_allowed = false
cutoff_contamination_count = 0
```

T1 必須重新驗證 receipt 的 strict fields 與 `seal_digest` identity；不得只相信呼叫端說它 valid。因 public receipt 的 schema version 與 private seal 不同，T1 必須用 receipt 內的 seal fields 重建 `v1.6-claim-consumption-oracle-seal.v1` digest payload，再驗證 `seal_digest`；不得直接對 receipt object 本身計算 digest。

T1 只使用下列 aggregate fields：

```text
case_count
claim_count
sealed_at
seal_digest
rubric_digest
case_set_digest
oracle_expectation_digest
cutoff_contamination_count
```

不得要求或接受 case-level answers。

## Q1 aggregate report input

T1 只接受 frozen Q1 report schema：

`v1.6-claim-consumption-qualification-report.v1`

必要條件：

```text
classification = private_external_evaluation
general_conformance_status = METRICS_ONLY
promotion_allowed = false
```

T1 必須重新驗證 Q1 `report_digest`。

T1 只讀 aggregate fields：

```text
case_count
claim_count
decision_alignment.matched
decision_alignment.partial
decision_alignment.missed
over_render_count
under_render_count
caveat_omission_count
unnecessary_caveat_count
specificity_overreach_count
specificity_excessive_downgrade_count
cutoff_contamination_count
input_set_digest
report_digest
```

T1 不重新打分、不讀 claim ids、不讀 private joined input。

T1 仍必須驗證 aggregate report 的內部一致性，包括：

```text
decision_alignment.matched
+ decision_alignment.partial
+ decision_alignment.missed
== claim_count
```

所有 counters 必須是 non-negative integer。`general_conformance_status` 對 private report 必須精確為 `METRICS_ONLY`。

## Cross-artifact identity checks

在 threshold evaluation 前，T1 必須先做 eligibility checks。

### Count identity

必須同時成立：

```text
sampling.case_count == identity.case_count == oracle.case_count == q1.case_count
sampling.claim_count == identity.claim_count == oracle.claim_count == q1.claim_count
```

不成立 → `INELIGIBLE`。

### Evaluation binding identity

必須同時成立：

```text
identity.oracle_seal_digest == oracle.seal_digest
identity.qualification_input_set_digest == q1.input_set_digest
oracle.sealed_at <= identity.bound_at
```

不成立 → `INELIGIBLE`。

`candidate_sha` 由 identity receipt 帶入 final report；T1 不從 Q1 metrics 猜測 candidate identity。T1 只驗證 SHA 格式與 aggregate binding，不自行連線 GitHub 驗證 Hosted status；candidate 是否已完成 local + Hosted freeze 仍由外部 Project governance 負責。

### Sequencing identity

必須同時成立：

```text
policy.policy_frozen_at < oracle.sealed_at
sampling.sealed_at <= oracle.sealed_at
```

不成立 → `INELIGIBLE`。

### Contamination identity

若：

```text
oracle.cutoff_contamination_count != 0
```

則 `INELIGIBLE`。

若 Q1 report 的：

```text
cutoff_contamination_count != 0
```

則該份 report 已進入 strict-zero metric failure，`private_gate_status=FAIL`。

### Integrity identity

任何 policy、sampling receipt、evaluation identity receipt、oracle receipt、Q1 report digest mismatch、schema mismatch、unknown field、NaN/Infinity、duplicate/invalid structure，都 fail closed。

對於「artifact 本身不可信」的情況，T1 不輸出普通 `FAIL`，而是拒絕 evaluation；CLI exit non-zero。

## Gate evaluation semantics

只有全部 eligibility checks 都通過後，T1 才會進行 threshold comparison。

### PASS

`private_gate_status=PASS` 需要所有 strict-zero metrics 都等於 0：

```text
cutoff_contamination_count == 0
over_render_count == 0
under_render_count == 0
caveat_omission_count == 0
unnecessary_caveat_count == 0
specificity_overreach_count == 0
specificity_excessive_downgrade_count == 0
decision_alignment.partial == 0
decision_alignment.missed == 0
```

任何 identity mismatch 會在進入 threshold comparison 前成為 `INELIGIBLE` 或 validation rejection，而不是被轉成可容忍的 scoring count。

### FAIL

eligibility 已通過，但至少一個 strict-zero Q1 metric > 0 → `private_gate_status=FAIL`。

### INELIGIBLE

下列情況之一：

- sampling receipt status 非 `ELIGIBLE`；
- sampling/identity/oracle/Q1 case counts 不一致；
- sampling/identity/oracle/Q1 claim counts 不一致；
- identity 的 oracle seal digest 或 qualification input-set digest 無法與 O1/Q1 對上；
- identity `bound_at` 早於 oracle seal；
- policy freeze 不早於 oracle seal；
- sampling receipt 晚於 oracle seal；
- oracle receipt 顯示 contamination；
- prospective sequencing 未成立。

`INELIGIBLE` 不是 PASS，也不是 FAIL；它代表這組 evidence 不具 release-gate資格。

## Report schema

Schema version：

`v1.6-claim-consumption-private-release-gate-report.v1`

Fields 必須且只能是：

```text
schema_version
policy_profile
policy_digest
sampling_profile
sampling_receipt_digest
evaluation_identity_receipt_digest
candidate_sha
oracle_seal_digest
qualification_input_set_digest
q1_report_digest
case_count
claim_count
eligibility_status
private_gate_status
strict_zero_metrics
promotion_allowed
report_digest
```

`eligibility_status`：

```text
ELIGIBLE
INELIGIBLE
```

`private_gate_status`：

```text
PASS
FAIL
INELIGIBLE
```

`strict_zero_metrics` 必須且只能包含 aggregate values：

```text
cutoff_contamination_count
over_render_count
under_render_count
caveat_omission_count
unnecessary_caveat_count
specificity_overreach_count
specificity_excessive_downgrade_count
partial_alignment_count
missed_alignment_count
```

Report 不得包含：

- case id；
- claim id；
- domain；
- expected/actual authorization；
- specificity per claim；
- event text；
- subject/birth data；
- adjudication prose。

固定：

```text
promotion_allowed = false
```

`report_digest` 為 canonical report（排除自身）SHA-256。

## Canonicalization

沿用 Q1/O1 deterministic convention：

```text
UTF-8
sort_keys=True
separators=(",", ":")
ensure_ascii=False
allow_nan=False
SHA-256 lowercase hexadecimal
```

所有 timestamp 都必須為 UTC RFC3339 `Z`。

## Current exposed pair 的永久處理

本研究週期開始前已存在一組：

- oracle 已 seal；
- candidate private output 已產生；
- joined Q1 input 已建立；
- Q1 evaluator 尚未執行。

T1 不讀也不使用該 pair 的 private candidate behavior 作 threshold design。

由於該 oracle 的 `sealed_at` 必然早於 T1 `policy_frozen_at`，它在 T1 sequencing check 下必然：

```text
INELIGIBLE
```

因此不得在 T1 完成後再把它拿回來跑 Q1 evaluator並宣稱 prospective PASS/FAIL。

這個 pair 只能保留為 blind-adjudication / pre-threshold-exposure audit evidence。

## Synthetic conformance matrix

T1 general-only tests 至少鎖定：

### T1-G1 Valid strict-zero PASS

- policy strict-zero；
- sampling `ELIGIBLE`；
- policy freeze < oracle seal；
- sampling seal <= oracle seal；
- counts 完全一致；
- Q1 所有 strict-zero metrics = 0；
- expected `PASS`。

### T1-G2 Over-render FAIL

只把 `over_render_count` 改為 1 → `FAIL`。

### T1-G3 Under-render FAIL

只把 `under_render_count` 改為 1 → `FAIL`。

### T1-G4 Caveat omission FAIL

只把 `caveat_omission_count` 改為 1 → `FAIL`。

### T1-G5 Unnecessary caveat FAIL

只把 `unnecessary_caveat_count` 改為 1 → `FAIL`。

### T1-G6 Specificity overreach FAIL

只把 `specificity_overreach_count` 改為 1 → `FAIL`。

### T1-G7 Excessive downgrade FAIL

只把 `specificity_excessive_downgrade_count` 改為 1 → `FAIL`。

### T1-G8 Partial alignment FAIL

只把 `decision_alignment.partial` 改為 1 → `FAIL`。

### T1-G9 Missed alignment FAIL

只把 `decision_alignment.missed` 改為 1 → `FAIL`。

### T1-G10 Q1 cutoff contamination FAIL

只把 Q1 `cutoff_contamination_count` 改為 1 → `FAIL`。

### T1-G11 Sampling missing / non-eligible

合法 receipt 的 status 為 `INELIGIBLE` → `INELIGIBLE`；CLI 缺少必要 receipt 則 usage error，絕不 PASS。

### T1-G12 Policy frozen too late

`policy_frozen_at >= oracle.sealed_at` → `INELIGIBLE`。

### T1-G13 Sampling sealed too late

`sampling.sealed_at > oracle.sealed_at` → `INELIGIBLE`。

### T1-G14 Count mismatch

任一 case/claim count identity 不一致 → `INELIGIBLE`。

### T1-G15 Oracle contamination

oracle receipt contamination > 0 → `INELIGIBLE`。

### T1-G16 Evaluation identity mismatch

identity 的 `oracle_seal_digest` 或 `qualification_input_set_digest` 與 O1/Q1 不一致 → `INELIGIBLE`。

### T1-G17 Tamper rejection

policy / sampling / evaluation identity / oracle / Q1 任一 digest tamper → validation error / CLI non-zero。

### T1-G18 Unknown/private field rejection

任一 schema 加入未知欄位、case-level/private欄位 → reject。

### T1-G19 Determinism

相同五份 aggregate artifacts 重複執行 → byte-identical report。

### T1-G20 CLI parity

CLI output 與 direct API canonical bytes 完全一致。

### T1-G21 Private contamination guard

T1 source/tests 不得 import、讀取或引用：

- 任何 private adjudication workspace / raw private artifact path；
- prior private aggregate metrics；
- case ids / claim ids；
- current exposed pair 的 candidate behavior。

## Hard gates

T1 cycle 的工程 hard gates：

1. design/spec freeze；
2. synthetic/general RED；
3. minimal policy/evaluator implementation GREEN；
4. CLI + deterministic policy artifact GREEN；
5. Q1/O1/C1 frozen regression GREEN；
6. full repository regression GREEN；
7. Python 3.9 compile GREEN；
8. AI distribution builder/check GREEN；
9. clean tree GREEN；
10. Hosted same-SHA Validation GREEN；
11. freeze T1 candidate SHA；
12. 本 cycle 不執行任何 private Q1 evaluator；
13. current exposed pair 永久不具 T1 prospective eligibility。

## Private 使用條件（未來 cycle）

T1 完成後，未來新的合法 private cycle 必須依序：

```text
1. freeze T1 policy
2. freeze sampling eligibility receipt
3. independent claim-level adjudication
4. O1 oracle seal
5. candidate local + Hosted freeze
6. generate candidate private output
7. O1 join
8. freeze aggregate evaluation identity receipt
9. execute Q1 private evaluator exactly once
10. execute T1 gate on aggregate Q1 report
11. PASS/FAIL/INELIGIBLE immutable record
```

任何順序倒置都不得補救為 prospective evidence。

## 安全與隱私

- T1 repo artifacts 全部是 general 或 aggregate-only。
- raw private oracle、joined private input、candidate case output 不得進 git。
- T1 report 不含 case/claim identity。
- T1 tests 只用 synthetic data。
- public policy artifact 可進 repo，因其不含 private outcome。
- 若任何工具發現 private field，fail closed，不做 redaction-after-ingestion。

## 成功條件

T1 成功不是「讓 private 比較容易 PASS」，而是：

- threshold 在 private evidence 前可驗證地 freeze；
- strict-zero policy deterministic；
- sampling eligibility 與 threshold authority 分離；
- retrospective pair 自動 ineligible；
- eligible aggregate Q1 report 可被 deterministic 地判定 PASS/FAIL；
- 不修改 Q1/O1/C1；
- 不接觸 private case content；
- local + Hosted hard gates 全綠；
- `promotion_allowed=false` 維持 release governance 邊界。
