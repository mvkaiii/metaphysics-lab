# Progressive Case + Historical Blind Calibration｜Selector v1 對齊修訂

- 日期：2026-08-23
- Branch：`design/progressive-case-historical-calibration`
- 狀態：Design amendment
- Applies to：`2026-08-23-Progressive-Case-Historical-Blind-Calibration-設計.md`
- Depends on：`2026-08-23-Historical-Activation-Selector-v1-設計.md`

本修訂處理 Selector v1 定稿後發現的 workflow 語意衝突。若原 Progressive Case spec 與本修訂／Selector v1 衝突，以本修訂與 Selector v1 為準。

---

## 1. 最近 10 年的時間單位

原文「最近 10 個完整年度」正式精確化為：

> **最近 10 個已完整結束的 Bazi flow-year periods，以立春為界。**

`label_year` 為該流年期起始立春所在 Gregorian year。

例如 `as_of_date = 2026-08-23`：

```text
eligible labels = 2016 ... 2025
```

使用者介面可顯示「2016 流年」，但 runtime 必須保存實際 `period_start` / `period_end`。

若使用者訂正事件為 2017 年 1 月，而日期仍落在 2016 流年 period，不得 mechanically 記為 `shifted +1`。

---

## 2. Canonical 4 High + 1 Control 不因 blind contamination 改選

刪除原規格「將 known years 傳入 selector `excluded_years`，再優先改選未知年份」的設計。

正式規則：

```text
canonical_selection
= Selector 對完整 10 年一視同仁計算後得到的真正 Top 4 + Bottom 1
```

canonical selection 不接受：

- known event years
- conversation history
- verified events
- user preferences
- manual excluded years

因此已知歷史事件不得讓 Selector 換掉真正的 Top 4 / Bottom 1。

若 canonical point 已在 conversation 中被使用者揭露：

```text
blindness_status = contaminated
```

該 point：

- 仍保留在 canonical selection。
- 不得冒充完整 blind evidence。
- 不計入 blind hit-rate / blind discrimination qualification。

若產品需要額外取得 5 個真正未知的回答，可從剩餘 ranking 產生：

```text
supplemental_blind_points[]
```

但 supplemental points 只能作補充測試，**不得取代或改寫 canonical 4+1**。

---

## 3. 不再為時間分散或跨運期人工改選

原規格「若跨大運／大限，盡量讓測試點涵蓋切換前後」與「連續年份去重／時間分散」不再作為 selection override。

正式規則：

> **Top 4 就是 rank vector 真正最高的 4 年。**

即使：

- 四年全部連續；
- 全部落在同一大運；
- 沒有跨到大運切換前後；

仍不得以 UX／樣本分散理由換掉較高年份。

`major_cycle_coverage` 只記 metadata：

```text
single_cycle
cross_cycle
boundary_in_window
```

不改 selection truth。

---

## 4. Control year 的用語依 control_quality 降級

原規格要求 control 年明確說「相對穩定」，改為依 Selector output：

```text
strong_control
acceptable_control
relative_low
```

AI 表達：

### strong_control

可以說：

> 這是近十年相對低活化、可作穩定控制的年份。

### acceptable_control

只能說：

> 這是近十年相對低活化年份，但仍有部分中度訊號。

### relative_low

必須說：

> 近十年沒有真正低訊號年；這只是相對最低的一年，不代表穩定。

不得把 `relative_low` 評為 `confirmed_stable / contradicted` 的二元穩定測試；應記：

```text
control_evaluation_scope = relative_low_only
```

---

## 5. Timing evaluation 改用 flow-year period 優先

原本：

```text
predicted_year: 2016
actual_year: 2017
=> shifted +1
```

不能只看 Gregorian year label。

新版流程：

1. 若使用者提供 actual date / month，可映射至實際 Bazi flow-year period。
2. 若 actual event 仍在 predicted flow-year period：

```text
timing_status = exact_flow_year
```

3. 若確實落在下一個／上一個 flow-year period：

```text
timing_status = shifted
offset_flow_years = +1 / -1 / ...
```

4. 若只知道粗略 Gregorian year，且涉及立春邊界：

```text
timing_status = unscorable_or_ambiguous
boundary_ambiguity = true
```

不得逼使用者猜月份來消除 ambiguity。

---

## 6. Blind Set 與 supplemental points

Historical Calibration lock payload 增加：

```text
canonical_selection_digest
canonical_test_points[]
  blindness_status = blind | contaminated

supplemental_blind_points[]  # optional
```

`canonical_selection_digest` 必須直接來自 Selector v1，不得由 AI 改動。

若 canonical 5 點中至少 3 點可 blind + scorable，仍可建立 `basic` calibration。

若不足 3 點：

- 可以使用 supplemental blind points 補足可評分證據。
- 但 Case 必須保留哪些是 canonical、哪些是 supplemental。
- 不得把 supplemental 偽裝成 Selector 原始 Top 4 / Bottom 1。

---

## 7. 測試修訂

Progressive Case / Historical Calibration tests 改為驗證：

- window = 最近 10 個已完成 Li-Chun flow-year periods。
- canonical selection 不因 contaminated years 改變。
- contaminated canonical points 仍保留但不算 blind evidence。
- supplemental points 不改 canonical digest。
- 連續 Top 4 必須保留。
- 大運切換 coverage 不得 override rank。
- `relative_low` 不得被 UI 稱為真正穩定年。
- Jan / early-Feb actual event 依 flow-year interval 評價，不 mechanically +1。

---

## 8. 修訂後核心原則

> **Selector 先給出命盤真正算出的 canonical 4 High + 1 Control。**
>
> **Blindness 是測試品質 metadata，不是改選年份的理由。**
>
> **已知事件可以讓某個 canonical point 失去盲測資格，但不能讓 Python 換掉盤面本來選出的年份。**
>
> **流年時間以立春 period 評價；Gregorian 年份只作使用者友善 label。**
