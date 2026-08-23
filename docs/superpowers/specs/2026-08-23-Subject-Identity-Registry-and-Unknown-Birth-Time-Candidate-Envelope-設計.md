# Subject Identity Registry + Unknown Birth Time Candidate Envelope｜設計規格

日期：2026-08-23  
狀態：Design approved in chat; written spec pending user review  
適用分支：`feature/progressive-case-historical-calibration`

---

## 1. 目標

本規格新增兩個互相關聯的產品契約：

1. **Subject Identity / Registry**：同一個私人 Project 可安全管理多位命主，檔名與 Markdown 內容都能直接辨識命主，同時保留穩定、非個資化的機器主鍵。
2. **Unknown Birth Time Candidate Envelope**：出生時間未知或只知道範圍時，仍可建立部分 Case，保存已確定事實、候選依賴事實與被封鎖結論；不得自行補一個時辰。

核心原則：

> 人看名稱，機器看 `subject_id`；名字可以改，身份主鍵不改。

> Precision must be earned by input：缺時間不代表整個 Case 失效，但任何需要唯一時辰才能成立的盤面不得冒充已確定事實。

---

## 2. Scope

### 2.1 In scope

- Project-level `命主索引.md`
- AI 發起、runtime 建立 opaque `subject_id`
- `subject_display_name`
- filename-safe display label
- subject short id
- 多命主 Case 檔名契約
- Case Schema 1.1 在尚未 release 前收斂到新 filename contract
- Legacy Case Schema 1.0 相容讀取與 explicit migration
- 命主改名 / rename operation
- exact / bounded / unknown_time / external_only natal precision states
- Bazi candidate envelope
- Ziwei candidate envelope
- Base Case 00–04 在 partial natal 下的 materialization contract
- allowed / blocked analysis scopes
- candidate rectification 的資料邊界與 evidence label

### 2.2 Out of scope

- 自動宣稱唯一出生時辰
- 以命理結果覆寫原始出生時間
- 將候選排序結果標記為外部已驗證出生時間
- 在本規格中定義完整 candidate-rectification scoring profile
- 把關係角色（本人、配偶、合作夥伴）永久寫死成 subject identity
- 在缺出生地／時區 provenance 時假裝完成 Project candidate natal

---

## 3. Subject Identity 模型

每一位命主至少有：

```yaml
subject_id: subj_7f3a2c91d4e8
subject_display_name: Kai
subject_short_id: 7F3A2C
```

### 3.1 `subject_id`

- 由 runtime 建立；AI 負責在 workflow 中發起建立，不讓使用者手動編造。
- opaque；不得包含姓名、生日、性別、出生地或其他可直接識別資料。
- 一旦建立後永久不變。
- 格式：`subj_` + 至少 12 個十六進位字元。
- 產生方式使用 runtime 的安全隨機來源；不得由 PII hash 推導。
- 一次建立後必須持久化到 `命主索引.md`，避免同一命主反覆生成不同 ID。
- identity creation 是一次性持久化動作，不要求與命盤計算相同的 deterministic 重算語意。

### 3.2 `subject_display_name`

- 人類可讀名稱。
- 可用真名、英文名、暱稱或私人標籤，例如 `Kai`、`媽媽`、`客戶A`。
- 不是 identity authority。
- 可被 rename，但不改 `subject_id`。

### 3.3 `subject_short_id`

- 由完整 `subject_id` 的十六進位部分衍生，只供檔名辨識與同名防碰撞。
- 預設先使用 6 個大寫十六進位字元。
- 建立／migration 時必須檢查 `命主索引.md` 內是否碰撞。
- 若 6 碼碰撞，依 8、10、12... 碼延長直到 registry 內唯一。
- 不作為唯一 authority。

---

## 4. Project-level Subject Registry

新增私人 Project 層文件：

```text
命主索引.md
```

此文件不屬於任何單一 Case，不使用 00～08 slot。

最小資料：

```yaml
registry_schema_version: 1.0
subjects:
  - subject_id: subj_7f3a2c91d4e8
    subject_short_id: 7F3A2C
    subject_display_name: Kai
    filename_label: Kai
    status: active
  - subject_id: subj_91c40b221a9f
    subject_short_id: 91C40B
    subject_display_name: Amy
    filename_label: Amy
    status: active
```

Registry 只保存 identity / display / Case discovery metadata，不保存完整生日、時辰、醫療、財務或人生事件。

### 4.1 Registry authority

- 新命主建立前，AI 應先讀／搜尋 `命主索引.md` 是否已有合理候選。
- 同名不等於同一人；如果有多個同名 subject，必須以 short id / context 區分。
- 不得只憑姓名自動合併兩個 subject。
- 若 registry 不存在，第一位命主建立時 materialize。
- AI 不能只在聊天文字宣稱「已建立命主」；若要成為持久身份，必須把 runtime 產生的 ID 寫進 registry。

### 4.2 Rename

Rename 是顯示層變更：

```text
小明__7F3A2C__01_命盤核心摘要.md
→
Eric__7F3A2C__01_命盤核心摘要.md
```

`subject_id` 不變。

Rename 必須一次更新：

- `命主索引.md`
- 該 subject 的所有已 materialize Case filenames
- 所有 Case front matter 的 `subject_display_name` / `filename_label`
- `00` manifest 內的 filename references

不得只改其中一個檔案。

---

## 5. Filename contract

新 Case canonical filename：

```text
<filename_label>__<SUBJECT_SHORT_ID>__<slot>_<canonical_title>.md
```

例如：

```text
Kai__7F3A2C__00_專案索引.md
Kai__7F3A2C__01_命盤核心摘要.md
Kai__7F3A2C__02_命盤資料校驗紀錄.md
Kai__7F3A2C__03_八字結構化資料包.md
Kai__7F3A2C__04_紫微基礎資料包.md
Kai__7F3A2C__05_驗證事件紀錄.md
Kai__7F3A2C__06_流年追蹤紀錄.md
Kai__7F3A2C__07_問事追蹤紀錄.md
Kai__7F3A2C__08_重大決策紀錄.md
```

### 5.1 filename label normalization

保留 Unicode / 中文，不強迫 romanize。

至少處理：

- trim 前後空白
- 連續空白折疊為 `-`
- `/ \\ : * ? \" < > |` 改為 `-`
- 連續 `-` 折疊
- 最長 32 個 Unicode 字元
- 正規化後不得為空；若為空則使用 `Subject`

例如：

```text
Kai Chen        → Kai-Chen
王小明          → 王小明
Amy / Marketing → Amy-Marketing
```

### 5.2 filename validation

Runtime 不再用完整 filename 直接判定 record type，而是 parse：

```text
<label>__<short_id>__<slot>_<canonical_title>.md
```

並驗證：

- slot / canonical title 合法
- filename short id 與 front matter `subject_short_id` 一致
- `subject_short_id` 能由 front matter `subject_id` 合法衍生
- filename label 與 front matter `filename_label` 一致
- front matter `subject_display_name` 屬於同一 subject
- 同一 Case pack 所有 `subject_id` 一致

違反時 fail closed，例如：

```text
case_subject_filename_mismatch
case_filename_slot_mismatch
```

---

## 6. Front matter 新欄位

Case Schema 1.1 新增：

```yaml
subject_id: subj_7f3a2c91d4e8
subject_display_name: Kai
subject_short_id: 7F3A2C
filename_label: Kai
```

`subject_id` 仍為 authority。

Markdown title 同時可讀：

```markdown
# Kai｜命盤核心摘要
```

單一檔案脫離 Project 後仍能知道命主顯示名稱與穩定身份。

---

## 7. Participant role 不屬於永久 Identity

`本人 / 配偶 / 合作夥伴 / 父親 / 母親 / 對方` 是問事情境角色，不是 subject 永久屬性。

合盤／多人問事紀錄應使用：

```yaml
participants:
  - subject_id: subj_7f3a2c91d4e8
    role: 本人
  - subject_id: subj_91c40b221a9f
    role: 配偶
```

不得把 `role: spouse` 固定寫入 Subject Registry。

---

## 8. Case Schema / compatibility

### 8.1 新 Case

因 Case Schema 1.1 尚未正式 release，本規格直接將新 filename / identity contract 納入 1.1，不額外先發 1.2。

目前 feature branch 先前產生的開發中 1.1 Case fixture 必須一起升級到此 filename contract；它們不是已發布 public contract，因此不另外建立 1.1→1.2 migration。

### 8.2 Legacy 1.0

- 舊 `00_專案索引.md`～`08_重大決策紀錄.md` 九檔仍可讀。
- 不要求自動 rename。
- migration 必須 explicit；不得靠 filename 或內容猜姓名。
- migration 若沒有 `subject_display_name`，必須取得一個使用者可接受的顯示名稱或私人標籤後才能建立新 filename。

---

## 9. Natal Precision State

新增統一 precision state：

```text
exact
bounded
unknown_time
external_only
```

### 9.1 exact

有足夠日期、時間、地點與 timezone provenance，可唯一解析目前 supported natal pipeline。

### 9.2 bounded

知道時間範圍，但不是唯一分鐘。

規則：

- 不得取中點當答案。
- runtime 將時間範圍切成所有會造成 Project natal 結果不同的 material timing states。
- 若所有 qualified states 的命理時辰／後續盤面完全一致，可將對應欄位標為 invariant；exact minute 仍 unknown。
- 若跨時辰或其他 material boundary，保存多候選。

### 9.3 unknown_time

完全不知道時間。

- 不得自行補 12:00、00:00 或其他 default。
- 將該 civil birth date 的未知時間範圍切成所有 material timing states。
- 一般情況可對應約 12 個時辰候選；若 time profile、真太陽時、DST、日界或其他 boundary 產生更多 material states，必須完整保留，不強制壓成 12。

### 9.4 external_only

只有外部既有命盤資料、沒有足夠 raw birth input 建立 Project natal。

沿用 External / Project / Resolved 分層，不反推缺少的出生時間。

### 9.5 Location / timezone boundary

`bounded` / `unknown_time` 只放寬出生時間精度，**不放寬出生地與 timezone provenance**。

若要建立 Project candidate natal，仍需能重現：

- civil birth date
- resolved birthplace / coordinates or equivalent approved location basis
- IANA timezone or equivalent approved timezone provenance
- sex where downstream capability requires it

若缺少上述必要 basis：

- 可保留 external-only / known raw facts
- 不得自行猜地點或 timezone
- 不得宣稱已建立 Project candidate envelope
- runtime 應回 machine-readable blocked / missing basis

---

## 10. Candidate Envelope

新增 capability working name：

```text
natal.candidate_envelope
```

初期：`implemented / experimental / on_demand`。

輸出至少包含：

```yaml
subject_id: subj_...
natal_precision_state: unknown_time
candidate_count: 12
candidate_time_basis: material_timing_state
known_facts: {}
invariant_bazi_facts: {}
variant_bazi_facts: {}
invariant_ziwei_facts: {}
variant_ziwei_facts: {}
boundary_ambiguities: []
allowed_analysis: []
blocked_analysis: []
```

### 10.1 Material timing state

Candidate 不是「每個時辰任選一個代表分鐘」。

Runtime 必須從使用者提供的 civil-time uncertainty interval 建立**會造成計算結果不同的等價區段**，至少考慮現有 Project 支援的：

- timezone / DST ambiguity
- true-solar correction
- civil date rollover
- Bazi early-Zi / day boundary
- hour branch boundary
- Ziwei effective-time / late-Zi profile
- 其他已版本化、會改變 natal output 的 timing boundary

同一等價區段只需保留一個 canonical material state；不同輸出狀態不得因為「同屬一個時辰名稱」而被合併。

### 10.2 核心規則

對所有合法 candidates：

1. 用同一版本化 profile 建立每個 candidate 的 Project natal。
2. 欄位完全一致者進 `invariant_*`。
3. 欄位存在差異者進 `variant_*`，保留候選對應值。
4. 不得使用多數決把 variant 轉成 invariant。
5. 某 candidate 無法 qualified 時必須記錄，不能靜默丟棄以製造一致性。
6. 同一輸入、同一 location/timezone basis、同一 profile 應得到相同 candidate partition 與 invariant/variant classification。

---

## 11. Bazi partial natal

不知道出生時間時，八字可保留的資料由 candidate comparison 決定，不用理論預設硬寫死。

典型情況可能包含：

- 年柱 invariant
- 月柱 invariant
- 日柱 invariant
- 日主 invariant
- 年／月／日藏干與十神 invariant
- 時柱 candidate-dependent
- 起運時間形成 range

但若出生日期接近：

- 立春／節氣切換
- Project day-boundary / early-Zi profile
- timezone / true-solar material boundary

則年、月、日任一欄位都可能 candidate-dependent。

因此 runtime 必須由實際候選計算後再分類，不能假定「未知時間一定只有時柱不確定」。

---

## 12. Ziwei partial natal

紫微對時辰依賴較深，unknown time 不可直接建立一張唯一正式盤。

對所有 candidates 建立候選 natal，然後輸出：

- 共同 invariant facts
- candidate-specific 命宮 / 身宮 / 宮位 / 星曜 / 大限等差異
- unavailable / unqualified candidate metadata

不得：

- 把其中一張候選盤當正式盤
- 因某盤較符合既有事件就覆寫 birth input
- 把 rectification ranking 當作外部 verified birth time

---

## 13. Base Case 00–04 在 partial natal 的行為

Partial natal 仍可建立 Base Case；Case 不再因缺時辰而整體 fail closed。

### 13.1 00｜專案索引

顯示：

```text
Natal Status: partial
Birth Time Status: unknown / bounded
Candidate Count: N
```

並列出：

- allowed analysis
- blocked analysis

### 13.2 01｜命盤核心摘要

固定分區：

```text
【已確定盤面】
【候選依賴盤面】
【目前不可唯一判定】
```

不得把 candidate-dependent 欄位寫成唯一值。

### 13.3 02｜命盤資料校驗紀錄

至少保存：

```yaml
birth_time_source: unknown | approximate | external
birth_time_precision: unknown | bounded | exact
candidate_count: N
confirmed_by_external_record: false
candidate_rectification_used: false
```

未來找到出生證明時使用 append-first correction / reconciliation，不假裝過去從未不確定。

### 13.4 03｜八字結構化資料包

固定提供：

```text
Invariant Facts
Candidate-dependent Facts
Candidate Set
Blocked Conclusions
```

### 13.5 04｜紫微基礎資料包

固定提供：

```text
Invariant Across Candidates
Candidate Summaries
Blocked Conclusions
```

同一命主仍是一個 Case；不得為候選時辰建立多個假 subject。

---

## 14. Candidate Rectification boundary

後續可新增：

```text
natal.candidate_rectification
```

用途是依已驗證事件與固定 profile **排序候選**，不是驗證出生時間。

結果語意：

```yaml
birth_time_status: rectified_candidate
remaining_candidates:
  - 辰時
  - 巳時
```

即使只剩一個最高候選，也只能記：

```yaml
rectification_rank: highest
```

不得記：

```yaml
verified_birth_time: 辰時
```

除非之後取得出生證明、戶籍紀錄或同等外部證據。

原始輸入永久保留：

```yaml
reported_birth_time: unknown
```

---

## 15. Historical Calibration interaction

Candidate rectification 與 Historical Blind Calibration 必須分開：

- HBC 驗證的是年度 selector / interpretation 對人生事件的辨識力。
- Candidate rectification 用已驗證事件比較不同 birth-time candidates。
- 同一批已知事件不能被假裝成 clean blind evidence。
- 若事件已知，candidate ranking 的 evidence status 必須標 `contaminated / non_blind`。

不得為了讓某 candidate 勝出而改寫原始事件或 blind prediction。

---

## 16. Runtime actions

建議新增／調整：

```text
subject.create_identity
subject.registry_validate
subject.rename
natal.candidate_envelope
```

現有：

```text
export_case_markdown
validate_case
migrate_case
```

需升級為 subject-aware filename contract。

AI workflow：

```text
新命主請求
→ 讀 / 建立 命主索引.md
→ 搜尋既有 subject
→ 無合理既有 subject 才 create_identity
→ 建 natal / candidate envelope
→ export subject-prefixed Base Case
```

---

## 17. Error handling

至少包含：

```text
duplicate_subject_identity
ambiguous_subject_reference
invalid_subject_display_name
subject_short_id_collision
case_subject_filename_mismatch
case_filename_slot_mismatch
subject_registry_mismatch
candidate_envelope_empty
candidate_profile_mismatch
partial_natal_scope_blocked
missing_candidate_location_basis
```

所有錯誤 machine-readable、fail closed，不用模糊文字默默 fallback。

---

## 18. Tests / acceptance

### Subject Identity

- runtime 產生 subject_id 不含 PII
- 同一 persisted subject 不重建 ID
- 同名 subject 可共存且 short id 唯一
- short-id collision 會 deterministic 延長顯示長度，不覆蓋既有 subject
- display name rename 不改 subject_id
- filename normalization deterministic
- filename / front matter mismatch fail closed
- multi-subject files 不可混在同一 Case validation
- legacy 1.0 pack 可讀
- explicit migration 不猜 display name

### Candidate Envelope

- unknown time 不使用 default 時間
- bounded range 不取中點
- candidate enumeration 依 material timing states 分割，不以任意代表分鐘取代
- same input / basis / profile candidate partition deterministic
- invariant facts 必須在所有 qualified candidates 完全一致
- variant facts 保留 candidate mapping
- boundary candidate 不被靜默丟棄
- missing location/timezone 不建立假 Project candidate natal
- partial Case 00–04 可 export / validate
- unique-time-only analysis 在 partial state 會 blocked
- candidate rectification 不改 raw birth input

### Distribution

- modular / bundled parity
- Python 3.9 compatibility
- deterministic build no drift
- current documentation consistency tests同步更新
- full repo regression 全綠後才允許 merge

---

## 19. Private Project migration

Repo 文件更新不代表既有私人 Project 自動同步。

升級時必須處理：

1. 既有 `命理分析作業規範.md` / Project Instructions 的舊 7 層與過期能力敘述。
2. 既有 legacy filename Case。
3. 建立 `命主索引.md`。
4. 為每個既有 Case 指定 `subject_display_name` 並保留既有 subject lineage。
5. migration 完成前不得同時混用舊／新 filename contract 來判斷同一 Case。

---

## 20. 不變原則

- Python 算盤，AI 讀盤。
- AI 可發起 Subject 建立，但 opaque ID 由 runtime 產生。
- 名字是 display metadata，不是 identity authority。
- 不知道出生時間可以保留部分盤面，但不能取得不存在的精度。
- 缺出生地／timezone 仍不得猜測 Project natal basis。
- Candidate ranking 不是出生時間驗證。
- 原始輸入、Project 計算、已校驗資料、已驗證事件、命理推論永遠分層。
