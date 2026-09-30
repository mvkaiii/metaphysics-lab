'use strict';

// Independent implementation of the supplied execution contract v2.1.
// No evaluated-system code, output, comparisons or qualification data is used.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const INPUT = path.resolve(__dirname, '../gate_extract');
const SOURCE = __filename;
const HASH_FILE = path.join(__dirname, 'oracle-source.sha256');
const OUTPUT = path.join(__dirname, 'oracle-output.json');
const RECEIPT = path.join(__dirname, 'sealing-receipt.json');
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const read = name => fs.readFileSync(path.join(INPUT, name));
const json = name => JSON.parse(read(name));
const canonical = value => {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value && typeof value === 'object') {
    return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
  }
  return JSON.stringify(value);
};
const hashWithout = (value, field) => {
  const copy = { ...value };
  delete copy[field];
  return sha(canonical(copy));
};
const paths = [
  '/decadal_direction', '/periods/0/pillar', '/periods/0/start_age_years',
  '/periods/0/start_datetime', '/periods/1/end_datetime'
];
const now = () => new Date(Date.now() + 8 * 3600000).toISOString().replace('Z', '+08:00');

// This record must exist BEFORE this executable can compute expected values.
assert(!fs.existsSync(OUTPUT) && !fs.existsSync(RECEIPT), 'Refuse to overwrite prior execution artifacts');
const frozenRecord = fs.readFileSync(HASH_FILE, 'utf8');
assert(/^[a-f0-9]{64}  oracle\.cjs\r?\n$/.test(frozenRecord), 'Missing/invalid source freeze record');
const frozenHash = frozenRecord.slice(0, 64);
assert.equal(sha(fs.readFileSync(SOURCE)), frozenHash, 'Frozen source SHA256 mismatch');
const freezeRecordedAt = new Date(fs.statSync(HASH_FILE).mtimeMs + 8 * 3600000).toISOString().replace('Z', '+08:00');

// Revalidate immutable input bindings before doing any oracle calculations.
for (const line of read('SHA256SUMS').toString('utf8').trim().split(/\r?\n/)) {
  const match = /^([a-f0-9]{64})\s+([^/\\]+)$/.exec(line);
  assert(match, 'Invalid SHA256SUMS entry');
  assert.equal(sha(read(match[2])), match[1]);
}
const manifest = json('handoff-manifest.v2.1.json');
for (const [name, entry] of Object.entries(manifest.files)) {
  assert.equal(read(name).length, entry.bytes);
  assert.equal(sha(read(name)), entry.sha256);
}
const bundle = json('bazi-decadal-oracle-case-inputs.v2.1.json');
const seal = json('bazi-decadal-preoracle-seal.v2.1.json');
const bindings = json('source-bindings.json');
const contract = read('bazi-decadal-independent-oracle-contract.v2.1.md').toString('utf8');
assert.equal(sha(Buffer.from(contract)), manifest.execution_contract_sha256);
assert.equal(seal.profile.specification_sha256, manifest.execution_contract_sha256);
assert.equal(hashWithout(bundle, 'bundle_sha256'), bundle.bundle_sha256);
assert.equal(bundle.bundle_sha256, manifest.case_bundle_sha256);
assert.equal(hashWithout(seal, 'seal_sha256'), seal.seal_sha256);
assert.equal(seal.seal_sha256, manifest.preoracle_seal_sha256);
assert.equal(bundle.expected_values_present, false);
assert.equal(manifest.expected_values_present, false);
assert.equal(seal.independence_boundary.expected_values_present, false);
assert.equal(bundle.cases.length, 12);
assert.equal(seal.case_census.length, 12);
for (const [i, c] of bundle.cases.entries()) {
  assert.equal(c.case_id, 'bdv2-' + String(i + 1).padStart(3, '0'));
  assert.deepEqual(Object.keys(c).sort(), ['case_id', 'coverage_tags', 'input', 'input_sha256']);
  assert.deepEqual(Object.keys(c.input).sort(), ['birth_datetime', 'sex', 'timezone']);
  assert.equal(c.input.timezone, 'Asia/Taipei');
  assert(['male', 'female'].includes(c.input.sex));
  assert.equal(sha(canonical(c.input)), c.input_sha256);
  assert.equal(seal.case_census[i].case_id, c.case_id);
  assert.equal(seal.case_census[i].input_sha256, c.input_sha256);
  assert.deepEqual(seal.case_census[i].coverage_tags, c.coverage_tags);
  assert.deepEqual(seal.case_census[i].comparisons.map(x => x.path), paths);
}

// Parse actual table tokens, including the 2015 omitted td closing tags.
// A following td implicitly closes the preceding td; original bytes stay intact.
function tableRows(html) {
  const rows = [];
  let row = null, cell = null;
  const closeCell = () => {
    if (cell !== null && row !== null) {
      row.push(cell.replace(/&nbsp;|&#160;/g, ' ').replace(/&amp;/g, '&').replace(/\s+/g, ' ').trim());
    }
    cell = null;
  };
  for (const token of html.match(/<[^>]*>|[^<]+/g) || []) {
    if (/^<tr\b/i.test(token)) row = [];
    else if (/^<\/(?:td|th)\s*>/i.test(token)) closeCell();
    else if (/^<(?:td|th)\b/i.test(token) && row !== null) { closeCell(); cell = ''; }
    else if (/^<\/tr\s*>/i.test(token) && row !== null) { closeCell(); rows.push(row); row = null; }
    else if (!token.startsWith('<') && cell !== null) cell += token;
  }
  return rows;
}
const jieMapping = [...contract.matchAll(/^\| ([^|]+?) \| ([^|]+?) \|$/gm)]
  .map(m => [m[1].trim(), m[2].trim()]).filter(([label]) => !['HKO label', '---'].includes(label));
assert.equal(jieMapping.length, 12);
const monthJie = ['立春', '驚蟄', '清明', '立夏', '芒種', '小暑', '立秋', '白露', '寒露', '立冬', '大雪', '小寒'];
const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const NS = 1000000000n;
function parseBirth(text) {
  assert(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$/.test(text));
  const ms = Date.parse(text);
  assert(Number.isFinite(ms));
  assert.equal(new Date(ms + 8 * 3600000).toISOString().slice(0, 19) + '+08:00', text);
  return BigInt(ms) * 1000000n;
}
function formatDatetime(ns) {
  // Final serialization only: exact seconds plus any fractional nanoseconds.
  const seconds = ns / NS, fraction = ns % NS;
  const civil = new Date(Number(seconds) * 1000 + 8 * 3600000).toISOString().slice(0, 19);
  return civil + (fraction ? '.' + fraction.toString().padStart(9, '0').replace(/0+$/, '') : '') + '+08:00';
}
const jie = [];
for (const source of bindings.sources) {
  const raw = read(source.file);
  assert.equal(sha(raw), source.sha256);
  assert.equal(seal.source_bindings.find(x => x.source_file_label === source.file).source_sha256, source.sha256);
  const html = new TextDecoder('utf-8', { fatal: true }).decode(raw);
  assert(html.includes('Hong Kong Time') && html.includes('eight hours ahead'));
  const rows = tableRows(html).filter(r => r.length === 4 && /^\d{2}:\d{2}$/.test(r[3]));
  assert.equal(rows.length, 24);
  assert.equal(new Set(rows.map(r => r[0])).size, 24);
  for (const [label, name] of jieMapping) {
    const matches = rows.filter(r => r[0] === label);
    assert.equal(matches.length, 1);
    const [, day, month, time] = matches[0];
    const m = months.indexOf(month) + 1;
    assert(m > 0);
    const iso = `${source.year}-${String(m).padStart(2, '0')}-${day.padStart(2, '0')}T${time}:00+08:00`;
    jie.push({ year: source.year, name, instant: parseBirth(iso) });
  }
}
jie.sort((a, b) => a.instant < b.instant ? -1 : a.instant > b.instant ? 1 : 0);

const GAN = [...'甲乙丙丁戊己庚辛壬癸'];
const ZHI = [...'子丑寅卯辰巳午未申酉戌亥'];
const cycle = Array.from({ length: 60 }, (_, i) => GAN[i % 10] + ZHI[i % 12]);
const mod = (n, d) => ((n % d) + d) % d;
const TEN_YEARS_NS = 315569520n * NS; // 10 * 365.2425 * 86400 seconds, exact.
function execute(c) {
  const birth = parseBirth(c.input.birth_datetime);
  const year = Number(c.input.birth_datetime.slice(0, 4));
  const spring = jie.find(j => j.year === year && j.name === '立春');
  assert(spring);
  const pillarYear = birth >= spring.instant ? year : year - 1;
  const ganIndex = mod(pillarYear - 4, 10);
  const yearPillar = GAN[ganIndex] + ZHI[mod(pillarYear - 4, 12)];
  assert(yearPillar.length === 2);
  const latest = jie.filter(j => j.instant <= birth).at(-1);
  assert(latest, 'Required prior Jie absent');
  const monthIndex = monthJie.indexOf(latest.name);
  assert(monthIndex >= 0);
  const firstGan = ((ganIndex % 5) * 2 + 2) % 10;
  const monthPillar = GAN[(firstGan + monthIndex) % 10] + ZHI[(2 + monthIndex) % 12];
  const forward = (ganIndex % 2 === 0) === (c.input.sex === 'male');
  const direction = forward ? 'forward' : 'reverse';
  const selected = forward ? jie.find(j => j.instant >= birth) : latest;
  assert(selected, 'Required start Jie absent');
  const intervalNs = forward ? selected.instant - birth : birth - selected.instant;
  assert(intervalNs >= 0n && intervalNs % NS === 0n);
  const intervalSeconds = intervalNs / NS;
  // Exact algebra of sections 7 and 9, no rounded intermediate age:
  // (interval_seconds / (3*86400)) * 365.2425 * 86400
  // = interval_seconds * 121.7475 seconds.
  const startNs = birth + intervalSeconds * 121747500000n;
  const index = cycle.indexOf(monthPillar);
  assert(index >= 0 && cycle.lastIndexOf(monthPillar) === index);
  const step = forward ? 1 : -1;
  const periods = Array.from({ length: 10 }, (_, i) => ({
    pillar: cycle[mod(index + step * (i + 1), 60)],
    startAgeNumerator: intervalSeconds + BigInt(10 * i) * 259200n,
    endAgeNumerator: intervalSeconds + BigInt(10 * (i + 1)) * 259200n,
    start: startNs + BigInt(i) * TEN_YEARS_NS,
    end: startNs + BigInt(i + 1) * TEN_YEARS_NS
  }));
  assert.equal(periods.length, 10);
  if (intervalSeconds === 0n) assert.equal(startNs, birth);
  return {
    case_id: c.case_id,
    input_sha256: c.input_sha256,
    expected_values: {
      '/decadal_direction': direction,
      '/periods/0/pillar': periods[0].pillar,
      '/periods/0/start_age_years': Number(periods[0].startAgeNumerator) / 259200,
      '/periods/0/start_datetime': formatDatetime(periods[0].start),
      '/periods/1/end_datetime': formatDatetime(periods[1].end)
    }
  };
}

// First expected-value generation occurs only after all source/input guards.
assert.equal(sha(fs.readFileSync(SOURCE)), frozenHash);
const generationStartedAt = now();
const results = bundle.cases.map(execute);
assert.equal(results.length, 12);
for (const result of results) assert.deepEqual(Object.keys(result.expected_values), paths);
const output = {
  schema_version: '1.0', bundle_type: 'bazi_decadal_independent_oracle_output',
  execution_contract_sha256: manifest.execution_contract_sha256,
  case_bundle_sha256: bundle.bundle_sha256, preoracle_seal_sha256: seal.seal_sha256,
  oracle_source_sha256: frozenHash, comparison_paths: paths,
  source_precision_seconds: 60, source_precision_policy: 'conservative +/-60 seconds',
  cases: results
};
fs.writeFileSync(OUTPUT, JSON.stringify(output, null, 2) + '\n', { flag: 'wx' });
const afterHash = sha(fs.readFileSync(SOURCE));
assert.equal(afterHash, frozenHash, 'Source changed after expected-value generation');
// Check every supplied file again after generation; no inputs are written.
for (const line of read('SHA256SUMS').toString('utf8').trim().split(/\r?\n/)) {
  const [, h, name] = /^([a-f0-9]{64})\s+([^/\\]+)$/.exec(line);
  assert.equal(sha(read(name)), h);
}
const receipt = {
  pre_execution_gate: 'PASS',
  pre_execution_gate_confirmed_by_user: true,
  oracle_source_frozen_before_expected_value_generation: true,
  freeze_method: 'exclusive SHA256 record written and source marked read-only before execution; digest checked before generation and after output',
  freeze_recorded_at: freezeRecordedAt,
  expected_value_generation_started_at: generationStartedAt,
  execution_completed_at: now(),
  oracle_source_file: 'oracle.cjs', oracle_source_sha256: frozenHash,
  oracle_source_sha256_after_generation: afterHash,
  oracle_source_unmodified_after_expected_value_generation: true,
  sealed_case_count: 12, executed_case_count: results.length,
  executed_case_ids: results.map(r => r.case_id),
  production_code_accessed: false, production_output_accessed: false,
  production_code_output_accessed: false, production_comparison_performed: false,
  prior_comparison_outcomes_accessed: false, prior_qualification_outcomes_accessed: false,
  comparison_paths: paths, inputs_unmodified_after_execution: true,
  execution_contract_sha256: manifest.execution_contract_sha256,
  case_bundle_sha256: bundle.bundle_sha256, preoracle_seal_sha256: seal.seal_sha256,
  oracle_output_file: 'oracle-output.json', oracle_output_sha256: sha(fs.readFileSync(OUTPUT)),
  runtime: process.version, datetime_arithmetic: 'exact integer nanoseconds; final start_age_years serialized as JSON number',
  source_precision_seconds: 60, source_precision_policy: 'conservative +/-60 seconds'
};
fs.writeFileSync(RECEIPT, JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ executed_case_count: results.length, oracle_source_sha256: frozenHash, oracle_output_sha256: receipt.oracle_output_sha256, source_unchanged: afterHash === frozenHash }));
