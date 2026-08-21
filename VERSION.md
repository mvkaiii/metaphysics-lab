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

目前 v1.2 開發線在 v1.1 正式版之上增加模組化架構、capability 狀態模型與 Calendar Resolver infrastructure。

- 八字正式模組：`engine/bazi/calendar.py`
- 紫微流月：`implemented / stable / default`
- Metaphysics Lab 紫微流日定位引擎：v1.0.0-exp
- 紫微流日推導規則：v1.0-exp
- 紫微流日：`implemented / experimental / on_demand`
- Metaphysics Lab 紫微流時定位引擎：v1.0.0-exp
- 紫微流時推導規則：v1.0-exp
- 紫微流時：`implemented / experimental / on_demand`
- Metaphysics Lab Calendar Resolver：v1.0.0
- Calendar / Input Resolver：implemented
- Ziwei Calendar Adapter：implemented
- Ziwei Transformation Core v1：`implemented / stable / on_demand`
- Ziwei Flying Core v1：`implemented / stable / on_demand`
- Phase 2A 公開 iztro 十干四化 qualification：`40 / 40 PASS`
- Phase 2A 私有 Astralium 十干四化 qualification：`40 / 40 PASS`
- Phase 2A 私有 Astralium flying qualification：`80 / 80 PASS`
- 紫微流月／流日／流時細運四化／飛化：`planned / on_demand`
- 紫微流曜：`planned / on_demand`
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
- Calendar / Input Resolver：v1.2 開發線已實作 v1.0.0；需要 `lunar-python 1.4.8` 與 `tzdata 2026.3`
- Ziwei Calendar Adapter：v1.2 開發線已實作
- 紫微十天干四化核心：v1.2 開發線已實作為 Stable / On-demand；rule profile `metaphysics-lab-common-v1`
- 紫微本命宮干、生年、大限、流年飛化核心：v1.2 開發線已實作為 Stable / On-demand
- Phase 2A qualification：pinned iztro `40/40`；私有 Astralium 四化 `40/40`、飛化 `80/80`；raw private chart 不存 repo
- 紫微流月／流日／流時細運四化／飛化與流曜：尚未實作，維持 Planned / On-demand

## 邊界提醒

八字流月採節氣月；紫微流月採農曆月。兩者在同一國曆日期可能不同月，屬正常設計，不是 bug。

Calendar Resolver v1 的 Gregorian→Lunar HKO exhaustive validated range 為 `1901-01-01..2100-12-31`；`2057-09-28..2057-10-27` 為 `boundary_conflict`，`2089-09-04` 與 `2097-08-07` 為 `boundary_caution`。2100 之後若 provider 可算，只能標記 `out_of_validated_range`，不得宣稱已通過 HKO validated range。

Calendar Resolver v1 使用 pinned `tzdata 2026.3 / IANA 2026c`。23:00 已屬子時，但 civil date 只在 00:00 換日，`metaphysics_day_boundary_applied = false`。八字既有 23:00 early-Zi 規則仍由八字引擎負責；紫微不自動沿用。

紫微流日／流時 core 仍接受已解析農曆資料；Ziwei Calendar Adapter 可把成功且可用的 `CalendarContext` 傳入既有 core。自然語言解析、真太陽時與紫微 23:00 命理日界仍在 Resolver 外。
