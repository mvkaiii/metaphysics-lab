from pathlib import Path


path = Path("core/核心提示詞.md")
text = path.read_text(encoding="utf-8")

old = (
    "BLOCKED 狀態下只提供解除 blocking conflict 的 recovery guidance；不得列出『衝突解除後可以問』的一般命理問題清單。\n"
    "建議問題的文字本身也不得超過 specificity ceiling；不得把 event_family 改寫成升職、加薪或其他 event_form 故事。\n"
)
new = (
    "BLOCKED 狀態下只提供解除 blocking conflict 的 recovery guidance；不得列出『衝突解除後可以問』的一般命理問題清單。\n"
    "建議問題的文字本身也不得超過 specificity ceiling；不得把 event_family 改寫成升職、加薪或其他 event_form 故事。\n"
    "Guided Inquiry 應主動顯示，預設 3 個；不得在盲判前用驗證事件產生建議；使用者可以直接自由輸入、不必選建議。\n"
)
if text.count(old) != 1:
    raise SystemExit("guided contract anchor mismatch")
text = text.replace(old, new, 1)

replacements = (
    (
        "使用者不是在讀 AI 報告。預設先把盤面訊號翻成現實中可能發生的事情，再視解讀偏好補命理原因。",
        "預設把盤面訊號翻成現實情境，依偏好補命理原因。",
    ),
    (
        "External / Project raw views 不互相覆寫，Resolved 也不得把 CONFLICT 改寫成 MATCH。對使用者聊天時預設不用這些工程名詞，改說「外部命盤」「本次系統推算」「校對後採用結果」「命盤校對」；只有問題本身是在做 runtime 除錯、schema 驗證、程式整合或開發稽核等真正的技術工作，而且使用者明確要求技術檢查時，才展開必要的原始術語。",
        "External / Project raw views 不互相覆寫，Resolved 不得把 CONFLICT 改寫成 MATCH。一般對話說「外部命盤」「本次系統推算」「校對後採用結果」「命盤校對」；只有做 runtime 除錯、schema 驗證、程式整合或開發稽核且明確要求技術檢查時，才展開術語。",
    ),
)
for old_text, new_text in replacements:
    if text.count(old_text) != 1:
        raise SystemExit("safe compression anchor mismatch")
    text = text.replace(old_text, new_text, 1)

required = (
    "BLOCKED 狀態下只提供解除 blocking conflict 的 recovery guidance；不得列出『衝突解除後可以問』的一般命理問題清單。",
    "建議問題的文字本身也不得超過 specificity ceiling；不得把 event_family 改寫成升職、加薪或其他 event_form 故事。",
    "主動顯示",
    "預設 3 個",
    "不得在盲判前用驗證事件產生建議",
    "使用者可以直接自由輸入、不必選建議",
)
for phrase in required:
    if phrase not in text:
        raise SystemExit("required phrase missing: " + phrase)
if len(text) > 8000:
    raise SystemExit("project instructions exceed 8000 chars: %d" % len(text))

path.write_text(text, encoding="utf-8")
print("project instructions chars:", len(text))
