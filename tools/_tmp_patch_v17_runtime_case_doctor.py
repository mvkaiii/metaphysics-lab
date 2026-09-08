from pathlib import Path


path = Path("engine/distribution/runtime.py")
text = path.read_text(encoding="utf-8")
old = '''        if action in ("validate_case", "migrate_case", "update_case_record"):
            from .case_pack import migrate_case, update_case_record, validate_case
            handler = {"validate_case": validate_case, "migrate_case": migrate_case, "update_case_record": update_case_record}[action]
            return _ok(action, handler(request))
'''
new = '''        if action in ("diagnose_case", "plan_case_reconciliation"):
            from .case_doctor import diagnose_case, plan_case_reconciliation
            handler = {
                "diagnose_case": diagnose_case,
                "plan_case_reconciliation": plan_case_reconciliation,
            }[action]
            return _ok(action, handler(request))
''' + old
if 'if action in ("diagnose_case", "plan_case_reconciliation"):' not in text:
    if old not in text:
        raise SystemExit("Case runtime dispatch marker not found")
    text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
