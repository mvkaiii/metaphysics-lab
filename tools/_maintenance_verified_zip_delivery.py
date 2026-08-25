#!/usr/bin/env python3
"""Temporary one-shot migration for verified ZIP delivery wording."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count == 0 and new in text:
        return
    if count != 1:
        raise RuntimeError(f"expected exactly one match in {path}: {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


workflow = ROOT / "core" / "AI工作流程.md"
rules = ROOT / "core" / "命理分析作業規範.md"

workflow_delivery = """## 2.3 可驗證資料包交付\n\nMarkdown 是 Project 內的正式資料；ZIP 只負責讓使用者跨 App／瀏覽器／裝置下載與搬運。需要交付 Case 檔案時：\n\n1. 先取得本次真正要交付的 Markdown mapping。首次本命為 `命主索引.md` 加該命主 00～04；後續只放新增或真正變動的 Markdown。\n2. 呼叫 runtime `build_delivery_bundle`；不得讓 AI 自己宣稱「已打包」或只建立 `.zip` 副檔名。\n3. 只有回傳 `generated = true` 且 `integrity_verified = true`，才把回傳 bytes 寫成實際 ZIP 附件。ZIP 使用標準 DEFLATE、無密碼／加密、平面檔案結構。\n4. 對使用者只說「資料包已建立並通過完整性檢查」；**不得宣稱下載成功**。`delivered` 保持 unknown，實際下載只能由使用者確認。\n5. 使用者第一次回報不能下載時，重新產生新的 ZIP 與新附件，不重貼舊連結。\n6. **第二次仍無法下載**時，明確回報「檔案傳輸失敗」，保留本次資料供稍後重新產包；**不得改用單獨 `.md`** 假裝解決下載問題，也不要求使用者預設安裝第三方解壓縮 App。\n\n"""

replace_once(
    workflow,
    "---\n\n# 三、Subject Identity 與第一次建立私人 Case",
    workflow_delivery + "---\n\n# 三、Subject Identity 與第一次建立私人 Case",
)
replace_once(
    workflow,
    "15. 對每一份已建立的 `.md` 提供實際檔案，並告訴使用者加入同一個 Project。",
    "15. 將 `命主索引.md` 與本次已建立的 00～04 Markdown 交給 `build_delivery_bundle`，只在 ZIP 通過完整性檢查後提供實際下載附件，並請使用者解壓後加入同一個 Project。",
)
replace_once(
    workflow,
    "19. finalize 後由 runtime／Case flow**實際產生**或更新 `05_驗證事件紀錄.md`；首次 materialize 05 時同步更新 00，並把真正變動的 `.md` 以可**下載**檔案交給使用者加入 Project。",
    "19. finalize 後由 runtime／Case flow**實際產生**或更新 `05_驗證事件紀錄.md`；首次 materialize 05 時同步更新 00，並把真正變動的 Markdown 用 `build_delivery_bundle` 產成通過完整性檢查的更新 ZIP 交給使用者加入 Project。",
)
replace_once(
    workflow,
    "6. 提供實際變動且可下載的檔案，明確說明新增／替換／移除哪份。",
    "6. 將實際變動的 Markdown 產成通過完整性檢查的 ZIP 下載包，明確說明解壓後要新增／替換／移除哪份。",
)

rules_delivery = """## 可驗證資料包交付\n\n**Markdown 是正式資料，ZIP 是下載／搬運用的傳輸格式。**正式交付 Case 時必須由 runtime `build_delivery_bundle` 建立標準 DEFLATE ZIP，產生後重新開啟並做完整性檢查；只有 `generated = true` 且 `integrity_verified = true` 才可提供附件。首次本命包包含 `命主索引.md` 與該命主 00～04；後續更新包只包含新增或真正變動的 Markdown。\n\nAI 可以確認 ZIP 已產生且通過驗證，但**不得宣稱下載成功**。若第一次下載失敗，重新產生新的 ZIP；**第二次仍無法下載**則明確標示為**檔案傳輸失敗**並保留資料供稍後重產，**不得改用單獨 `.md`** 當下載備援。ZIP 不加密、不設密碼、不巢狀壓縮，且不把安裝第三方解壓縮 App 當成標準前置條件。\n\n"""

replace_once(
    rules,
    "## 建盤後的過去事件校準",
    rules_delivery + "## 建盤後的過去事件校準",
)
replace_once(
    rules,
    "AI 必須把真正變動的 Markdown 以可**下載**檔案交給使用者加入同一個 Project；未變動檔案不要重產。",
    "AI 必須把真正變動的 Markdown 交給 `build_delivery_bundle`，以通過完整性檢查的 ZIP 讓使用者下載、解壓後加入同一個 Project；未變動檔案不要重產。",
)

subprocess.run([sys.executable, str(ROOT / "tools" / "build_ai_distribution.py")], cwd=ROOT, check=True)
subprocess.run([sys.executable, str(ROOT / "tools" / "build_ai_distribution.py"), "--check"], cwd=ROOT, check=True)
print("verified ZIP delivery migration complete")
