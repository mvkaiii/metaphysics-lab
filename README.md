# Metaphysics Lab

Metaphysics Lab 是一套以「可重現、可驗證、以決策為導向」為核心的命理分析框架。

它把命理分析拆成可管理的層級：原始盤面、資料校驗、固定算法推導、第一階段盲判、第二階段事件校準、現實決策策略與後續結果驗證。

## 第一次使用，從這裡開始

- 想先快速了解怎麼用 → [快速開始](docs/快速開始.md)
- 要裝進 ChatGPT Project → [安裝到 ChatGPT Project](docs/安裝到ChatGPT-Project.md)
- 不知道要準備哪些出生／命盤／事件資料 → [命盤資料準備指南](docs/命盤資料準備指南.md)
- 還沒有八字或紫微結構化資料 → [Astralium 資料取得指南](docs/Astralium資料取得指南.md)
- GitHub 更新後，不知道 Project 哪些檔案要換 → [更新與版本同步](docs/更新與版本同步.md)
- 想了解資料分類與隱私 → [資料治理](docs/資料治理.md)
- 想了解整體設計 → [架構說明](docs/架構說明.md)

---

## 核心理念

- 命盤提供模型。
- Project 推導提供時間層級。
- 事件提供證據。
- 現實背景決定策略。
- 問事先盲判，再校準。
- 原始盤面、Project 推導盤面與命理推論必須分開。
- 系統核心與私人個案資料必須分開保存。

## 目前能力

Metaphysics Lab v1.1 目前正式納入：

- 子平八字本命與運限分析規範
- 紫微斗數本命、大限、小限、流年資料使用規範
- Project 紫微流月：斗君、流月命宮、流月十二宮重排
- 問事雙階段流程：先盲判、後事件校準
- Project 八字流年、流月、流日、流時推導
- 23:00 換日
- 五虎遁與五鼠遁
- 天干十神推導
- 節氣交界警告
- 問事追蹤與結果驗證制度

目前正式版本尚未具備：

- 紫微流日／流時 Project 推導
- 紫微流月四化／流曜／細層飛化
- 完整 Project 干支互動引擎
- 奇門自動排盤引擎

---

## v1.2 引擎重構準備

目前開發分支已把正式 Python 實作拆成兩套模組：

```text
engine/bazi/   八字正式模組
engine/ziwei/  紫微正式模組
```

八字與紫微維持不同曆法與推導邏輯，不混寫在同一支 Python。

既有入口仍保留：

```text
engine/project_bazi_calendar.py
engine/project_ziwei_month.py
```

這兩支檔案現在是 compatibility wrapper（相容入口）。既有 ChatGPT Project 不需要因內部重構立即改檔名；一般使用者仍可同步這兩支檔案。新模組路徑主要提供後續 Skill、完整 Python 環境與開發測試使用。

v1.2 的目標不是把紫微細部功能永久關閉，而是建立「**能力先完成實作與驗證，平常不預設執行，需要提高解析度時才按需調用**」的 capability 模型。

後續規劃的紫微 on-demand capabilities 包含：

- 流日
- 流時
- 細部四化
- 流曜
- 細層飛化

各 capability 會分開記錄是否已實作、成熟度（Experimental / Stable）與調度方式（Default / On-demand）。Experimental 能力可以執行，但分析時必須降權，不得單獨支撐高確信結論。

本 PR 本身只完成模組化重構，**尚未實作上述新紫微細部算法**。

---

## 最短建置流程

### 1. 建立命盤資料

建議先準備：

- 出生年月日、時間、出生地與性別
- 八字結構化資料
- 紫微結構化資料

可使用 [Astralium](https://getastralium.com/) 取得可複製給 AI 的結構化命盤資料；也可以使用其他可靠排盤來源，但必須保留來源與時間口徑。

### 2. 建立 ChatGPT Project

將 `core/核心提示詞.md` 內容同步到 Project Instructions。

Project 檔案至少加入：

```text
core/命理分析作業規範.md
core/命理推導計算規則.md
core/紫微流月推導規則.md
engine/project_bazi_calendar.py
engine/project_ziwei_month.py
```

詳細步驟請看 [安裝到 ChatGPT Project](docs/安裝到ChatGPT-Project.md)。

### 3. 建立私人 Case

從 `templates/` 複製需要的模板，建立自己的：

```text
命盤核心摘要.md
命盤資料校驗紀錄.md
驗證事件紀錄.md
流年追蹤紀錄.md
問事追蹤紀錄.md
重大決策紀錄.md
```

這些是私人資料，不應提交回共用 GitHub repo。

### 4. 先校驗，再問事

第一次使用先確認出生資料、四柱、大運、紫微宮位與時間口徑；確認後再建立核心摘要。

未來問事採：

**第一階段盲判 → 第二階段事件校準**

---

## 目錄

```text
core/           核心規範、推導規則、系統提示詞
engine/bazi/    八字正式 Python 模組
engine/ziwei/   紫微正式 Python 模組
engine/*.py     既有相容入口
tests/          自動測試與人工回歸測試紀錄
templates/      新命主建立私人 Case 時使用的空白模板
docs/           安裝、資料準備、更新、架構與資料治理說明
```

## 重要邊界

本儲存庫只保存可共用的系統核心，不應提交真實命主的出生資料、命盤、醫療、家庭、工作、資產、感情、問事與其他可識別私人事件。

個人資料應保存在自己的私人 ChatGPT Project、私人知識庫或其他受控環境中。

---

## 八字時間推導

正式模組：

`engine/bazi/calendar.py`

相容入口：

`engine/project_bazi_calendar.py`

規則：

`core/命理推導計算規則.md`

所有細部時間計算結果都必須標示為「Project 推導盤面」，不得冒充 Astralium、原始 PDF 或其他第三方排盤系統的直接輸出。

## 紫微流月

正式模組：

`engine/ziwei/month.py`

相容入口：

`engine/project_ziwei_month.py`

規則：

`core/紫微流月推導規則.md`

Metaphysics Lab 已啟用紫微流月定位，但目前正式實作只做到月份層級：斗君、流月命宮與流月十二宮。

- 紫微流月採農曆月，農曆初一換月。
- 閏月採初一至十五歸原月、十六起歸下一月。
- 八字流月採節氣月。

因此同一個國曆日期的八字流月與紫微流月可能不同，這是兩套系統的月份邊界差異，**不是 bug**。

紫微流日、流時、細部四化、流曜與細層飛化將依 v1.2 capability 規格逐項完成實作、測試與外部校驗；完成後預設採按需調用，而不是每次問事全部執行。

---

## Python 檔案與 ChatGPT Project

把 `.py` 放進 Project，代表 Project 保存正式算法來源；**不代表每次對話都會自動執行 Python**。

如果 GitHub 的引擎更新，Project 中的 Python 副本也需要同步更新。詳細規則請看 [更新與版本同步](docs/更新與版本同步.md)。

---

## 使用提醒

命理只能提供趨勢、時間壓力、決策風險與策略參考。醫療、法律、稅務、保險、房產、大額投資與高槓桿事項，仍應以相關專業人士的判斷為準。
