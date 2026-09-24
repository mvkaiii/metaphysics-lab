# Metaphysics Lab

Metaphysics Lab 是一套把**命盤計算**和**AI 命理解讀**分開的命理分析系統。

核心概念很簡單：**Python 負責固定計算，AI 負責解讀。** 一般使用者不需要先理解 repo、模組或 capability，也不需要自己決定八字／紫微該跑哪個程式。

目前版本識別為 **v1.7.0**（release candidate）。在 `v1.7.0` Git tag / GitHub Release 正式建立前，公開最新正式 Release 仍是 v1.6.0；這不改變本候選版的安裝與升級契約。v1.7.0 維持 **Case Schema 1.1**，既有 Case 不需要重建。

## 第一次使用

最簡單的方式是到 GitHub Release 的**下載區（GitHub 顯示為 Assets）**下載 `Metaphysics-Lab-v1.7.0-User-Package.zip`。下載後只需要解壓縮這個 User Package；ZIP 內固定只有下面 3 個檔案，也可以單獨下載。**不要下載 GitHub 自動產生的 Source code ZIP 當成使用者包。**

| 用途 | 實際檔名 | 你要做什麼 |
|---|---|---|
| **命理計算程式** | `metaphysics_lab.py` | 上傳到 ChatGPT Project 或 Claude Project |
| **命理分析核心規則** | `metaphysics_core.md` | 上傳到 Project |
| **Project 設定指令** | `project_instructions.txt` | 打開後，把全文貼到 Project Instructions |

如果你是從 **v1.6.0 升級到 v1.7.0**，請三個檔案一起同步：替換 `metaphysics_lab.py`、替換 `metaphysics_core.md`，並把新版 `project_instructions.txt` 全文重新貼到 Project Instructions。保留既有 `命主索引.md`、私人 Case、驗證事件與追蹤紀錄；本次沒有 Case Schema migration，也不要做破壞性 Case 重建。

設定完成後，先對 AI 說：

> **「開始建立我的命理專案。」**

### 首次建立流程：Birth Data first

AI 先確認建立完整本命所需的出生資料，只追問缺少欄位：

- 性別
- Gregorian 出生日期
- 出生時間
- 出生地

目前 single-file runtime 已內建固定版本的核心曆法 dependency 與有限、版本化的 **offline registry**。出生地若命中支援的 offline registry 記錄，可以直接建立 Project Natal，**不需要網路**，也**不需要額外 Python 套件**。

出生地解析順序固定：

1. 若使用者／AI host 已提供完整 `resolved_location`，直接使用並保留 provenance。
2. 否則先查 Project 內建 offline registry。
3. offline registry 找不到時，預設 fail closed；只有明確啟用 network location resolution 時才使用網路 fallback。
4. offline alias 若有多個候選，直接回報 ambiguity，不用網路結果偷偷覆蓋。

offline registry 不是全球地理資料庫；它的 coverage 有限且版本化。未支援地點可以提供已確認的座標＋IANA timezone，或明確選擇啟用 network location resolution。

Astralium 仍然可以提供八字／紫微第三方排盤，但現在回到**可選的 External Natal Source／交叉校驗來源**，不是首次建立 Project 的必要前置步驟，也不是 Project Natal calculation authority。

完整命盤、流年、合盤或重大決策需要較多推理；如果你使用的平台提供**較高推理強度**或深度思考模式，可以優先使用。

詳細步驟：

- [快速開始](docs/快速開始.md)
- [安裝到 ChatGPT / Claude Project](docs/安裝到ChatGPT-Project.md)
- [命盤資料準備指南](docs/命盤資料準備指南.md)
- [Astralium 資料取得指南](docs/Astralium資料取得指南.md)
- [更新與版本同步](docs/更新與版本同步.md)
- [v1.7.0 發布說明](docs/發布說明-v1.7.0.md)

## 命盤資料可以怎麼提供？

目前建議依下面順序使用：

1. **只有出生資料**：提供性別、出生日期、出生時間與出生地。支援的 offline registry 地點可直接建立 Project 原生八字／紫微命盤；不需要網路，也不需要額外 Python 套件。
2. **出生資料 + Astralium**：若手上已有 Astralium 八字／紫微命盤，可以一起提供，作為 External Natal Source 與 Project Natal 做 reconciliation／交叉校驗。
3. **只有第三方排盤**：只有 Astralium、其他排盤網站、命理軟體或命理師提供的結構化命盤，也可以先保存與分析；系統不會因此假裝已完成 Project 原生計算。

第三方排盤與 Project 自己計算的結果會分開保存；有差異就明確標示，不會為了讓兩邊看起來一致而互相覆寫。

## 出生時間不確定也不要亂猜

如果只知道「大概晚上7、8點」、一段時間範圍，甚至完全不知道出生時間，系統不會自行補 12:00、區間中點或任意時辰。

資料足夠時，系統可以保留多個候選狀態，只把所有候選都一致的部分視為已確定資料；需要唯一出生時辰才能成立的結論則保持未確定。這類技術流程在系統內稱為 Candidate Envelope，詳細規則見[命盤資料準備指南](docs/命盤資料準備指南.md)。

## 一個 Project 可以管理多人

你可以在同一個 Project 管理本人、家人、朋友或合作對象。系統會先辨識目前是在問哪一位命主，再讀取對應的私人 Case，避免不同人的命盤與事件紀錄混在一起。

公開文件中的姓名、日期與識別碼都是**虛構示例**。例如某位命主可能顯示為 Alex，但真正私人 Project 可以使用你自己習慣的暱稱或標籤。

## 問未來時，先看盤再校準

流年、未來趨勢與重大決策採「**先盲判，再事件校準**」：第一版先根據盤面與必要現實條件完成，不先偷看已驗證事件；之後才用你已確認的人生事件校準落地形式與信心。

Project 原生本命與由本命／運限／目標時間建立的 **Project 推導盤面** 會分開標示，避免把衍生計算冒充原始第三方資料。

## v1.7 的使用導航與可靠性

v1.7 新增 Guided Inquiry：AI 可以主動顯示 3～4 個後續詢問方向，預設 3 個，但你仍可自由輸入任何問題；這些建議只是導航，不是新的命理證據，也不能提高原本證據允許的 specificity 或信心。

Case Doctor 用來診斷 authority、legacy、duplicate 與 conflict，並可提出 reconciliation dry-run；它不會自行刪除使用者檔案。Prospective Validation 2.0 會分開 clean、conditional、hidden-existing-reality 與 retrospective context，避免把已知安排混入乾淨預測命中率。

## 如果 AI 無法執行 Python

AI 必須明確說明**無法執行 Python**，不得假裝已跑過命盤計算。這時可以先保留 Astralium 等 External Natal Source；若仍需要 Project 原生計算，也可以在本機使用同一個命理計算程式：

```bash
python metaphysics_lab.py request --input request.json --pretty
```

把輸出的 JSON 結果交回 AI，再繼續解讀。

## 隱私

私人出生資料、`命主索引.md`、Case Markdown、事件紀錄、PDF、截圖與**私人 Astralium raw chart** 不應提交到公開／共用 GitHub repo；這些資料留在你自己的 Project 或本機。

## 想看技術細節？

一般使用者不需要閱讀開發 Phase 或能力狀態表。若你要追蹤技術版本、完整變更與架構：

- [VERSION.md](VERSION.md)：技術版本與能力狀態
- [CHANGELOG.md](CHANGELOG.md)：正式版本與尚未發布的變更
- [架構說明](docs/架構說明.md)
- [資料治理](docs/資料治理.md)

目前實際可執行的能力仍以程式回傳的 `runtime_info` 為技術權威來源；正式發版不會自動把仍在實驗中的能力升為 Stable。這項規則主要供開發與稽核使用，一般使用者不需要自行判讀。