# 流年追蹤紀錄

## YYYY

### 主題

- 建立日期：
- 現實計畫時間：
- 命理原始預測時間窗：
- 預測主題：
- 信心：
- 盤面依據：
- Project 推導依據：
- 狀態：待驗證

> 現實計畫日期可以更新；命理原始預測時間窗不得覆寫，只能追加修正版。

## v1.5 Prospective Contamination

每筆可驗證未來預測應標示：

- claim_id：
- contamination_state：`clean_prospective` / `partially_known` / `known_before_lock`
- knowledge_cutoff_at：
- forecast_window：
- evaluation_eligibility：

`known_before_lock` 與 `partially_known` 可以保留做策略背景，但不得進 clean prospective denominator。現實排程更新不得覆寫事前鎖定的命理預測時間窗。
