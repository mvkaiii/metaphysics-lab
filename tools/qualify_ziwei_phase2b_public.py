from __future__ import annotations
import argparse, json, re, sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.calendar.sexagenary import five_mouse_hour, five_tiger_month, lunar_year_stem, sexagenary_day
from engine.ziwei.errors import ZiweiFineCycleError
from engine.ziwei.fine_cycle_stems import FINE_CYCLE_PROFILE_ID, FINE_CYCLE_RULE_VERSION

SOURCE_NAME = 'SylarLong/lunar-lite'

def _fail(message, details=None):
    raise ZiweiFineCycleError('qualification_mismatch', message, details)

def parse_lunar_lite_contract(source_text: str):
    compact = re.sub(r'\s+', '', source_text)
    checks = {
        'separate_exact_month_path': 'monthlyDivide==="exact"' in compact and 'getMonthGanExact()' in compact,
        'normal_month_leap_split': 'constfixLeap=lunar.getMonth()<0&&lunar.getDay()>15?1:0;' in compact,
        'normal_month_five_tiger': 'FIVE_TIGER[HEAVENLY_STEMS.indexOf(yearlyGan)]' in compact,
        'normal_month_ordinal': 'Math.abs(lunar.getMonth())-1+fixLeap' in compact,
        'exact_day_stem': 'lunar.getDayGanExact()' in source_text,
        'exact_day_branch': 'lunar.getDayZhiExact()' in source_text,
        'time_stem': 'lunar.getTimeGan()' in source_text,
        'time_branch': 'lunar.getTimeZhi()' in source_text,
    }
    missing = [k for k, v in checks.items() if not v]
    if missing:
        _fail('lunar-lite Ganzhi contract changed', {'missing': missing})
    return checks

def _pillars(value):
    parts = tuple(value.split())
    if len(parts) != 4 or any(len(x) != 2 for x in parts):
        _fail('invalid external four-pillar vector', {'value': value})
    return parts

def _date(value):
    y, m, d = (int(x) for x in value.split('-'))
    return date(y, m, d)

def qualify_lunar_lite(payload, source_revision, package_version, source_contract):
    checks, mismatches = [], []
    def compare(case_id, category, expected, project):
        item = {'case_id': case_id, 'category': category, 'expected_external': expected,
                'project': project, 'matched': expected == project}
        checks.append(item)
        if not item['matched']:
            mismatches.append(item)

    for row in payload.get('lunar', []):
        _, month_pillar, day_pillar, hour_pillar = _pillars(row['result'])
        ly, lm, ld = (int(x) for x in row['date'].split('-'))
        ordinal = lm + (1 if row['is_leap'] and ld > 15 else 0)
        compare(row['id'], 'lunar_month_normal', month_pillar,
                ''.join(five_tiger_month(lunar_year_stem(ly), ordinal)))
        compare(row['id'], 'hour_from_external_exact_day_stem', hour_pillar,
                ''.join(five_mouse_hour(day_pillar[0], hour_pillar[1])))

    for row in payload.get('solar', []):
        _, _, day_pillar, hour_pillar = _pillars(row['result'])
        civil = _date(row['date'])
        effective = civil + timedelta(days=1) if row['time_index'] == 12 else civil
        day_tuple = sexagenary_day(effective)
        compare(row['id'], 'ziwei_effective_day_ganzhi', day_pillar, ''.join(day_tuple))
        compare(row['id'], 'hour_ganzhi', hour_pillar,
                ''.join(five_mouse_hour(day_tuple[0], hour_pillar[1])))

    matched = sum(x['matched'] for x in checks)
    return {
        'source_name': SOURCE_NAME,
        'source_revision': source_revision,
        'package_version': package_version,
        'rule_profile': FINE_CYCLE_PROFILE_ID,
        'rule_version': FINE_CYCLE_RULE_VERSION,
        'cases_checked': len(checks),
        'cases_matched': matched,
        'external_coverage': ['lunar_month_normal', 'leap_month_first_half', 'leap_month_second_half', 'regular_day_hour', 'late_zi_day_hour'],
        'not_externally_covered': ['leap_twelfth_month_second_half'],
        'source_contract': dict(source_contract),
        'checks': checks,
        'mismatches': mismatches,
        'status': 'PASS' if checks and matched == len(checks) and not mismatches else 'FAIL',
    }

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--vectors-json', required=True)
    p.add_argument('--ganzhi-source', required=True)
    p.add_argument('--revision', required=True)
    p.add_argument('--output-dir', required=True)
    a = p.parse_args(argv)
    payload = json.loads(Path(a.vectors_json).read_text(encoding='utf-8'))
    if payload.get('revision') != a.revision:
        _fail('external vector revision mismatch')
    version = payload.get('package_version')
    if version != '0.2.8':
        _fail('unexpected lunar-lite package version', {'version': version})
    contract = parse_lunar_lite_contract(Path(a.ganzhi_source).read_text(encoding='utf-8'))
    report = qualify_lunar_lite(payload, a.revision, version, contract)
    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'public-lunar-lite-1d104fff.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PUBLIC_LUNAR_LITE_QUALIFICATION_%s %d/%d' %
          (report['status'], report['cases_matched'], report['cases_checked']))
    return 0 if report['status'] == 'PASS' else 1

if __name__ == '__main__':
    raise SystemExit(main())

IZTRO_SOURCE_NAME = 'SylarLong/iztro'
IZTRO_PACKAGE_VERSION = '2.6.0'


def normalize_ts(source_text: str) -> str:
    return re.sub(r'\s+', '', source_text)


def _project_fine_cycle_sample_counts():
    from engine.calendar.resolver import resolve_calendar
    from engine.ziwei.fine_cycle_stems import resolve_day_stem, resolve_hour_stem, resolve_month_stem
    from engine.ziwei.transformations import get_transformation_set

    calendar = resolve_calendar('2023-07-30T21:30:00', 'Asia/Taipei')
    if not calendar.ok or calendar.context is None:
        _fail('Project calendar sample could not be resolved')
    context = calendar.context
    resolutions = (
        resolve_month_stem(context),
        resolve_day_stem(context),
        resolve_hour_stem(context),
    )
    counts = {}
    stems = {}
    for resolution in resolutions:
        transformation_set = get_transformation_set(resolution.heavenly_stem)
        counts[resolution.scope] = len(transformation_set.transformations)
        stems[resolution.scope] = resolution.heavenly_stem
    return counts, stems


def qualify_iztro_source(functional_source: str, source_revision: str, run_timestamp: str) -> dict:
    normalized = normalize_ts(functional_source)
    links = {
        'monthly': bool(re.search(r'monthly:\{[^}]*mutagen:getMutagensByHeavenlyStem\(monthly\[0\]\)', normalized)),
        'daily': bool(re.search(r'daily:\{[^}]*mutagen:getMutagensByHeavenlyStem\(daily\[0\]\)', normalized)),
        'hourly': bool(re.search(r'hourly:\{[^}]*mutagen:getMutagensByHeavenlyStem\(hourly\[0\]\)', normalized)),
    }
    missing = [scope for scope, ok in links.items() if not ok]
    if missing:
        _fail('iztro fine-cycle mutagen source linkage changed', {'missing_scopes': missing})
    counts, stems = _project_fine_cycle_sample_counts()
    if set(counts) != {'monthly', 'daily', 'hourly'} or any(value != 4 for value in counts.values()):
        _fail('Project fine-cycle transformation cardinality changed', {'counts': counts})
    return {
        'source_name': IZTRO_SOURCE_NAME,
        'source_revision': source_revision,
        'package_version': IZTRO_PACKAGE_VERSION,
        'run_timestamp': run_timestamp,
        'monthly_mutagen_uses_monthly_stem': links['monthly'],
        'daily_mutagen_uses_daily_stem': links['daily'],
        'hourly_mutagen_uses_hourly_stem': links['hourly'],
        'project_sample_transformations_each': 4,
        'project_sample_scopes': list(counts.keys()),
        'project_sample_stems': stems,
        'status': 'PASS',
    }
