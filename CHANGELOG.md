# 變更紀錄

## 未發布｜v1.2 引擎重構與細時間 capability

### 引擎模組化

- 八字正式實作拆入 `engine/bazi/`。
- 紫微流月正式實作拆入 `engine/ziwei/`。
- 紫微共用地支、十二宮與輸入驗證集中於 `engine/ziwei/common.py`。
- 新增 `tests/test_engine_module_layout.py`，驗證新模組路徑與既有相容入口結果一致。
- `engine/project_bazi_calendar.py`、`engine/project_ziwei_month.py`、`engine/project_ziwei_day.py` 與 `engine/project_ziwei_hour.py` 保留為 compatibility wrapper。

### 相容性

- 一般 ChatGPT Project 可繼續使用 `project_*.py` 相容入口，不需要因內部重構立即改變呼叫方式。
- 完整 Python 環境與未來 Skill 可改用 `engine.bazi`、`engine.ziwei` package。
- 模組化重構不改變既有八字流年／流月／流日／流時算法，也不改變紫微流月斗君與閏月規則。

### v1.2 capability 模型

- 紫微細部能力改採「是否已實作、成熟度、預設調度」三軸管理，不再只用 enabled / disabled 二元表示。
- On-demand 代表能力已存在且可執行，但平常不預設跑；只有細看日期／時段、比較候選時間、處理跨系統衝突或使用者明確要求時才調用。
- Experimental 能力可以執行與累積驗證，但分析權重較低，不得單獨支撐高確信結論。

### 紫微流日 capability

- 新增 `engine/ziwei/capabilities.py`，集中記錄 implementation / maturity / routing / rule version / dependency。
- 新增 `engine/ziwei/day.py`，實作「流月命宮起初一、順行十二宮、一日一宮」的紫微流日定位。
- 流日第一版狀態：`implemented / experimental / on_demand`。
- 流日十二宮與流月共用 `palaces_from_ming_branch()`，避免宮位方向重複實作。
- 新增 `core/紫微流日推導規則.md`，記錄算法、輸入邊界、閏月 convention、外部來源與升級門檻。
- 新增 `tests/test_project_ziwei_day.py`、`tests/test_ziwei_capabilities.py`、`tests/test_ziwei_package_exports.py` 與人工回歸案例。
- 流日一般公式已對照 iztro 公開安星訣／固定程式，以及其他獨立公開排法資料。
- 閏月後半採 Project 既有拆半規則，先解析有效流月，再以實際農曆日數推流日；此細節先維持 Experimental。
- 流月結構化輸出保留 `flow_day_enabled = false` 表示「本次流月預設路徑不跑流日」，並新增 `flow_day_available_on_demand = true` 避免誤解為能力不存在。

### PR #3：紫微流時 capability

- 新增 `engine/ziwei/hour.py`，固定「流日命宮起子時、每時辰順行一宮」的流時命宮定位。
- 新增 `engine/project_ziwei_hour.py` 相容入口。
- `ziwei.flow_hour_palaces` 第一版狀態：`implemented / experimental / on_demand`，rule version `1.0-exp`。
- 流時十二宮直接共用 `palaces_from_ming_branch()`，不複製另一套宮位方向算法。
- 新增 `core/紫微流時推導規則.md` 與 `tests/紫微流時推導測試案例.md`。
- 外部驗證使用 iztro 固定 commit `814b77e6371e1050cac31bbf674db3c3138fcfde`，並以獨立公開文字排法交叉支持核心起法。
- 採 1.5 架構：flow-hour core 只接受已確認農曆日期與 `hour_branch`；這些民用時間責任當時保留給後續 infrastructure，現已由 Calendar Resolver v1 + Ziwei Calendar Adapter 承接 neutral context 層；紫微命理日界仍未在 flow-hour core 內定義。
- flow-day structured output 現在明確標示 `flow_hour_implemented = true`、`flow_hour_default_routing = false`，避免把 on-demand 誤讀成能力不存在。
- 流時天干、流時四化、流曜、細層飛化與 Cross-System Validation 不在本 PR。

### Calendar Resolver v1

- 新增 system-neutral `engine/calendar/` subsystem：precision policy、contract models、pinned timezone normalization、lunar provider 與 Resolver orchestration。
- 新增上游 Input Resolution / Precision Gate：先判斷 target capability 最低時間精度；不足或不唯一時只能追問、保留候選或降級，不得補假日期／假時間。
- Runtime lunar provider 固定 `lunar-python==1.4.8`；qualification source revision `000c8a3d74eed098d6256a28fdd51b869324c559`。
- HKO Gregorian→Lunar exhaustive validated range 固定 `1901-01-01..2100-12-31`。
- `2057-09-28..2057-10-27` 固定標記 `boundary_conflict`；`2089-09-04`、`2097-08-07` 固定標記 `boundary_caution`。
- Timezone provider 固定 `tzdata==2026.3` / IANA `2026c`；DST nonexistent / ambiguous local time 與 `utc_offset_hint` contract 已鎖定。
- Resolver civil date 只在 00:00 換日；23:00 已屬子時，但 `metaphysics_day_boundary_applied = false`。不把八字 23:00 early-Zi policy 套到紫微。
- 新增 `engine/ziwei/calendar_adapter.py` 作為第一個正式 adapter；`boundary_conflict` 不會被靜默當作正常可信日期。
- 本次沒有 refactor Bazi；自然語言解析、真太陽時、Qimen、紫微細部四化／流曜／細飛與紫微 23:00 命理日界不在本次範圍。

### 證據權重

- v1.2 採質性證據階層，不先設定八字／紫微或 Stable／Experimental 的任意固定百分比。
- 正式判斷同時考慮資料品質、capability 成熟度、問題時間層級、跨系統一致度與第二階段個人事件校準。
- Stable 且對應問題時間粒度者可作主要證據；較細 Stable 層主要用於細化；Experimental 必須降權；Planned／未實作／未達最低驗證門檻者不得進入正式權重判斷。
- 更細時間層不能在沒有充分理由時無條件推翻較高層主軸；若問題本身提升到特定日期或時段，對應流日／流時才可成為主要時間證據。
- 第二階段事件校準可以調整個人化可信度，但不得改寫第一階段盲判、原始盤面或正式算法。
- 未來若累積足夠追蹤與 Issue 可重現案例，數值權重必須由版本化 calibration model 與實證資料估計，不得憑直覺指定。

### 後續尚未實作

- 紫微細部四化、流曜與細層飛化算法。
- Cross-System Validation 正式引擎。

以上是後續 capability / infrastructure PR 的目標，不代表 Metaphysics Lab 的終局設計要排除這些能力。

## v1.1.0｜2026-08-20

### 新增

- 啟用 Project 紫微流月定位層。
- 新增流年斗君、流月命宮與流月十二宮重排。
- 新增 `engine/project_ziwei_month.py`。
- 新增紫微流月自動測試與人工測試紀錄。
- 新增 `core/紫微流月推導規則.md`。

### 文件與安裝流程

- 新增 `docs/安裝到ChatGPT-Project.md`，說明 Project Instructions、核心規則、Python 引擎與私人 Case 的安裝方式。
- 新增 `docs/命盤資料準備指南.md`，區分出生基本資料、八字、紫微、校驗、驗證事件與追蹤資料。
- 新增 `docs/Astralium資料取得指南.md`，說明如何使用 Astralium 或其他排盤來源取得原始結構化資料。
- 新增 `docs/更新與版本同步.md`，明確區分 GitHub 核心更新與私人 Project 資料。
- 重寫 `README.md` 與 `docs/快速開始.md`，加入第一次使用者的完整入口。
- 明確要求 v1.0 升級到 v1.1 的 Project 同步 `project_ziwei_month.py`、紫微流月規則與最新版 Project Instructions。

### 固定邊界

- 紫微流月採農曆月，農曆初一換月。
- 閏月採初一至十五歸原月、十六起歸下一月。
- 八字流月仍採節氣月；兩者不同步不是 bug。
- 紫微流月引擎不負責國曆轉農曆，輸入農曆資料必須來自可信曆法來源。
- GitHub 與 ChatGPT Project 視為兩套環境；核心更新需要同步，私人 Case 不得被覆蓋。

### 當時仍未啟用

- 紫微流日。
- 紫微流時。
- 流月四化。
- 流月流曜。
- 流月細層飛化。

## v1.0.0｜2026-08-20

### 新增

- 建立 Metaphysics Lab 共用核心架構。
- 建立命理分析作業規範。
- 建立問事「先盲判、後事件校準」雙階段制度。
- 建立 Project 推導盤面資料類型。
- 建立八字流年、流月、流日、流時固定算法。
- 建立 23:00 換日規則。
- 建立五虎遁、五鼠遁與天干十神推導。
- 建立節氣交界 15 分鐘警告。
- 建立 Project Bazi Calendar Engine v1.0.0。
- 建立回歸測試與人工測試紀錄。
- 建立空白個案模板與資料治理原則。

### 暫不啟用

- 紫微流月／流日／流時 Project 推導。
- 完整 Project 干支互動引擎。
- 奇門自動排盤引擎。
