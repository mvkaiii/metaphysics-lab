# Metaphysics Lab 版本

## 最新正式發布

- Metaphysics Lab Core：v1.1.0
- 命理推導計算規則：v1.2
- Project Bazi Calendar Engine：v1.0.0
- Metaphysics Lab 紫微流月定位引擎：v1.0.0
- 紫微流月推導規則：v1.0
- 問事追蹤制度：v1.0
- 發布日期：2026-08-20

## v1.2 開發線狀態

目前 v1.2 開發線在 v1.1 正式版之上增加模組化架構與 capability 狀態模型。

- 八字正式模組：`engine/bazi/calendar.py`
- 紫微流月：`implemented / stable / default`
- Metaphysics Lab 紫微流日定位引擎：v1.0.0-exp
- 紫微流日推導規則：v1.0-exp
- 紫微流日：`implemented / experimental / on_demand`
- Metaphysics Lab 紫微流時定位引擎：v1.0.0-exp
- 紫微流時推導規則：v1.0-exp
- 紫微流時：`implemented / experimental / on_demand`
- 紫微細部四化／流曜／細層飛化：`planned / on_demand`
- Calendar / Input Resolver：planned
- Cross-System Validation：planned

`Experimental / On-demand` 代表能力已有可執行 Python 與驗證紀錄，但一般年度／月份問事不預設執行，分析時也必須降權；不等於 Stable，也不等於能力不存在。

## 相容性

- Python：3.9 以上
- 時區：八字引擎需支援 `zoneinfo`
- 八字流月／流日／流時：已啟用
- 紫微流月：Stable，只含斗君、流月命宮、流月十二宮
- 紫微流月月份邊界：農曆初一；閏月拆半
- 紫微流日：v1.1 正式版未包含；v1.2 開發線已實作為 Experimental / On-demand
- 紫微流時：v1.1 正式版未包含；v1.2 開發線已實作為 Experimental / On-demand，只含流時命宮與十二宮定位
- 紫微細部四化／流曜／細層飛化：尚未實作
- Calendar / Input Resolver：尚未實作

## 邊界提醒

八字流月採節氣月；紫微流月採農曆月。兩者在同一國曆日期可能不同月，屬正常設計，不是 bug。

紫微流日直接接受已由可信曆法來源確認的農曆月、日與閏月狀態；本引擎不自行做國曆轉農曆，也不自行宣稱未固定的紫微換日口徑。

紫微流時再接受已解析的 `hour_branch`。流時 core 不處理民用 datetime、timezone、DST、國曆轉農曆或 23:00 日界；這些責任留給未來版本化的 Calendar / Input Resolver。
