from pathlib import Path


def replace_version_constants() -> None:
    path = Path("engine/distribution/constants.py")
    text = path.read_text(encoding="utf-8")
    assert 'RUNTIME_SCHEMA_VERSION = "1.1"' in text
    assert 'CASE_SCHEMA_VERSION = "1.1"' in text

    old_project = 'PROJECT_CONTRACT_VERSION = "1.1"'
    new_project = 'PROJECT_CONTRACT_VERSION = "1.2"'
    if new_project not in text:
        assert text.count(old_project) == 1
        text = text.replace(old_project, new_project, 1)

    old_runtime = 'DISTRIBUTION_RUNTIME_VERSION = "1.1-exp"'
    new_runtime = 'DISTRIBUTION_RUNTIME_VERSION = "1.2-exp"'
    if new_runtime not in text:
        assert text.count(old_runtime) == 1
        text = text.replace(old_runtime, new_runtime, 1)

    path.write_text(text, encoding="utf-8")


def update_version_doc() -> None:
    path = Path("VERSION.md")
    text = path.read_text(encoding="utf-8")
    heading = "## v1.7.0 Release Contract｜整合候選"
    if heading in text:
        return

    marker = "## 最新正式發布\n"
    assert text.count(marker) == 1
    section = """## v1.7.0 Release Contract｜整合候選

v1.7.0 定位為**可靠性與可用性版本**。此區塊描述目前整合候選的版本契約；在正式 Git tag / GitHub Release 建立前，`v1.6.0` 仍是最新正式發布。發布日期不在 implementation 階段預填，而是在正式 Release 執行時依 Asia/Taipei 當地日期確定。

```text
Project Contract          1.2
Runtime Schema            1.1
Case Schema               1.1
AI Distribution Runtime   1.2-exp
Capability Manifest       1.0
```

- **Case Schema 1.1 維持不變**；既有 Case 不需要破壞性重建，也不需要 schema migration。
- Historical Activation **selector v1** 與 Interpretation Contract **interpretation v1** 繼續作為正式 default；v1.7 發布本身不構成 v2 promotion。
- **Guided Inquiry** 是建議式導覽與追問導航，**不是新的命理證據**，不得提高既有盤面或 capability 的 specificity / confidence authority。
- Capability Manifest、Case Doctor、Prospective Validation 2.0 與 Guided Inquiry 的加入不會自動提升任何 Experimental capability maturity。

---

"""
    path.write_text(text.replace(marker, section + marker, 1), encoding="utf-8")


def update_changelog() -> None:
    path = Path("CHANGELOG.md")
    text = path.read_text(encoding="utf-8")
    heading = "## v1.7.0｜發行日期於正式 Release 執行時確定"
    if heading in text:
        return

    marker = "## v1.6.0｜2026-09-05\n"
    assert text.count(marker) == 1
    section = """## v1.7.0｜發行日期於正式 Release 執行時確定

### 可靠性與可用性整合候選

- 新增 Capability Manifest 1.0，讓 runtime capability 的 implementation、maturity、routing 與版本資訊有單一可驗證來源。
- 新增 Case Doctor + Legacy Reconciliation，以唯讀診斷與明確 reconciliation plan 處理 legacy / duplicate / subject-integrity 問題；不自動刪除或合併使用者檔案。
- 新增 Prospective Validation 2.0，將 clean prospective、conditional / known context、hidden existing reality 與 retrospective calibration 分開；只有合格且已裁決的 clean records 可進 clean denominator。
- 新增 Guided Inquiry，預設提供 3 個、必要時 4 個建議方向；它只做對話導航，不讀取盲判前禁止的驗證事件，且**不是新的命理證據**。
- Project Contract 升為 1.2；Runtime Schema 與 **Case Schema 1.1** 維持不變。既有 Case **不需要破壞性重建**或 schema migration。
- Historical Activation **selector v1** 與 Interpretation Contract **interpretation v1** 仍是 default；本 release 不包含 v2 promotion，也不因發版提升 Experimental capability maturity。
- AI Distribution Runtime 目標版本為 1.2-exp；正式發布日期、release candidate SHA、User Package digest 與 sandbox evidence 只在正式 Release gate 完成後記錄，不在 implementation 階段預填。

"""
    path.write_text(text.replace(marker, section + marker, 1), encoding="utf-8")


def main() -> None:
    replace_version_constants()
    update_version_doc()
    update_changelog()


if __name__ == "__main__":
    main()
