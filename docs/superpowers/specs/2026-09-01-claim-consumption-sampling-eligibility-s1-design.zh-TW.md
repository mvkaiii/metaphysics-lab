# Claim Consumption Sampling Eligibility S1 設計規格

## 1. 文件狀態

- 狀態：**書面設計草案，待使用者核准後才可進 implementation plan / TDD**
- 研究代號：`S1`
- 正式名稱：`Claim Consumption Sampling Eligibility S1`
- 建議 sampling profile：`lin_tianji_claim_consumption_complete_census_v1`
- 預定 upstream：frozen T1 candidate `2fd80d234a04d40bafe66db21aa96c4a2594e2a1`
- upstream tree：`19d1829d926132202e42778f1ab8975e41a19cd4`
- T1 policy profile：`lin_tianji_claim_consumption_private_strict_zero_v1`
- T1 policy digest：`65a072b2de63d6f509cc79139442263695589feca28ee99da0ab976ba0c3118a`
- 本文件只定義 general / prospective sampling authority；**不得執行 private Q1 evaluator**。

---

## 2. 問題定義

T1 已經建立 prospective-only 的 private release gate，但 T1 故意不自行決定「多少 private cases 才夠」或「要挑哪些 cases」。

若 sampling authority 不獨立，容易出現三種研究污染：

1. 看過 candidate behavior 後才選較有利的 cases；
2. 看過 adjudication label 後才依 `render / caveat / abstain` 比例挑樣本；
3. 為了讓 private gate 有資料可跑而任意指定最低樣本數。

S1 的任務不是讓 private evaluation 一定可執行，而是建立一個可重現、不可 cherry-pick 的 prospective sampling authority。

核心原則：

> **先固定母體，再完整納入所有符合事前規則且尚未暴露的 cases。沒有足夠合法母體時，輸出 `INELIGIBLE`，不硬湊樣本。**

---

## 3. 方案決策

正式採用：**Complete-Census Prospective Sampling Protocol（完整母體普查式取樣）**。

S1 v1 不採：

- 固定 N random sample；
- 任意百分比抽樣；
- 依 outcome / adjudication / candidate behavior 做 stratified sampling；
- 從已暴露 private cases 中重新包裝子集；
- 為通過 T1 而事後調整 inclusion / exclusion 規則。

---

## 4. Authority 邊界

### 4.1 S1 可以做

S1 僅負責：

- 驗證 public sampling protocol；
- 建立 / 驗證 private sampling frame；
- 依 frozen protocol 對 frame cases 做 deterministic inclusion / exclusion；
- 鎖定每個 included case 的 outcome-free `locked_claim_ids`；
- 檢查 complete-census 是否成立；
- 建立 T1 已接受的 aggregate-only sampling eligibility receipt；
- 在 oracle adjudication 完成後、O1 seal 前，驗證 oracle 的 case / claim identity set 與 frozen sampling frame **完全一致**。

### 4.2 S1 不可以做

S1 不得：

- 讀 C1 candidate output 來決定 sampling；
- 讀 Q1 scoring result 來決定 sampling；
- 讀 claim-level adjudication labels 來決定 sampling；
- 重新打分 claim；
- 修改 Q1/O1/C1、Coordination、Phase 3、Interpretation ranking 或 Hybrid authority；
- 自行創造最低 private case 數；
- 把舊 exposed private pair 洗成 prospective evidence；
- 把 `ELIGIBLE` 等同 release / promotion；
- 將 raw private frame、case IDs、claim IDs 或 private prose commit 到 git。

---

## 5. Prospective 順序

合法流程固定為：

```text
T1 policy freeze
    ↓
S1 sampling protocol freeze
    ↓
private source manifest lock
    ↓
private outcome-free claim universe lock
    ↓
private sampling frame lock
    ↓
S1 sampling eligibility receipt freeze
    ↓
claim-level adjudication
    ↓
S1 oracle identity-set verification
    ↓
O1 oracle seal
    ↓
candidate freeze
    ↓
candidate output / O1 join
    ↓
evaluation identity receipt
    ↓
Q1 exactly once
    ↓
T1 gate
```

禁止倒序補救。

特別地：

- sampling frame 必須在 claim-level adjudication 前 lock；
- sampling receipt 必須在 O1 oracle seal 前 freeze；
- candidate behavior 必須在 frame lock 時仍未對 included cases 暴露；
- 已暴露 cases 只能 `EXCLUDE_PREVIOUSLY_EXPOSED`，不得重新納入。

---

## 6. Public Sampling Protocol

### 6.1 Schema

新增：

`v1.6-claim-consumption-sampling-protocol.v1`

公開 artifact 預定路徑：

`qualification/claim_consumption/v1.6/sampling-protocol.complete-census.v1.json`

### 6.2 欄位

```text
schema_version
sampling_profile
required_t1_policy_profile
required_t1_policy_digest
protocol_frozen_at
allowed_case_statuses
allowed_exclusion_reason_codes
complete_census_required
candidate_exposure_must_be_unexposed
claim_universe_must_be_outcome_free
minimum_case_count_rule
minimum_claim_count_rule
protocol_digest
promotion_allowed
```

固定值：

```text
schema_version = v1.6-claim-consumption-sampling-protocol.v1
sampling_profile = lin_tianji_claim_consumption_complete_census_v1
required_t1_policy_profile = lin_tianji_claim_consumption_private_strict_zero_v1
required_t1_policy_digest = 65a072b2de63d6f509cc79139442263695589feca28ee99da0ab976ba0c3118a
complete_census_required = true
candidate_exposure_must_be_unexposed = true
claim_universe_must_be_outcome_free = true
minimum_case_count_rule = at_least_one_if_eligible
minimum_claim_count_rule = at_least_one_if_eligible
promotion_allowed = false
```

S1 v1 **不放任意數值最低樣本門檻**。

### 6.3 Protocol digest

`protocol_digest`：

- 對移除 `protocol_digest` 後的完整 protocol payload；
- 使用 UTF-8 canonical JSON；
- `sort_keys=true`；
- separators 為 `(',', ':')`；
- `allow_nan=false`；
- 計算 SHA-256 lowercase hex。

---

## 7. Private Sampling Source Manifest

### 7.1 Schema

新增 private-only schema：

`v1.6-claim-consumption-sampling-source-manifest.v1`

此 manifest 是 complete-census 的母體 authority，必須在 sampling frame 之前 lock，且**不得進 git**。

### 7.2 Root 欄位

```text
schema_version
sampling_profile
sampling_protocol_digest
required_t1_policy_digest
cutoff_timestamp
source_locked_at
records
source_manifest_digest
```

### 7.3 Record 欄位

每筆只保存 opaque / structured eligibility facts：

```text
opaque_case_id
source_record_digest
within_cutoff
candidate_exposure_status
confirmation_status
input_validity_status
scope_status
eligibility_facts_digest
record_digest
```

固定 enum：

```text
candidate_exposure_status = UNEXPOSED | PREVIOUSLY_EXPOSED
confirmation_status = CONFIRMED | NON_CONFIRMATION
input_validity_status = VALID | INVALID
scope_status = IN_SCOPE | OUT_OF_SCOPE
```

禁止 free-text eligibility facts。

### 7.4 Eligibility facts 的時間邊界

上述 facts 必須在 claim-level adjudication 前固定：

- `within_cutoff` 只由 frozen cutoff 與 source timestamp 判斷；
- `candidate_exposure_status` 只由既有 exposure registry / audit 判斷，不得看即將評估 candidate 的輸出；
- `confirmation_status` 是 sampling source quality / confirmation eligibility，不是 claim-level authorization label；
- `input_validity_status` 只描述資料是否足以建立 outcome-free claim universe；
- `scope_status` 只描述是否屬 frozen research scope。

這些欄位不得保存事件 prose、oracle answer 或 Q1 result。

### 7.5 Deterministic exclusion precedence

同一 case 若同時符合多個 exclusion 條件，status 不得人工選擇，固定 precedence：

```text
1. within_cutoff = false                -> EXCLUDE_AFTER_CUTOFF
2. PREVIOUSLY_EXPOSED                   -> EXCLUDE_PREVIOUSLY_EXPOSED
3. NON_CONFIRMATION                     -> EXCLUDE_NON_CONFIRMATION
4. INVALID                              -> EXCLUDE_INPUT_INVALID
5. OUT_OF_SCOPE                         -> EXCLUDE_OUT_OF_SCOPE
6. 其餘                                 -> INCLUDE
```

precedence 只決定唯一 audit reason，不改變 inclusion eligibility。

### 7.6 `eligibility_facts_digest`

對以下 canonical payload 計算 SHA-256：

```text
within_cutoff
candidate_exposure_status
confirmation_status
input_validity_status
scope_status
```

### 7.7 `record_digest`

對以下 canonical payload 計算 SHA-256：

```text
opaque_case_id
source_record_digest
eligibility_facts_digest
```

### 7.8 `source_manifest_digest`

對 root payload 移除 `source_manifest_digest` 後計算 canonical SHA-256；`records` 必須先依 `opaque_case_id` 排序。

source manifest 一旦 lock，不得因後續 adjudication 或 candidate behavior 重寫。

---

## 8. Private Outcome-Free Claim Universe Lock

### 8.1 Schema

新增 private-only schema：

`v1.6-claim-consumption-sampling-claim-universe-lock.v1`

此 artifact 在 source manifest lock 後、sampling frame lock 前建立，**不得進 git**。

### 8.2 Root 欄位

```text
schema_version
sampling_profile
sampling_protocol_digest
source_manifest_digest
claim_authority_profile
claim_authority_digest
locked_at
cases
claim_universe_digest
```

### 8.3 Case 欄位

```text
opaque_case_id
locked_claim_ids
claim_case_digest
```

### 8.4 Case-set 規則

claim universe lock 必須只包含依 source manifest + frozen exclusion precedence 推導為 `INCLUDE` 的 cases，而且 case set 必須**完全相等**：

- 不得少一個應 INCLUDE case；
- 不得多一個 excluded case；
- 每個 included case 的 `locked_claim_ids` 必須非空；
- claim IDs 必須唯一、canonical sort。

若 source manifest 推導出的 INCLUDE case set 為空，claim universe lock 可有空 `cases`，後續 sampling receipt 只能 `INELIGIBLE`。

### 8.5 Claim authority

`claim_authority_profile / claim_authority_digest` 用來綁定 outcome-free claim-generation authority 的版本與固定規則，例如 frozen Phase 3 / selector / interpretation input authority。

要求：

- authority 本身不得讀 verified outcome；
- authority 不得讀 C1 render decision；
- authority 不得讀 Q1 result；
- authority digest 必須在 claim universe lock 前固定；
- 同一 source manifest + 同一 authority 必須可重現同一 claim identity set。

### 8.6 `claim_case_digest`

對以下 canonical payload計算 SHA-256：

```text
opaque_case_id
locked_claim_ids
```

### 8.7 `claim_universe_digest`

對 root payload 移除 `claim_universe_digest` 後計算 canonical SHA-256；`cases` 依 `opaque_case_id` 排序，`locked_claim_ids` 各自排序。

---

## 9. Private Sampling Frame

### 9.1 Schema

新增 private-only schema：

`v1.6-claim-consumption-sampling-frame.v1`

此 artifact **不得進 git**。

### 9.2 Root 欄位

```text
schema_version
sampling_profile
sampling_protocol_digest
required_t1_policy_digest
cutoff_timestamp
source_manifest_digest
claim_universe_digest
claim_authority_profile
claim_authority_digest
locked_at
cases
frame_digest
```

### 9.3 Case 欄位

每個 case 僅保存 opaque / structured identity，不保存事件 prose：

```text
opaque_case_id
source_record_digest
status
exclusion_reason_code
locked_claim_ids
case_digest
```

### 9.4 Case status

允許：

```text
INCLUDE
EXCLUDE_AFTER_CUTOFF
EXCLUDE_PREVIOUSLY_EXPOSED
EXCLUDE_NON_CONFIRMATION
EXCLUDE_INPUT_INVALID
EXCLUDE_OUT_OF_SCOPE
```

規則：

- `INCLUDE`：`exclusion_reason_code = null`，`locked_claim_ids` 必須非空；
- `EXCLUDE_*`：`exclusion_reason_code` 必須與 status 對應；
- 所有 `locked_claim_ids` 若存在，都必須來自 outcome-free claim universe；
- included case 不得因為 adjudication 結果或 candidate output 被排除；
- opaque case ID 必須唯一；
- `INCLUDE` case 的 `locked_claim_ids` 必須逐字來自 claim universe lock；excluded case 的 `locked_claim_ids` 固定為空 list。
- claim IDs 在同一 case 內必須唯一並 canonical sort。
- `status / exclusion_reason_code` 必須由 source manifest eligibility facts 與 frozen precedence 自動推導；不得由使用者任意指定。
- sampling frame 的 case ID set 與 source manifest 的 case ID set 必須完全相等。
- sampling frame 的每個 `source_record_digest` 必須與 source manifest 同 case 完全相等。

### 9.5 Exclusion reason codes

固定：

```text
after_cutoff
previously_exposed
non_confirmation
input_invalid
out_of_scope
```

不得接受 free-text exclusion reason。

### 9.6 `source_record_digest`

直接沿用 private source manifest 同 case 的 `source_record_digest`，不得在 frame 階段重新計算成另一份 identity。

S1 不規定 source record 的業務內容，但要求其 digest 在 source manifest lock 前產生，且 candidate output / adjudication label 不得參與。

### 9.7 `case_digest`

對以下 canonical payload 計算 SHA-256：

```text
opaque_case_id
source_record_digest
status
exclusion_reason_code
locked_claim_ids
```

### 9.8 `frame_digest`

對 root payload 移除 `frame_digest` 後計算 canonical SHA-256。

`cases` 必須先依 `opaque_case_id` 排序，避免輸入順序影響 digest。

---

## 10. Complete-Census 規則

S1 `ELIGIBLE` 的核心不是抽樣率，而是「完整母體是否被無裁量地處理」。

必須同時滿足：

1. public protocol valid 且 digest 正確；
2. private source manifest valid 且 digest 正確；
3. source manifest 使用同一 frozen protocol / T1 policy digest；
4. private claim universe lock valid 且 digest 正確；
5. claim universe lock 綁定同一 source manifest / protocol；
6. claim universe case set 與 manifest deterministic `INCLUDE` case set 完全相等；
7. sampling frame valid 且 digest 正確；
8. frame 的 `source_manifest_digest / claim_universe_digest` 與 frozen inputs 完全一致；
9. frame case ID set 與 source manifest record ID set 100% 相等；
10. frame 每案 `source_record_digest` 與 manifest 同案完全一致；
11. frame 的 included `locked_claim_ids` 與 claim universe lock 同案完全一致；
12. frame 在 adjudication 前 lock；
13. 每個 frame case 必須恰有一個由 fixed precedence 自動推導的 status；
14. 所有不符合 inclusion 的 case 必須使用 fixed exclusion reason；
15. 所有符合 inclusion 的 unexposed cases 必須 `INCLUDE`；
16. included cases 不得是 previously exposed；
17. included claims 全部來自 outcome-free locked claim universe；
18. 沒有 discretionary / free-text exclusion；
19. included `case_count >= 1`；
20. included `claim_count >= 1`；
21. `promotion_allowed=false`。

若合法 frame 中沒有任何 included case 或 claim：

```text
sampling receipt status = INELIGIBLE
case_count = 0
claim_count = 0
```

不得為了把 receipt 變成 `ELIGIBLE` 而重新定義母體。

---

## 11. Previously Exposed 定義

case 在 sampling frame lock 前，只要符合以下任一條件，即視為 exposed：

- frozen / experimental candidate 曾對該 case 產生 claim consumption output；
- candidate output 曾被研究者或自動流程讀取；
- Q1 / equivalent claim-level scoring 曾對該 candidate-case pair 執行；
- candidate behavior 已進入任何可影響 sampling/adjudication 的人類或機器決策流程。

已知目前先前暴露的 private pair：

- 必須永久 `EXCLUDE_PREVIOUSLY_EXPOSED`；
- 不得因為換 case ID、換 digest、換 branch 或重跑 candidate 而恢復 eligibility。

S1 不在 public artifact 保存 exposed case IDs；只在 private frame 表達狀態。

---

## 12. Outcome-Free Claim Universe

`locked_claim_ids` 必須在 outcome / adjudication / candidate output 之前可重現。

允許來源：

- frozen Phase 3 authority；
- frozen selector / interpretation input；
- 其他已事前鎖定且不含 outcome 的 claim-generation authority。

禁止來源：

- verified-event outcome；
- claim-level oracle labels；
- C1 render decision；
- Q1 private result；
- candidate output 後人工刪除或新增 claims。

S1 只鎖 claim identity，不決定：

- `render`
- `render_with_caveat`
- `abstain_claim`
- specificity bounds

這些仍屬後續 claim-level adjudication / O1 oracle authority。

---

## 13. Oracle Identity-Set Verification

為避免 sampling frame 與後續 oracle 在 case/claim 集合上悄悄漂移，S1 必須提供一個 **identity-only** verifier。

建議 API：

```python
verify_oracle_identity_against_sampling_frame(
    sampling_frame,
    oracle,
) -> dict
```

此函式只比較 identity，不讀取或評價 oracle answer semantics。

對每個 `INCLUDE` case：

- sampling `opaque_case_id` 必須對應 oracle `case_id`；
- oracle expectation `claim_id` set 必須與 `locked_claim_ids` **完全相等**；
- 不得多 claim；
- 不得少 claim；
- excluded cases 不得出現在 oracle；
- oracle 不得新增 sampling frame 外的 case。

驗證成功只輸出：

```text
schema_version
status = VALID
case_count
claim_count
sampling_frame_digest
oracle_identity_digest
verification_digest
promotion_allowed = false
```

此 verification 可以留在 private adjudication workspace；public repo 不要求保存 case/claim identity。

重要：

- 這個 verifier **不得呼叫 Q1 evaluator**；
- 不得根據 `expected_authorization` 改 sampling；
- 不修改 O1 seal semantics。

---

## 14. Sampling Eligibility Receipt

S1 必須輸出 frozen T1 已接受的既有 schema：

`v1.6-claim-consumption-sampling-eligibility-receipt.v1`

欄位完全沿用 T1：

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

### 12.1 `ELIGIBLE`

只有 Complete-Census 規則全部成立且 included count >0 才可：

```text
status = ELIGIBLE
case_count = number of INCLUDE cases
claim_count = total locked claims across INCLUDE cases
sampling_profile = lin_tianji_claim_consumption_complete_census_v1
sampling_protocol_digest = frozen S1 protocol digest
promotion_allowed = false
```

### 12.2 `INELIGIBLE`

以下情況輸出 `INELIGIBLE`，不是 validation error：

- valid sampling frame 中沒有任何新的 unexposed included case；
- valid sampling frame 的 included claim count 為 0；
- protocol 明確允許且可稽核的 sampling eligibility 條件未達成，但 artifact 本身未遭竄改。

### 12.3 Validation error

以下必須 fail closed / raise `ValueError` / CLI non-zero，不得包裝成 `INELIGIBLE`：

- unknown fields；
- malformed schema；
- digest mismatch；
- free-text exclusion reason；
- duplicate case / claim IDs；
- illegal status/reason mapping；
- protocol/T1 digest mismatch；
- included previously-exposed case；
- included case 缺 outcome-free claims；
- 明顯不完整的 frame / census assertion 被竄改。

---

## 15. Public / Private Artifact 分界

### 13.1 可進 git

- S1 design spec；
- implementation plan；
- general sampling protocol JSON；
- synthetic fixtures；
- source / CLI / tests；
- general method doc；
- aggregate/digest-only receipts（若無 private IDs / prose）。

### 13.2 不得進 git

- real private sampling frame；
- opaque private case IDs；
- real locked claim IDs；
- source record；
- adjudication notes；
- oracle expectations；
- candidate private output；
- joined private Q1 input；
- case-level private scoring。

---

## 16. 建議 Production API

新增獨立 module：

`engine/distribution/claim_consumption_sampling_eligibility.py`

建議 API：

```python
validate_sampling_protocol(payload) -> dict
validate_sampling_source_manifest(payload, protocol) -> dict
validate_claim_universe_lock(payload, source_manifest, protocol) -> dict
build_sampling_frame(source_manifest, claim_universe_lock, protocol, locked_at) -> dict
validate_sampling_frame(payload, source_manifest, claim_universe_lock, protocol) -> dict
build_sampling_eligibility_receipt(frame, source_manifest, claim_universe_lock, protocol, sealed_at) -> dict
verify_sampling_eligibility_receipt(receipt) -> dict
verify_oracle_identity_against_sampling_frame(frame, oracle) -> dict
```

module 不 import / 呼叫：

- `evaluate_claim_consumption_qualification`
- `evaluate_claim_consumption_private_threshold`
- C1 scoring / decision builder

可重用 O1 oracle validator 的 schema-level identity parsing，但不得呼叫 O1 scoring（O1 本身也不 scoring）。若 import 會造成 authority 混淆，則只在 S1 實作最小 strict oracle identity parser。

---

## 17. CLI

建議：

`tools/evaluate_v16_claim_consumption_sampling_eligibility.py`

模式：

```text
validate-protocol
validate-source-manifest
validate-claim-universe-lock
build-frame
validate-frame
seal-receipt
verify-receipt
verify-oracle-identity
```

private artifacts 的所有輸出都必須要求 explicit output path。

CLI 不得：

- 預設把 private JSON 寫到 repo；
- 執行 Q1；
- 執行 T1；
- 自動讀取舊 private aggregate；
- 自動尋找或補齊 cases。

---

## 18. Synthetic / General Test Matrix

至少鎖定：

### S1-G1 合法完整普查

- 2 個 included unexposed cases；
- outcome-free claims 非空；
- 預期 `ELIGIBLE`。

### S1-G2 零新 case

- 全部 cases 合法但皆 `EXCLUDE_PREVIOUSLY_EXPOSED`；
- 預期 receipt `INELIGIBLE`，counts = 0。

### S1-G3 已暴露 case 被 INCLUDE

- 預期 fail closed。

### S1-G4 after-cutoff exclusion

- fixed reason 合法；
- 不影響其他 included cases eligibility。

### S1-G5 non-confirmation exclusion

- fixed reason 合法；
- 不可用 free text。

### S1-G6 input-invalid / out-of-scope

- reason/status mapping 必須精確。

### S1-G7 outcome-free claim universe 缺失

- included case claims = []；
- fail closed。

### S1-G8 duplicate claim ID

- fail closed。

### S1-G9 duplicate case ID

- fail closed。

### S1-G10 protocol digest tamper

- fail closed。


### S1-G10a source manifest digest tamper

- fail closed。

### S1-G10b source manifest / frame case-set mismatch

- fail closed。

### S1-G10c exclusion precedence determinism

- 同一 case 同時 after-cutoff + previously-exposed 時，固定輸出 `EXCLUDE_AFTER_CUTOFF`；不得因輸入順序不同改 reason。

### S1-G10d claim universe 少 INCLUDE case

- fail closed。

### S1-G10e claim universe 多 excluded case

- fail closed。

### S1-G10f claim universe / frame claim-set mismatch

- fail closed。

### S1-G11 frame digest tamper

- fail closed。

### S1-G12 case digest tamper

- fail closed。

### S1-G13 T1 policy digest mismatch

- fail closed。

### S1-G14 unknown field

- protocol / frame / case / receipt 任何層級均 fail closed。

### S1-G15 permutation determinism

- case order / claim order permutation 不得改變 canonical frame digest / receipt digest。

### S1-G16 complete-census mutation guard

- source manifest 固定不變；從 frame 偷刪一個 manifest case 後，即使 included counts 看似合理，也必須因 case-set 不等而 fail closed。

### S1-G17 oracle 少 claim

- identity verifier FAIL。

### S1-G18 oracle 多 claim

- identity verifier FAIL。

### S1-G19 oracle 多 / 少 case

- identity verifier FAIL。

### S1-G20 oracle answer permutation

- 若 case/claim identity set 相同，S1 identity verifier不得因 authorization/specificity answer不同而改 sampling validity；S1不評 answer correctness。

### S1-G21 private contamination guard

- tests/source/docs 不得 import/read real private workspace、prior private aggregate、real case IDs、real claim IDs。

### S1-G22 upstream mutation guard

- Q1/O1/C1/T1/Coordination/Phase 3 semantics 不變。

---

## 19. Hard Gates

S1 cycle 必須依序完成：

1. design spec freeze；
2. implementation plan；
3. synthetic/general RED；
4. minimal implementation GREEN；
5. S1 focused regression GREEN；
6. frozen T1/Q1/O1/C1 regressions GREEN；
7. CLI/doc RED→GREEN；
8. formal AI builder/check GREEN；
9. full repository regression GREEN；
10. Python 3.9 compile GREEN；
11. private-artifact contamination scan GREEN；
12. clean tree GREEN；
13. GitHub exact-tree transport；
14. Hosted same-SHA Validation GREEN；
15. freeze S1 candidate；
16. **只有 freeze 後才允許建立 real private source manifest / claim universe lock / sampling frame。**

S1 cycle 本身：

- 不執行 Q1 private evaluator；
- 不執行 T1 private gate；
- 不建立 claim-level oracle；
- 不 merge / default switch / tag / release。

---

## 20. Real Sampling Frame 建立後的決策

S1 infrastructure freeze 後，才可使用真實 private sources 先建立並 lock source manifest，再用 frozen outcome-free claim authority 建立 claim universe lock，最後由 S1 deterministic builder 產生 frame。

若：

```text
new unexposed eligible cases > 0
and locked claims > 0
```

則：

```text
S1 receipt = ELIGIBLE
```

接著才進 claim-level adjudication / O1 seal。

若：

```text
new unexposed eligible cases = 0
or locked claims = 0
```

則：

```text
S1 receipt = INELIGIBLE
```

此結果不是失敗，也不得透過修改 protocol 來「救」成 ELIGIBLE。

---

## 21. Release / Promotion 邊界

即使未來 S1 receipt = `ELIGIBLE`：

- 不代表 Q1 PASS；
- 不代表 T1 PASS；
- 不代表 merge；
- 不代表 default switch；
- 不代表 tag / release。

所有 S1 public artifacts 與 receipts 必須保留：

```text
promotion_allowed = false
```

---

## 22. 核心設計結論

S1 v1 不嘗試回答「幾個 case 才夠」。

它只回答：

> **在一個事前固定、candidate-independent、adjudication-independent 的 private sampling frame 中，是否已完整納入所有合法、未暴露、符合規則的 cases 與其 outcome-free claim universe？**

答案若是「是」且 counts > 0，輸出 `ELIGIBLE`。

答案若是「合法母體目前沒有新 case」，輸出 `INELIGIBLE`。

答案若涉及 schema、digest、frame completeness 或 exposure 規則被破壞，直接 fail closed。

這樣才能讓未來 Q1 private evaluation 保持 prospective、不可 cherry-pick，也不需要為了趕版本任意降低 sampling gate。
