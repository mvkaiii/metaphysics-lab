# Metaphysics Lab｜Historical Activation Selector v1 設計規格

- 日期：2026-08-23
- Branch：`design/progressive-case-historical-calibration`
- 狀態：Design spec，等待使用者 final review；尚未進入 implementation plan
- 分類：Architectural / Algorithm sub-spec
- Base：`main` commit `f7e48ebea8c841194b71b8c0f2c2168550763322`（v1.3.0）
- 前置規格：`2026-08-23-Progressive-Case-Historical-Blind-Calibration-設計.md`
- 目標：由 Python 對最近 10 個已完成的年度運期逐年做 deterministic structural activation 計算，固定選出 4 個最高活化年 + 1 個最低活化控制年，供 AI 做 Historical Blind Calibration。

---

## 一、核心問題

Historical Blind Calibration 若讓 AI 自己「看盤後挑 5 年」，即使 AI 沒有刻意作弊，也會出現：

- ChatGPT 與 Claude 選到不同年份。
- 同一模型不同對話選到不同年份。
- AI 可能被已知人生事件污染後改挑容易中的年份。
- 無法知道某一年為什麼被判定為高訊號／低訊號。
- 無法做 regression test 或 qualification。

因此本能力的硬性原則是：

> **年份必須由 Python 算出來。**
>
> **AI 只能解讀已選年份，不能選年、換年、重排年份。**
>
> **同一命盤、同一 as_of_date、同一 rule profile，輸出必須完全一致。**

本 Selector 不直接預測「某年一定離職／結婚」。它只回答：

> 在固定規則下，最近 10 個已完成年度中，哪些年度的盤面結構互動相對最密集，哪些相對最低。

---

## 二、Capability 定位

正式 capability id 建議：

```text
historical.activation_selector
```

初始狀態：

```text
implementation = planned
maturity       = experimental
routing        = on_demand
rule_version   = 1.0-exp
profile_id     = historical-activation-bazi-v1
```

正式實作前不得在 runtime manifest 宣稱 `implemented`。

即使第一版通過 deterministic qualification，也不得因單一命主事件吻合自動升 Stable。

輸出分類：

```text
Project 推導盤面 / deterministic selector evidence
```

它不是 Astralium、lunar-python 或其他第三方直接輸出的「重大事件年份」。

---

## 三、責任邊界

### 3.1 Python 負責

- 建立最近 10 個 eligible annual periods。
- 找出每個 annual period 對應的八字大運。
- 計算流年干支。
- 依 versioned relation tables 建立 Tier 1 / Tier 2 / Tier 3 evidence。
- evidence 去重與 suppression。
- deterministic ranking。
- 直接選出 Top 4 high + Bottom 1 control。
- 產生 provenance、rank vector、selection digest。

### 3.2 AI 負責

- 讀取 Python 已選出的 5 年。
- 根據 deterministic evidence 解讀最可能活躍的事件領域／事件家族。
- 將盲讀鎖定後交給使用者驗證。
- 不得改 selector selection。

### 3.3 使用者負責

- 驗證／訂正實際事件。
- 若年份不對，直接提供正確年份／月份（若記得）。

Historical event ground truth **不得回流改寫當次 Selector output**。

---

## 四、資料隔離與 anti-contamination

Selector 正式執行前允許讀取：

```text
00_專案索引.md
01_命盤核心摘要.md
02_命盤資料校驗紀錄.md
03_八字結構化資料包.md
04_紫微基礎資料包.md
```

實際 ranking v1 只依 deterministic Bazi basis；Ziwei 見第十二節。

禁止讀取／使用：

```text
05_驗證事件紀錄.md
06_流年追蹤紀錄.md
07_問事追蹤紀錄.md
08_重大決策紀錄.md
conversation 中已揭露的歷史事件答案
```

runtime action 必須接受 canonical structured natal input，而不是由 AI 傳入「我覺得這年有事」等自由文字 ranking hints。

Selector payload 不接受：

```text
preferred_years
known_event_years
event_keywords
manual_rank_override
```

---

## 五、最近 10 年的正式時間單位

### 5.1 使用 Bazi Flow-Year Period，而不是模糊的 Jan–Dec

Historical Activation Selector v1 的 ranking unit 固定為：

> **八字流年期，以立春為年度切換。**

annual period identity：

```text
label_year = 該流年期起始立春所在 Gregorian year
period_start = 該年立春交接時刻
period_end   = 下一年立春交接時刻
```

例如：

```text
label_year: 2016
period: 2016 立春 → 2017 立春前
```

使用者介面可顯示「2016 流年」，但必須保留實際 period start/end。

### 5.2 只選已完整走完的流年期

以 `as_of_date` 為準，取最近 10 個**已完整結束**的 Bazi flow-year periods。

例如 `as_of_date = 2026-08-23`：

```text
current incomplete flow year = 2026
eligible completed labels     = 2016 ... 2025
```

因此標準 window：

```text
2016-2025
```

若 `as_of_date = 2026-01-15`，2025 流年尚未走完，最近完整 10 期應往前推，不得把未完成流年放入 calibration。

### 5.3 使用者回憶年份與流年邊界

若 AI 盲讀的是：

```text
2016 流年
= 約 2016 立春至 2017 立春前
```

使用者回答「2017 年 1 月換工作」，runtime 評價時應映射到實際日期；若該日期仍落在 2016 流年 period，不能錯算成 `shifted +1`。

若使用者只記得「2017 年」但不記得月份，且可能涉及立春邊界，標示：

```text
timing_resolution = coarse_calendar_year
boundary_ambiguity = true
```

不得逼使用者亂填月份。

---

## 六、Evidence Tier 定義

Tier 命名固定：

```text
Tier 1 = 核心強訊號
Tier 2 = 中度支持訊號
Tier 3 = 輔助訊號
```

方向永遠固定：

> **Tier 1 最強 → Tier 2 次之 → Tier 3 輔助。**

不使用 Tier 0。

Tier 不是吉凶：

- 高 activation 不等於一定是壞事。
- 低 activation 不等於一定平安無事。
- Selector 只衡量結構互動密度／強度，不判定事件好壞。

---

## 七、Versioned Bazi Relation Tables v1

Selector 不可由 AI 臨場決定「哪些支互沖／相合」。正式表格必須 hard-code / version-control / test。

### 7.1 六沖

```text
子-午
丑-未
寅-申
卯-酉
辰-戌
巳-亥
```

### 7.2 六合

```text
子-丑
寅-亥
卯-戌
辰-酉
巳-申
午-未
```

### 7.3 三合

```text
申-子-辰
亥-卯-未
寅-午-戌
巳-酉-丑
```

### 7.4 三會

```text
亥-子-丑
寅-卯-辰
巳-午-未
申-酉-戌
```

### 7.5 刑

v1 固定 structural sets：

```text
寅-巳-申
丑-戌-未
子-卯
辰-辰
午-午
酉-酉
亥-亥
```

三支組在年度加入後完整形成時，可視為 full punishment completion；只有其中兩支時只記 pairwise punishment support。

### 7.6 害

```text
子-未
丑-午
寅-巳
卯-辰
申-亥
酉-戌
```

### 7.7 破

```text
子-酉
丑-辰
寅-亥
卯-午
巳-申
未-戌
```

### 7.8 天干五合

```text
甲-己
乙-庚
丙-辛
丁-壬
戊-癸
```

### 7.9 v1 明確不納入

以下不進 ranking v1：

- 天干沖（不同流派定義／權重差異較大，留待 qualification 後再考慮）。
- 一般五行生剋（過於普遍，辨識力低）。
- 單純十神名稱，例如「七殺年」本身不得自動加 activation。
- 喜用神／忌神判斷。
- 格局強弱分數。
- 神煞。
- AI 主觀判定的「這個十神很重要」。

十神仍可供 AI 後續做事件領域解讀，但不是 Selector 強弱證據。

---

## 八、Tier 1｜核心強訊號

Tier 1 v1 只接受以下 deterministic evidence family。

### T1-01｜大運交界落在該流年期

若該 Bazi flow-year period 內包含正式 `BaziDecadalPeriod` start/end transition timestamp：

```text
relation_family = decadal_boundary
```

這是運期結構本身的變更，不判吉凶。

### T1-02｜歲運並臨

若流年完整干支與當時大運干支完全相同：

```text
flow_year_pillar == decadal_pillar
```

記：

```text
relation_family = sui_yun_bing_lin
```

同一對象不得再重複記較低層的 stem_repeat / branch_repeat。

### T1-03｜流年完整干支伏吟本命柱

若流年完整干支與本命年／月／日／時任一柱完全相同：

```text
relation_family = natal_pillar_repeat
```

每個實際命中的 natal component 可留 target metadata，但同一 target 不再另外記 stem_repeat / branch_repeat。

### T1-04｜流年支六沖本命支

若流年支與本命任一柱地支形成六沖：

```text
relation_family = branch_clash_natal
```

v1 不因年柱／月柱／日柱／時柱位置不同另給不同權重；target component 只供後續 AI 解讀。

### T1-05｜流年支六沖大運支

若流年支與當時大運地支形成六沖：

```text
relation_family = branch_clash_decadal
```

### T1-06｜流年支補成完整三合

若流年支加入後，與本命 + 當時大運可用支集合補成一組完整三合：

```text
relation_family = completes_three_harmony
```

同一 canonical 三合組只記一次 pattern evidence，參與位置另列 participants；不得因本命有重複支把同一組重複計數。

### T1-07｜流年支補成完整三會

規則同上：

```text
relation_family = completes_three_meeting
```

### T1-08｜流年支補成完整三刑

僅指：

```text
寅-巳-申
丑-戌-未
```

流年支加入後完整形成三支組：

```text
relation_family = completes_three_punishment
```

`子-卯` 與自刑在 v1 歸 Tier 2，不放 Tier 1。

### Tier 1 cross-layer flag

若同一流年同時具有：

- 至少一個針對 natal 的 Tier 1 evidence；且
- 至少一個針對 decadal 的 Tier 1 evidence，

則額外標：

```text
cross_layer_tier1 = true
```

這是 ranking tie-break metadata，**不是額外新增一條 Tier 1 evidence**，避免 double counting。

---

## 九、Tier 2｜中度支持訊號

### T2-01｜六合

流年支與本命任一支或大運支六合：

```text
relation_family = branch_six_harmony
```

### T2-02｜三合半組／待補完整

流年支與現有支形成三合組中的兩支，但未湊成完整三支：

```text
relation_family = partial_three_harmony
```

同一 canonical pattern 只記一次。

### T2-03｜三會半組／待補完整

```text
relation_family = partial_three_meeting
```

同一 canonical pattern 只記一次。

### T2-04｜刑的 pairwise / self-punishment

包含：

- `子-卯`
- `寅-巳-申` 中未完整成三支時的 pairwise structural relation
- `丑-戌-未` 中未完整成三支時的 pairwise structural relation
- `辰-辰`、`午-午`、`酉-酉`、`亥-亥`

```text
relation_family = branch_punishment_support
```

若該年已形成 Tier 1 full punishment completion，相關 partial evidence 必須 suppression。

### T2-05｜單支伏吟

流年支與本命任一支或大運支相同，但完整干支不相同：

```text
relation_family = branch_repeat
```

若已被 `sui_yun_bing_lin` 或 `natal_pillar_repeat` 吸收，不重複記。

### T2-06｜天干五合

流年干與本命任一干或大運干構成固定五合：

```text
relation_family = stem_combination
```

v1 只記「合關係存在」，不自行判定是否化、化成何五行。

---

## 十、Tier 3｜輔助訊號

### T3-01｜六害

流年支與本命任一支或大運支形成六害：

```text
relation_family = branch_harm
```

### T3-02｜六破

```text
relation_family = branch_break
```

### T3-03｜天干同干

流年干與本命任一干或大運干相同，但未構成完整柱伏吟：

```text
relation_family = stem_repeat
```

Tier 3 不得單獨把某年描述成「高活化」。

---

## 十一、Evidence 去重與 suppression

### 11.1 Pair evidence

pair relation 一律用 canonical key：

```text
(flow_year_label, tier, relation_family, target_layer, target_component)
```

相同 key 不得重複。

### 11.2 Pattern evidence

三合／三會／三刑使用 canonical pattern id，例如：

```text
three_harmony:申子辰
```

同一年度同一 pattern 只記一次，participants 可以列多個來源位置。

### 11.3 強訊號吸收弱訊號

固定 suppression：

- `sui_yun_bing_lin` 吸收同一 annual↔decadal 的 stem_repeat + branch_repeat。
- `natal_pillar_repeat` 吸收同一 annual↔natal target 的 stem_repeat + branch_repeat。
- `completes_three_harmony` 吸收同一 canonical pattern 的 partial_three_harmony。
- `completes_three_meeting` 吸收同一 canonical pattern 的 partial_three_meeting。
- `completes_three_punishment` 吸收同一 canonical pattern 的 pairwise punishment support。

不得為了提高 activation 數字，把同一件結構拆成多個同義 evidence 重複加分。

---

## 十二、Ziwei 在 v1 的角色

### 12.1 不進主 ranking

v1 **不讓 Ziwei 改變 4 high + 1 control 的選年結果**。

原因不是紫微不重要，而是目前 repo 雖已有：

- Ziwei natal / decadal facts
- stable transformations / flying core
- experimental yearly flowing stars

但尚未有一套已 version / qualification 的「Ziwei annual activation strength」規則。

若直接拿流曜數量、四化數量或某顆星落宮做加權，會再次變成任意規則。

因此 v1：

```text
selector_basis = bazi_structural_v1
ziwei_role     = interpretation_context_only
```

Python 可以在 5 個年份選定後，另產生該年的 Ziwei deterministic context 給 AI 做盲讀，但不得回頭改排名。

### 12.2 未來 cross-system selector

若後續完成獨立：

```text
historical-activation-ziwei-v1
```

並通過 qualification，才可設計：

```text
historical-activation-cross-system-v2
```

那時再討論 Ziwei 是 tie-break 或共同 ranking，不在 v1 偷渡。

---

## 十三、Ranking：不用黑箱分數

### 13.1 每年輸出 rank vector

每個年度先計算：

```text
tier1_family_count
tier1_evidence_count
cross_layer_tier1
tier2_family_count
tier2_evidence_count
tier3_family_count
tier3_evidence_count
```

### 13.2 lexicographic ranking

v1 不建立 100 分制或任意權重。

高活化排序 key 固定：

```text
(
  tier1_family_count,
  tier1_evidence_count,
  cross_layer_tier1,
  tier2_family_count,
  tier2_evidence_count,
  tier3_family_count,
  tier3_evidence_count,
  label_year
)
```

由大到小排序。

最後 `label_year` 只作完全同分時的 deterministic tie-break；較近年度優先，理由是使用者記憶通常較可靠，但不得凌駕盤面 evidence。

### 13.3 為什麼 family_count 在 evidence_count 前

目的：避免某個命盤因重複支，使同一種 relation 對多個 target 重複出現，就壓過另一年「多種不同強結構同時成立」。

v1 優先：

> evidence family 多樣性 → 同 tier evidence 數量。

此規則必須進 qualification；若未來證據顯示不合理，只能升 profile version，不能偷偷改 v1。

---

## 十四、4 High + 1 Control Selection Policy

### 14.1 High 年

完整 10 年 ranking 後：

```text
high = ranking[0:4]
```

**不得再做人為時間分散。**

因此：

- 若 Top 4 剛好連續四年，就選連續四年。
- 不因「看起來太集中」替換成較低年份。
- 不為了跨大運而換掉真正排名更高的年份。

大運／大限切換 coverage 只作 metadata，不改 selection truth。

### 14.2 Control 年

從剩餘年份中取 rank vector 最低者：

```text
control = min(remaining_years)
```

control quality：

```text
strong_control:
  tier1_family_count == 0
  tier2_family_count == 0

acceptable_control:
  tier1_family_count == 0
  tier2_family_count > 0

relative_low:
  tier1_family_count > 0
```

若 10 年每一年都有 Tier 1，仍可選相對最低年，但 AI 必須說：

> 這是「相對低訊號控制年」，不是盤面真正低活化年。

不得硬稱穩定年。

### 14.3 高低不是事件結果

Selector output：

```text
HIGH / CONTROL
```

代表 profile-relative structural rank。

不得在 Python output 寫：

```text
major_event = true
stable_year = true
```

事件假說只能由 AI 後續產生並接受使用者反駁。

---

## 十五、輸出資料結構

示意：

```json
{
  "capability": "historical.activation_selector",
  "profile_id": "historical-activation-bazi-v1",
  "rule_version": "1.0-exp",
  "as_of_date": "2026-08-23",
  "window": {
    "period_type": "bazi_flow_year_li_chun",
    "labels": [2016,2017,2018,2019,2020,2021,2022,2023,2024,2025]
  },
  "years": [
    {
      "label_year": 2020,
      "period_start": "...",
      "period_end": "...",
      "flow_year_pillar": "庚子",
      "decadal_pillar": "...",
      "rank_vector": {
        "tier1_family_count": 2,
        "tier1_evidence_count": 3,
        "cross_layer_tier1": true,
        "tier2_family_count": 1,
        "tier2_evidence_count": 1,
        "tier3_family_count": 0,
        "tier3_evidence_count": 0
      },
      "evidence": [
        {
          "tier": 1,
          "relation_family": "branch_clash_natal",
          "target_layer": "natal",
          "target_component": "month"
        }
      ]
    }
  ],
  "selection": {
    "high": [2017,2020,2023,2025],
    "control": 2019,
    "control_quality": "strong_control"
  },
  "selector_basis": "bazi_structural_v1",
  "ziwei_role": "interpretation_context_only",
  "basis_digest": "...",
  "selection_digest": "..."
}
```

實際 JSON schema 在 implementation plan 固定；欄位語意不得低於本設計。

---

## 十六、AI 取得 Selector 後的限制

AI 可以：

- 將 Tier evidence 翻成事件領域假說。
- 參考本命十神、宮位、當時大運／大限作 interpretation。
- 對 4 high 年提出具體但可被否定的盲讀。
- 對 control 年提出「相對低活化」假說，前提是 control quality 支持。

AI 不可以：

- 把 2020 換成「我覺得更準的 2021」。
- 因聊天裡知道 2018 有大事，就要求 runtime 改選 2018。
- 將 `relative_low` 說成「2019 一定沒事」。
- 把 Tier 1 解釋成凶年。
- 將十神本身新增成未經 profile 定義的 activation evidence。

---

## 十七、Qualification 設計

Selector qualification 必須拆成兩層。

### 17.1 Deterministic / structural qualification

必須先 100% PASS：

- 六沖、六合、三合、三會、刑、害、破、天干五合 tables。
- 大運交界判定。
- 歲運並臨。
- 本命柱伏吟。
- full / partial pattern completion。
- suppression / dedup。
- Li-Chun annual-period boundary。
- 10-year completed-window selection。
- lexicographic rank。
- Top 4 / Bottom 1 deterministic output。
- JSON canonical digest。

### 17.2 Historical discrimination qualification

結構算法正確不代表事件預測一定有效，因此另做 held-out historical qualification：

1. 先 freeze selector profile / rule version。
2. 在不知道事件答案的前提下先產生 4 high + 1 control。
3. 再揭露 ground truth。
4. 評估：
   - high 年是否較常有可確認重大變化。
   - control 年是否較少出現重大結構變化。
   - 是否存在系統性 +1 / -1 flow-year 偏移。
5. 不因看到結果後重寫 v1 profile。

單一命主只能是 case evidence，不構成 promotion。

初期即使 empirical qualification 表現良好，capability 仍維持 `experimental / on_demand`，Stable promotion 另走正式 governance。

---

## 十八、Regression / Failure Tests

最低測試：

### 18.1 Determinism

同一：

```text
normalized_natal
as_of_date
profile_id
```

重跑 100 次 selection digest 必須一致。

### 18.2 Input-order independence

JSON key order、natal records serialization order 不得改變 selection。

### 18.3 Contamination resistance

把 05～08 或聊天事件答案提供給外層 workflow，不得讓 selector canonical input 接收到它們；選年必須不變。

### 18.4 Suppression

若歲運並臨：

- 只能保留 `sui_yun_bing_lin` Tier 1。
- 不得另外灌入同一對象的 branch_repeat + stem_repeat 來膨脹排名。

### 18.5 Consecutive Top 4

fixture 若真正排名前四為連續年份，selection 必須保留連續年份，不得為了「分散」替換。

### 18.6 No true low year

fixture 若所有年份都有 Tier 1：

```text
control_quality = relative_low
```

不得錯標 `strong_control`。

### 18.7 Li-Chun user correction

預測 2016 flow year，實際事件 2017-01：若日期仍在 2016 flow-year period，evaluation 必須判為 same flow year，而不是 mechanically `+1`。

---

## 十九、錯誤與降級

### 19.1 無可靠大運

v1 需要：

- 已解析本命四柱
- 日主
- deterministic Bazi decadal periods
- Li-Chun flow-year calculation

若大運缺失或 BLOCKING conflict：

```text
status = unavailable
reason = insufficient_bazi_basis
```

不得讓 AI fallback 自己挑年份。

### 19.2 年齡／歷史不足

若不足 10 個已完成 flow-year periods，但仍有至少 5 個可用期間，後續是否允許 limited-window calibration 由 workflow spec 決定；Selector 必須明確回報實際 window size，不得假裝有 10 年。

若少於 5 個可用年度，不產生正式 4+1 set。

### 19.3 boundary conflict

若 Li-Chun boundary / natal basis 有 blocking conflict：

- fail closed。
- 不猜年份。

---

## 二十、工程邊界（未實作）

未來程式模組建議獨立於現有 Bazi natal / forecast：

```text
engine/historical/
  activation_models.py
  bazi_relations.py
  bazi_activation.py
  selector.py
```

原因：

- 本命算法不應混入 empirical selector governance。
- relation tables 需獨立版本化。
- 後續可新增 `ziwei_activation.py` 而不污染 Bazi core。

Distribution runtime 再包裝 action：

```text
prepare_historical_calibration
```

但本規格尚未授權寫 production code。

---

## 二十一、v1 明確非目標

本版不做：

- AI 自由選年。
- 100 分制 activation score。
- 為了讓年份分散而替換真正 Top 4。
- 為了跨大運而人工改選年份。
- 把高 activation 說成凶年。
- 用喜用神、格局、神煞直接加分。
- 用單一十神名稱直接加分。
- 未定義天干沖就臨場加入。
- 讓 experimental Ziwei flowing stars 決定 ranking。
- 看過歷史事件後調整 v1 權重。

---

## 二十二、最終演算法心智模型

```text
00～04 deterministic natal basis
↓
找最近 10 個已完成 Bazi flow-year periods
↓
每一年：
  resolve flow-year pillar
  resolve current Da-Yun
  ↓
  detect Tier 1
  detect Tier 2
  detect Tier 3
  ↓
  dedup + suppression
  ↓
  build rank vector
↓
10 年 lexicographic ranking
↓
真正 Top 4 = Historical High Years
真正 Bottom 1 = Control Year
↓
selection digest 鎖定
↓
AI 才開始解讀「這些年可能發生什麼」
↓
使用者驗證／訂正
```

核心原則：

> **Python 不是幫 AI 找容易中的年份，而是按固定 profile 對 10 年全部一視同仁地計算。**
>
> **高低來自同一套可重現結構規則；Top 4 / Bottom 1 不接受人工美化。**
>
> **Selector 算的是結構活化，不是命中保證；真正有沒有大事，要等 blind calibration 的 ground truth 才知道。**
