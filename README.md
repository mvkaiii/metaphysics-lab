# Metaphysics Lab

Metaphysics Lab 是一套把**可重現的命盤計算**與**AI 命理解讀**分開的命理分析系統。

核心原則很簡單：**Python 算盤，AI 讀盤。** 使用者不需要理解 repo 結構，也不需要自己挑八字／紫微模組。

目前正式 release identity 為 **v1.3.0｜2026-08-23**。AI Distribution Pack 已是正式發行方式；命理 capability 的 implementation / maturity / routing 仍以 `runtime_info` 為權威來源，正式 v1.3.0 不自動把 Experimental 能力升 Stable。

> 目前 `feature/progressive-case-historical-calibration` / Draft PR #160 另有 **Unreleased Project Contract 1.1 + Case Schema 1.1**：Progressive Case、Historical Blind Calibration 與 deterministic Historical Activation Selector。這些變更尚未成為新的正式 GitHub Release。

## 第一次使用｜最短流程

正式版一般使用者請直接打開 GitHub **Latest Release → Assets**，逐檔下載，不需要下載或解壓 ZIP。

你只需要三個發行檔：

```text
metaphysics_lab.py
METAPHYSICS_CORE.md
PROJECT_INSTRUCTIONS.md
```

在 ChatGPT Project 或 Claude Project：

1. 上傳 `metaphysics_lab.py`。
2. 上傳 `METAPHYSICS_CORE.md`。
3. 打開 Project Instructions，把 `PROJECT_INSTRUCTIONS.md` 的內容完整貼進去；這份檔案不是第三個知識檔上傳。
4. 完整命盤／流年／決策分析建議選 **High reasoning**。Medium 可用於一般分析與設定；Instant 不建議作為完整命理解讀的預設。
5. 對 AI 說：**「開始建立我的命理專案。」**

完成後，AI 應自行確認需要的出生資料、呼叫 deterministic runtime、區分盤面事實與命理推論，並建立私人 Case。你不需要知道內部 Phase 名稱或 capability 檔案位置。

詳細步驟：

- [快速開始](docs/快速開始.md)
- [安裝到 ChatGPT / Claude Project](docs/安裝到ChatGPT-Project.md)
- [更新與版本同步](docs/更新與版本同步.md)
- [命盤資料準備指南](docs/命盤資料準備指南.md)

## 如果 AI 環境不能執行 Python

AI 必須明確說明**無法執行 Python**，不得假裝已跑過命盤計算。此時用同一個單檔 runtime 在本機執行 request：

```bash
python metaphysics_lab.py request --input request.json --pretty
```

把 JSON 結果交回 AI 後再繼續解讀。一般使用者不需要改 Python 原始碼。

## Progressive Case｜Unreleased 1.1

Case 的完整 record type 仍是00～08，但新版流程不再一開始建立九個空檔。

第一次完成本命後先得到五份 **Base Case**：

```text
00_專案索引.md
01_命盤核心摘要.md
02_命盤資料校驗紀錄.md
03_八字結構化資料包.md
04_紫微基礎資料包.md
```

後續才按真正用途 materialize：

```text
05_驗證事件紀錄.md    ← Historical Blind Calibration / 已確認事件
06_流年追蹤紀錄.md    ← 第一次永久追蹤流年／年度預測
07_問事追蹤紀錄.md    ← 第一次永久追蹤一般問事
08_重大決策紀錄.md    ← 第一次永久追蹤重大決策
```

`00_專案索引.md` 作為 manifest。Case Schema 1.0 的既有九檔 Case 仍可讀，不會因升級而要求刪除舊檔。

## Historical Blind Calibration｜Unreleased 1.1

如果 Case 尚未校準，而使用者第一次問未來趨勢／流年／行動決策：

1. AI 先只讀 Base Case 00～04，完成並鎖定該問題的 Stage 1 盲判。
2. Python 執行 `historical.activation_selector`。
3. Selector 計算最近10個已完整結束的立春流年期，依固定 Tier 1／2／3 evidence 排序。
4. canonical selection 固定取真正 **Top 4 High + Bottom 1 Control**；AI、已知事件與聊天內容都不能換年。
5. AI 再對這5年提出明確「年份＋事件領域／形式」的歷史盲讀，讓使用者逐題驗證／訂正。
6. 使用者確認的實際事件才首次 materialize `05_驗證事件紀錄.md`。
7. 之後才回到未來問題的 Stage 2 事件校準。

Selector v1 的 ranking authority 是 Bazi。Ziwei yearly context 可在 canonical 5年選定後附加為 `support_only`，**不得改 Top 4、Control 或 Bazi selection digest**。

## 三個發行檔各自負責什麼

| 檔案 | 責任 | 使用者要做的事 |
|---|---|---|
| `metaphysics_lab.py` | deterministic 計算、驗證、Historical selector、Case export；不做自由命理解讀 | 上傳；runtime 更新時替換 |
| `METAPHYSICS_CORE.md` | AI 工作流程與分析治理的固定核心 | 上傳；Project Contract 更新時才替換 |
| `PROJECT_INSTRUCTIONS.md` | AI 的最高層角色、證據層級、禁令與問事流程 | 複製內容到 Project Instructions |

私人 Case MD 只保存個案資料與追蹤紀錄，不保存程式邏輯。

## 能力狀態以 runtime 為準

固定 Markdown 不複製動態 capability snapshot。要知道目前 runtime 真正支援什麼，讓 AI 呼叫：

```text
runtime_info
```

`runtime_info` 會回傳 implementation、maturity、routing、版本與 dependency 狀態。這可避免 README 與實際程式因版本演進而互相矛盾。

## 分析治理

Metaphysics Lab 固定區分八種資料：

1. 原始盤面事實
2. 已校驗資料
3. Project 原生盤面
4. Project 推導盤面
5. 已驗證事件
6. 命理推論
7. 研究假說
8. 當次現實背景

未來趨勢／流年／決策採**先盲判、再事件校準**。第一階段不先讀已驗證事件來製造預測感；第二階段才用事件校準落地形式與信心。

`Precision must be earned by input`：出生資料不足只能追問、保留候選或降低時間精度，不得自行猜值。

## 隱私

共用 repo 不應提交真實命主 raw birth input、完整住址、私人 Astralium raw chart、PDF、截圖、Historical Calibration 回答或私人事件。Case 留在使用者自己的 Project／本機。

## 開發者與歷史資料

一般使用者不需要閱讀開發 Phase。若要追蹤正式版本、qualification 與架構：

- [VERSION.md](VERSION.md)：正式 release identity
- [CHANGELOG.md](CHANGELOG.md)：Release / Unreleased 歷史
- [架構說明](docs/架構說明.md)
- [資料治理](docs/資料治理.md)

v1.3.0 已正式收斂 Natal Foundation、Ziwei Fine Cycle、Ziwei Flowing Stars 與 AI Distribution Pack。Unreleased 1.1 變更仍待完整驗證與正式發版；任何 capability 的當前 implementation / maturity / routing 仍以 runtime metadata 為準。
