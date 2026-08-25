#!/usr/bin/env python3
"""One-shot migration from ZIP-only delivery to ZIP + individual Markdown."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feature/portable-offline-natal-pipeline"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one replacement in {path}: found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


workflow = ROOT / "core" / "AI工作流程.md"
rules = ROOT / "core" / "命理分析作業規範.md"
prompt = ROOT / "core" / "核心提示詞.md"

replace_once(
    workflow,
    """Markdown 是 Project 內的正式資料；ZIP 只負責讓使用者跨 App／瀏覽器／裝置下載與搬運。需要交付 Case 檔案時：\n\n1. 先取得本次真正要交付的 Markdown mapping。首次本命為 `命主索引.md` 加該命主 00～04；後續只放新增或真正變動的 Markdown。\n2. 呼叫 runtime `build_delivery_bundle`；不得讓 AI 自己宣稱「已打包」或只建立 `.zip` 副檔名。\n3. 只有回傳 `generated = true` 且 `integrity_verified = true`，才把回傳 bytes 寫成實際 ZIP 附件。ZIP 使用標準 DEFLATE、無密碼／加密、平面檔案結構。\n4. 對使用者只說「資料包已建立並通過完整性檢查」；**不得宣稱下載成功**。`delivered` 保持 unknown，實際下載只能由使用者確認。\n5. 使用者第一次回報不能下載時，重新產生新的 ZIP 與新附件，不重貼舊連結。\n6. **第二次仍無法下載**時，明確回報「檔案傳輸失敗」，保留本次資料供稍後重新產包；**不得改用單獨 `.md`** 假裝解決下載問題，也不要求使用者預設安裝第三方解壓縮 App。\n""",
    """Markdown 是 Project 內的正式資料；ZIP 與單獨 `.md` 都是使用者可選的下載方式。需要交付 Case 檔案時：\n\n1. 先取得本次真正要交付的 Markdown mapping。首次本命為 `命主索引.md` 加該命主 00～04；後續**只包含新增或真正變動的 Markdown**。\n2. 呼叫 runtime `build_delivery_bundle`；不得讓 AI 自己重複 render Markdown，也不得只建立副檔名假裝已產出附件。\n3. runtime 先把每份 Markdown 正規化成**同一份 canonical Markdown bytes**，再由同一批 bytes 同時建立 ZIP 與 individual Markdown artifacts；ZIP 內檔案與個別下載檔必須**逐 byte 完全相同**。\n4. 只有回傳 `generated = true` 且 `integrity_verified = true`，才提供附件。ZIP 使用標準 DEFLATE、無密碼／加密、平面檔案結構；個別 Markdown 使用 UTF-8。\n5. **ZIP 與單獨 `.md` 兩種下載方式預設同時提供**：一個完整 ZIP 下載連結，加上本次每份 Markdown 的**個別下載**連結。單獨 `.md` 是正常交付選項，不是 ZIP 失敗後才出現的備援。\n6. 對使用者只能說附件已建立／已通過完整性檢查；**不得宣稱下載成功**。`delivered` 保持 unknown，實際下載只能由使用者確認。\n7. 使用者回報某種下載方式失敗時，對本次相同 canonical bytes **重新產生新的附件**，不要重貼舊連結；若 ZIP 與個別 Markdown 經重新交付後仍都無法下載，明確回報**檔案傳輸失敗**並保留資料供稍後重產。不得要求使用者預設安裝第三方解壓縮 App。\n""",
)

replace_once(
    workflow,
    "15. 將 `命主索引.md` 與本次已建立的 00～04 Markdown 交給 `build_delivery_bundle`，只在 ZIP 通過完整性檢查後提供實際下載附件，並請使用者解壓後加入同一個 Project。",
    "15. 將 `命主索引.md` 與本次已建立的 00～04 Markdown 交給 `build_delivery_bundle`；通過完整性檢查後，同時提供完整 ZIP 與各份 `.md` 個別下載連結。使用者可直接下載 Markdown，或下載 ZIP 後解壓，再把取得的 `.md` 加入同一個 Project。",
)
replace_once(
    workflow,
    "19. finalize 後由 runtime／Case flow**實際產生**或更新 `05_驗證事件紀錄.md`；首次 materialize 05 時同步更新 00，並把真正變動的 Markdown 用 `build_delivery_bundle` 產成通過完整性檢查的更新 ZIP 交給使用者加入 Project。",
    "19. finalize 後由 runtime／Case flow**實際產生**或更新 `05_驗證事件紀錄.md`；首次 materialize 05 時同步更新 00，並把真正變動的 Markdown 用 `build_delivery_bundle` 同時產成通過完整性檢查的更新 ZIP 與個別 `.md` 下載附件。",
)
replace_once(
    workflow,
    "6. 將實際變動的 Markdown 產成通過完整性檢查的 ZIP 下載包，明確說明解壓後要新增／替換／移除哪份。",
    "6. 將實際變動的 Markdown 交給 `build_delivery_bundle`，同時提供通過完整性檢查的 ZIP 與個別 `.md` 下載附件，明確說明要新增／替換／移除哪份。",
)

replace_once(
    rules,
    """**Markdown 是正式資料，ZIP 是下載／搬運用的傳輸格式。**正式交付 Case 時必須由 runtime `build_delivery_bundle` 建立標準 DEFLATE ZIP，產生後重新開啟並做完整性檢查；只有 `generated = true` 且 `integrity_verified = true` 才可提供附件。首次本命包包含 `命主索引.md` 與該命主 00～04；後續更新包只包含新增或真正變動的 Markdown。\n\nAI 可以確認 ZIP 已產生且通過驗證，但**不得宣稱下載成功**。若第一次下載失敗，重新產生新的 ZIP；**第二次仍無法下載**則明確標示為**檔案傳輸失敗**並保留資料供稍後重產，**不得改用單獨 `.md`** 當下載備援。ZIP 不加密、不設密碼、不巢狀壓縮，且不把安裝第三方解壓縮 App 當成標準前置條件。\n""",
    """**Markdown 是正式資料；ZIP 與單獨 `.md` 是並列的下載／搬運方式。**正式交付 Case 時必須由 runtime `build_delivery_bundle` 對**同一份 canonical Markdown bytes**一次正規化後，同時建立標準 DEFLATE ZIP 與 individual Markdown artifacts；ZIP 內 member 與單獨下載檔必須**逐 byte 完全相同**。只有 `generated = true` 且 `integrity_verified = true` 才可提供附件。首次本命交付包含 `命主索引.md` 與該命主 00～04；後續更新**只包含新增或真正變動的 Markdown**。\n\n**ZIP 與單獨 `.md` 預設同時提供**，個別 Markdown 應有可直接使用的**個別下載**附件；不得為兩種格式重新 render 兩份內容。AI 可以確認附件已產生且通過驗證，但**不得宣稱下載成功**。若使用者回報某一下載方式失敗，使用同一批 canonical bytes **重新產生新的附件**；若 ZIP 與個別 Markdown 重新交付後仍都失敗，明確標示為**檔案傳輸失敗**並保留資料供稍後重產。ZIP 不加密、不設密碼、不巢狀壓縮，也不把第三方解壓縮 App 當成標準前置條件。\n""",
)
replace_once(
    rules,
    "校準 finalize 後不得只在聊天裡摘要。Runtime／Case flow 必須**實際產生**或更新該命主的 `05_驗證事件紀錄.md`；若是首次 materialize 05，同步產生新版 `00_專案索引.md`。AI 必須把真正變動的 Markdown 交給 `build_delivery_bundle`，以通過完整性檢查的 ZIP 讓使用者下載、解壓後加入同一個 Project；未變動檔案不要重產。",
    "校準 finalize 後不得只在聊天裡摘要。Runtime／Case flow 必須**實際產生**或更新該命主的 `05_驗證事件紀錄.md`；若是首次 materialize 05，同步產生新版 `00_專案索引.md`。AI 必須把真正變動的 Markdown 交給 `build_delivery_bundle`，同時提供通過完整性檢查的 ZIP 與個別 `.md` 下載附件；未變動檔案不要重產。",
)

replace_once(
    prompt,
    """**Markdown 是正式資料；ZIP 只是跨裝置下載與搬運用的傳輸包。**需要把 Case 檔案交給使用者時，不得只把單獨 `.md` 附件當成可下載方案；先呼叫 runtime 的 `build_delivery_bundle`，再把回傳的 ZIP bytes 實際寫入 `.zip` 檔並作為附件提供。只有 runtime 回報 `generated = true` 且 `integrity_verified = true` 才能說「資料包已建立並通過完整性檢查」；**不得宣稱下載成功**，因為是否真的下載到裝置只能由使用者確認。\n\n首次本命資料包包含 `命主索引.md` 與該命主已建立的 00～04；後續更新包**只包含新增或真正變動的 Markdown**。使用標準 ZIP／DEFLATE、無密碼、無加密、平面檔案結構，不要求使用者另外安裝特定解壓縮 App。\n\n使用者回報不能下載時，先**重新產生新的 ZIP**並提供新的附件。若**第二次仍無法下載**，明確說明目前是**檔案傳輸失敗**，保留本次資料供稍後重新產包；**不得改用單獨 `.md`** 假裝已解決下載問題，也不得把未驗證或僅有 `.zip` 副檔名的內容交付給使用者。\n""",
    """**Markdown 是正式資料；ZIP 與單獨 `.md` 都是正常下載方式。**交付 Case 時先呼叫 runtime `build_delivery_bundle`，由**同一份 canonical Markdown bytes**同時建立 ZIP 與個別 Markdown；兩邊內容必須**逐 byte 完全相同**。只有 `generated = true` 且 `integrity_verified = true` 才能提供附件。\n\n首次本命交付包含 `命主索引.md` 與該命主 00～04；後續**只包含新增或真正變動的 Markdown**。預設**同時提供**一個 ZIP 下載與每份 `.md` 的**個別下載**附件；不得為兩種格式重新 render。ZIP 使用標準 DEFLATE、無密碼／加密、平面結構。\n\nAI **不得宣稱下載成功**。使用者回報某種方式無法下載時，用同一批內容**重新產生新的附件**；若 ZIP 與個別 Markdown 都經重新交付仍失敗，明確說明**檔案傳輸失敗**並保留資料供稍後重產。\n""",
)

subprocess.run(["python", "tools/build_ai_distribution.py"], cwd=ROOT, check=True)
subprocess.run(["python", "tools/build_ai_distribution.py", "--check"], cwd=ROOT, check=True)

combined = "\n".join(path.read_text(encoding="utf-8") for path in (prompt, workflow, rules))
for phrase in (
    "ZIP 與單獨 `.md`",
    "同時提供",
    "個別下載",
    "同一份 canonical Markdown bytes",
    "逐 byte 完全相同",
    "不得宣稱下載成功",
    "重新產生新的附件",
    "檔案傳輸失敗",
    "只包含新增或真正變動的 Markdown",
):
    if phrase not in combined:
        raise SystemExit(f"missing required dual-delivery phrase: {phrase}")
if "不得改用單獨 `.md`" in combined:
    raise SystemExit("obsolete ZIP-only fallback wording remains")
if len(prompt.read_text(encoding="utf-8")) > 8000:
    raise SystemExit("Project Instructions exceeds 8000 characters")

subprocess.run(
    ["git", "add", "core/AI工作流程.md", "core/命理分析作業規範.md", "core/核心提示詞.md", "dist/ai"],
    cwd=ROOT,
    check=True,
)
subprocess.run(
    ["git", "-c", "user.name=github-actions[bot]", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com", "commit", "-m", "fix: offer zip and markdown downloads together"],
    cwd=ROOT,
    check=True,
)
subprocess.run(["git", "push", "origin", f"HEAD:{BRANCH}"], cwd=ROOT, check=True)
