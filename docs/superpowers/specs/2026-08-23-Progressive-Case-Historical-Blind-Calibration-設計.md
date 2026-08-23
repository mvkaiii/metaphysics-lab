# Metaphysics Lab｜Progressive Case + Historical Blind Calibration 設計規格

- 日期：2026-08-23
- Branch：`design/progressive-case-historical-calibration`
- 狀態：Design spec，等待使用者 final review；尚未進入 implementation plan
- 分類：Architectural
- Base：`main` commit `f7e48ebea8c841194b71b8c0f2c2168550763322`（v1.3.0）
- 範圍：Progressive Case lifecycle、第一次未來問事校準門檻、Historical Blind Calibration protocol、盲測鎖定與使用者訂正、Case materialization / compatibility
- 不在本規格內：八字／紫微 historical activation selector 的最終命理訊號 profile 與權重；該部分須另開規格並通過 qualification 後才能進 production

---

## 一、問題與目的

v1.3.0 的 AI Distribution Pack 將私人 Case 定義為 9 份 Markdown，runtime 目前也會在第一次 `export_case_markdown` 時一次產生 00～08，並要求 validator 同時看到完整 9-file set。

這個做法在工程上簡單，但與真實使用生命週期不一致：

- 第一次建盤時，使用者尚未有 Metaphysics Lab 的「驗證事件紀錄」。
- 尚未問流年，就不應存在空的「流年追蹤紀錄」。
- 尚未問具體問題，就不應存在空的「問事追蹤紀錄」。
- 尚未做重大決策，就不應存在空的「重大決策紀錄」。

因此新版心智模型改為：

> **Case 是隨使用歷程長出來的，不是在安裝時假裝已經有完整人生紀錄。**

同時，未來趨勢與重大決策若完全沒有歷史事件校準，第二階段個人化判斷容易過度依賴一般命理解讀。因此新增 Historical Blind Calibration：

> **AI 先在不知道答案的情況下提出可被反駁的歷史年份／事件假說，再由使用者確認、訂正或否定。**

目標不是為了提高表面命中率，而是建立可追溯的個人化證據：

1. 年份有沒有抓對。
2. 事件領域有沒有抓對。
3. 事件形式有沒有抓對。
4. 是否存在固定時間偏移。
5. 模型在這位命主身上的落地形式如何。

---

## 二、核心設計原則

### 2.1 Progressive Case

正式 record type 仍維持 00～08 共 9 種，但**不是 9 份檔案一開始必須全部存在**。

Base Case：

```text
00_專案索引.md
01_命盤核心摘要.md
02_命盤資料校驗紀錄.md
03_八字結構化資料包.md
04_紫微基礎資料包.md
```

Progressive Records：

```text
05_驗證事件紀錄.md
06_流年追蹤紀錄.md
07_問事追蹤紀錄.md
08_重大決策紀錄.md
```

第一次建盤／校盤只建立 00～04。

05～08 只有在對應資料第一次真正產生時才 materialize。

### 2.2 本命可直接使用；第一次未來個人化分析前要完成校準

使用者建立 Base Case 後可以直接做：

- 本命結構分析
- 命盤資料核對
- 八字／紫微本命解讀
- 一般長期傾向分析

第一次進入下列任務時，Historical Blind Calibration 會被觸發：

- 流年／未來趨勢
- 近期工作、財務、感情、家庭等未來問事
- 重大行動決策

但 Calibration Gate **不得破壞原本「第一階段盲判 → 第二階段事件校準」的順序**。

### 2.3 Python 算盤，AI 讀盤

Historical Blind Calibration 分工固定為：

```text
Python
= deterministic candidate window / eligible-year selection contract
= activation evidence serialization
= lock digest / schema validation
= Case materialization

AI
= 根據被選中的年份與 deterministic evidence 做盲讀
= 將盤面訊號翻成可被使用者驗證的事件領域／事件家族
= 解讀使用者訂正
= 第二階段個人化策略

使用者
= 提供 ground truth
= matched / partial / not matched / cannot recall
= 必要時訂正實際年份與實際事件
```

Python 不直接宣稱「某年一定離職／結婚」。AI 不得自由改 selector 年份來迎合已知事件。

---

## 三、Progressive Case Lifecycle

### 3.1 第一次建盤

標準流程：

```text
安裝發行包
↓
提供出生資料／第三方命盤
↓
Python 建立 Project 原生盤面
↓
External / Project / Resolved reconciliation
↓
產生 Base Case 00～04
↓
可做本命分析
```

此時：

```text
05 = absent
06 = absent
07 = absent
08 = absent
historical_calibration_status = uncalibrated
```

不得建立四個內容為「目前沒有已記錄項目」的空 tracking files。

### 3.2 00_專案索引.md 成為 Case manifest

`00` 除了 subject metadata，還要明確列出目前 materialized files 與 calibration state。

例如第一次建盤：

```text
目前 Case Files
✓ 00 專案索引
✓ 01 命盤核心摘要
✓ 02 命盤資料校驗紀錄
✓ 03 八字結構化資料包
✓ 04 紫微基礎資料包
○ 05 驗證事件紀錄
○ 06 流年追蹤紀錄
○ 07 問事追蹤紀錄
○ 08 重大決策紀錄

Historical Calibration: uncalibrated
```

第一次 materialize 某個 progressive file 時，runtime 回傳該檔與新版 `00`。

例如第一次建立 05：

```text
changed_files:
- 00_專案索引.md
- 05_驗證事件紀錄.md
```

既有 05 後續只是 append 新事件時，不需每次更新 00。

### 3.3 06～08 觸發條件

`06_流年追蹤紀錄.md`

- 第一次有正式年度／半年／月份 forecast 需要永久追蹤時建立。
- 第一版盲判 immutable。

`07_問事追蹤紀錄.md`

- 第一次有一般具體問事值得永久追蹤時建立。
- 例如 offer、合作、短期工作問題。

`08_重大決策紀錄.md`

- 第一次有高影響決策時建立。
- 例如離職／創業、買房、大額投入、搬遷、長期合作。

同一件事若已屬重大決策，以 08 為主，不為了湊紀錄同時複製到 07。

---

## 四、Historical Blind Calibration 觸發與 anti-leak

### 4.1 關鍵問題：不能先看歷史答案，再做第一次未來 Stage 1

若第一次未來問事時先跑 Historical Calibration，使用者會在同一個對話中揭露過去事件。之後即使 AI「不讀 05」，語言模型仍已在 conversation context 看過答案，第一階段未來盲判會被污染。

因此第一次未來問事必須採以下順序：

```text
使用者提出第一次未來／流年／重大決策問題
↓
檢查 00：historical_calibration_status = uncalibrated
↓
只讀 00～04
↓
先完成該未來問題 Stage 1
↓
鎖定 first-version blind forecast
↓
啟動 Historical Blind Calibration
↓
使用者驗證／訂正歷史盲讀
↓
materialize 05 + 更新 00
↓
永久保存原本 Stage 1 到對應 06／07／08
↓
才讀 05 做 Stage 2
```

這裡的 Calibration Gate 定義為：

> **未完成校準時，可以產生並鎖定純盤面 Stage 1；但不得完成個人化 Stage 2，也不得把未校準判斷包裝成已校準高信心結論。**

### 4.2 第一次未來 Stage 1 的 temporary lock

若對應 06／07／08 尚未 materialize，Stage 1 可以先存在 temporary locked payload，而不是為了存盲判提前建立空 tracking file。

lock payload 最低包含：

```text
blind_forecast_id
subject_id
question_type
question_reference
locked_at
project_contract_version
runtime_version
source_files_used = [00,01,02,03,04]
forbidden_sources_read = [05,06,07,08]
blind_forecast_payload
payload_digest
```

Historical Calibration 完成後，runtime 才將同一份 payload 原樣 materialize 到 06／07／08。

不得重新生成或改寫 first-version blind forecast。

---

## 五、Recent 10-Year Calibration Window

### 5.1 標準視窗

第一次 Historical Blind Calibration 採：

> **最近 10 個完整年度。**

例如使用者 local date 為 2026-08-23：

```text
window_start_year = 2016
window_end_year   = 2025
```

當年度因尚未走完，不納入第一次標準盲測。

runtime 必須接受明確 `as_of_date` / timezone provenance，不依 host 隱含系統時間猜日期。

### 5.2 測試點數

標準測試固定為：

```text
4 個高 activation 年
1 個低 activation control 年
```

目的：

- 高訊號年測「能不能抓到變動期與事件領域」。
- 控制年測「模型是否把每一年都說成有大事」。

### 5.3 不要求跨整個人生

第一次校準不強迫跨不同人生階段。

理由：

- 太久以前的事件記憶品質下降。
- 年份與月份容易被回憶偏差污染。
- 近期十年對下一階段的流年／決策通常更有實務價值。

若最近 10 年全部落在同一八字大運或紫微大限，只能標示：

```text
calibration_scope = recent_10_years
major_cycle_coverage = single_cycle
```

不得宣稱已完成全生命跨運期驗證。

若視窗剛好跨大運／大限切換，selector 應在不犧牲主要 activation ranking 的前提下盡量讓測試點涵蓋切換前後；實際 selection policy 由後續 selector profile 規格定義。

### 5.4 可用年份不足

若因出生年齡、資料缺失、BLOCKING conflict 或 capability 不足，最後可可靠評估的完整年份少於 5 個：

- 不得硬湊 5 年。
- Historical Calibration 回報 `insufficient_history`。
- 未來分析仍可做純盤面 Stage 1，但 Stage 2 必須標示「無法完成標準歷史校準」並降信心。

---

## 六、Historical Activation Selector 的責任邊界

本規格只定義 selector contract，不定義最終八字／紫微訊號 profile。

### 6.1 不可接受的做法

不得：

- 由 AI 看完盤後憑感覺挑 5 年。
- 由使用者自己先挑 5 個「我記得有大事」的年份。
- 讀 05～08 後挑容易命中的年份。
- 看到 conversation 已知事件後再選那些年份。
- 用不可解釋的單一「92 分 activation score」而沒有證據明細。

### 6.2 selector 必須輸出透明 evidence

未來 selector profile 至少要輸出：

```text
reference_year
activation_tier
basis = bazi_only | ziwei_only | cross_system
evidence_items[]
major_cycle_context
capability_maturity_used
qualification_provenance
selection_reason
```

每一個 evidence item 要能追溯到 deterministic rule / capability，不接受自由命理文字。

Experimental capability 可作輔助 evidence，但不得單獨把年份推成高 activation。

### 6.3 known-history contamination

若使用者已在當前 conversation、上傳文件或其他明確來源透露某年份實際事件，該年份視為 contaminated。

AI 應將已知年份傳給 selector 的 `excluded_years`。

如果仍有足夠年份，優先改選未知年份。

若未知年份不足 5 個，必須標示 `reduced_blindness`，不得把結果描述成完整盲測。

---

## 七、AI 給使用者看的盲讀格式

### 7.1 一定要先押年份＋事件領域

不能只顯示：

```text
2016 = 高訊號年
```

必須顯示可被反駁的判斷，例如：

```text
2016年｜工作／職責有明顯重大變化
較可能涉及換工作、職務調整、責任明顯增加，或團隊／工作模式重組。
```

使用者若實際是 2017 才發生，應直接訂正為 2017；系統不得將 2016 事後改成 2016～2017。

### 7.2 預測寬度限制

高訊號年：

- 1 個 primary domain 為原則。
- 若盤面確有兩個同等主訊號，最多 2 個 primary domains。
- event family 最多列 3 種同類落地形式。
- 不得把工作／財務／感情／家庭／健康／搬遷全部列進去。

低訊號 control 年：

- 明確說「相對穩定」。
- 可指出 1～2 個不特別支持的重大領域。
- 不使用「可能只是你沒注意到」等不可反駁話術。

### 7.3 使用者指引

固定告知：

> 請直接回答「符合／部分符合／不符合／想不起來」。如果年份不對但附近年份確實發生同類事件，請直接告訴我真正年份與事情，不需要配合我的原始判斷。

月份可補充，但不是硬性必填。

不得逼使用者為了滿足格式而猜月份。

---

## 八、Blind Set Lock

### 8.1 歷史盲測必須先鎖，再讓使用者回答

AI 完成 5 個年份的盲讀後，先呼叫 lock action，產生 immutable fingerprint，再展示給使用者。

建議 structured payload：

```text
calibration_id
subject_id
window_start_year
window_end_year
test_points[5]
  reference_year
  role = high_activation | control
  primary_domains[]
  event_family[]
  confidence
  interpretation_text
locked_at
runtime_version
project_contract_version
selector_profile_id
payload_digest
```

`payload_digest` 由 deterministic runtime 對 canonical serialized payload 計算。

使用者回答後，finalization 必須提交同一份 locked payload 與 digest；若內容被修改，runtime 拒絕 finalize。

這個 lock 的目的不是防惡意 cryptographic attack，而是防止 AI 在知道答案後靜默改寫第一版盲測。

### 8.2 abandoned session

若使用者中途停止，不產生 05。

下次可重新發起新的 calibration session，使用新的 calibration_id。

未完成 session 不算 verified Case data。

---

## 九、使用者驗證與年份訂正

### 9.1 自然語言優先

使用者不需要填 JSON。

例如：

```text
2017：不符合，真正換工作是2018年3月。
2019：符合，那年確實沒有重大變化。
2020：部分符合，公司重整但我沒有離職。
2023：想不起來。
2025：符合，7月開始帶新人。
```

AI 將自然語言 normalization 成 structured verification。

### 9.2 verification state

每個測試點至少支援：

```text
matched
partial
not_matched
cannot_recall
```

`cannot_recall` 不可計成 missed。

### 9.3 timing evaluation

時間評價固定拆開：

```text
exact
shifted
missed
unscorable
```

若使用者訂正年份：

```text
predicted_year: 2016
actual_year: 2017
timing_status: shifted
offset_years: +1
```

不得因 domain / event form 猜對就把 timing 改成 exact。

### 9.4 domain / event-form evaluation

分開保存：

```text
domain_status = matched | partial | missed | unscorable
event_form_status = matched | partial | missed | unscorable
```

例如：

```text
預測：2020工作／組織結構變化，較像換工作或責任增加
實際：公司重整，本人留下但接更多責任

timing_status: exact
domain_status: matched
event_form_status: matched
```

若實際是結婚：

```text
timing_status: exact
domain_status: missed
event_form_status: missed
```

v1 不產生一個容易被誤解的「總準確率 82%」。先保存可審查的 counts / dimensions。

### 9.5 control year

若 control 年被使用者確認真的相對平穩：

```text
control_status: confirmed_stable
```

若使用者確認該年有結婚、買房、離職等重大轉折：

```text
control_status: contradicted
```

不得用鄰年訊號替 control year 解套。

---

## 十、05_驗證事件紀錄.md 首次 materialization

### 10.1 何時建立

Historical Blind Calibration 在使用者完成驗證／訂正後，才首次建立 05。

不能在 lock blind set 時建立空 05。

### 10.2 05 的內容責任

05 不再只是「一串事件」，而是 **事件驗證 ledger**。

Historical Calibration record 要同時保存三種證據層：

```text
blind_prediction
  classification: 命理推論

user_confirmed_actual
  classification: 已驗證事件

calibration_evaluation
  classification: 已校驗資料
```

三者不得混寫成同一種事實。

對 `cannot_recall` 的項目可保存 calibration audit，但不得創造 actual_event。

### 10.3 例子

```text
record_id: HC-2026-001-01
calibration_id: HC-2026-001

blind_prediction:
  classification: 命理推論
  predicted_year: 2016
  domain: 工作／職責
  hypothesis: 明顯工作結構變化

user_confirmed_actual:
  classification: 已驗證事件
  actual_year: 2017
  actual_month: 9
  actual_event: 換工作並升任主管

evaluation:
  classification: 已校驗資料
  timing_status: shifted
  offset_years: +1
  domain_status: matched
  event_form_status: matched
```

### 10.4 後續新增事件

Historical Calibration 完成後，後續真正已發生的重要事件仍可 append 到 05。

不得因後續事件修改原 Historical Blind Set。

需要更正使用者原本提供的事件時，採 correction record，保留歷史。

---

## 十一、Calibration Status

### 11.1 初始狀態

Base Case：

```text
historical_calibration_status = uncalibrated
```

### 11.2 Basic

第一次 Recent 10-Year Historical Blind Calibration 完成後，只要取得至少 3 個 scorable points，即可：

```text
historical_calibration_status = basic
```

scorable = 非 `cannot_recall`。

`basic` 代表「已有足夠個人化歷史證據可進 Stage 2」，不代表模型表現良好。

即使 3 個以上都 missed，仍然是完成校準；但 Stage 2 必須依實際結果降低信心。

若 5 題中可評分少於 3 題：

- 狀態維持 `uncalibrated`。
- 可從剩餘未使用、未 contaminated 的候選年補測。
- 若候選池不足，回報 `insufficient_scorable_history`。

### 11.3 Calibrated

`calibrated` 保留給後續多輪 evidence promotion，不由第一次 5 題自動授予。

本規格不建立自動 promotion 規則，避免第一次盲測就過度宣稱「已完整校準」。

---

## 十二、第二階段未來分析

Historical Calibration 完成後，回到原本第一次未來問題。

流程：

```text
Stage 1 已事先鎖定
↓
05 已建立
↓
現在才可讀 05
↓
比較同類年份／同類 domain 的實際落地
↓
提高或降低事件形式權重
↓
產生 Stage 2
```

Stage 2 可以說：

> 過去同類盤面訊號兩次主要落在工作責任增加，而不是直接離職，因此本次將「直接換工作」權重下調，將「職責／團隊結構重組」權重提高。

但不得改寫 Stage 1 原文。

若 Historical Calibration 表現很差，也要如實使用：

> 目前近十年盲測在年份或事件領域命中有限，因此本次第二階段不提高個人化信心，仍以純盤面方向為主。

---

## 十三、Case Schema / Project Contract 版本影響

### 13.1 這不是 runtime-only change

本設計改變：

- 第一次 Case materialization contract。
- validator 對檔案集合的定義。
- 第一次未來問事流程。
- Stage 1 / Historical Calibration / Stage 2 的順序。
- 05 的責任與資料分層。

因此未來正式發版時屬於 Project Contract update，不應只叫使用者替換 `metaphysics_lab.py`。

需要同步更新：

```text
METAPHYSICS_CORE.md
PROJECT_INSTRUCTIONS.md
metaphysics_lab.py
```

### 13.2 Case Schema

建議新 Case 使用 `case_schema_version = 1.1`。

理由：

- v1.0 定義完整 9-file set。
- v1.1 定義 Base 5 + Progressive 4。
- 新 runtime 可向後接受既有 v1.0 9-file Case。
- 舊 runtime 不會誤把 v1.1 Progressive Case 當成同 schema。

### 13.3 legacy v1.0 Case

既有 v1.3.0 使用者若已經有 9 份 Case，其中 05～08 只是空檔：

- 不強迫刪除。
- 不重建私人 Case。
- 新 runtime 應接受 legacy 9-file Case。
- 空的 05～08 可繼續存在，不影響使用。
- 若進行 explicit 1.0 → 1.1 migration，只更新必要 metadata / manifest，不刪除使用者檔案。

新建立的 Case 才採 Progressive 00～04 起步。

---

## 十四、Runtime Action Contract（架構層）

未來實作可新增或擴充以下 action；具體命名在 implementation plan 前固定：

```text
export_case_markdown
  -> 新 Case 只輸出 00～04

validate_case
  -> 接受 v1.1 Base + optional progressive files
  -> 仍接受 legacy v1.0 9-file Case

prepare_historical_calibration
  -> 建立最近十年候選 window
  -> 呼叫 selector profile
  -> 輸出 4 high + 1 control candidate evidence

lock_historical_calibration
  -> 對 AI 完成的五題 blind interpretation 做 canonical digest

finalize_historical_calibration
  -> 驗證 locked digest
  -> normalization user answers
  -> 首次 materialize 05
  -> 更新 00 calibration state / manifest

lock_blind_forecast
  -> 第一次未來問事在 Historical Calibration 前鎖 Stage 1

materialize_tracking_record
  -> 在適當時間首次建立 06／07／08
```

不得讓 AI 直接繞過 runtime 修改 immutable blind payload。

---

## 十五、錯誤與降級

### 15.1 沒有 runtime execution

若 AI host 不能執行 Python：

- 不得假裝已 deterministic selection / lock。
- 可使用同一 single-file CLI fallback。
- 若連 fallback structured output 都沒有，不能宣稱完成正式 Historical Blind Calibration。

### 15.2 Base Case conflict

若 02 顯示會影響年運基礎的 BLOCKING natal conflict：

- 不進 Historical Blind Calibration。
- 先解決命盤 basis。

### 15.3 selector capability 不足

若 deterministic selector profile 尚未正式可用：

- 不允許 AI 自己替代 selector 憑感覺挑年份。
- Historical Calibration 標示 unavailable。
- 可繼續本命與純盤面未來分析，但不得宣稱完成正式個人化校準。

### 15.4 使用者記不得

`cannot_recall` = unscorable。

不得當成模型 miss，也不得逼使用者猜年月。

---

## 十六、測試與驗收方向

### 16.1 Progressive Case

必須驗證：

- 新 Case export 只有 00～04。
- 05～08 不存在時 validator 仍 PASS。
- 任意已 materialize progressive file 與 00 manifest 一致。
- 第一次新增 05 回傳 00 + 05。
- 後續 append 05 只回傳 05。
- legacy v1.0 9-file Case 仍可讀。

### 16.2 anti-leak

必須驗證：

- uncalibrated first future question 的 Stage 1 source allowlist 只有 00～04。
- Stage 1 payload 在 Historical Calibration 後 byte / digest 不變。
- finalize 後才可進 Stage 2 read 05。
- 嘗試替換 locked Stage 1 / historical blind set 被拒絕。

### 16.3 Historical Calibration

必須驗證：

- window 使用最近 10 個完整年度。
- current incomplete year 不入選。
- 4 high + 1 control schema 正確。
- contaminated year exclusion 正常。
- cannot_recall 不計 miss。
- user correction year 可產生 shifted + offset_years。
- control year 可記 confirmed_stable / contradicted。
- 少於 3 scorable points 不升 basic。

### 16.4 Evidence governance

必須驗證：

- blind_prediction = 命理推論。
- user_confirmed_actual = 已驗證事件。
- calibration_evaluation = 已校驗資料。
- 不因使用者事件修改 natal facts。
- 不因 missed result 重寫 blind prediction。

---

## 十七、明確非目標

本設計不做：

- 為了提高命中率自動放寬成 ±1 年區間。
- 用事件反推修改四柱／宮位／星曜。
- 第一次 5 題就宣稱全生命已校準。
- 產生單一神祕 accuracy score。
- 強迫使用者記住月份。
- 把過去所有人生事件一次收集完。
- 新增第 10 份 Case Markdown。
- 在 selector profile 尚未設計／驗證前由 AI 自由選年份。

---

## 十八、需要下一份規格解決的子系統

Historical Calibration 要正式進 production 前，必須另外完成：

**Historical Activation Selector v1**

該規格只處理命理演算法層，至少要固定：

- 八字年度 activation evidence 定義。
- 紫微年度 activation evidence 定義。
- Stable / Experimental evidence 權重與排除規則。
- cross-system 合併方式。
- 4 high + 1 control 的 deterministic selection policy。
- 連續年份去重／時間分散規則。
- 大運／大限切換 coverage 規則。
- qualification fixtures 與 failure cases。

在該 selector profile 尚未通過設計與 qualification 前，本規格只完成 workflow / data contract，不允許進 production 自動選年。

---

## 十九、最終產品心智模型

新版 Metaphysics Lab Case 應呈現：

```text
第一次建盤
00～04 Base Case
↓
本命分析可直接使用
↓
第一次未來問事
先鎖該題 Stage 1
↓
Recent 10-Year Historical Blind Calibration
4 high + 1 control
↓
使用者直接驗證／訂正年份與事件
↓
首次建立 05
↓
永久保存原盲讀 + ground truth + evaluation
↓
首次建立該題對應 06／07／08
↓
讀 05 做 Stage 2
↓
後續 Case 依使用生命週期持續長出來
```

核心原則：

> **Case 不預先製造空紀錄。**
>
> **盲讀先鎖，答案後看。**
>
> **年份錯了就留下年份錯，不用區間救答案。**
>
> **命盤提供模型，事件提供證據，校準結果不能反過來竄改原始盤面。**
