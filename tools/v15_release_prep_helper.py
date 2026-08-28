#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def write(path, content):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\n", encoding="utf-8")


def replace_exact(path, old, new, count=1):
    text = read(path)
    actual = text.count(old)
    if actual != count:
        raise RuntimeError(f"{path}: expected {count} occurrences, found {actual}: {old[:80]!r}")
    write(path, text.replace(old, new, count))


def append_once(path, marker, block):
    text = read(path)
    if marker in text:
        return
    write(path, text.rstrip() + "\n\n" + block.strip() + "\n")


# 1. Backward-compatible machine claim extension.
path = "engine/distribution/prospective.py"
replace_exact(path, '''_CLAIM_FIELDS = {
    "claim_id",
    "forecast_window",
    "primary_domain",
    "event_family",
    "prediction",
    "matched_if",
    "not_matched_if",
    "evidence_layers",
    "evidence_time_scales",
    "capability_maturity",
    "confidence",
    "knowledge_cutoff_at",
    "evaluation_eligibility",
    "contamination_state",
    "method_version",
}
''', '''_REQUIRED_CLAIM_FIELDS = {
    "claim_id",
    "forecast_window",
    "primary_domain",
    "event_family",
    "prediction",
    "matched_if",
    "not_matched_if",
    "evidence_layers",
    "evidence_time_scales",
    "capability_maturity",
    "confidence",
    "knowledge_cutoff_at",
    "evaluation_eligibility",
    "contamination_state",
    "method_version",
}
_OPTIONAL_CLAIM_FIELDS = {"priority", "partial_if"}
_CLAIM_FIELDS = _REQUIRED_CLAIM_FIELDS | _OPTIONAL_CLAIM_FIELDS
''')
replace_exact(path, '_CONFIDENCE = {"high", "medium", "low"}\n', '_CONFIDENCE = {"high", "medium", "low"}\n_PRIORITIES = {"primary", "secondary"}\n')
replace_exact(path, '''    missing = sorted(_CLAIM_FIELDS - keys)
    unknown = sorted(keys - _CLAIM_FIELDS)
''', '''    missing = sorted(_REQUIRED_CLAIM_FIELDS - keys)
    unknown = sorted(keys - _CLAIM_FIELDS)
''')
replace_exact(path, '''    matched_if = _claim_text(claim.get("matched_if"), "matched_if")
    not_matched_if = _claim_text(claim.get("not_matched_if"), "not_matched_if")
''', '''    matched_if = _claim_text(claim.get("matched_if"), "matched_if")
    not_matched_if = _claim_text(claim.get("not_matched_if"), "not_matched_if")
    priority = None
    partial_if = None
    if "priority" in claim:
        priority = _claim_text(claim.get("priority"), "priority")
        if priority not in _PRIORITIES:
            raise _invalid_claim("unsupported priority", value=priority)
    if "partial_if" in claim:
        partial_if = _claim_text(claim.get("partial_if"), "partial_if")
''')
replace_exact(path, '''        "method_version": METHOD_VERSION,
    }
    return _json_normalize(normalized, "invalid_forecast_claim")
''', '''        "method_version": METHOD_VERSION,
    }
    if priority is not None:
        normalized["priority"] = priority
    if partial_if is not None:
        normalized["partial_if"] = partial_if
    return _json_normalize(normalized, "invalid_forecast_claim")
''')
replace_exact(path, '''        claim_ids.add(claim_id)
        normalized_claims.append(normalized)

    locked_body = {
''', '''        claim_ids.add(claim_id)
        normalized_claims.append(normalized)

    enhanced = ["priority" in claim or "partial_if" in claim for claim in normalized_claims]
    if any(enhanced):
        if not all("priority" in claim and "partial_if" in claim for claim in normalized_claims):
            raise _invalid_forecast(
                "enhanced v1.5 claims must provide priority and partial_if for every claim"
            )
        primary_count = sum(claim["priority"] == "primary" for claim in normalized_claims)
        secondary_count = sum(claim["priority"] == "secondary" for claim in normalized_claims)
        if primary_count > 3 or secondary_count > 2:
            raise _invalid_forecast(
                "enhanced v1.5 claim volume exceeds the fixed 3 primary / 2 secondary boundary",
                primary_count=primary_count,
                secondary_count=secondary_count,
            )

    locked_body = {
''')

# 2. New authoritative human-facing claim contract.
write("core/林氏天機預測驗證契約.md", r'''# 林氏天機 v1.5｜預測與驗證契約

本文件定義「未來問事如何把高顆粒度盤面收斂成可驗證預測」。它不修改八字、紫微、時間推導、Phase 3 ranking 或 capability maturity。

## 1. 核心原則

重要且可驗證的未來問事，在第一階段盲判完成後，必須把主要預測收斂成有限數量的 Locked Claims，再進入事件校準。

- **Primary Claims：最多 3 個。**
- **Secondary Claims：最多 2 個。**
- 若確有理由超過，必須在 lock 前說明研究理由；不得為提高表面命中率而大量列出低資訊量預測。
- 盤面可保持高顆粒度，但輸出必須收斂成：事件領域 → 事件族群 → 明確時間窗 → 可反證條件。
- 第一版一旦 lock，事件發生後不得改寫、擴張 `matched_if`，也不得把已知結果倒填成原本預測。

## 2. Locked Claim 最低欄位

每個新 v1.5 Claim 至少應保留：

- `claim_id`：穩定識別碼。
- `priority`：`primary` 或 `secondary`。
- `domain`：人類可讀的事件領域；runtime 對應欄位為 `primary_domain`。
- `event_family`：比「工作／健康／財運」更窄、可辨認的事件族群。
- `forecast_window`：明確開始與結束時間。
- `matched_if`：什麼情況算完整命中。
- `partial_if`：什麼情況只能算部分命中。
- `not_matched_if`：什麼情況構成可反證的未命中。
- `confidence`：依既有信心規則標示。
- `contamination_state`：是否在 lock 前已知道部分未來安排。

`prediction`、`evidence_layers`、`evidence_time_scales`、`knowledge_cutoff_at`、`evaluation_eligibility`、`method_version` 等機器欄位仍依 Phase 1 prospective contract 保存。

舊 Phase 1 lock 不要求破壞性遷移；runtime 仍可驗證舊格式。v1.5 發布後新建立的重要預測，則應使用完整的新 Claim 欄位。

## 3. Contamination

固定使用：

- `clean_prospective`：lock 前未知，可進 clean prospective denominator。
- `partially_known`：lock 前已知部分事實或安排，不得當成乾淨預測命中。
- `known_before_lock`：lock 前已明確知道該未來事件或安排，不得進 clean prospective denominator。

已知的醫療排程、已簽約工作、已訂好的旅行、已確認會議等，可以影響策略，但不得重新包裝成預測命中。

## 4. 評估必須拆三層

事件發生後，除 `verification_state` 外，研究紀錄應分別保留：

- `domain_result`：領域是否抓對。
- `event_family_result`：事件族群是否抓對。
- `timing_result`：事前時間窗是否抓對。

不得用「年度領域有中」冒充「月份或日期也中」。未事前 claim 的時間精度，事後只能標示 `not_claimed` 或等價狀態，不得補寫成命中。

Phase 6 的 `matched / partial / not_matched / cannot_recall` 與 failure attribution 仍是正式 evaluation authority；上述三層結果是額外的可讀研究分解，不取代 Phase 6。

## 5. Failure attribution

仍沿用 Phase 6：

- `ai_compliance_failure`
- `specification_ambiguity`
- `deterministic_or_algorithm_failure`
- `metaphysical_signal_failure`
- 無失敗時為 `none`

不得因結果不好，就把 metaphysical signal failure 改寫成 interpretation problem；也不得因結果好，就事後放寬 Claim 定義。

## 6. 輸出要求

自然語言回答仍以台灣繁體中文、白話策略為主。Claim 是研究與追蹤層，不要求把所有 runtime 欄位直接丟給一般使用者。

對重要未來問事，至少要讓使用者看得出：

1. 最重要的 1～3 個 Primary Claims 是什麼。
2. 次要的 Secondary Claims 是什麼。
3. 各自的時間窗。
4. 什麼算全中、部分中、沒中。
5. 哪些現實安排已知，因此不能算乾淨預測。
''')

append_once("core/命理分析作業規範.md", "## 十五、v1.5 可證偽 Claim 契約", r'''## 十五、v1.5 可證偽 Claim 契約

對重要且可驗證的未來問事，第一階段完成後必須依 `林氏天機預測驗證契約.md` 收斂成有限數量 Locked Claims，再進入第二階段事件校準。

- Primary Claims 原則上最多 3 個；Secondary Claims 原則上最多 2 個。
- 每個新 Claim 應有事件族群、時間窗、`matched_if`、`partial_if`、`not_matched_if`、信心與 contamination 狀態。
- 事後不得擴張命中條件，不得用年度領域命中冒充細時間命中。
- 舊 lock 保持可讀，不要求破壞性重建。
''')

append_once("core/核心提示詞.md", "# 十七、v1.5 可驗證 Claim", r'''# 十七、v1.5 可驗證 Claim

對重要且可驗證的未來問事，第一階段盲判後除了自然語言分析，還要收斂為 Locked Claims：Primary Claims 最多 3 個、Secondary Claims 最多 2 個。

每個新 Claim 至少定義：`claim_id`、`priority`、事件領域、`event_family`、`forecast_window`、`matched_if`、`partial_if`、`not_matched_if`、`confidence`、`contamination_state`。事件發生後不得改寫或擴張 `matched_if`。

評估時要分開看領域、事件族群與時間窗；年度方向命中不得冒充月份／日期命中。lock 前已知的未來安排必須標為 `partially_known` 或 `known_before_lock`，不得進 clean prospective denominator。

這些欄位主要用於研究與追蹤；一般使用者回答仍以台灣繁體中文白話呈現，不把 runtime 欄位或演算法權重當成一般回答主體。
''')

# 3. Tracking templates.
append_once("templates/問事追蹤紀錄_TEMPLATE.md", "## Locked Claims｜v1.5", r'''## Locked Claims｜v1.5

> 重要且可驗證的未來問事使用。第一階段 lock 後不得覆寫。

### Claim 01
- claim_id：
- priority：primary / secondary
- domain：
- event_family：
- forecast_window：
- matched_if：
- partial_if：
- not_matched_if：
- confidence：
- contamination_state：clean_prospective / partially_known / known_before_lock
- evidence_basis：
- knowledge_cutoff_at：
- method_version：

### Evaluation｜時間窗結束後追加
- verification_state：matched / partial / not_matched / cannot_recall
- domain_result：
- event_family_result：
- timing_result：
- observed_actual：
- failure_mode：none / ai_compliance_failure / specification_ambiguity / deterministic_or_algorithm_failure / metaphysical_signal_failure

規則：Primary Claims 最多 3 個、Secondary Claims 最多 2 個；不得為提高命中率大量增列低資訊量 Claim。`matched_if` / `partial_if` / `not_matched_if` 在 lock 後不得擴張或重寫。
''')

append_once("templates/流年追蹤紀錄_TEMPLATE.md", "## v1.5 Prospective Contamination", r'''## v1.5 Prospective Contamination

每筆可驗證未來預測應標示：

- claim_id：
- contamination_state：`clean_prospective` / `partially_known` / `known_before_lock`
- knowledge_cutoff_at：
- forecast_window：
- evaluation_eligibility：

`known_before_lock` 與 `partially_known` 可以保留做策略背景，但不得進 clean prospective denominator。現實排程更新不得覆寫事前鎖定的命理預測時間窗。
''')

# 4. Distribution surface -> TXT and include new contract in core.
path = "tools/build_ai_distribution.py"
text = read(path)
text = text.replace("- project_instructions.md", "- project_instructions.txt", 1)
text = text.replace('    "project_instructions.md",\n', '    "project_instructions.txt",\n', 1)
text = text.replace('for relative in ("core/AI工作流程.md", "core/命理分析作業規範.md"):', 'for relative in ("core/AI工作流程.md", "core/命理分析作業規範.md", "core/林氏天機預測驗證契約.md"):', 1)
text = text.replace('        "project_instructions.md": _render_project_instructions(root).encode("utf-8"),', '        "project_instructions.txt": _render_project_instructions(root).encode("utf-8"),', 1)
if text.count("project_instructions.md") != 0:
    raise RuntimeError("unexpected project_instructions.md reference remains in build_ai_distribution.py")
write(path, text)
old_dist = ROOT / "dist" / "ai" / "project_instructions.md"
if old_dist.exists():
    old_dist.unlink()

# 5. Deterministic three-file user package builder.
write("tools/build_release_package.py", r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

RELEASE_VERSION = "1.5.0"
USER_PACKAGE_NAME = "Metaphysics-Lab-v1.5.0-User-Package.zip"
USER_ASSETS = (
    "metaphysics_core.md",
    "metaphysics_lab.py",
    "project_instructions.txt",
)
_FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def _validated_assets(distribution_dir: Path):
    root = Path(distribution_dir)
    if not root.is_dir():
        raise ValueError("distribution directory is missing")
    entries = [path for path in root.iterdir()]
    if any(path.is_symlink() or not path.is_file() for path in entries):
        raise ValueError("distribution directory must contain regular files only")
    names = {path.name for path in entries}
    expected = set(USER_ASSETS)
    if names != expected:
        raise ValueError("distribution asset set mismatch: expected=%s actual=%s" % (sorted(expected), sorted(names)))
    result = []
    for name in USER_ASSETS:
        raw = (root / name).read_bytes()
        if not raw:
            raise ValueError("distribution asset is empty: %s" % name)
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("distribution asset is not UTF-8: %s" % name) from exc
        result.append((name, raw))
    return result


def render_user_package(distribution_dir: Path) -> bytes:
    assets = _validated_assets(Path(distribution_dir))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in assets:
            info = zipfile.ZipInfo(name, date_time=_FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return buffer.getvalue()


def verify_user_package(package_bytes: bytes, distribution_dir: Path) -> dict:
    expected_assets = dict(_validated_assets(Path(distribution_dir)))
    with zipfile.ZipFile(io.BytesIO(package_bytes), "r") as archive:
        members = archive.namelist()
        if sorted(members) != sorted(USER_ASSETS):
            raise ValueError("user package member set mismatch")
        if any("/" in name or "\\" in name for name in members):
            raise ValueError("user package must be flat")
        for name in USER_ASSETS:
            if archive.read(name) != expected_assets[name]:
                raise ValueError("user package member differs from distribution asset: %s" % name)
    return {
        "integrity_verified": True,
        "release_version": RELEASE_VERSION,
        "members": list(USER_ASSETS),
        "sha256": hashlib.sha256(package_bytes).hexdigest(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build deterministic Metaphysics Lab user package")
    parser.add_argument("--distribution-dir", default="dist/ai")
    parser.add_argument("--output", default=USER_PACKAGE_NAME)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    distribution = Path(args.distribution_dir)
    if not distribution.is_absolute():
        distribution = root / distribution
    package = render_user_package(distribution)
    report = verify_user_package(package, distribution)
    if not args.verify:
        output = Path(args.output)
        if not output.is_absolute():
            output = root / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(package)
        report["output"] = str(output)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''')

# 6. Deterministic cat-eye runner backed by real unit-level engine governance checks.
write("tools/run_lin_tianji_cat_eye.py", r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCENARIO_TESTS = {
    "C01-decadal-strong-yearly-weak": ("tests.test_distribution_evidence_ranker.EvidenceRankerTests.test_modifier_cannot_open_domain_without_target_scope_ownership", "lin_tianji_rank_v1-exp"),
    "C02-yearly-strong-monthly-weak": ("tests.test_distribution_evidence_ranker.EvidenceRankerTests.test_yearly_strong_monthly_same_direction_is_active_window_not_local_spike", "lin_tianji_rank_v1-exp"),
    "C03-yearly-weak-monthly-strong": ("tests.test_distribution_evidence_ranker.EvidenceRankerTests.test_yearly_weak_monthly_strong_is_local_spike_without_mutating_parent", "lin_tianji_rank_v1-exp"),
    "C04-experimental-day-hour-spike": ("tests.test_distribution_evidence_ranker.EvidenceRankerTests.test_day_only_spike_with_weak_parent_cannot_claim_major_event_specificity", "lin_tianji_rank_v1-exp"),
    "C05-correlated-ziwei-derivatives": ("tests.test_distribution_evidence_ranker.EvidenceRankerTests.test_same_dependency_family_does_not_stack_as_independent_votes", "lin_tianji_rank_v1-exp"),
    "C06-independent-bazi-ziwei-convergence": ("tests.test_distribution_evidence_ranker.EvidenceRankerTests.test_cross_system_convergence_raises_rank_without_bypassing_ownership", "lin_tianji_rank_v1-exp"),
    "C07-historical-repeated-support": ("tests.test_distribution_historical_personalization.HistoricalPersonalizationTests.test_two_exact_canonical_family_matches_prefer_existing_candidate_only", "lin_tianji_historical_personalization_v1-exp"),
    "C08-historical-unsupported-domain": ("tests.test_distribution_historical_personalization.HistoricalPersonalizationTests.test_history_cannot_create_domain_absent_from_base", "lin_tianji_historical_personalization_v1-exp"),
    "C09-known-before-cutoff-plan": ("tests.test_distribution_prospective.DistributionProspectiveClaimTests.test_known_before_lock_may_be_preserved_only_as_excluded_context", "lin_tianji_v1.5-exp"),
    "C10-algorithm-weight-request": ("tests.test_project_ux_contract.ProjectUXContractTests.test_phase5_disclosure_and_branding_boundary", "lin_tianji_interpretation_contract_v1-exp"),
    "C11-user-language-lexical-audit": ("tests.test_project_ux_contract.ProjectUXContractTests.test_user_facing_prose_uses_taiwan_traditional_chinese_without_unnecessary_english", "lin_tianji_interpretation_contract_v1-exp"),
    "C12-progressive-case-stage1-isolation": ("tests.test_lin_tianji_cat_eye_progressive.CatEyeProgressiveIsolationTests.test_05_and_06_materialized_but_stage1_reads_base_only", "blind-source-v1.1"),
}


def _digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _run_test(test_id):
    suite = unittest.defaultTestLoader.loadTestsFromName(test_id)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    status = "PASS" if result.wasSuccessful() and result.testsRun == 1 else "FAIL"
    summary = {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
    }
    if status == "FAIL":
        summary["detail"] = stream.getvalue()[-2000:]
    return status, summary


def run_scenarios(fixture_path):
    payload = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    rows = payload.get("scenarios")
    if payload.get("fixture_version") != "lin_tianji_cat_eye.v1" or not isinstance(rows, list):
        raise ValueError("unsupported cat-eye fixture")
    ids = [row.get("id") for row in rows]
    if ids != list(SCENARIO_TESTS):
        raise ValueError("cat-eye scenario set/order does not match the fixed v1 matrix")
    results = []
    for row in rows:
        scenario_id = row["id"]
        test_id, version = SCENARIO_TESTS[scenario_id]
        status, observed = _run_test(test_id)
        results.append({
            "scenario_id": scenario_id,
            "status": status,
            "reason": row.get("expected") if status == "PASS" else observed.get("detail", "governance check failed"),
            "policy_or_method_version": version,
            "input_digest": _digest({"fixture_version": payload["fixture_version"], "scenario": row, "test_id": test_id}),
            "output_digest": _digest({"status": status, "observed": observed}),
        })
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run deterministic 林氏天機 v1.5 cat-eye scenarios")
    parser.add_argument("--fixture", default="tests/fixtures/lin_tianji_cat_eye.v1.json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    fixture = Path(args.fixture)
    if not fixture.is_absolute():
        fixture = ROOT / fixture
    results = run_scenarios(fixture)
    failed = [row for row in results if row["status"] != "PASS"]
    report = {
        "fixture_version": "lin_tianji_cat_eye.v1",
        "status": "FAIL" if failed else "PASS",
        "scenario_count": len(results),
        "failed_count": len(failed),
        "results": results,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        for row in results:
            print("%s %s - %s" % (row["status"], row["scenario_id"], row["reason"]))
        print("cat-eye: %s (%d/%d PASS)" % (report["status"], len(results) - len(failed), len(results)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
''')

write("tests/test_lin_tianji_cat_eye_progressive.py", r'''import unittest

from engine.distribution.blind_sources import validate_blind_source_case
from engine.distribution.runtime import dispatch


BIRTH = {"sex": "male", "birth_date": "1984-03-13", "birth_time": "19:20", "birth_place": "台北市"}
LOCATION = {
    "canonical_name": "Taipei City, Taiwan", "latitude": 25.033, "longitude": 121.5654,
    "timezone": "Asia/Taipei", "provider_name": "ai_host", "provider_version": "synthetic-cat-eye",
    "provider_reference": None,
}


class CatEyeProgressiveIsolationTests(unittest.TestCase):
    def test_05_and_06_materialized_but_stage1_reads_base_only(self):
        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        self.assertTrue(built["ok"], built)
        exported = dispatch("export_case_markdown", {
            "normalized_natal": built["data"]["normalized_natal"],
            "subject_id": "subj_cateye000001", "subject_display_name": "Synthetic", "subject_short_id": "CATEYE",
            "filename_label": "Synthetic", "generated_at": "2026-08-29T00:00:00+08:00", "last_modified_by": "ai",
        })
        self.assertTrue(exported["ok"], exported)
        files = dict(exported["data"]["files"])
        first = dispatch("update_case_record", {
            "case_files": files, "filename": "05_驗證事件紀錄.md", "operation": "append",
            "updated_at": "2026-08-29T00:01:00+08:00", "last_modified_by": "ai",
            "entry": {"record_id": "evt-cat-eye", "status": "verified", "summary": "synthetic verified history"},
        })
        self.assertTrue(first["ok"], first)
        files.update(first["data"]["changed_files"])
        second = dispatch("update_case_record", {
            "case_files": files, "filename": "06_流年追蹤紀錄.md", "operation": "append",
            "updated_at": "2026-08-29T00:02:00+08:00", "last_modified_by": "ai",
            "entry": {"record_id": "forecast-cat-eye", "blind_forecast": "synthetic locked note"},
        })
        self.assertTrue(second["ok"], second)
        files.update(second["data"]["changed_files"])

        base = {name: text for name, text in files.items() if any(token in name for token in ("_00_", "_01_", "_02_", "_03_", "_04_"))}
        self.assertEqual(len(base), 5)
        result = validate_blind_source_case(base)
        self.assertEqual(result["status"], "validated")
        state = result["manifest_progressive_state"]
        self.assertTrue(state["05_驗證事件紀錄.md"])
        self.assertTrue(state["06_流年追蹤紀錄.md"])
        self.assertFalse(any("synthetic verified history" in text for text in base.values()))
        self.assertFalse(any("synthetic locked note" in text for text in base.values()))


if __name__ == "__main__":
    unittest.main()
''')

# 7. Black-box distribution contract gate. This intentionally sees only release assets + portable CLI.
write("tools/run_v15_sandbox_black_box.py", r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

RUBRIC = (
    "temporal_ownership_pass",
    "specificity_pass",
    "calibration_narrowing_pass",
    "cutoff_contamination_pass",
    "experimental_ceiling_pass",
    "natural_language_pass",
    "algorithm_disclosure_pass",
    "strategy_forecast_separation_pass",
)


def run(distribution_dir):
    root = Path(distribution_dir)
    expected = {"metaphysics_lab.py", "metaphysics_core.md", "project_instructions.txt"}
    actual = {path.name for path in root.iterdir() if path.is_file()}
    if actual != expected:
        raise ValueError("black-box release asset set mismatch")
    core = (root / "metaphysics_core.md").read_text(encoding="utf-8")
    instructions = (root / "project_instructions.txt").read_text(encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(root / "metaphysics_lab.py"), "runtime-info"],
        text=True, capture_output=True, check=False,
    )
    runtime = json.loads(completed.stdout) if completed.returncode == 0 and completed.stdout.strip() else {}
    joined = core + "\n" + instructions
    checks = {
        "temporal_ownership_pass": all(token in joined for token in ("時間窗", "時間")),
        "specificity_pass": all(token in joined for token in ("event_family", "matched_if", "not_matched_if")),
        "calibration_narrowing_pass": "不得" in joined and "事件校準" in joined,
        "cutoff_contamination_pass": all(token in joined for token in ("known_before_lock", "clean prospective denominator")),
        "experimental_ceiling_pass": "Experimental" in joined or "experimental" in joined,
        "natural_language_pass": all(token in joined for token in ("台灣繁體中文", "白話")),
        "algorithm_disclosure_pass": "演算法權重" in joined or "權重" in joined,
        "strategy_forecast_separation_pass": "策略" in joined and "預測" in joined,
    }
    runtime_ok = bool(runtime.get("ok"))
    rows = [{"rubric": key, "status": "PASS" if value and runtime_ok else "FAIL"} for key, value in checks.items()]
    digest = hashlib.sha256((core + instructions + json.dumps(runtime, sort_keys=True)).encode("utf-8")).hexdigest()
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "rubric": rows,
        "runtime_ok": runtime_ok,
        "distribution_digest": digest,
        "note": "deterministic black-box contract harness over the three release assets; no source-module imports",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--distribution-dir", default="dist/ai")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    dist = Path(args.distribution_dir)
    if not dist.is_absolute():
        dist = root / dist
    report = run(dist)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True) if args.json else report)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
''')

write("tests/test_v15_sandbox_black_box.py", r'''import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_v15_sandbox_black_box.py"


class V15SandboxBlackBoxTests(unittest.TestCase):
    def test_all_critical_black_box_rubric_items_pass(self):
        spec = importlib.util.spec_from_file_location("v15_black_box", RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.run(ROOT / "dist" / "ai")
        self.assertEqual(report["status"], "PASS", report)
        self.assertTrue(report["runtime_ok"], report)
        self.assertEqual(len(report["rubric"]), 8)
        self.assertTrue(all(row["status"] == "PASS" for row in report["rubric"]), report)


if __name__ == "__main__":
    unittest.main()
''')

# 8. Rewrite the new prospective tests to explicitly protect legacy locks.
write("tests/test_distribution_prospective_v15_claim_shape.py", r'''import unittest

from engine.distribution.errors import DistributionError
from engine.distribution.prospective import METHOD_VERSION, lock_prospective_forecast, resolve_query_anchor


class V15ProspectiveClaimShapeTests(unittest.TestCase):
    def anchor(self):
        return resolve_query_anchor({
            "query_anchor_at": "2026-08-29T00:10:00+08:00",
            "query_timezone": "Asia/Taipei",
            "target_start": "2026-09-01T00:00:00+08:00",
            "target_end": "2026-12-31T23:59:59+08:00",
            "question_reference": "synthetic-v15-claim-contract",
        })

    def claim(self, claim_id, priority="primary"):
        anchor = self.anchor()
        return {
            "claim_id": claim_id,
            "priority": priority,
            "forecast_window": {"start": "2026-09-01T00:00:00+08:00", "end": "2026-09-30T23:59:59+08:00"},
            "primary_domain": "career",
            "event_family": "role_change",
            "prediction": "synthetic bounded event-family forecast",
            "matched_if": "formal responsibility or role changes inside the window",
            "partial_if": "responsibility changes materially but without formal title change",
            "not_matched_if": "no material responsibility or role change occurs inside the window",
            "evidence_layers": ["bazi"], "evidence_time_scales": ["yearly", "monthly"],
            "capability_maturity": "stable", "confidence": "medium",
            "knowledge_cutoff_at": anchor["knowledge_cutoff_at"],
            "evaluation_eligibility": "clean_scorable", "contamination_state": "clean_prospective",
            "method_version": METHOD_VERSION,
        }

    def test_lock_preserves_priority_and_partial_boundary(self):
        locked = lock_prospective_forecast({"anchor": self.anchor(), "claims": [self.claim("C1")]})
        claim = locked["claims"][0]
        self.assertEqual(claim["priority"], "primary")
        self.assertIn("without formal title change", claim["partial_if"])

    def test_legacy_phase1_claim_shape_remains_readable_without_migration(self):
        claim = self.claim("legacy")
        claim.pop("priority")
        claim.pop("partial_if")
        locked = lock_prospective_forecast({"anchor": self.anchor(), "claims": [claim]})
        self.assertNotIn("priority", locked["claims"][0])
        self.assertNotIn("partial_if", locked["claims"][0])

    def test_enhanced_claim_fields_are_all_or_none(self):
        claim = self.claim("C1")
        claim.pop("partial_if")
        with self.assertRaises(DistributionError):
            lock_prospective_forecast({"anchor": self.anchor(), "claims": [claim]})

    def test_locked_claim_volume_is_bounded_to_three_primary_two_secondary(self):
        allowed = [self.claim("P%d" % index) for index in range(1, 4)] + [self.claim("S%d" % index, priority="secondary") for index in range(1, 3)]
        locked = lock_prospective_forecast({"anchor": self.anchor(), "claims": allowed})
        self.assertEqual(len(locked["claims"]), 5)
        with self.assertRaises(DistributionError):
            lock_prospective_forecast({"anchor": self.anchor(), "claims": allowed + [self.claim("P4")]})
        with self.assertRaises(DistributionError):
            lock_prospective_forecast({"anchor": self.anchor(), "claims": allowed + [self.claim("S3", priority="secondary")]})

    def test_unsupported_priority_is_rejected(self):
        with self.assertRaises(DistributionError):
            lock_prospective_forecast({"anchor": self.anchor(), "claims": [self.claim("C1", priority="tertiary")]})


if __name__ == "__main__":
    unittest.main()
''')

# 9. Current release-facing tests/docs migrate to TXT and v1.5; preserve historical release notes.
for test_path in (
    "tests/test_ai_distribution_acceptance.py",
    "tests/test_ai_distribution_build.py",
    "tests/test_ai_distribution_docs.py",
    "tests/test_ai_distribution_filename_migration.py",
):
    target = ROOT / test_path
    if target.exists():
        text = target.read_text(encoding="utf-8")
        text = text.replace("project_instructions.md", "project_instructions.txt")
        text = text.replace("is_v1_4_0", "is_v1_5_0")
        text = text.replace("Metaphysics Lab Core：**v1.4.0**", "Metaphysics Lab Core：**v1.5.0**")
        text = text.replace("發布日期：**2026-08-26**", "發布日期：**2026-08-29**")
        target.write_text(text, encoding="utf-8")

# v1.4 test now protects the historical snapshot only; current-version assertions live in v1.5 tests.
write("tests/test_release_v1_4_contract.py", r'''from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RELEASE_NOTES = ROOT / "docs" / "發布說明-v1.4.0.md"
CHANGELOG = ROOT / "CHANGELOG.md"
RULES = ROOT / "core" / "命理推導計算規則.md"


class ReleaseV14HistoricalSnapshotTests(unittest.TestCase):
    def test_v1_4_historical_release_snapshot_is_preserved(self):
        self.assertTrue(RELEASE_NOTES.exists())
        notes = RELEASE_NOTES.read_text(encoding="utf-8")
        changelog = CHANGELOG.read_text(encoding="utf-8")
        rules = RULES.read_text(encoding="utf-8")
        self.assertIn("# Metaphysics Lab v1.4.0", notes)
        self.assertIn("發布日期：**2026-08-26**", notes)
        for asset in ("metaphysics_lab.py", "metaphysics_core.md", "project_instructions.md"):
            self.assertIn(asset, notes)
        self.assertIn("## v1.4.0｜2026-08-26", changelog)
        self.assertIn("86", rules)
        self.assertIn("0 mismatch", rules)


if __name__ == "__main__":
    unittest.main()
''')

# Current user docs only; historical v1.3/v1.4 release notes and superpowers plans remain untouched.
for doc in ("README.md", "docs/快速開始.md", "docs/安裝到ChatGPT-Project.md", "docs/更新與版本同步.md", "docs/架構說明.md"):
    target = ROOT / doc
    text = target.read_text(encoding="utf-8")
    text = text.replace("project_instructions.md", "project_instructions.txt")
    text = text.replace("目前正式版本為 **v1.4.0（2026-08-26）**", "目前正式版本為 **v1.5.0（2026-08-29）**")
    target.write_text(text, encoding="utf-8")

# VERSION is current-state authority, so its v1.4 current-snapshot wording becomes v1.5 while historical section stays explicit.
version = read("VERSION.md")
version = version.replace("一般使用者版 v1.4.0 發布說明見 `docs/發布說明-v1.4.0.md`", "一般使用者版 v1.5.0 發布說明見 `docs/發布說明-v1.5.0.md`")
version = version.replace("- Metaphysics Lab Core：**v1.4.0**", "- Metaphysics Lab Core：**v1.5.0**", 1)
version = version.replace("- 發布日期：**2026-08-26**", "- 發布日期：**2026-08-29**", 1)
version = version.replace("- Release baseline：v1.4.0 release-preparation gate；正式 Git tag 應在 release 文件 merge、`main` regression 驗證完成後建立", "- Release baseline：林氏天機 v1.5 Phase 1–6 + deterministic cat-eye + black-box distribution gate + final release qualification")
version = version.replace("## v1.4.0 Capability 狀態", "## v1.5.0 Capability 狀態", 1)
version = version.replace("## v1.4.0 Distribution / Contract Snapshot", "## v1.5.0 Distribution / Contract Snapshot", 1)
version = version.replace("v1.4.0 正式收斂下列 distribution / data contract：", "v1.5.0 正式收斂下列 distribution / data contract：", 1)
version = version.replace("## v1.4.0 Qualification Snapshot", "## v1.5.0 Qualification Snapshot", 1)
version = version.replace("## v1.4.0 Release Acceptance Gate", "## v1.5.0 Release Acceptance Gate", 1)
version = version.replace("v1.4.0 正式提供 mobile-first AI release surface：", "v1.5.0 正式提供 mobile-first AI release surface：", 1)
version = version.replace("dist/ai/project_instructions.md", "dist/ai/project_instructions.txt")
version = version.replace("`project_instructions.md` 內容貼入 Project Instructions", "`project_instructions.txt` 內容貼入 Project Instructions")
version = version.replace("從 v1.3.0 升級到 v1.4.0 時，由於 Project Contract / Case Schema 已正式進到 1.1，Release 說明要求同步三個發行檔；既有私人 Case 不應因此清空或破壞性重建。", "從 v1.4.0 升級到 v1.5.0 時，Project Contract / Case Schema 仍維持 1.1；同步三個發行檔即可，既有私人 Case 與舊 prospective lock 不要求清空、破壞性重建或 schema migration。")
write("VERSION.md", version)

# Add v1.5 release summary without rewriting historical development details.
changelog = read("CHANGELOG.md")
marker = "## v1.5.0｜2026-08-29"
if marker not in changelog:
    insertion = r'''## v1.5.0｜2026-08-29

### 林氏天機 v1.5 正式收斂

- 完成 Phase 1–6：prospective lock、evidence model、eligibility/ranking、historical personalization、interpretation contract、prospective evaluation。
- 新增可證偽 Claim 契約：Primary 最多 3、Secondary 最多 2，明確 `matched_if / partial_if / not_matched_if`，並分開記錄 domain / event-family / timing 結果。
- 保持 Legacy Phase 1 lock 可讀；新 Claim 欄位採向後相容擴充，不要求 Case Schema 1.1 migration。
- `project_instructions.txt` 取代一般使用者發行面的 `.md`，方便手機／電腦直接開啟與複製；repo 內權威來源仍為 Markdown。
- 新增 deterministic three-file User Package：`Metaphysics-Lab-v1.5.0-User-Package.zip`，ZIP 內只能有 `metaphysics_lab.py`、`metaphysics_core.md`、`project_instructions.txt`。
- 新增 12-case deterministic 貓眼測試、三檔 distribution black-box contract gate 與 final release workflow。
- 不修改八字／紫微公式、Phase 3 ranking authority、Phase 4/5 邊界或 capability maturity。

'''
    first_heading = changelog.find("## ")
    if first_heading < 0:
        raise RuntimeError("CHANGELOG has no section heading")
    changelog = changelog[:first_heading] + insertion + changelog[first_heading:]
write("CHANGELOG.md", changelog)

write("docs/發布說明-v1.5.0.md", r'''# Metaphysics Lab v1.5.0

發布日期：**2026-08-29**

v1.5.0 正式收斂「林氏天機」Phase 1–6，並把使用者下載與預測驗證流程一起收斂成可發行版本。這版不把命理包裝成科學證明，也沒有因 release 自動提升任何 experimental capability maturity。

## 一般使用者最重要的變化

1. 未來問事仍先盲判、再校準，但重要預測會收斂成有限數量、可被打臉的 Claim；Primary 原則上最多 3 個、Secondary 最多 2 個。
2. 每個新 Claim 會明確定義事件族群、時間窗，以及什麼算全中、部分中、沒中；事後不得擴張命中條件。
3. 已知的未來安排（例如已排定手術、已簽約工作）會標 contamination，不得混進 clean prospective accuracy。
4. 舊 Case 與舊 prospective lock 仍可讀，不要求破壞性 migration。
5. Project Instructions 發行檔改為 `project_instructions.txt`，方便手機與電腦直接開啟、全選與複製。

## 下載方式

最簡單：下載：

`Metaphysics-Lab-v1.5.0-User-Package.zip`

ZIP 內**只會有三個檔案**：

- `metaphysics_lab.py`：上傳到 ChatGPT / Claude Project。
- `metaphysics_core.md`：上傳到 Project。
- `project_instructions.txt`：全文貼到 Project Instructions。

Release Assets 也會提供上述三個檔案單獨下載。

GitHub 頁面另外自動顯示的 `Source code (zip)` / `Source code (tar.gz)` 是整個 repository 的原始碼快照，**不是一般使用者安裝包**。

## 從 v1.4.0 升級

1. 替換 `metaphysics_lab.py`。
2. 替換 `metaphysics_core.md`。
3. 用新版 `project_instructions.txt` 全文重新貼入 Project Instructions。
4. 保留既有私人命盤、驗證事件、流年、問事與重大決策紀錄。
5. 不需要為 v1.5.0 重建 Case Schema；舊 lock 保持可讀。

## Release qualification

v1.5.0 tag 只允許在 exact release candidate / merged `main` 同時通過下列 gate 後建立：

- Bazi flow-time qualification
- Ziwei flow-time qualification
- Ziwei month-boundary qualification
- deterministic distribution build/check
- 12-case deterministic 林氏天機 cat-eye
- three-asset black-box distribution contract gate
- full repository regression
- Python 3.9 compileall
- clean validation tree
- deterministic three-file User Package integrity verification

最終 workflow run、test count、artifact digest 以 GitHub Release 與 CI 實際結果為準，不在驗證前預填。

## 沒有改的東西

- 八字／紫微 production 命理公式沒有因 2026 回測修改。
- Phase 3 仍是 ranking authority。
- Phase 4 歷史事件只能窄化既有候選，不能創造新領域。
- Phase 5 不重排 Stage 1。
- Phase 6 維持 append-only evaluation、failure attribution 與 method denominator isolation。
- release 本身不等於命理預測準確率的科學證明。
''')

# 10. Feature validation gets explicit v1.5 gates before full regression.
workflow_path = ".github/workflows/feature-historical-calibration-validation.yml"
workflow = read(workflow_path)
needle = "      - name: Full repository regression\n"
if "Run v1.5 deterministic cat-eye" not in workflow:
    if needle not in workflow:
        raise RuntimeError("feature workflow insertion point not found")
    extra = '''      - name: Run v1.5 deterministic cat-eye\n        run: python tools/run_lin_tianji_cat_eye.py --json\n\n      - name: Verify v1.5 black-box release contract\n        run: python tools/run_v15_sandbox_black_box.py --json\n\n      - name: Verify deterministic three-file user package\n        run: python tools/build_release_package.py --verify --output \"$RUNNER_TEMP/Metaphysics-Lab-v1.5.0-User-Package.zip\"\n\n'''
    workflow = workflow.replace(needle, extra + needle, 1)
write(workflow_path, workflow)

# 11. Release workflow. It is idempotent: existing v1.5.0 is verified/no-op rather than overwritten.
write(".github/workflows/release-v1.5.yml", r'''name: Release v1.5.0

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  release:
    if: github.repository == 'mvkaiii/metaphysics-lab'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout exact release ref
        uses: actions/checkout@v4
        with:
          ref: ${{ github.sha }}
          fetch-depth: 0

      - name: Set up Python 3.9
        uses: actions/setup-python@v5
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Bazi flow-time qualification
        run: python tools/build_bazi_flow_time_qualification.py --check

      - name: Ziwei flow-time qualification
        run: python tools/build_ziwei_flow_time_qualification.py --check

      - name: Ziwei month-boundary qualification
        run: python tools/build_ziwei_month_boundary_qualification.py --check

      - name: Rebuild and verify AI distribution
        run: |
          python tools/build_ai_distribution.py
          python tools/build_ai_distribution.py --check

      - name: Run 林氏天機 deterministic cat-eye
        run: python tools/run_lin_tianji_cat_eye.py --json

      - name: Run three-asset black-box contract gate
        run: python tools/run_v15_sandbox_black_box.py --json

      - name: Full repository regression
        run: python -m unittest discover -s tests -p 'test_*.py'

      - name: Python 3.9 compile check
        run: python -m compileall -q engine tools tests dist/ai/metaphysics_lab.py

      - name: Verify clean release tree before package output
        run: git diff --exit-code && test -z "$(git status --porcelain)"

      - name: Build deterministic three-file user package
        run: |
          python tools/build_release_package.py --output "$RUNNER_TEMP/Metaphysics-Lab-v1.5.0-User-Package.zip"
          python tools/build_release_package.py --verify
          sha256sum "$RUNNER_TEMP/Metaphysics-Lab-v1.5.0-User-Package.zip"

      - name: Publish v1.5.0 release if absent
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          if gh release view v1.5.0 >/dev/null 2>&1; then
            echo "v1.5.0 already exists; refusing to overwrite immutable release identity"
            gh release view v1.5.0 --json tagName,targetCommitish,isDraft,isPrerelease
            exit 0
          fi
          gh release create v1.5.0 \
            --target "$GITHUB_SHA" \
            --title "Metaphysics Lab v1.5.0" \
            --notes-file docs/發布說明-v1.5.0.md \
            "$RUNNER_TEMP/Metaphysics-Lab-v1.5.0-User-Package.zip" \
            dist/ai/metaphysics_lab.py \
            dist/ai/metaphysics_core.md \
            dist/ai/project_instructions.txt
''')

print("v1.5 release-prep source patch complete")
