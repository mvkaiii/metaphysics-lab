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
    "1. 先確認首次建立的 5 項必填資料：**命主稱呼、性別、出生年月日、出生時間、出生地**；只追問缺少欄位。命主稱呼**用於檔名**，可填暱稱／代號，**不一定要真名**；不得使用 Project 擁有者或目前聊天者的名字代填。",
)

replace_once(
    workflow,
    "1. 讀取核心規範與 `runtime_info`。\n2. 讀取 `命主索引.md`；若不存在，在第一位命主建立時 materialize。\n3. 判斷這是既有 subject 或新命主。\n4. 既有 subject：沿用原 `subject_id`。新命主：由 AI 發起 `subject.create_identity`，**opaque `subject_id` 必須由 runtime 產生**，不得由姓名／生日／出生地拼出或 hash PII。\n5. 保存 `subject_display_name`、`subject_short_id`、`filename_label` 至 `命主索引.md`。\n6. 檢查 natal 所需輸入；只詢問缺少欄位，不重問已知資料。",
    "1. 先確認首次建立的 5 項必填資料：**命主稱呼、性別、出生年月日、出生時間、出生地**；只詢問缺少欄位，不重問已知資料。\n2. **命主稱呼必填**，作為 `subject_display_name` 與後續 `filename_label` 的人類可讀來源，**用於檔名**；可填暱稱／代號，**不一定要真名**。不得使用 Project 擁有者或目前聊天者的名字代填，也不得因為使用者說「幫我排盤」就自動假定命主是目前聊天者。\n3. 讀取核心規範與 `runtime_info`。\n4. 讀取 `命主索引.md`；若不存在，在第一位命主建立時 materialize。\n5. 判斷這是既有 subject 或新命主。\n6. 既有 subject：沿用原 `subject_id`。新命主：由 AI 發起 `subject.create_identity`，**opaque `subject_id` 必須由 runtime 產生**，不得由命主稱呼、姓名／生日／出生地拼出或 hash PII。\n7. 保存 `subject_display_name`、`subject_short_id`、`filename_label` 至 `命主索引.md`；產生本命基礎檔案時，檔名前綴使用這次明確提供的命主稱呼所衍生的 `filename_label`。",
)

replace_once(
    rules,
    "完整單一本命通常需要：性別、Gregorian 出生日期、出生時間、出生地。若由 AI host／使用者提供 pre-resolved 座標與 IANA timezone，必須保存 provenance，不得冒充 runtime 自己查得。",
    "完整單一本命的盤面計算通常需要：性別、Gregorian 出生日期、出生時間、出生地。首次建立私人命盤專案時，另有一項使用者層必填資料：**命主稱呼**。因此首次建立固定收集：**命主稱呼、性別、出生年月日、出生時間、出生地**。命主稱呼**用於檔名**，可使用暱稱／代號，**不一定要真名**；不得使用 Project 擁有者或目前聊天者的名字代填。若由 AI host／使用者提供 pre-resolved 座標與 IANA timezone，必須保存 provenance，不得冒充 runtime 自己查得。",
)

replace_once(
    rules,
    "- 新命主由 AI 發起建立，opaque `subject_id` 必須由 runtime 產生，不得由姓名、生日、性別、出生地或其他 PII 推導。\n- `subject_display_name` 可改，`subject_id` 不變。",
    "- 新命主建立前，**命主稱呼必填**；它作為 `subject_display_name` 與 `filename_label` 的顯示來源，後續本命基礎檔案的檔名前綴由此產生。\n- 命主稱呼可填暱稱／代號，不一定要真名；不得使用 Project 擁有者或目前聊天者的名字代填。\n- 新命主由 AI 發起建立，opaque `subject_id` 必須由 runtime 產生，不得由命主稱呼、姓名、生日、性別、出生地或其他 PII 推導。\n- `subject_display_name` 可改，`subject_id` 不變。",
)

print("subject-name onboarding transform applied")
