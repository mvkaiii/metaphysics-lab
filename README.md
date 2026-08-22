# Metaphysics Lab

Metaphysics Lab 是一套把**可重現的命盤計算**與**AI 命理解讀**分開的命理分析系統。

核心原則很簡單：**Python 算盤，AI 讀盤。** 使用者不需要理解 repo 結構，也不需要自己挑八字／紫微模組。

目前正式 release identity 仍為 **v1.2.0｜2026-08-21**。AI Distribution Pack 是目前工作樹的 Unreleased 發行方式，不改寫 `VERSION.md`、Git tag 或既有正式 release。

## 第一次使用｜最短流程

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

完成後，AI 應自行確認需要的出生資料、呼叫 deterministic runtime、區分盤面事實與命理推論，並產生私人 Case Markdown Pack。你不需要知道內部 Phase 名稱或 capability 檔案位置。

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

## 第一次建立 Case 會得到什麼

系統的私人 Case 固定為九份 Markdown：

```text
00_專案索引.md
01_命盤核心摘要.md
02_命盤資料校驗紀錄.md
03_八字結構化資料包.md
04_紫微基礎資料包.md
05_驗證事件紀錄.md
06_流年追蹤紀錄.md
07_問事追蹤紀錄.md
08_重大決策紀錄.md
```

這些是**你的私人資料**，不是共用程式。AI 建立後，下載並放回自己的 Project 即可。之後一般更新採增量方式：例如新增已驗證事件只更新 `05_驗證事件紀錄.md`；第一版盲判不得事後覆寫。

## 三個發行檔各自負責什麼

| 檔案 | 責任 | 使用者要做的事 |
|---|---|---|
| `metaphysics_lab.py` | deterministic 計算、驗證、Case export；不做自由命理解讀 | 上傳；runtime 更新時替換 |
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

共用 repo 不應提交真實命主 raw birth input、完整住址、私人 Astralium raw chart、PDF、截圖或私人事件。Case Pack 留在使用者自己的 Project／本機。

## 開發者與歷史資料

一般使用者不需要閱讀開發 Phase。若要追蹤正式版本、Unreleased capability 演進、qualification 與架構：

- [VERSION.md](VERSION.md)：正式 release identity
- [CHANGELOG.md](CHANGELOG.md)：Release / Unreleased 歷史
- [架構說明](docs/架構說明.md)
- [資料治理](docs/資料治理.md)

目前既有 Unreleased 工作包含 Natal Foundation、Ziwei Fine Cycle、Ziwei Flowing Stars 與 AI Distribution Pack；其 implementation / maturity / routing 以 runtime metadata 與 CHANGELOG 的對應歷史紀錄為準，不以舊文件快照覆蓋現況。
