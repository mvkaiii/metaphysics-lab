# 變更紀錄

## 未發布｜v1.2 引擎重構準備

### 引擎模組化

- 八字正式實作拆入 `engine/bazi/`。
- 紫微流月正式實作拆入 `engine/ziwei/`。
- 紫微共用地支、十二宮與輸入驗證集中於 `engine/ziwei/common.py`。
- 新增 `tests/test_engine_module_layout.py`，驗證新模組路徑與既有相容入口結果一致。
- `engine/project_bazi_calendar.py` 與 `engine/project_ziwei_month.py` 保留為 compatibility wrapper。

### 相容性

- 一般 ChatGPT Project 仍可繼續使用兩支 `project_*.py`，不需要因內部重構立即改檔名。
- 完整 Python 環境與未來 Skill 可改用 `engine.bazi`、`engine.ziwei` package。
- 本次只重構模組，不改變八字流年／流月／流日／流時算法，也不改變紫微流月斗君與閏月規則。

### 仍未啟用

- 紫微流日。
- 紫微流時。
- Cross-System Validation 正式引擎。
- 紫微流月四化、流曜與細層飛化。

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

### 仍未啟用

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
