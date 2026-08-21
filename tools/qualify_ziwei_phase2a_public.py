from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.ziwei.errors import ZiweiPhase2AError
from engine.ziwei.transformation_profiles import PROFILE_ID, RULE_VERSION
from engine.ziwei.transformations import get_transformation_set

STEM_KEYS = {
    "jiaHeavenly": "甲",
    "yiHeavenly": "乙",
    "bingHeavenly": "丙",
    "dingHeavenly": "丁",
    "wuHeavenly": "戊",
    "jiHeavenly": "己",
    "gengHeavenly": "庚",
    "xinHeavenly": "辛",
    "renHeavenly": "壬",
    "guiHeavenly": "癸",
}

STAR_KEYS = {
    "lianzhenMaj": "廉貞",
    "pojunMaj": "破軍",
    "wuquMaj": "武曲",
    "taiyangMaj": "太陽",
    "tianjiMaj": "天機",
    "tianliangMaj": "天梁",
    "ziweiMaj": "紫微",
    "taiyinMaj": "太陰",
    "tiantongMaj": "天同",
    "wenchangMin": "文昌",
    "tanlangMaj": "貪狼",
    "youbiMin": "右弼",
    "wenquMin": "文曲",
    "jumenMaj": "巨門",
    "zuofuMin": "左輔",
}


def parse_iztro_heavenly_stems(source_text):
    table = {}
    for source_stem_key, stem in STEM_KEYS.items():
        pattern = re.compile(
            re.escape(source_stem_key) + r"\s*:\s*\{.*?mutagen\s*:\s*\[(.*?)\]",
            re.S,
        )
        match = pattern.search(source_text)
        if not match:
            raise ZiweiPhase2AError(
                "qualification_mismatch",
                "missing iztro heavenly-stem mutagen block",
                {"stem_key": source_stem_key},
            )
        raw_keys = re.findall(r"['\"]([A-Za-z0-9_]+)['\"]", match.group(1))
        if len(raw_keys) != 4:
            raise ZiweiPhase2AError(
                "qualification_mismatch",
                "iztro mutagen block must contain exactly four quoted star keys",
                {"stem_key": source_stem_key, "count": len(raw_keys)},
            )
        try:
            stars = tuple(STAR_KEYS[key] for key in raw_keys)
        except KeyError as exc:
            raise ZiweiPhase2AError(
                "qualification_mismatch",
                "unknown iztro star key",
                {"stem_key": source_stem_key, "star_key": str(exc.args[0])},
            ) from exc
        table[stem] = stars

    if len(table) != 10:
        raise ZiweiPhase2AError(
            "qualification_mismatch",
            "expected exactly ten parsed heavenly stems",
            {"count": len(table)},
        )
    return table


def qualify_public_profile(source_table, source_revision, run_timestamp):
    mismatches = []
    matched = 0
    for stem in "甲乙丙丁戊己庚辛壬癸":
        external = tuple(source_table.get(stem, ()))
        project = tuple(item.star for item in get_transformation_set(stem).transformations)
        for idx, transformation_type in enumerate(("祿", "權", "科", "忌")):
            external_star = external[idx] if idx < len(external) else None
            project_star = project[idx]
            if external_star == project_star:
                matched += 1
            else:
                mismatches.append(
                    {
                        "stem": stem,
                        "type": transformation_type,
                        "expected_external": external_star,
                        "project": project_star,
                    }
                )

    return {
        "source_name": "SylarLong/iztro",
        "source_revision": source_revision,
        "rule_profile": PROFILE_ID,
        "rule_version": RULE_VERSION,
        "cases_checked": 40,
        "cases_matched": matched,
        "mismatches": mismatches,
        "status": "PASS" if matched == 40 and not mismatches else "FAIL",
        "run_timestamp": run_timestamp,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-ts", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--run-timestamp", default="2026-08-21T00:00:00Z")
    args = parser.parse_args(argv)

    source_text = Path(args.source_ts).read_text(encoding="utf-8")
    source_table = parse_iztro_heavenly_stems(source_text)
    evidence = qualify_public_profile(
        source_table,
        args.source_revision,
        args.run_timestamp,
    )
    Path(args.output).write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if evidence["status"] == "PASS":
        print("EXTERNAL_PROFILE_PASS 40/40")
        return 0
    print("EXTERNAL_PROFILE_FAIL %d/40" % evidence["cases_matched"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
