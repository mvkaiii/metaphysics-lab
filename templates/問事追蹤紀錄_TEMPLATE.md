# 問事追蹤紀錄

本檔案用來保存具有明確問題、時間窗與可驗證結果的重要問事。

目的：

- 保留第一版盲判
- 避免事後改寫
- 區分盤面判斷與事件校準
- 追蹤預測是否真正落地
- 累積命主個人化的命理模型

一般聊天式、沒有明確時間窗或無法驗證的問題，不必強制記錄。

---

## 使用規則

1. 第一階段盲判完成後再寫入
2. 第一版盲判不得因後續事件而刪改
3. 事件校準只能追加
4. 實際結果發生後再補結果
5. 未發生前不得提前寫成驗證事件
6. 若問事涉及重大決策，可同步連結「重大決策紀錄.md」

---

# 問事紀錄模板

## YYYY-MM-DD｜主題

### 基本資料

- 問事日期：
- 問事時間：
- 問事地點／時區：
- 類別：
- 狀態：待驗證
- 命主：

### 原始問題

> 保留使用者原始問題，不事後改寫。

### 問題範圍

- 目標事件：
- 分析時間窗：
- 需要精度：年／月／日／時
- 是否為重大決策：是／否

### 使用資料

#### 原始盤面

- 八字：
- 紫微：
- 其他：

#### 已校驗資料

- 命盤資料校驗紀錄：
- 採用時辰：
- 採用版本：

#### Project 推導盤面

- 八字大運：
- 流年：
- 流月：
- 流日：
- 流時：
- 推導規則版本：

### 第一階段盲判

#### 核心結論

- 

#### 最可能發生的主題

- 

#### 次要可能

- 

#### 主要機會

- 

#### 主要風險

- 

#### 有利時間窗

- 

#### 不利時間窗

- 

#### 觀察指標

- 

#### 第一階段信心

- 高度確信／中度推測／低度推測

#### 第一階段依據

- 

---

### 第二階段事件校準

> 僅在第一版盲判完成後填寫。

#### 讀取的已驗證事件

- 

#### 支持程度

- 高度支持／部分支持／不支持／資料不足

#### 命主過往落地模式

- 

#### 是否調整信心

- 

#### 是否調整可能落地形式

- 

#### 不得改寫的部分

- 第一階段盲判原文保持不變

---

### 最終策略

#### 宜

- 

#### 忌

- 

#### 底線

- 

#### 進攻條件

- 

#### 防守條件

- 

#### 停損條件

- 

---

### 實際結果

- 日期：
- 實際事件：
- 結果：
- 是否落在預測時間窗：
- 是否符合第一階段盲判：
- 是否符合第二階段校準：

### 結果評估

- 命中程度：高／中／低
- 哪部分有效：
- 哪部分失準：
- 失準可能原因：
- 是否需要調整算法：
- 是否需要調整命理解讀模型：

### 後續更新

- [ ] 若事件已發生，視需要更新「驗證事件紀錄.md」
- [ ] 若屬重大決策，更新「重大決策紀錄.md」
- [ ] 若顯示穩定長期模式，評估是否更新「命盤核心摘要.md」
- [ ] 若顯示算法問題，更新「命理推導計算規則.md」

## Locked Claims｜v1.5

> 重要且可驗證的未來問事使用。第一階段 lock 後不得覆寫。

### Claim 01
- claim_id：
- priority：primary / secondary
- domain：
- event_family：
- forecast_window：
- matched_if：
- partial_if：
- not_matched_if：
- confidence：
- contamination_state：clean_prospective / partially_known / known_before_lock
- evidence_basis：
- knowledge_cutoff_at：
- method_version：

### Evaluation｜時間窗結束後追加
- verification_state：matched / partial / not_matched / cannot_recall
- domain_result：
- event_family_result：
- timing_result：
- observed_actual：
- failure_mode：none / ai_compliance_failure / specification_ambiguity / deterministic_or_algorithm_failure / metaphysical_signal_failure

規則：Primary Claims 最多 3 個、Secondary Claims 最多 2 個；不得為提高命中率大量增列低資訊量 Claim。`matched_if` / `partial_if` / `not_matched_if` 在 lock 後不得擴張或重寫。
