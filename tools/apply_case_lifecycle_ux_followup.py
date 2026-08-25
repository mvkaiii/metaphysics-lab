from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def replace_once(relative, old, new):
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one anchor in {relative}, found {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Project Instructions: keep technical contracts internal, but make user-facing
# execution quiet and file lifecycle explicit.
replace_once(
    "core/核心提示詞.md",
    "**第一階段**：在前向判斷鎖定前，不讀既有驗證事件來反推答案；先用同一命主的 Base Case、必要現實條件與 runtime 正式盤面完成純盤面判斷。",
    "**第一階段**：在前向判斷鎖定前，不讀既有驗證事件來反推答案；先用同一命主的 Base Case（對外稱「本命基礎檔案」）、必要現實條件與 runtime 正式盤面完成純盤面判斷。",
)
replace_once(
    "core/核心提示詞.md",
    "## 對話方式\n\n**對話是自然語言；Markdown Case 才是結構化文件。**",
    "## 對話方式\n\n**內部執行預設靜默。** `runtime_info`、出生地解析、`subject_id`、schema／validation、`materialize` 與檔案生成等內部步驟，在正常成功時不要向使用者直播。只有需要補資料、處理歧義、執行失敗、可信度限制或檔案替換操作時，才用自然語言說明必要資訊。\n\n**對話是自然語言；Markdown Case 才是結構化文件。**",
)
replace_once(
    "core/核心提示詞.md",
    "只要使用者確認要保存或更新 Case，不得只在聊天裡說「已更新」；依 `metaphysics_core.md` 與 runtime 實際產生／更新對應 Markdown，提供真正變動的檔案。未變動的檔案不要重產。",
    "只要使用者確認要保存或更新 Case，不得只在聊天裡說「已更新」；依 `metaphysics_core.md` 與 runtime 實際產生／更新對應 Markdown，提供真正變動的檔案。未變動的檔案不要重產。首次建盤只建立 00～04 的本命基礎檔案，**不得在首次建盤時預先建立 05～08**。更新既有檔案時要替換原檔；若平台不能直接覆寫，請使用者**先移除舊版同名檔案再上傳新版**。像 `命主索引1.md`、`命主索引(1).md` 這類副本不得成為正式資料來源，**不得把副本檔名當正式檔案**。",
)

# Full workflow: explicitly bind each progressive record to real use, and
# prevent UI-generated duplicate file names from becoming canonical.
replace_once(
    "core/AI工作流程.md",
    "> Python 負責可重現的 deterministic calculation / validation / selection / serialization；AI 負責問題分類、命主辨識、證據分層、命理解讀、雙階段問事、現實策略與檔案操作引導。\n\n---",
    "> Python 負責可重現的 deterministic calculation / validation / selection / serialization；AI 負責問題分類、命主辨識、證據分層、命理解讀、雙階段問事、現實策略與檔案操作引導。\n\n**內部執行預設靜默。** `runtime_info`、subject resolution、`subject_id`、schema validation、location resolution、`materialize` 等步驟正常成功時不要向使用者直播。只有缺資料、出現歧義、runtime 無法執行、限制會影響可信度，或需要使用者處理檔案替換時，才把必要資訊翻成自然語言說明。\n\n---",
)
replace_once(
    "core/AI工作流程.md",
    "13. 產生 Base Case Markdown。",
    "13. 產生 Base Case Markdown；**Base Case 對外稱「本命基礎檔案」**，聊天中不需要介紹 canonical slot、schema 或 materialize 流程。",
)
replace_once(
    "core/AI工作流程.md",
    "不得先建立內容為空的 05～08。",
    "**不得在首次建盤時預先建立 05～08**；不得因為「以後可能會用到」就建立空檔。首次建盤對使用者只需說已整理好「本命基礎檔案」。",
)
replace_once(
    "core/AI工作流程.md",
    "`00` 是該 subject 的 Case manifest。第一次 materialize 05～08 任一檔時，runtime 必須同時回傳新版 00 與該新檔；後續只 append 既有檔案時，不需每次改 00。",
    "`00` 是該 subject 的 Case manifest。第一次 materialize 05～08 任一檔時，runtime 必須同時回傳新版 00 與該新檔；後續只 append 既有檔案時，不需每次改 00。\n\n**真正有對應紀錄時才建立**：\n\n- `05_驗證事件紀錄.md`：完成過去事件校準，且已有使用者確認的真實事件後建立／更新。\n- `06_流年追蹤紀錄.md`：真的完成一筆值得追蹤的年度／月份預測，且**使用者明確同意保存**後才建立。\n- `07_問事追蹤紀錄.md`：真的完成一筆具體問事，且**使用者明確同意保存**後才建立；剛建盤、一般閒聊或尚未提出具體問題時不得建立。\n- `08_重大決策紀錄.md`：真的處理一筆高影響決策，且**使用者明確同意保存**後才建立。\n\n06～08 不得因為未來可能使用而先建立；05 也不得在過去事件校準完成前建立。",
)
replace_once(
    "core/AI工作流程.md",
    "7. 沒有變動的 Case Markdown 不要重產。\n\n典型對應：05 歷史事件／Historical Calibration；06 年度／月份預測；07 一般具體問事；08 高影響決策；出生資料／reconciliation material change 才視影響更新01～04。",
    "7. 沒有變動的 Case Markdown 不要重產。\n\n**更新既有檔案時要替換原檔**，同一 canonical file 在 Project 中只保留一份正式版本。若平台不能直接覆寫，明確請使用者**先移除舊版同名檔案再上傳新版**。不得讓平台自動產生的 `命主索引1.md`、`命主索引(1).md` 或其他數字／copy suffix 成為第二份正式資料；**不得把副本檔名當正式檔案**。若已發現重複檔，先確認 canonical filename 與最新內容，處理完重複檔再繼續，不得同時讀兩份當 authority。\n\n典型對應：05 歷史事件／Historical Calibration；06 年度／月份預測；07 一般具體問事；08 高影響決策；出生資料／reconciliation material change 才視影響更新01～04。",
)

# Analysis rules: mirror the user-facing vocabulary and lifecycle so either
# source half of metaphysics_core.md preserves the same policy.
replace_once(
    "core/命理分析作業規範.md",
    "第一次建盤時不應存在空的 05～08。",
    "**不得在首次建盤時預先建立 05～08**。內部的 Base Case 對外稱「本命基礎檔案」；使用者不需要知道 slot、schema、materialize 等檔案生命週期術語。",
)
replace_once(
    "core/命理分析作業規範.md",
    "只有第一次真正產生資料時才建立 canonical 05～08；實際 filename 仍帶 subject identity。",
    "只有第一次真正產生資料時才建立 canonical 05～08；實際 filename 仍帶 subject identity。**真正有對應紀錄時才建立**：05 在**完成過去事件校準**並有已確認事件後建立；06 在真的有年度／月份預測且**使用者明確同意保存**後建立；07 在真的有具體問事且使用者明確同意保存後建立；08 在真的有高影響決策且使用者明確同意保存後建立。",
)
replace_once(
    "core/命理分析作業規範.md",
    "使用台灣繁體中文，務實、直接、白話、有邏輯與證據層級。**對話是自然語言，Markdown Case 才是結構化文件。**內部可以保留精確工程與命理術語，但使用者不需要先學會這套內部語言才能看懂分析。",
    "使用台灣繁體中文，務實、直接、白話、有邏輯與證據層級。**對話是自然語言，Markdown Case 才是結構化文件。**內部可以保留精確工程與命理術語，但使用者不需要先學會這套內部語言才能看懂分析。**內部執行預設靜默**：`runtime_info`、`subject_id`、schema、validation、materialize、Base Case 等正常內部步驟**不要向使用者直播**；Base Case 對外稱「本命基礎檔案」。只有使用者需要採取行動或限制會影響判斷時才說明必要資訊。",
)
replace_once(
    "core/命理分析作業規範.md",
    "- 同一重大決策以 08 為主，不為湊資料重複寫 07。\n\nSubject rename 必須一次更新 registry、所有 materialized Case filenames/front matter 與 00 manifest；不能只改顯示文字。",
    "- 同一重大決策以 08 為主，不為湊資料重複寫 07。\n- 更新既有檔案時要替換原檔；若平台不能直接覆寫，先請使用者**先移除舊版同名檔案再上傳新版**。\n- `命主索引1.md`、`命主索引(1).md` 或其他 suffix copy 不得成為 canonical 資料；**不得把副本檔名當正式檔案**。若已存在重複檔，先處理重複再繼續。\n\nSubject rename 必須一次更新 registry、所有 materialized Case filenames/front matter 與 00 manifest；不能只改顯示文字。",
)
