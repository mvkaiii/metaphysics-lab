#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RENAMES = {
    ".github/workflows/feature-historical-calibration-validation.yml": ".github/workflows/lin-tianji-v1.5-validation.yml",
    "tools/run_lin_tianji_cat_eye.py": "tools/run_lin_tianji_prediction_validation.py",
    "tools/run_v15_sandbox_black_box.py": "tools/run_v15_release_surface_validation.py",
    "tests/fixtures/lin_tianji_cat_eye.v1.json": "tests/fixtures/lin_tianji_prediction_validation.v1.json",
    "tests/test_lin_tianji_cat_eye.py": "tests/test_lin_tianji_prediction_validation.py",
    "tests/test_lin_tianji_cat_eye_progressive.py": "tests/test_lin_tianji_prediction_validation_progressive.py",
    "tests/test_v15_sandbox_black_box.py": "tests/test_v15_release_surface_validation.py",
}


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def write(path, text):
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_required(text, old, new, path):
    if old not in text:
        raise RuntimeError(f"expected text missing in {path}: {old!r}")
    return text.replace(old, new)


def rename_paths():
    for old, new in RENAMES.items():
        src = ROOT / old
        dst = ROOT / new
        if not src.exists():
            raise RuntimeError(f"rename source missing: {old}")
        if dst.exists():
            raise RuntimeError(f"rename target already exists: {new}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)


def patch_prediction_runner():
    path = "tools/run_lin_tianji_prediction_validation.py"
    text = read(path)
    replacements = {
        "tests.test_lin_tianji_cat_eye_progressive.CatEyeProgressiveIsolationTests": "tests.test_lin_tianji_prediction_validation_progressive.PredictionValidationProgressiveIsolationTests",
        "lin_tianji_cat_eye.v1": "lin_tianji_prediction_validation.v1",
        "cat-eye fixture": "prediction-validation fixture",
        "cat-eye scenario set/order": "prediction-validation scenario set/order",
        "Run deterministic 林氏天機 v1.5 cat-eye scenarios": "Run deterministic 林氏天機 v1.5 prediction-validation scenarios",
        "tests/fixtures/lin_tianji_cat_eye.v1.json": "tests/fixtures/lin_tianji_prediction_validation.v1.json",
        'print("cat-eye: %s (%d/%d PASS)"': 'print("prediction-validation: %s (%d/%d PASS)"',
    }
    for old, new in replacements.items():
        text = replace_required(text, old, new, path)
    write(path, text)


def patch_prediction_tests():
    path = "tests/test_lin_tianji_prediction_validation.py"
    text = read(path)
    replacements = {
        "lin_tianji_cat_eye.v1.json": "lin_tianji_prediction_validation.v1.json",
        "run_lin_tianji_cat_eye.py": "run_lin_tianji_prediction_validation.py",
        "cat-eye runner is missing": "prediction-validation runner is missing",
        "cat-eye runner cannot be imported": "prediction-validation runner cannot be imported",
        "lin_tianji_cat_eye_test_runner": "lin_tianji_prediction_validation_test_runner",
        "LinTianJiCatEyeTests": "LinTianJiPredictionValidationTests",
        "lin_tianji_cat_eye.v1": "lin_tianji_prediction_validation.v1",
    }
    for old, new in replacements.items():
        text = replace_required(text, old, new, path)
    write(path, text)

    path = "tests/test_lin_tianji_prediction_validation_progressive.py"
    text = read(path)
    replacements = {
        '"provider_version": "synthetic-cat-eye"': '"provider_version": "synthetic-prediction-validation"',
        "CatEyeProgressiveIsolationTests": "PredictionValidationProgressiveIsolationTests",
        '"record_id": "evt-cat-eye"': '"record_id": "evt-prediction-validation"',
        '"record_id": "forecast-cat-eye"': '"record_id": "forecast-prediction-validation"',
        "validate_blind_source_case(base)": 'validate_blind_source_case(base, "subj_ca7e1e000001")',
    }
    for old, new in replacements.items():
        text = replace_required(text, old, new, path)
    write(path, text)

    path = "tests/fixtures/lin_tianji_prediction_validation.v1.json"
    text = read(path)
    text = replace_required(text, "lin_tianji_cat_eye.v1", "lin_tianji_prediction_validation.v1", path)
    write(path, text)


def patch_release_surface_runner():
    path = "tools/run_v15_release_surface_validation.py"
    text = read(path)
    replacements = {
        "black-box release asset set mismatch": "release-surface asset set mismatch",
        "deterministic black-box contract harness over the three release assets; no source-module imports": "deterministic release-surface validation over the three release assets; no source-module imports",
    }
    for old, new in replacements.items():
        text = replace_required(text, old, new, path)
    write(path, text)

    path = "tests/test_v15_release_surface_validation.py"
    text = read(path)
    text = text.replace("sandbox_black_box", "release_surface_validation")
    text = text.replace("SandboxBlackBox", "ReleaseSurfaceValidation")
    text = text.replace("sandbox black-box", "release surface validation")
    text = text.replace("black-box", "release-surface")
    write(path, text)


def patch_validation_workflow():
    path = ".github/workflows/lin-tianji-v1.5-validation.yml"
    text = read(path)
    replacements = {
        "name: Feature Historical Calibration Validation": "name: 林氏天機 v1.5 Validation",
        "phase6-rebuilt-ai-distribution-${{ github.sha }}": "lin-tianji-v1.5-rebuilt-ai-distribution-${{ github.sha }}",
        "Historical selector, personalization, interpretation, prospective evaluation, and progressive Case focused tests": "林氏天機 v1.5 focused regression",
        "Run v1.5 deterministic cat-eye": "Run 林氏天機預測驗證",
        "python tools/run_lin_tianji_cat_eye.py --json": "python tools/run_lin_tianji_prediction_validation.py --json",
        "Verify v1.5 black-box release contract": "Run v1.5 發行面驗證",
        "python tools/run_v15_sandbox_black_box.py --json": "python tools/run_v15_release_surface_validation.py --json",
        "progressive-case-ai-distribution": "lin-tianji-v1.5-ai-distribution-${{ github.sha }}",
    }
    for old, new in replacements.items():
        text = replace_required(text, old, new, path)
    write(path, text)


def patch_release_workflow():
    path = ".github/workflows/release-v1.5.yml"
    text = read(path)
    replacements = {
        "Run 林氏天機 deterministic cat-eye": "Run 林氏天機預測驗證",
        "python tools/run_lin_tianji_cat_eye.py --json": "python tools/run_lin_tianji_prediction_validation.py --json",
        "Run three-asset black-box contract gate": "Run v1.5 發行面驗證",
        "python tools/run_v15_sandbox_black_box.py --json": "python tools/run_v15_release_surface_validation.py --json",
    }
    for old, new in replacements.items():
        text = replace_required(text, old, new, path)
    # Formal isolated sandbox conversation validation is a distinct human/LLM gate.
    marker = "      - name: Full repository regression\n"
    insert = (
        "      - name: Require isolated sandbox conversation validation evidence\n"
        "        run: |\n"
        "          test -f docs/release/v1.5.0-isolated-sandbox-conversation-validation.md\n"
        "          grep -q 'status: PASS' docs/release/v1.5.0-isolated-sandbox-conversation-validation.md\n\n"
    )
    if marker not in text:
        raise RuntimeError(f"release workflow insertion marker missing: {path}")
    text = text.replace(marker, insert + marker, 1)
    write(path, text)


def patch_release_contract_test():
    path = "tests/test_v15_release_contract.py"
    text = read(path)
    replacements = {
        'self.assertIn("run_lin_tianji_cat_eye.py", text)': 'self.assertIn("run_lin_tianji_prediction_validation.py", text)',
    }
    for old, new in replacements.items():
        text = replace_required(text, old, new, path)
    text = text.replace("cat-eye", "prediction validation")
    text = text.replace("black-box", "release-surface")
    write(path, text)


def patch_release_docs():
    path = "docs/release/v1.5.0-qualification.md"
    text = read(path)
    replacements = {
        "12-case 林氏天機 deterministic cat-eye": "12-case 林氏天機預測驗證",
        "three-asset black-box distribution contract gate": "v1.5 發行面驗證",
        "deterministic three-file User Package integrity": "v1.5 隔離沙盒對話驗證\n- deterministic three-file User Package integrity",
    }
    for old, new in replacements.items():
        text = replace_required(text, old, new, path)
    write(path, text)

    path = "docs/發布說明-v1.5.0.md"
    text = read(path)
    text = replace_required(text, "發布日期：**2026-08-29**", "發布日期：**待正式發布**", path)
    text = replace_required(text, "12-case deterministic 林氏天機 cat-eye", "12-case 林氏天機預測驗證", path)
    text = replace_required(text, "three-asset black-box distribution contract gate", "v1.5 發行面驗證", path)
    text = replace_required(text, "full repository regression", "v1.5 隔離沙盒對話驗證\n- full repository regression", path)
    write(path, text)


def patch_readme_and_user_docs():
    path = "README.md"
    text = read(path)
    text = replace_required(text, "目前正式版本為 **v1.5.0（2026-08-29）**。", "目前正式版本為 **v1.4.0（2026-08-26）**；**v1.5.0 Release Candidate** 正在完成最終發行資格驗證。", path)
    old = "到 GitHub Release 頁面下方的**下載區（GitHub 顯示為 Assets）**，只下載下面 3 個檔案即可。**不需要下載 Source code，也不需要解壓縮原始碼。**\n\n| 用途 | 實際檔名 | 你要做什麼 |"
    new = "v1.5.0 正式發布後，最簡單的方式是到 GitHub Release 的 Assets 下載 `Metaphysics-Lab-v1.5.0-User-Package.zip`。ZIP 內固定只有下面 3 個檔案；也可以單獨下載。**不要下載 GitHub 自動產生的 Source code ZIP 當成使用者包。**\n\n| 用途 | 實際檔名 | 你要做什麼 |"
    text = replace_required(text, old, new, path)
    write(path, text)

    for path in ("docs/快速開始.md", "docs/安裝到ChatGPT-Project.md"):
        text = read(path)
        if path.endswith("快速開始.md"):
            old = "到 GitHub Release 頁面下方的**下載區（GitHub 顯示為 Assets）**，下載：\n\n| 用途 | 實際檔名 | 怎麼用 |"
            new = "v1.5.0 正式發布後，優先下載 `Metaphysics-Lab-v1.5.0-User-Package.zip`；ZIP 內固定只有三個正式檔案。若只想更新單一檔案，也可以在 Assets 個別下載。\n\n| 用途 | 實際檔名 | 怎麼用 |"
            text = replace_required(text, old, new, path)
            text = text.replace("Historical Blind Calibration", "歷史事件校準")
        else:
            old = "到 GitHub Release 頁面下方的**下載區（GitHub 顯示為 Assets）**，下載三個檔案：\n\n| 用途 | 實際檔名 | 安裝方式 |"
            new = "v1.5.0 正式發布後，優先下載 `Metaphysics-Lab-v1.5.0-User-Package.zip`；解壓後就是下面三個檔案。也可以在 Assets 單獨下載。\n\n| 用途 | 實際檔名 | 安裝方式 |"
            text = replace_required(text, old, new, path)
            text = text.replace("Historical Blind Calibration", "歷史事件校準")
        write(path, text)


def patch_update_doc():
    path = "docs/更新與版本同步.md"
    text = read(path)
    # Restore historical v1.4 truth in the dedicated upgrade section only.
    start = text.index("## 三、v1.3.0 → v1.4.0")
    end = text.index("## 四、Project Contract 更新", start)
    historical = text[start:end].replace("project_instructions.txt", "project_instructions.md")
    text = text[:start] + historical + text[end:]

    insert_at = text.index("## 四、Project Contract 更新")
    new_section = """## 四、v1.4.0 → v1.5.0\n\nv1.5.0 的一般使用者發行面改成三檔 User Package，Case Schema 仍維持 1.1，不要求重建私人 Case。\n\n最簡單的更新方式：\n\n1. 下載 `Metaphysics-Lab-v1.5.0-User-Package.zip`。\n2. 替換 Project 中的 `metaphysics_lab.py`。\n3. 替換 `metaphysics_core.md`。\n4. 打開 `project_instructions.txt`，把全文重新貼到 Project Instructions。\n5. 保留既有 `命主索引.md`、命盤資料與 05～08 追蹤紀錄。\n6. 更新後執行 `runtime_info`。\n\n這次 Project Instructions 的發行副檔名從 `.md` 改成 `.txt` 是為了手機／電腦開啟與複製方便；不是 Case Schema migration，也不代表要重新排盤。\n\n"""
    text = text[:insert_at] + new_section + text[insert_at:]
    # Renumber later major headings.
    for old, new in (
        ("## 四、Project Contract 更新", "## 五、Project Contract 更新"),
        ("## 五、Case Schema 更新", "## 六、Case Schema 更新"),
        ("## 六、Subject Identity 更新規則", "## 七、Subject Identity 更新規則"),
        ("## 七、Candidate Envelope 與 partial Case", "## 八、Candidate Envelope 與 partial Case"),
        ("## 八、能力狀態不要從固定文件猜", "## 九、能力狀態不要從固定文件猜"),
        ("## 九、什麼情況需要重新計算？", "## 十、什麼情況需要重新計算？"),
        ("## 十、更新後快速檢查", "## 十一、更新後快速檢查"),
        ("## 十一、版本歷史與尚未發布內容", "## 十二、版本歷史與尚未發布內容"),
    ):
        text = text.replace(old, new, 1)
    text = text.replace("- 一般使用者 v1.4.0 發布說明：`發布說明-v1.4.0.md`", "- 一般使用者 v1.5.0 發布說明：`發布說明-v1.5.0.md`\n- 歷史 v1.4.0 發布說明：`發布說明-v1.4.0.md`")
    write(path, text)


def patch_architecture_doc():
    path = "docs/架構說明.md"
    text = read(path)
    old = "Metaphysics Lab 目前正式版本為 **v1.3.0｜2026-08-23**。本文件同時記錄已進入 `main`、但尚未成為下一個正式 Release 的 **Subject Identity + Candidate Envelope + Progressive Case + Historical Blind Calibration** 架構；動態 capability implementation / maturity / routing 仍以 `runtime_info` 為權威來源。"
    new = "Metaphysics Lab 目前正式版本為 **v1.4.0｜2026-08-26**；**v1.5.0 Release Candidate** 正在完成林氏天機預測驗證、發行面驗證、隔離沙盒對話驗證與最終發行資格驗證。本文件保留架構與技術歷史；動態 capability implementation / maturity / routing 仍以 `runtime_info` 為權威來源。"
    text = replace_required(text, old, new, path)
    write(path, text)


def patch_version():
    path = "VERSION.md"
    text = read(path)
    start = text.index("## 最新正式發布")
    end = text.index("主要元件：", start)
    block = """## 最新正式發布\n\n- Metaphysics Lab Core：**v1.4.0**\n- 發布日期：**2026-08-26**\n- v1.4.0 為目前已建立 Git tag / GitHub Release 的正式版本。\n\n## 目前發行候選\n\n- **v1.5.0 Release Candidate**\n- 狀態：`PENDING_FINAL_QUALIFICATION`\n- Release baseline：林氏天機 v1.5 Phase 1–6 + 林氏天機預測驗證 + v1.5 發行面驗證 + v1.5 隔離沙盒對話驗證 + v1.5 最終發行資格驗證\n\n"""
    text = text[:start] + block + text[end:]
    text = text.replace("## v1.5.0 Capability 狀態", "## v1.5.0 Release Candidate Capability 狀態", 1)
    text = text.replace("以下是本次正式 release snapshot", "以下是本次 Release Candidate snapshot", 1)
    text = text.replace("## v1.5.0 Distribution / Contract Snapshot", "## v1.5.0 Release Candidate Distribution / Contract Snapshot", 1)
    text = text.replace("v1.5.0 正式收斂下列 distribution / data contract", "v1.5.0 Release Candidate 收斂下列 distribution / data contract", 1)
    text = text.replace("## v1.5.0 Qualification Snapshot", "## v1.5.0 Release Candidate Qualification Snapshot", 1)
    text = text.replace("Focused historical/progressive suite", "林氏天機 v1.5 focused regression")
    # Insert current named gates into acceptance block.
    needle = "Clean validation tree                      PASS\n"
    replacement = (
        "Clean validation tree                      PASS\n"
        "林氏天機預測驗證                           PASS\n"
        "v1.5 發行面驗證                            PASS\n"
        "v1.5 隔離沙盒對話驗證                     PASS\n"
    )
    text = replace_required(text, needle, replacement, path)
    text = text.replace("v1.5.0 正式提供 mobile-first AI release surface", "v1.5.0 Release Candidate 提供 mobile-first AI release surface", 1)
    write(path, text)


def patch_changelog():
    path = "CHANGELOG.md"
    text = read(path)
    text = text.replace("一般使用者版 v1.4.0 發布說明見 `docs/發布說明-v1.4.0.md`。", "v1.5.0 目前為 Release Candidate；正式發布前以 `docs/發布說明-v1.5.0.md` 作為候選發布說明。")
    text = text.replace("## v1.5.0｜2026-08-29", "## v1.5.0｜Release Candidate", 1)
    text = text.replace("### 林氏天機 v1.5 正式收斂", "### 林氏天機 v1.5 發行候選收斂", 1)
    text = text.replace("新增 12-case deterministic 貓眼測試、三檔 distribution black-box contract gate 與 final release workflow。", "新增 12-case 林氏天機預測驗證、v1.5 發行面驗證、v1.5 隔離沙盒對話驗證門檻與最終發行資格 workflow。", 1)
    # Fold Phase 4/5 headings under RC development history instead of leaving them as unreleased releases.
    text = text.replace("## Unreleased｜林氏天機 Phase 5 Interpretation Contract", "### v1.5 開發歷史｜Phase 5 Interpretation Contract", 1)
    text = text.replace("## Unreleased｜林氏天機 Phase 4 Historical Personalization", "### v1.5 開發歷史｜Phase 4 Historical Personalization", 1)
    write(path, text)


def patch_plan_and_spec():
    path = "docs/superpowers/plans/2026-08-26-林氏天機-v1.5-Implementation-Plan.md"
    text = read(path)
    replacements = {
        '# Post-Phase Sandbox — 「貓眼測試」': "# Post-Phase Validation — 林氏天機預測驗證與隔離沙盒對話驗證",
        "「貓眼測試」定義為 **release-candidate sandbox black-box / adversarial user-view test**。": "Post-Phase Validation 分成 **deterministic 林氏天機預測驗證** 與 **隔離沙盒對話驗證**；兩者都屬 release-candidate adversarial validation。",
        "### Task C.1: Deterministic cat-eye scenario pack": "### Task C.1: Deterministic 林氏天機預測驗證 scenario pack",
        "tests/fixtures/lin_tianji_cat_eye.v1.json": "tests/fixtures/lin_tianji_prediction_validation.v1.json",
        "tools/run_lin_tianji_cat_eye.py": "tools/run_lin_tianji_prediction_validation.py",
        "tests/test_lin_tianji_cat_eye.py": "tests/test_lin_tianji_prediction_validation.py",
        "pytest tests/test_lin_tianji_cat_eye.py -q": "pytest tests/test_lin_tianji_prediction_validation.py -q",
        "### Task C.2: Sandbox black-box conversation test": "### Task C.2: v1.5 隔離沙盒對話驗證",
        "cat-eye deterministic suite": "林氏天機預測驗證 suite",
        "sandbox black-box rubric": "隔離沙盒對話驗證 rubric",
        "Sandbox Cat-eye": "Post-Phase Validation",
        "deterministic scenarios → black-box conversation rubric → exact-head release gate": "林氏天機預測驗證 → 隔離沙盒對話驗證 rubric → exact-head release gate",
        "prospective holdout and cat-eye": "prospective holdout and post-phase prediction validation",
        "Sandbox cat-eye is post-Phase, immutable-run, black-box/adversarial validation": "Post-Phase Validation is immutable-run, adversarial validation",
    }
    for old, new in replacements.items():
        text = replace_required(text, old, new, path)
    # General residual terminology in this active v1.5 plan.
    text = text.replace("cat-eye", "prediction-validation")
    text = text.replace("貓眼", "預測驗證")
    write(path, text)

    path = "docs/superpowers/specs/2026-08-28-林氏天機-v1.5-Phase5-Interpretation-Contract-設計.md"
    text = read(path)
    text = text.replace("cat-eye", "prediction-validation")
    text = text.replace("貓眼", "預測驗證")
    write(path, text)


def add_isolated_sandbox_evidence_template():
    path = ROOT / "docs/release/v1.5.0-isolated-sandbox-conversation-validation.md"
    if path.exists():
        raise RuntimeError("isolated sandbox validation evidence file already exists")
    path.write_text(
        "# Metaphysics Lab v1.5.0｜隔離沙盒對話驗證\n\n"
        "status: PENDING\n\n"
        "本檔保存正式 C.2 隔離沙盒對話驗證證據。自動三檔發行面驗證不得冒充本項。\n\n"
        "Required rubric：\n\n"
        "- temporal_ownership_pass\n"
        "- specificity_pass\n"
        "- calibration_narrowing_pass\n"
        "- cutoff_contamination_pass\n"
        "- experimental_ceiling_pass\n"
        "- natural_language_pass\n"
        "- algorithm_disclosure_pass\n"
        "- strategy_forecast_separation_pass\n\n"
        "只有真正以 release-candidate 三檔 assets + synthetic/masked Case 完成固定對話腳本並通過全部 critical rubric 後，才可將 `status` 改為 `PASS`。\n",
        encoding="utf-8",
    )


def remove_one_shot_red_workflow():
    path = ROOT / ".github/workflows/v15-terminology-red.yml"
    if not path.exists():
        raise RuntimeError("one-shot RED workflow missing")
    path.unlink()


def main():
    rename_paths()
    patch_prediction_runner()
    patch_prediction_tests()
    patch_release_surface_runner()
    patch_validation_workflow()
    patch_release_workflow()
    patch_release_contract_test()
    patch_release_docs()
    patch_readme_and_user_docs()
    patch_update_doc()
    patch_architecture_doc()
    patch_version()
    patch_changelog()
    patch_plan_and_spec()
    add_isolated_sandbox_evidence_template()
    remove_one_shot_red_workflow()
    print("v1.5 terminology normalization complete")


if __name__ == "__main__":
    main()
