import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from engine.ziwei.basis import build_palace_stem_index, build_star_location_index
from engine.ziwei.flying import build_natal_flying_graph, fly_transformations
from engine.ziwei.models import CycleStemSource
from engine.ziwei.transformations import get_transformation_set
from tests.ziwei_phase2a_fixtures import (
    CHART,
    PROVENANCE,
    SYNTHETIC_PALACE_STEM_RECORDS,
    SYNTHETIC_STAR_RECORDS,
)
from tools.qualify_ziwei_phase2a_public import (
    parse_iztro_heavenly_stems,
    qualify_public_profile,
)

IZTRO_FRAGMENT = """
export const heavenlyStems = {
  jiaHeavenly: { mutagen: ['lianzhenMaj', 'pojunMaj', 'wuquMaj', 'taiyangMaj'] },
  yiHeavenly: { mutagen: ['tianjiMaj', 'tianliangMaj', 'ziweiMaj', 'taiyinMaj'] },
  bingHeavenly: { mutagen: ['tiantongMaj', 'tianjiMaj', 'wenchangMin', 'lianzhenMaj'] },
  dingHeavenly: { mutagen: ['taiyinMaj', 'tiantongMaj', 'tianjiMaj', 'jumenMaj'] },
  wuHeavenly: { mutagen: ['tanlangMaj', 'taiyinMaj', 'youbiMin', 'tianjiMaj'] },
  jiHeavenly: { mutagen: ['wuquMaj', 'tanlangMaj', 'tianliangMaj', 'wenquMin'] },
  gengHeavenly: { mutagen: ['taiyangMaj', 'wuquMaj', 'taiyinMaj', 'tiantongMaj'] },
  xinHeavenly: { mutagen: ['jumenMaj', 'taiyangMaj', 'wenquMin', 'wenchangMin'] },
  renHeavenly: { mutagen: ['tianliangMaj', 'ziweiMaj', 'zuofuMin', 'wuquMaj'] },
  guiHeavenly: { mutagen: ['pojunMaj', 'jumenMaj', 'taiyinMaj', 'tanlangMaj'] },
};
"""


def synthetic_private_shape():
    stars = build_star_location_index(SYNTHETIC_STAR_RECORDS, CHART, PROVENANCE)
    stems = build_palace_stem_index(SYNTHETIC_PALACE_STEM_RECORDS, CHART, PROVENANCE)
    graph = build_natal_flying_graph(stems, stars)
    natal_expected = [
        {
            "source_palace": edge.source.palace,
            "source_stem": edge.source.heavenly_stem,
            "type": edge.transformation_type.value,
            "star": edge.star,
            "target_palace": edge.target_palace,
        }
        for edge in graph.edges
    ]
    decadal_source = CycleStemSource(
        "cycle_stem", CHART, "decadal", "43-52-virtual-age", "癸"
    )
    decadal_edges = fly_transformations(
        get_transformation_set("癸"), stars, decadal_source
    )
    year_stems = (
        ("2023", "癸"),
        ("2024", "甲"),
        ("2025", "乙"),
        ("2026", "丙"),
        ("2027", "丁"),
        ("2028", "戊"),
        ("2029", "己"),
    )
    yearly = []
    for reference, stem in year_stems:
        source = CycleStemSource("cycle_stem", CHART, "yearly", reference, stem)
        edges = fly_transformations(get_transformation_set(stem), stars, source)
        yearly.append(
            {
                "reference": reference,
                "stem": stem,
                "expected_edges": [
                    {
                        "type": edge.transformation_type.value,
                        "star": edge.star,
                        "target_palace": edge.target_palace,
                    }
                    for edge in edges
                ],
            }
        )
    return {
        "source_profile": "synthetic-private-shape-v1",
        "chart_id": CHART.chart_id,
        "star_locations": [
            {"star": record.star, "palace": record.palace}
            for record in SYNTHETIC_STAR_RECORDS
        ],
        "palace_stems": [
            {"palace": record.palace, "heavenly_stem": record.heavenly_stem}
            for record in SYNTHETIC_PALACE_STEM_RECORDS
        ],
        "natal_expected_edges": natal_expected,
        "decadal": {
            "reference": "43-52-virtual-age",
            "stem": "癸",
            "expected_edges": [
                {
                    "type": edge.transformation_type.value,
                    "star": edge.star,
                    "target_palace": edge.target_palace,
                }
                for edge in decadal_edges
            ],
        },
        "yearly": yearly,
        "presentation_expected": [],
    }


class ZiweiPublicQualificationTests(unittest.TestCase):
    def test_parser_extracts_ten_stems(self):
        table = parse_iztro_heavenly_stems(IZTRO_FRAGMENT)
        self.assertEqual(len(table), 10)
        self.assertEqual(table["丙"], ("天同", "天機", "文昌", "廉貞"))

    def test_exact_external_table_is_40_of_40_pass(self):
        table = parse_iztro_heavenly_stems(IZTRO_FRAGMENT)
        evidence = qualify_public_profile(
            table,
            "814b77e6371e1050cac31bbf674db3c3138fcfde",
            "2026-08-21T00:00:00Z",
        )
        self.assertEqual(evidence["cases_checked"], 40)
        self.assertEqual(evidence["cases_matched"], 40)
        self.assertEqual(evidence["mismatches"], [])
        self.assertEqual(evidence["status"], "PASS")

    def test_one_external_mismatch_is_fail(self):
        table = dict(parse_iztro_heavenly_stems(IZTRO_FRAGMENT))
        table["丙"] = ("天同", "天機", "文昌", "天機")
        evidence = qualify_public_profile(
            table,
            "814b77e6371e1050cac31bbf674db3c3138fcfde",
            "2026-08-21T00:00:00Z",
        )
        self.assertEqual(evidence["cases_matched"], 39)
        self.assertEqual(evidence["status"], "FAIL")

    def test_direct_cli_invocation_can_import_project_engine(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "heavenlyStems.ts"
            output_path = Path(tmp_dir) / "evidence.json"
            source_path.write_text(IZTRO_FRAGMENT, encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "tools/qualify_ziwei_phase2a_public.py",
                    "--source-ts",
                    str(source_path),
                    "--source-revision",
                    "814b77e6371e1050cac31bbf674db3c3138fcfde",
                    "--run-timestamp",
                    "2026-08-21T00:00:00Z",
                    "--output",
                    str(output_path),
                ],
                cwd=str(repo_root),
                text=True,
                capture_output=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            evidence = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(evidence["status"], "PASS")


class ZiweiPrivateQualificationTests(unittest.TestCase):
    def test_summary_has_explicit_40_stem_and_80_flying_gates_without_private_payload(self):
        from tools.qualify_ziwei_phase2a_private import qualify_private

        evidence = qualify_private(
            synthetic_private_shape(),
            "abc123",
            "2026-08-21T00:00:00Z",
        )
        self.assertEqual(evidence["transformation_profile"]["checked"], 40)
        self.assertEqual(evidence["natal"]["checked"], 48)
        self.assertEqual(evidence["decadal"]["checked"], 4)
        self.assertEqual(evidence["yearly"]["checked"], 28)
        self.assertEqual(evidence["flying_total"]["checked"], 80)
        serialized = json.dumps(evidence, ensure_ascii=False)
        for forbidden in (
            "star_locations",
            "palace_stems",
            "expected_edges",
            "birth_datetime",
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertEqual(evidence["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
