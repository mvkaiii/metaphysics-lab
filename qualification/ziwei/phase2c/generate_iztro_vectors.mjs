#!/usr/bin/env node

import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const require = createRequire(import.meta.url);

const PINNED_VERSION = '2.6.0';
const PINNED_REVISION = '814b77e6371e1050cac31bbf674db3c3138fcfde';
const PROFILE_ID = 'ziwei-flowing-stars-common-v1';
const SCOPES = ['decadal', 'yearly', 'monthly', 'daily', 'hourly'];
const STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
const BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
const PALACE_INDEX_TO_BRANCH = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑'];
const BASE_CATALOG = ['天魁', '天鉞', '文昌', '文曲', '祿存', '擎羊', '陀羅', '天馬', '紅鸞', '天喜'];
const SUFFIX = {
  天魁: '魁', 天鉞: '鉞', 文昌: '昌', 文曲: '曲', 祿存: '祿',
  擎羊: '羊', 陀羅: '陀', 天馬: '馬', 紅鸞: '鸞', 天喜: '喜',
};
const PREFIX = { decadal: '運', yearly: '流', monthly: '月', daily: '日', hourly: '時' };
const SOURCE_FILES = [
  'src/star/horoscopeStar.ts',
  'src/star/location.ts',
  'src/utils/index.ts',
  'src/i18n/locales/zh-TW/star.ts',
];

function fail(message) {
  process.stderr.write(`Phase 2C iztro generator error: ${message}\n`);
  process.exit(2);
}

function normalizeRoot(raw) {
  if (!raw) fail('usage: generate_iztro_vectors.mjs <built-iztro-checkout>');
  const root = path.resolve(raw);
  if (!fs.existsSync(path.join(root, 'package.json'))) fail(`package.json not found: ${root}`);
  if (!fs.existsSync(path.join(root, 'lib', 'index.js'))) fail(`built lib/index.js not found: ${root}`);
  return root;
}

function verifyPinnedCheckout(root) {
  const pkg = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
  if (pkg.name !== 'iztro' || pkg.version !== PINNED_VERSION) {
    fail(`expected iztro ${PINNED_VERSION}, got ${pkg.name} ${pkg.version}`);
  }
  const revision = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim();
  if (revision !== PINNED_REVISION) fail(`expected revision ${PINNED_REVISION}, got ${revision}`);
  for (const sourceFile of SOURCE_FILES) {
    if (!fs.existsSync(path.join(root, sourceFile))) fail(`missing pinned source file: ${sourceFile}`);
  }
  return { pkg, revision };
}

function displayNameMap(scope) {
  const result = new Map();
  for (const baseStar of BASE_CATALOG) result.set(`${PREFIX[scope]}${SUFFIX[baseStar]}`, baseStar);
  if (scope === 'yearly') result.set('年解', '年解');
  return result;
}

function extractPlacements(getHoroscopeStar, scope, stem, branch) {
  const byPalace = getHoroscopeStar(stem, branch, scope);
  if (!Array.isArray(byPalace) || byPalace.length !== 12) fail(`unexpected palace array for ${scope}/${stem}${branch}`);
  const names = displayNameMap(scope);
  const found = [];
  byPalace.forEach((stars, palaceIndex) => {
    if (!Array.isArray(stars)) fail(`unexpected stars array at palace ${palaceIndex}`);
    for (const star of stars) {
      const baseStar = names.get(star.name);
      if (!baseStar) fail(`excluded or unknown star ${String(star.name)} in ${scope}/${stem}${branch}`);
      found.push({ base_star: baseStar, category: star.type, target_branch: PALACE_INDEX_TO_BRANCH[palaceIndex] });
    }
  });

  const order = scope === 'yearly' ? [...BASE_CATALOG, '年解'] : BASE_CATALOG;
  if (found.length !== order.length) fail(`expected ${order.length} placements, got ${found.length} for ${scope}/${stem}${branch}`);
  if (new Set(found.map((item) => item.base_star)).size !== order.length) fail(`duplicate base star in ${scope}/${stem}${branch}`);
  const byBase = new Map(found.map((item) => [item.base_star, item]));
  for (const baseStar of order) {
    if (!byBase.has(baseStar)) fail(`missing ${baseStar} in ${scope}/${stem}${branch}`);
  }
  return order.map((baseStar) => byBase.get(baseStar));
}

const root = normalizeRoot(process.argv[2]);
const { pkg, revision } = verifyPinnedCheckout(root);
const iztro = require(path.join(root, 'lib', 'index.js'));
const i18n = require(path.join(root, 'lib', 'i18n', 'index.js'));
if (!iztro?.star?.getHoroscopeStar) fail('star.getHoroscopeStar export not found');
if (typeof i18n.setLanguage !== 'function') fail('i18n.setLanguage export not found');
i18n.setLanguage('zh-TW');

const getHoroscopeStar = iztro.star.getHoroscopeStar;
const cases = [];
let placementCheckCount = 0;
for (const scope of SCOPES) {
  for (const stem of STEMS) {
    for (const branch of BRANCHES) {
      const placements = extractPlacements(getHoroscopeStar, scope, stem, branch);
      placementCheckCount += placements.length;
      cases.push({ scope, stem, branch, placements });
    }
  }
}

const goldenAnchors = [
  { scope: 'decadal', stem: '庚', branch: '辰' },
  { scope: 'yearly', stem: '癸', branch: '卯' },
].map((anchor) => ({ ...anchor, placements: extractPlacements(getHoroscopeStar, anchor.scope, anchor.stem, anchor.branch) }));

if (cases.length !== 600) fail(`expected 600 cases, got ${cases.length}`);
if (placementCheckCount !== 6120) fail(`expected 6120 placements, got ${placementCheckCount}`);

const output = {
  schema: 'metaphysics-lab.ziwei.phase2c.public-qualification.v1',
  profile_id: PROFILE_ID,
  oracle: {
    repository: 'SylarLong/iztro',
    package_version: pkg.version,
    revision,
    language: 'zh-TW',
    source_files: SOURCE_FILES,
    palace_index_order: PALACE_INDEX_TO_BRANCH,
  },
  scopes: SCOPES,
  stems: STEMS,
  branches: BRANCHES,
  source_case_count: cases.length,
  placement_check_count: placementCheckCount,
  golden_anchors: goldenAnchors,
  cases,
};

process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
