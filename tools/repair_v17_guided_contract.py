from pathlib import Path


path = Path("core/核心提示詞.md")
text = path.read_text(encoding="utf-8")

old = (
    "BLOCKED 狀態下只提供解除 blocking conflict 的 recovery guidance；不得列出『衝突解除後可以問』的一般命理問題清單。\n"
    "建議問題的文字本身也不得超過 specificity ceiling；不得把 event_family 改寫成升職、加薪或其他 event_form 故事。\n"
)
new = (
    "BLOCKED 時只提供解除衝突的 recovery guidance，不列一般命理問題。"
    "建議文字不得超過 specificity ceiling，不得把 event_family 改寫成升職、加薪或其他 event_form。"
    "Guided Inquiry 應主動顯示，預設 3 個；不得在盲判前用驗證事件產生建議；使用者可以直接自由輸入、不必選建議。\n"
)
if text.count(old) != 1:
    raise SystemExit("guided contract anchor mismatch")
text = text.replace(old, new, 1)

old2 = "使用者不是在讀 AI 報告。預設先把盤面訊號翻成現實中可能發生的事情，再視解讀偏好補命理原因。"
new2 = "預設先把盤面訊號翻成現實情境，再依偏好補命理原因。"
if text.count(old2) != 1:
    raise SystemExit("safe compression anchor mismatch")
text = text.replace(old2, new2, 1)

required = (
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
