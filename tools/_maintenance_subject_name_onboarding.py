from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


prompt = ROOT / "core" / "核心提示詞.md"
workflow = ROOT / "core" / "AI工作流程.md"
rules = ROOT / "core" / "命理分析作業規範.md"

replace_once(
    prompt,
    "1. 先確認出生資料：性別、Gregorian 出生日期、出生時間、出生地；只追問缺少欄位。",
    "1. 先確認首次建立的 5 項必填資料：**命主稱呼、性別、出生年月日、出生時間、出生地**；只追問缺少欄位。命主稱呼**用於檔名**，可填暱稱／代號，**不一定要真名**；不得使用 Project 擁有者的名字代填，也不得使用目前聊天者的名字代填。",
)

replace_once(
    workflow,
    "1. 讀取核心規範與 `runtime_info`。\n2. 讀取 `命主索引.md`；若不存在，在第一位命主建立時 materialize。\n3. 判斷這是既有 subject 或新命主。\n4. 既有 subject：沿用原 `subject_id`。新命主：由 AI 發起 `subject.create_identity`，**opaque `subject_id` 必須由 runtime 產生**，不得由姓名／生日／出生地拼出或 hash PII。\n5. 保存 `subject_display_name`、`subject_short_id`、`filename_label` 至 `命主索引.md`。\n6. 檢查 natal 所需輸入；只詢問缺少欄位，不重問已知資料。\n7. 遵守 `Precision must be earned by input`；模糊時間不得自行取中點或 default time。\n8. 取得或確認出生地解析結果；保留 provenance。\n9. exact input：呼叫 runtime 建立單一 Project 原生本命。bounded / unknown time：若 `natal.candidate_envelope` 可執行且 location/timezone basis 完整，建立 Candidate Envelope；不得自己挑一個候選。\n10. 若使用者有 Astralium、已知四柱或其他 structured external chart，保留 External view，再執行 reconciliation；External 與 Project raw views 不互相覆寫。\n11. 查看 BLOCKING conflict / partial blocked scopes。若仍有 material conflict 或唯一時辰未解，不把高精度單一盤分析當確定基礎。\n12. AI 依 deterministic facts 完成本命解讀；解讀必須標為命理推論，不得寫回盤面事實。\n13. 產生 Base Case Markdown；**Base Case 對外稱「本命基礎檔案」**，聊天中不需要介紹 canonical slot、schema 或 materialize 流程。\n14. 對每一份已建立的 `.md` 提供實際檔案，並告訴使用者加入同一個 Project。\n15. 使用者加入後，重新檢查 `命主索引.md`、Case filenames、subject_id、schema 與 `00` manifest 是否一致。\n16. **本命盤建立完成後**且 precision 允許年度校準時，標準下一步就是做**過去 10 年**的過去事件校準；**排除今年，從去年往前**取 10 個 Gregorian label years。例如 2026 年固定校準 2016～2025。\n17. 校準先 lock blind predictions，再讓使用者確認／訂正；不得先看既有事件再改題。\n18. finalize 後由 runtime／Case flow**實際產生**或更新 `05_驗證事件紀錄.md`；首次 materialize 05 時同步更新 00，並把真正變動的 `.md` 以可**下載**檔案交給使用者加入 Project。\n19. 使用者若暫時不做校準，可保留 `uncalibrated`，但後續個人化預測必須降權；不得假裝已完成校準。",
    "1. 先確認首次建立的 5 項必填資料：**命主稱呼、性別、出生年月日、出生時間、出生地**；只詢問缺少欄位，不重問已知資料。\n2. **命主稱呼必填**，作為 `subject_display_name` 與後續 `filename_label` 的人類可讀來源，**用於檔名**；可填暱稱／代號，**不一定要真名**。不得使用 Project 擁有者的名字代填，也不得使用目前聊天者的名字代填；也不得因為使用者說「幫我排盤」就自動假定命主是目前聊天者。\n3. 讀取核心規範與 `runtime_info`。\n4. 讀取 `命主索引.md`；若不存在，在第一位命主建立時 materialize。\n5. 判斷這是既有 subject 或新命主。\n6. 既有 subject：沿用原 `subject_id`。新命主：由 AI 發起 `subject.create_identity`，**opaque `subject_id` 必須由 runtime 產生**，不得由命主稱呼、姓名／生日／出生地拼出或 hash PII。\n7. 保存 `subject_display_name`、`subject_short_id`、`filename_label` 至 `命主索引.md`；產生本命基礎檔案時，檔名前綴使用這次明確提供的命主稱呼所衍生的 `filename_label`。\n8. 遵守 `Precision must be earned by input`；模糊時間不得自行取中點或 default time。\n9. 取得或確認出生地解析結果；保留 provenance。\n10. exact input：呼叫 runtime 建立單一 Project 原生本命。bounded / unknown time：若 `natal.candidate_envelope` 可執行且 location/timezone basis 完整，建立 Candidate Envelope；不得自己挑一個候選。\n11. 若使用者有 Astralium、已知四柱或其他 structured external chart，保留 External view，再執行 reconciliation；External 與 Project raw views 不互相覆寫。\n12. 查看 BLOCKING conflict / partial blocked scopes。若仍有 material conflict 或唯一時辰未解，不把高精度單一盤分析當確定基礎。\n13. AI 依 deterministic facts 完成本命解讀；解讀必須標為命理推論，不得寫回盤面事實。\n14. 產生 Base Case Markdown；**Base Case 對外稱「本命基礎檔案」**，聊天中不需要介紹 canonical slot、schema 或 materialize 流程。\n15. 對每一份已建立的 `.md` 提供實際檔案，並告訴使用者加入同一個 Project。\n16. 使用者加入後，重新檢查 `命主索引.md`、Case filenames、subject_id、schema 與 `00` manifest 是否一致。\n17. **本命盤建立完成後**且 precision 允許年度校準時，標準下一步就是做**過去 10 年**的過去事件校準；**排除今年，從去年往前**取 10 個 Gregorian label years。例如 2026 年固定校準 2016～2025。\n18. 校準先 lock blind predictions，再讓使用者確認／訂正；不得先看既有事件再改題。\n19. finalize 後由 runtime／Case flow**實際產生**或更新 `05_驗證事件紀錄.md`；首次 materialize 05 時同步更新 00，並把真正變動的 `.md` 以可**下載**檔案交給使用者加入 Project。\n20. 使用者若暫時不做校準，可保留 `uncalibrated`，但後續個人化預測必須降權；不得假裝已完成校準。",
)

replace_once(
    rules,
    "完整單一本命通常需要：性別、Gregorian 出生日期、出生時間、出生地。若由 AI host／使用者提供 pre-resolved 座標與 IANA timezone，必須保存 provenance，不得冒充 runtime 自己查得。",
    "完整單一本命的盤面計算通常需要：性別、Gregorian 出生日期、出生時間、出生地。首次建立私人命盤專案時，另有一項使用者層必填資料：**命主稱呼**。因此首次建立固定收集：**命主稱呼、性別、出生年月日、出生時間、出生地**。命主稱呼**用於檔名**，可使用暱稱／代號，**不一定要真名**；不得使用 Project 擁有者的名字代填，也不得使用目前聊天者的名字代填。若由 AI host／使用者提供 pre-resolved 座標與 IANA timezone，必須保存 provenance，不得冒充 runtime 自己查得。",
)

replace_once(
    rules,
    "- 新命主由 AI 發起建立，opaque `subject_id` 必須由 runtime 產生，不得由姓名、生日、性別、出生地或其他 PII 推導。\n- `subject_display_name` 可改，`subject_id` 不變。",
    "- 新命主建立前，**命主稱呼必填**；它作為 `subject_display_name` 與 `filename_label` 的顯示來源，後續本命基礎檔案的檔名前綴由此產生。\n- 命主稱呼可填暱稱／代號，不一定要真名；不得使用 Project 擁有者的名字代填，也不得使用目前聊天者的名字代填。\n- 新命主由 AI 發起建立，opaque `subject_id` 必須由 runtime 產生，不得由命主稱呼、姓名、生日、性別、出生地或其他 PII 推導。\n- `subject_display_name` 可改，`subject_id` 不變。",
)

print("subject-name onboarding transform applied")
