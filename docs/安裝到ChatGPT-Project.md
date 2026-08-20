# 安裝到 ChatGPT Project

本文件說明如何把 Metaphysics Lab 的共用核心安裝到一個新的 ChatGPT Project，並與私人命盤資料分開管理。

核心原則：

> GitHub 保存系統核心；ChatGPT Project 保存實際分析環境與私人 Case。

GitHub 更新不應直接覆蓋命主私人資料。

---

## 一、建立新的 ChatGPT Project

先建立一個新的 ChatGPT Project。建議一位主要命主使用一個獨立 Project，或至少在 Project 內用明確檔名區分不同命主。

不要把多人命盤混在同一組未標示的檔案中。

---

## 二、設定 Project Instructions

開啟：

`core/核心提示詞.md`

把內容複製到 ChatGPT Project 的 Instructions／專案指示中。

這份提示詞負責：

- 角色定位
- 資料讀取順序
- 問事先盲判、後事件校準
- 八字／紫微／奇門分工
- 資料類型區分
- 高風險領域邊界
- 輸出格式與信心標示

若核心提示詞更新，Project Instructions 也需要同步更新。

---

## 三、上傳正式規則與引擎

### 一般 ChatGPT Project：建議使用相容入口

目前一般 Project 最小安裝仍建議加入：

```text
core/命理分析作業規範.md
core/命理推導計算規則.md
core/紫微流月推導規則.md
engine/project_bazi_calendar.py
engine/project_ziwei_month.py
```

用途：

- `命理分析作業規範.md`：最高層分析流程與資料治理規則。
- `命理推導計算規則.md`：八字流年／流月／流日／流時的固定算法與邊界。
- `紫微流月推導規則.md`：紫微流月斗君、流月命宮、十二宮與月份邊界。
- `project_bazi_calendar.py`：八字引擎相容入口。
- `project_ziwei_month.py`：紫微流月引擎相容入口。

v1.2 重構後，正式實作已拆到：

```text
engine/bazi/calendar.py
engine/ziwei/common.py
engine/ziwei/month.py
```

但一般 ChatGPT Project **不需要因這次內部重構立刻把整個 package 都上傳**。兩支 `project_*.py` 會保留作 compatibility wrapper，讓既有安裝方式繼續可用。

完整 Python 環境、未來 Skill 或開發測試環境，才建議直接使用 `engine.bazi` 與 `engine.ziwei` package。

### 建議加入的驗證資料

若 Project 檔案空間允許，也建議加入：

```text
tests/命理推導測試案例.md
tests/紫微流月推導測試案例.md
```

這兩份文件讓 AI 知道正式算法曾用哪些案例驗證，也方便之後排查結果差異。

`tests/test_project_bazi_calendar.py`、`tests/test_project_ziwei_month.py` 與 `tests/test_engine_module_layout.py` 是開發與回歸測試用途，不是一般問事的必要檔案。

---

## 四、建立私人 Case

從 `templates/` 複製空白模板到自己的私人環境，並把 `_TEMPLATE` 移除。

建議至少準備：

```text
命盤核心摘要.md
命盤資料校驗紀錄.md
驗證事件紀錄.md
流年追蹤紀錄.md
問事追蹤紀錄.md
重大決策紀錄.md
```

第一次建立時，不需要一次把每個檔案填滿。

優先順序是：

1. 出生資料與正式命盤來源
2. 命盤資料校驗
3. 命盤核心摘要
4. 已確認的重要事件
5. 之後再累積流年、問事與重大決策追蹤

詳細欄位請看 `docs/命盤資料準備指南.md`。

---

## 五、加入原始命盤資料

建議至少準備一份八字原始資料與一份紫微原始資料。

可使用 Astralium 或其他可靠排盤來源。若使用 Astralium，請看：

`docs/Astralium資料取得指南.md`

原始資料請保留來源名稱與產出日期，不要先自行刪改欄位後再交給 Project。

第三方排盤直接提供的內容屬於「原始盤面事實」；Metaphysics Lab 自己計算的流月、流日等屬於「Project 推導盤面」，兩者不得混稱。

---

## 六、第一次啟動 Project

資料加入後，可先要求 Project 做「命盤建立／校驗」，不要直接跳到未來預測。

建議第一次對話確認：

- 是否成功讀到 `命理分析作業規範.md`
- 出生年月日時與出生地是否正確
- 八字四柱是否一致
- 日主與八字大運是否已確認
- 紫微十二宮、大限、流年等資料是否可讀
- 是否有不同來源的時間口徑差異
- 哪些欄位是原始來源，哪些是 Project 推導

確認完成後，再建立 `命盤核心摘要.md`。

---

## 七、Python 檔案放進 Project 代表什麼

把 `.py` 檔加入 Project，代表 Project 保存了正式算法來源。

**不代表每一個 ChatGPT 對話都會自動執行 Python。**

若當次環境能執行 Python，可依正式程式計算；若無法執行，AI 只能閱讀規則與程式內容，不得假裝已執行程式。

因此回答中若宣稱「程式已計算」「測試已通過」，必須真的有執行證據。

---

## 八、目前 v1.1 必須同步的紫微檔案

若 Project 是從 v1.0 建立，現在至少要新增／更新：

```text
core/命理分析作業規範.md
core/命理推導計算規則.md
core/紫微流月推導規則.md
engine/project_ziwei_month.py
```

並更新 Project Instructions 使用最新版 `core/核心提示詞.md`。

否則 Project 可能仍回答「紫微流月尚未啟用」。

v1.2 的模組化重構只改內部 Python 結構，**不會自動啟用紫微流日或流時**。

---

## 九、更新時不要覆蓋私人資料

日後更新 Metaphysics Lab 時，只同步：

- `core/`
- `engine/`
- 必要的 `tests/`
- Project Instructions

不要用 GitHub 版本覆蓋自己的：

- 命盤核心摘要
- 命盤資料校驗紀錄
- 驗證事件紀錄
- 流年追蹤紀錄
- 問事追蹤紀錄
- 重大決策紀錄

詳細更新方式請看 `docs/更新與版本同步.md`。
