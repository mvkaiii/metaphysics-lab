# Claim Consumption Oracle Seal O1 設計規格

## 狀態與來源追溯

- 研究週期：`v1.6 Claim Consumption Oracle Seal O1`。
- GitHub 上具權威性的上游 frozen Q1 candidate：`4c5df745554b1d14a08b58aae45f4212b0162132`。
- GitHub 上具權威性的上游 frozen C1 candidate：`39a084b9e7e5d56f0d6ac0970ed5683258a4d402`。
- 本地 workspace 內含經 byte 驗證的 Q1/C1 source state，但本地 commit lineage 是重建的；本地 commit SHA 不得作為 GitHub provenance 對外聲稱。
- O1 期間，Q1 evaluator semantics 與 C1 production policy 均視為唯讀。
- Coordination、Phase 3 ranking、Claim Evidence candidate sets、Interpretation ranking、Hybrid render policy 均視為唯讀。
- 任何既有 private aggregate outcome 都不得作為 O1 policy-selection 的輸入。

## 問題定義

Q1 已能對完整的 `v1.6-claim-consumption-qualification-input.v1` payload 進行 deterministic scoring，但該 evaluator input 同時包含：

1. candidate 產生的 `claim_consumption_bundle`；以及
2. 獨立 adjudication 後得到的 claim-level `expectations`。

這份合併後的 evaluator input 本身不能直接當成「candidate 產生前的 oracle seal」。如果在 candidate freeze 前就準備完整 evaluator input，就必須先有尚不存在的 candidate output；但如果等 candidate freeze 後才建立 evaluator input，又沒有更早的 expectation seal，Project 就無法證明 claim-level answers 在 scoring 前已固定。

因此，Project 需要一個獨立的 sealing authority：在 candidate scoring 前，只封存已 adjudicate 的 oracle expectations 與 case-set identity，並讓 private structured inputs 保持在 git 之外。candidate freeze 後，再由 join step 將 sealed oracle 與 frozen candidate 的 C1 output 組成既有 Q1 evaluator input，而且不得改變 Q1 scoring semantics。

## 目標

新增一套 deterministic、保護隱私的 Oracle Seal subsystem，使其可以：

1. 嚴格驗證與 candidate 無關的 claim-level oracle；
2. 計算 deterministic 的 case / oracle / rubric / set / seal digests；
3. 產生 aggregate-only 的 public seal receipt，且不得包含 case-level answers；
4. 之後可驗證使用的是同一份 sealed oracle；
5. 將 sealed oracle 與 frozen candidate C1 output join 成已凍結的 Q1 evaluator input schema；以及
6. 在 adjudication、sealing、candidate execution、private evaluation 之間維持清楚的 audit boundary。

O1 建立的是 evaluation integrity。它不定義、不調整 C1 行為，也不會自行授權 private evaluation、promotion、merge、default switch、tag 或 release。

## 非目標

O1 不得：

- 修改 `engine/distribution/claim_consumption_contract.py`；
- 修改 `engine/distribution/claim_consumption_qualification.py` 的 scoring semantics；
- 修改 Coordination semantics；
- 改變 Phase 3 ranking 或 Interpretation candidate sets；
- 從既有 private Interpretation domain/event-family labels 推導 claim-level oracle labels；
- 根據過去 private aggregate PASS/FAIL 結果反推出 oracle expectations；
- 將 raw private oracle answers、private case identifiers、subject data、birth data、event text 或 narrative adjudication 放進 git；
- 用「加密後放進 git」取代「private answers 保持在 git 外」這個原則；
- 為 under-render、caveat excess 或 specificity downgrade 任意定義非零 release tolerance；
- 在 O1 開發過程執行 private Q1 evaluation；
- promotion、merge、default-switch、tag 或 release。

## 架構

O1 有四個互相隔離的責任。

### 1. Oracle contract 與 sealing

建立 `engine/distribution/claim_consumption_oracle_seal.py`。

它負責：

- 嚴格驗證 `v1.6-claim-consumption-oracle.v1`；
- canonical case digest 計算；
- oracle expectation-set digest 計算；
- rubric digest 驗證；
- deterministic seal 建立；
- seal 驗證；
- aggregate-only seal-receipt 建立。

它不得 import private fixtures，也不得呼叫 C1 policy。

### 2. Candidate-output join

同一個 module 負責 deterministic join function，將：

- 一份已驗證的 sealed oracle；以及
- 一份由 frozen candidate 產生的 candidate-output package；

組成既有 Q1 input schema：

`v1.6-claim-consumption-qualification-input.v1`。

join step 不進行 claim scoring，也不重新解讀 expectations。它只驗證 identity/digests，然後組裝已凍結的 evaluator input。

### 3. 精簡 CLI surface

建立 `tools/seal_v16_claim_consumption_oracle.py`，提供三個明確模式：

- `seal`：驗證 oracle，寫出 private seal，並可選擇產生 public receipt；
- `verify`：驗證 oracle 是否符合 seal，輸出只含 status 的 verification report；
- `join`：將已驗證 sealed oracle 與 candidate output 結合，寫出 Q1 evaluator input。

CLI 不得自動 commit、upload，或把 private input 複製到 repository paths。

### 4. 僅 synthetic 的 fixtures 與 tests

建立 synthetic fixtures 與 tests，涵蓋：

- valid sealing；
- 與輸入順序無關的 digests；
- tamper detection；
- unknown/private-field rejection；
- rubric mismatch；
- case-set mismatch；
- candidate-output mismatch；
- exact join behavior；
- public receipt 不含答案；
- Q1 scoring 不變。

O1 開發期間不得使用任何真實 private case content。

## 資料契約

### Oracle schema

Schema version：

`v1.6-claim-consumption-oracle.v1`

Top-level fields 必須且只能是：

```text
schema_version
oracle_profile
rubric_digest
cases
```

`oracle_profile` 必須是非空、具版本資訊的識別字，例如：

`lin_tianji_claim_consumption_oracle_v1`

`rubric_digest` 是建立 expectations 時所使用之 frozen human/machine adjudication rubric artifact 的小寫 SHA-256 digest。

每個 case 必須且只能包含：

```text
case_id
expectations
cutoff_contamination
oracle_case_digest
```

`expectations` 結構必須完全等同 frozen Q1 expectation contract：

```text
claim_id
expected_authorization
minimum_acceptable_specificity
maximum_specificity
caveat_required
```

Oracle schema 中不得出現 `claim_consumption_bundle`。Candidate output 刻意不包含在 seal 裡。

### Oracle case identity

`oracle_case_digest` 是 canonical case payload（排除 `oracle_case_digest` 本身）的 SHA-256。

其涵蓋：

- opaque `case_id`；
- 已排序正規化的 expectations；
- `cutoff_contamination`。

digest 前，expectations 必須依 `claim_id` 正規化排序。若有重複 `claim_id`，必須 fail closed。

### Oracle seal schema

Schema version：

`v1.6-claim-consumption-oracle-seal.v1`

Fields 必須且只能是：

```text
schema_version
oracle_profile
case_count
claim_count
rubric_digest
oracle_expectation_digest
case_set_digest
cutoff_contamination_count
sealed_at
seal_digest
```

定義：

- `oracle_expectation_digest`：將 canonical normalized case payload list 計算 SHA-256；每個 case 移除 `oracle_case_digest`，cases 依 `case_id` 排序，每個 case 的 expectations 依 `claim_id` 排序。因此它涵蓋 opaque case identity、全部 expectation answers 與 cutoff contamination，同時對輸入 list order 不敏感。
- `case_set_digest`：對排序後的 `oracle_case_digest` list 計算 SHA-256。這個資訊刻意與 `oracle_expectation_digest` 有部分重疊，讓 audit 時可以區分「整體 oracle expectation drift」與「case-set identity drift」。
- `cutoff_contamination_count`：只保存 aggregate count。
- `sealed_at`：由外部提供的 UTC RFC3339 timestamp，供 audit 使用；它會納入 `seal_digest`，但不作為 semantic correctness 的判斷依據。
- `seal_digest`：對完整 seal object（排除 `seal_digest` 本身）計算 SHA-256。

seal 可以保持 private，因為其中 digests 與 private oracle 有關，但 seal 本身不包含 raw event text 或 subject data。

### Public seal receipt schema

Schema version：

`v1.6-claim-consumption-oracle-seal-receipt.v1`

Fields 必須且只能是：

```text
schema_version
status
oracle_profile
case_count
claim_count
rubric_digest
case_set_digest
oracle_expectation_digest
cutoff_contamination_count
sealed_at
seal_digest
promotion_allowed
```

必要值：

```text
status = SEALED
promotion_allowed = false
```

Public receipt 不得包含：

- `case_id`；
- `claim_id`；
- `expected_authorization`；
- specificity bounds；
- domains；
- reason codes；
- subject/birth/event data；
- free-form adjudication text。

即使 `cutoff_contamination_count > 0`，receipt 仍可以證明「這份 seal 存在」，但不得進入後續 private qualification execution。join step 必須對 contaminated seal fail closed。

### Candidate-output package schema

Schema version：

`v1.6-claim-consumption-candidate-output.v1`

Top-level fields 必須且只能是：

```text
schema_version
candidate_sha
cases
```

每個 case 必須且只能包含：

```text
case_id
claim_consumption_bundle
candidate_case_digest
```

`candidate_sha` 必須是 40 字元的小寫 Git commit SHA。O1 不負責判斷該 SHA 是否通過 Hosted validation；在執行 private 前，由 Project governance 另外確認。

`claim_consumption_bundle` 使用既有 frozen C1 public bundle shape，也就是 Q1 已接受的格式。

`candidate_case_digest` 是 canonical `case_id + claim_consumption_bundle` 的 SHA-256，排除 `candidate_case_digest` 本身。

未知欄位一律 fail closed。

### Join output

join function 必須輸出：

```text
schema_version = v1.6-claim-consumption-qualification-input.v1
classification = private_external_evaluation
cases = [...]
```

每個 joined case 必須且只能包含 Q1 input fields：

```text
case_id
claim_consumption_bundle
expectations
cutoff_contamination
input_digest
```

`input_digest` 必須使用既有 Q1 canonical case rule 重新計算。O1 不得把 oracle digest 或 candidate digest 直接重用成 `input_digest`。

## Canonicalization 規則

所有 O1 digests 都使用 v1.6 qualification code 既有的 deterministic JSON convention：

```text
UTF-8
sort_keys=True
separators=(",", ":")
ensure_ascii=False
allow_nan=False
SHA-256 lowercase hexadecimal
```

順序正規化：

- top-level case order 在 semantics 上不具意義；
- 建立 aggregate digest 時，cases 依 `case_id` canonicalize；
- expectations 依 `claim_id` canonicalize；
- candidate cases 依 `case_id` canonicalize；
- duplicate IDs 必須 fail closed，不得自行 deduplicate。

## 嚴格驗證與隱私控制

O1 在每一個 schema level 都拒絕 unknown fields。

明確禁止的例子包含：

```text
subject_name
birth_date
birth_time
full_address
actual_event
event_text
narrative
notes
raw_chart
```

這份清單只是例示，不是完整列舉；真正 enforcement 由 strict allowlists 負責。

Public receipt 與 verification outputs 必須是 aggregate-only，不得 serialize case IDs 或 expectation contents。

join output 是 private structured evaluation input，必須留在 git 外。任何 CLI default 都不得把 joined private output 指向 repository path。

## Seal workflow

合法流程：

```text
1. Freeze adjudication rubric
2. 在沒有 candidate output 的情況下準備 claim-level expectations
3. 驗證 oracle schema
4. Seal oracle
5. Oracle + seal 存在 git 外
6. 如需要，只 commit aggregate seal receipt
7. 獨立 freeze candidate SHA
8. 通過 local + Hosted general gates
9. 對同一 opaque case set 匯出 candidate C1 output
10. 驗證 oracle seal
11. 驗證 candidate-output package
12. Join oracle + candidate output
13. Q1 private evaluator 只執行一次
14. 發布 aggregate-only Q1 result
```

非法流程包括：

- 看到 candidate output 後再修改 expectations；
- 看完 private evaluation 結果後 reseal，卻仍宣稱是同一 evaluation cycle；
- 用既有 Interpretation private labels 充當 Q1 claim expectations；
- join 未 seal 的 oracle；
- join 與 sealed oracle 不同 case set 的 candidate；
- 在 candidate freeze 或 Hosted qualification 前執行 Q1 private evaluation。

## Seal verification semantics

`verify_oracle_seal(oracle, seal)` 在以下任何項目不一致時都必須 fail closed：

- schema/profile；
- rubric digest；
- case count；
- claim count；
- 任一 case digest；
- case-set digest；
- oracle-expectation digest；
- contamination count；
- seal digest。

Verification 只能回傳 minimal status object，絕不可回傳 oracle answers。

## Join semantics

`join_sealed_oracle_with_candidate(oracle, seal, candidate_output)` 必須：

1. 用 seal 驗證 oracle；
2. 拒絕 `cutoff_contamination_count > 0`；
3. 驗證 candidate package 與 candidate SHA 格式；
4. 要求 oracle 與 candidate 的 `case_id` sets 完全相等；
5. 對每個 case，要求 oracle expectation 的 `claim_id` set 與 candidate C1 decision 的 `claim_id` set 完全相等；
6. canonical normalization 後，byte-semantically 保留 oracle expectations；
7. validation 後，byte-semantically 保留 candidate C1 bundle；
8. 為每個 joined case 計算全新的 Q1 `input_digest`；
9. 依 `case_id` 輸出 deterministic case ordering；
10. 對完整 joined payload 呼叫既有唯讀 `validate_claim_consumption_qualification_input()`；以及
11. join 階段絕不呼叫 `evaluate_claim_consumption_qualification()` 或任何 Q1 scoring function。

通過 validation 的 joined input 之後才另外交給 unchanged Q1 evaluator。這樣 O1 可以證明 schema compatibility，同時不改變、也不預先執行 qualification scoring。

## Rubric identity

O1 要求明確的 `rubric_digest`，但不負責建立 rubric 內容。

Rubric 必須在 private adjudication 前先 freeze，而且至少要定義：

- 三種 authorization labels；
- caveat-required semantics；
- specificity scale 與 minimum/maximum rules；
- claim-id matching rules；
- cutoff/contamination handling；
- adjudicator disagreement resolution process。

未來的 private oracle 若沒有在 seal 中引用 frozen rubric digest，就不視為有效 oracle。

O1 開發 tests 只使用 synthetic rubric digest，不建立 private adjudication rubric。

## General hard gates

O1 general/synthetic conformance 必須符合：

```text
所有 positive synthetic seal/verify/join fixtures PASS
所有 tamper fixtures fail closed
unknown/private fields 被拒絕
public receipt 不含 case/claim answers
case/expectation 順序變動不改變 digests
oracle/candidate case-set mismatch 被拒絕
oracle/candidate claim-set mismatch 被拒絕
contaminated oracle 不得 join
joined Q1 input 通過 unchanged Q1 validator
generated AI distribution parity PASS
full repository regression PASS
Python 3.9 compile PASS
clean tree PASS
Hosted same-SHA validation PASS
```

O1 要成為 general-qualified，不需要任何 private result。

## Private threshold 邊界

O1 不定義 Q1 private metrics 的 performance thresholds。

O1 在 private run 前只強制以下 structural/integrity safety preconditions：

```text
seal valid
rubric identity valid
case/claim set identity valid
cutoff contamination = 0
candidate 已 freeze，且依 Project governance 通過外部 qualification
```

若未來要加入 Q1 private performance thresholds，必須另開 prospective research decision，以 general rationale 為基礎，並且在看見任何 private result 前先 freeze。

## Failure 與 cycle semantics

- Seal verification failure：不得 join；不得執行 private evaluation。
- Candidate-output identity failure：不得 join；不得執行 private evaluation。
- Contaminated oracle：不得 join；不得執行 private evaluation。
- Joined-input validation failure：在執行任何 private evaluation 前，先停止並 debug infrastructure/contracts。
- 一旦 valid frozen candidate 對 valid sealed private oracle 執行 evaluation，該 candidate/oracle pair 的 private evaluation 只能執行一次。
- 若未來 cycle 存在 private performance gate 且結果 FAIL，不得在同一 cycle 依該結果修改 sealed oracle、C1 policy、Q1 scoring 或 thresholds。

## Implementation 預期檔案

建立：

```text
engine/distribution/claim_consumption_oracle_seal.py
tools/seal_v16_claim_consumption_oracle.py
tests/fixtures/v1.6-claim-consumption-oracle.synthetic.v1.json
tests/fixtures/v1.6-claim-consumption-candidate-output.synthetic.v1.json
tests/test_v16_claim_consumption_oracle_seal.py
docs/research/2026-09-01-v1.6-claim-consumption-oracle-seal-o1.md
```

僅在 formal builder 確實需要時修改：

```text
dist/ai/metaphysics_lab.py
```

Implementation 不得修改 C1 或 Q1 evaluator semantics。

## 成功標準

當 Project 可以只用 synthetic/general evidence 證明以下事項時，O1 即視為成功：

1. claim-level expectations 可以獨立於 candidate output 被 freeze；
2. 之後對 oracle 的修改可以被偵測；
3. 之後對 candidate-output 的修改可以被偵測；
4. candidate 無法 join 到不同的 sealed case/claim set；
5. public seal receipt 可以證明 seal identity，但不洩漏 answers；
6. joined private input 完全符合既有 Q1 contract；
7. Q1 scoring 保持不變；
8. local 與 Hosted hard gates 在同一 frozen candidate SHA 全部 PASS；以及
9. O1 開發期間沒有執行 private Q1 evaluation。
