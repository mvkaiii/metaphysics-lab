# Metaphysics Lab Portable Offline Natal Pipeline｜設計規格

- 日期：2026-08-24
- Branch：`design/portable-offline-natal-pipeline`
- 狀態：Design spec，等待使用者 final review；尚未進入 implementation plan
- 分類：Architectural
- Base：`main` commit `86e951a71132b8b499429493c966558ec9e5fd9f`
- 產品目標：讓單一 `metaphysics_lab.py` 在乾淨 Python 環境中，不需 `pip install`、不需網路、也不需 Astralium，即可用「性別 + 出生日期 + 出生時間 + Project offline registry 可辨識的出生地」建立完整 Project 原生本命盤
- 核心方案：Private Vendored Runtime + Bundled Offline Birth Place Registry
- 不變原則：repo 內維持模組化；八字／紫微核心演算法與已通過 qualification 的命盤規則不因本階段任意改寫；Astralium 維持 optional cross-check；Project Natal maturity 不在本階段自動升 Stable

---

## 一、背景與問題定義

目前 Metaphysics Lab 的一般使用者安裝流程已收斂為三個對外 distribution artifacts：

```text
metaphysics_lab.py
metaphysics_core.md
project_instructions.md
```

README 的產品心智模型是：一般使用者只需要下載上述檔案，將出生資料交給 AI，即可由 Project 原生 engine 建立八字與紫微本命；Astralium 或其他第三方命盤只作交叉校驗，不是基本安裝必要條件。

但目前 portable runtime 仍存在一個 deployment gap：

1. generated bundle 只內嵌 Metaphysics Lab owned runtime source。
2. `lunar-python==1.4.8` 與 `tzdata==2026.3` 仍由 host Python environment 提供。
3. `build_natal` 在 `python -S` 或缺少 site-packages 的乾淨環境中無法完成核心 calendar resolution。
4. 出生地若沒有預先提供 `resolved_location`，目前只能走 explicit network resolver 或 fail closed。

這表示目前「只有一支 `metaphysics_lab.py` 就能完成 Natal」並未成為真正的 deployment contract。

本階段要修正的是 **portable execution architecture**，不是重寫命理規則。

---

## 二、正式產品契約

### 2.1 Portable 的正式定義

本階段完成後，`metaphysics_lab.py` 的核心 Natal path 必須滿足：

```text
Python standard library
+
metaphysics_lab.py
+
出生資料
=
可完成 Project Natal
```

對 offline registry 已支援的出生地，不允許再要求：

- `pip install lunar-python`
- `pip install tzdata`
- `pip install geopy`
- `pip install timezonefinder`
- 網路連線
- Astralium
- repo source tree
- 另外一個 vendor ZIP

### 2.2 Astralium 定位不變

Astralium、其他排盤網站、命理軟體與命理師資料仍屬：

```text
External Natal Source
```

用途：

- 外部交叉校驗
- reconciliation
- 保存第三方盤面差異

不得因使用者沒有 Astralium 而阻止 Project Natal。

不得把 Astralium 的出生地或盤面偷偷轉成 Project 原生計算 authority。

### 2.3 Project Natal maturity 不變

本階段只提升 deployment portability，不代表命理 capability 自動升 Stable。

因此既有 Project Natal source metadata 中的 experimental maturity、qualification status 與 capability governance，除非有獨立 evidence 支持，均維持現有正式規則。

---

## 三、正式架構決策

採用：

**Private Vendored Runtime + Bundled Offline Birth Place Registry**

整體結構：

```text
metaphysics_lab.py
│
├─ embedded Metaphysics Lab owned runtime
│
├─ embedded private vendor runtime
│  ├─ lunar-python 1.4.8
│  └─ tzdata 2026.3 / IANA 2026c
│
├─ embedded offline birth-place registry
├─ embedded third-party provenance / license manifest
│
└─ optional external integrations
   ├─ geopy
   └─ timezonefinder
```

Project Natal flow：

```text
birth payload
    │
    ▼
Birth Input Resolution
    │
    ▼
Location Resolution Authority
    │
    ├─ explicit resolved_location
    ├─ Project Offline Registry
    └─ explicit network fallback
    │
    ▼
ResolvedBirthPlace
    │
    ▼
Bundled Calendar Runtime
    ├─ private bundled tzdata
    └─ private bundled lunar-python
    │
    ├──────────────┐
    ▼              ▼
Project Bazi   Project Ziwei
    └──────┬───────┘
           ▼
   ProjectNatalView
           ▼
 NormalizedNatalChart
```

---

## 四、Hard Invariants

以下屬本設計不可在 implementation 中弱化的 invariant。

### 4.1 Core dependency authority 不得來自 host

對核心 Natal path：

```text
lunar-python
+
tzdata
```

計算 authority 必須永遠來自 Metaphysics Lab bundled vendor bytes。

host environment：

- 沒有套件
- 有相同版本
- 有舊版本
- 有新版本
- 已先 import 同名 host package

都不得改變 Project 結果。

### 4.2 不使用 top-level vendor import name

Project-owned runtime 不得把核心計算依賴繼續視為：

```python
import lunar_python
import tzdata
```

private vendor 必須有不與 host package 共用的 namespace。

建議 namespace：

```text
_metaphysics_lab_vendor.lunar_python
_metaphysics_lab_vendor.tzdata
```

實際 module root 若 implementation plan 有充分理由可微調，但必須維持：

- private namespace
- host 不可覆蓋
- bundled origin 可驗證

### 4.3 Offline location 不可由 AI 猜測

出生地座標與 timezone 必須來自：

- explicit `resolved_location`
- committed Project offline registry
- explicit network provider

不得使用：

- LLM 常識補座標
- 自動猜錯字
- 不可重現的 fuzzy matching
- 看似合理的 timezone 推測

### 4.4 Ambiguity 必須 fail closed

同一 location query 若對應多個 material candidate，不得自行挑一筆。

正式 error code沿用既有：

```text
ambiguous_birth_place
```

### 4.5 Distribution build 不得自動下載 dependency

一般 distribution build 必須完全由 committed repo state 產生。

禁止：

```text
build 時 pip install
build 時 PyPI download
build 時 GitHub fetch vendor source
build 時 live geocoding
```

vendor refresh 必須是另一個明確、可稽核的 maintenance flow。

### 4.6 Modular runtime 與 bundle 使用同一份 vendor authority

repo test execution與generated bundle不得一邊使用host package、一邊使用vendor package。

兩者都必須由同一份 committed vendor source / binary bytes建立，以維持真正的 parity。

---

## 五、Private Vendor Runtime

### 5.1 Canonical vendor layout

建議 repo 新增：

```text
vendor/
├─ manifest.json
├─ licenses/
│  ├─ lunar-python-LICENSE.txt
│  ├─ tzdata-LICENSE.txt
│  └─ THIRD_PARTY_NOTICES.md
│
└─ python/
   └─ _metaphysics_lab_vendor/
      ├─ __init__.py
      ├─ lunar_python/
      │  └─ ...
      └─ tzdata/
         ├─ __init__.py
         └─ zoneinfo/
            └─ ... binary TZif resources ...
```

這是建議 ownership boundary，不要求 implementation 必須逐字採用路徑；但以下責任必須存在：

- vendor manifest
- vendored package bytes
- bundled license notices
- private namespace
- binary resource support

### 5.2 `lunar-python` pin

正式 pin：

```text
package: lunar-python
version: 1.4.8
source revision: 000c8a3d74eed098d6256a28fdd51b869324c559
license: MIT
```

本階段不得修改 upstream calendar logic 以追求「更準」。

若未來要修改 upstream algorithm，必須是獨立 capability / calendar qualification change，不可混進 portable distribution work。

### 5.3 `tzdata` pin

正式 pin：

```text
package: tzdata
version: 2026.3
IANA tzdb: 2026c
license: Apache-2.0
```

Project timezone provider必須讀 bundled zoneinfo resource，不依賴：

- host OS `/usr/share/zoneinfo`
- host installed `tzdata`
- host IANA version

### 5.4 Private import compatibility qualification

vendor refresh必須對 vendored package 執行 import graph / source scan，確認：

- package internal imports不會跳回host top-level package
- 沒有意外 dependency on undeclared third-party package
- package可以從private namespace載入

不得只靠抽查一兩個檔案推定全package安全。

---

## 六、Vendor Manifest 與 Supply-chain Contract

### 6.1 Manifest 最低欄位

每個 bundled dependency至少保存：

```text
package_name
import_namespace
version
source_repository
source_revision
source_artifact
artifact_sha256
vendored_tree_sha256
license_spdx
license_file
bundled
runtime_authority
```

`runtime_authority` 對 `lunar-python` 與 `tzdata` 必須明確表示：

```text
bundled
```

而不是 `host`。

### 6.2 Build-time verification

正式 build 前必須驗證：

1. manifest存在。
2. license file存在。
3. declared vendor tree存在。
4. tree checksum符合manifest。
5. package metadata符合expected pin。
6. private import scan通過。
7. 不含symlink escape。
8. 不含超出allowlist的vendor path。

任一失敗：

```text
build fail closed
```

### 6.3 Vendor refresh

vendor refresh是maintenance action，不是distribution build的一部分。

正式流程概念：

```text
指定 package / version / source
        ↓
下載固定 artifact
        ↓
驗 upstream artifact hash
        ↓
extract 到 staging
        ↓
namespace transformation / packaging
        ↓
license capture
        ↓
import scan
        ↓
compute vendored tree hash
        ↓
reviewable repo change
```

refresh tool若需要network可以接受，但必須：

- explicit command
- deterministic input
- 固定version
- 驗checksum
- 不在runtime執行

---

## 七、Generated Bundle Payload Format

### 7.1 現況問題

目前 distribution builder 只適合 UTF-8文字檔：

- `engine/**/*.py`
- `templates/**/*.tmpl`

但 `tzdata.zoneinfo` 包含binary TZif resource。

因此舊payload format無法成為portable timezone runtime的正式基礎。

### 7.2 Build format upgrade

正式要求：

```text
BUILD_FORMAT_VERSION 1.0 → 1.1
```

新payload必須是byte-oriented。

每筆record最低包含：

```text
path
sha256
encoding
content
```

其中：

- `encoding`可為固定 `base64`，或其他經spec明確定義的byte-safe encoding。
- `content`解碼後必須逐檔驗 `sha256`。
- 第一方文字檔可在進payload前沿用既有newline normalization。
- vendor source與binary resource必須byte-for-byte保存。

### 7.3 Extraction security

bundle extract時必須拒絕：

- absolute path
- `..`
- duplicate target path
- invalid path component
- payload record checksum mismatch
- overall source digest mismatch

不得讓embedded payload寫出runtime temp root之外。

### 7.4 SOURCE_DIGEST

現有整體`SOURCE_DIGEST`概念保留。

新digest authority必須涵蓋：

- owned runtime source
- templates
- bundled dependencies
- bundled registry
- vendor manifest
- required third-party notices

這樣同一source tree才能產生可稽核的同一distribution。

---

## 八、Offline Birth Place Registry

### 8.1 定位

本階段不建立全球地址搜尋引擎。

Offline registry只負責：

```text
常見 birth-place label
→ deterministic canonical place
→ latitude / longitude / timezone
```

### 8.2 建議資料位置

```text
data/birth_places/
├─ registry.v1.json
├─ schema.v1.json
└─ SOURCES.md
```

實際檔名可在implementation plan微調，但registry必須是：

- committed
- versioned
- deterministic
- reviewable
- bundled

### 8.3 Canonical record schema

每筆record至少包含：

```text
record_id
canonical_name
country_code
admin_area
latitude
longitude
timezone
aliases
source
source_version
source_reference
```

`aliases`必須是明確清單，不依賴runtime NLP猜測。

### 8.4 v1 coverage policy

v1正式保證：

1. 台灣縣市層級完整offline coverage。
2. 常見台灣繁體中文與英文別名。
3. Project明確收錄的國際主要城市。
4. 實際coverage以registry內容為準，不做「全球城市皆支援」的產品承諾。

### 8.5 Geographic source policy

正式registry資料不得由AI自由生成。

每筆canonical data必須能回溯來源。

允許使用有明確授權與版本資訊的geographic dataset作為source，例如GeoNames；但本階段只bundle經Project篩選的必要records，不bundle整套全球database。

如果採用GeoNames或其他第三方geodata，必須把其license / attribution納入vendor／data notice治理。

---

## 九、Alias Normalization Contract

### 9.1 Runtime normalization只做有限、可重現轉換

允許：

```text
Unicode NFKC
trim
case folding
collapse whitespace
有限標點／separator normalization
```

不允許：

```text
LLM fuzzy matching
phonetic guessing
自動翻譯
自動行政區推測
任意簡繁轉換
自動修正拼字
```

### 9.2 Alias equality由資料宣告，不由演算法猜

例如：

```text
台北
臺北
台北市
臺北市
Taipei
Taipei City
```

是否相等，必須因為registry明確列為同一canonical record的aliases，而不是resolver自行推理。

### 9.3 Ambiguous alias

normalized query若命中多個record：

```text
ambiguous_birth_place
```

details最低包含：

```text
query
candidate_count
candidates[]
```

candidate應提供足以讓AI或使用者選擇的識別資訊，例如：

```text
canonical_name
country_code
admin_area
record_id
```

不得自動選第一筆。

### 9.4 Unknown alias

完全沒有record：

```text
location_not_resolved
```

若network fallback沒有explicit enable，流程在此停止。

---

## 十、Location Resolution Precedence

正式precedence固定為：

```text
1. explicit resolved_location
2. Project Offline Registry
3. explicitly enabled network resolver
4. fail closed
```

### 10.1 Explicit `resolved_location`

維持現有 backward-compatible authority。

現有欄位要求繼續有效：

```text
canonical_name
latitude
longitude
timezone
provider_name
provider_version
```

`provider_reference`保持optional。

### 10.2 Project Offline Registry

offline唯一命中時，產生標準`ResolvedBirthPlace`。

建議provenance：

```text
provider_name = metaphysics_lab_offline_registry
provider_version = 1.0
provider_reference = <source-id / record-id>
resolution_status = resolved
```

### 10.3 Ambiguous offline result不可fall through network

若offline registry已知道此query存在多個candidate，這代表使用者輸入不夠精確。

此時即使network resolver已enable，也必須：

```text
ambiguous_birth_place
```

不得讓network provider替使用者偷偷做disambiguation。

### 10.4 Offline miss才可進network fallback

只有：

```text
offline candidate count = 0
+
network_location.enabled = true
```

才進現有Nominatim＋TimezoneFinder external path。

如果network沒有enable：

```text
location_not_resolved
```

---

## 十一、External Network Location Boundary

### 11.1 Network resolver保持optional

`geopy`與`timezonefinder`不進核心portable dependency。

理由：

- offline Natal不需要它們
- `geopy`本身需要network provider
- `timezonefinder`相對大型，且只為external network geocode後補timezone

### 11.2 Network依賴仍可由host提供

這兩者是optional external integrations，因此可以維持host dependency model。

正式必須清楚區分：

```text
Bundled Core Dependencies
vs
Optional External Dependencies
```

### 11.3 Network provenance不得偽裝成offline

Nominatim／TimezoneFinder輸出的location不得寫成Project offline provider。

同理，user-supplied `resolved_location`也保留其自身provider provenance。

---

## 十二、Calendar Runtime Refactor Boundary

### 12.1 `lunar-python`

現有calendar provider應從host-oriented provider改為bundled provider。

正式要求：

- 使用private bundled lunar source
- 版本metadata讀vendor authority
- 不再以host `importlib.metadata.version("lunar_python")` 作核心計算資格判斷

### 12.2 `tzdata`

現有`PinnedTzdataProvider`概念保留：

- pinned package version
- pinned IANA version
- explicit resource load

但resource authority改為private bundled tzdata package。

### 12.3 Existing calendar qualification不因bundling失效

本階段不可因「套件現在變成vendor」就刪除既有：

- Gregorian / lunar validation range
- HKO validation profile
- known conflict window
- caution boundary
- timezone ambiguity / nonexistent local time處理

portable architecture只改provider source，不改已核准的calendar correctness contract。

---

## 十三、Natal Pipeline Contract

### 13.1 Offline happy path

正式最小input：

```json
{
  "birth": {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time": "19:20",
    "birth_place": "台北市"
  }
}
```

若`台北市`在offline registry唯一命中，`build_natal`必須在：

- no site-packages
- no network
- no Astralium
- no explicit `resolved_location`

條件下完成。

### 13.2 Output shape

本階段不要求破壞現有`build_natal` output shape。

仍回：

```text
input_resolution
resolved_location
project_natal
normalized_natal
```

`resolved_location`增加offline provenance，但維持既有資料模型。

### 13.3 Candidate Envelope

`natal.candidate_envelope`目前要求pre-resolved location。

本階段設計允許implementation將它接入相同offline resolver，前提是：

- 不改Candidate Envelope核心精度規則
- ambiguity同樣fail closed
- output schema不發生無理由breaking change

若implementation plan判斷Candidate Envelope接入offline resolver會擴大scope，可保留既有explicit resolved location要求；但核心`build_natal` offline path必須完成。

---

## 十四、`runtime_info` 新 Dependency Contract

### 14.1 問題

目前所有runtime dependency都被集中在：

```text
external_dependencies
```

portable architecture完成後，這已不能表達真正execution authority。

### 14.2 Canonical schema

`runtime_info.data`新增：

```text
dependency_authority
bundled_dependencies
optional_external_dependencies
offline_location_registry
```

### 14.3 `bundled_dependencies`

每項最低回傳：

```text
package
version
bundled
available
runtime_uses_host
source_revision
artifact_sha256
vendored_tree_sha256
license
role
required_for
```

`lunar-python`與`tzdata`必須：

```text
bundled = true
available = true
runtime_uses_host = false
```

在`python -S`下仍成立。

### 14.4 `optional_external_dependencies`

保留host inspection semantics給：

```text
geopy
timezonefinder
```

可繼續回：

```text
installed
version
matches_pin
```

但明確標示它們不是核心Natal dependency。

### 14.5 `offline_location_registry`

最低回：

```text
version
record_count
coverage_profile
source_profiles
bundled
```

不得在runtime_info裡回整份aliases或大量資料。

### 14.6 Backward compatibility

舊`external_dependencies`保留至少一個runtime schema generation作compatibility view。

其語意調整為：

```text
host environment dependency diagnostics
```

不得再作core execution authority。

文件需標示deprecated。

---

## 十五、Versioning 決策

本階段預期：

```text
PROJECT_CONTRACT_VERSION
1.1 → 1.1

CASE_SCHEMA_VERSION
1.1 → 1.1

RUNTIME_SCHEMA_VERSION
1.0 → 1.1

DISTRIBUTION_RUNTIME_VERSION
1.0-exp → 1.1-exp

BUILD_FORMAT_VERSION
1.0 → 1.1
```

理由：

- AI治理契約不發生breaking change。
- Case Markdown schema不需要改。
- runtime dependency schema與location behavior發生正式變更。
- bundle payload format因binary support而變更。

如果implementation中發現Case schema或Project Contract真的需要breaking change，必須停止並回到design review，不得自行順手升版。

---

## 十六、Error Semantics

正式沿用／新增以下machine-readable errors。

### 16.1 Location

```text
invalid_resolved_location
ambiguous_birth_place
location_not_resolved
location_provider_unavailable
timezone_not_resolved
invalid_network_location_config
location_dependency_unavailable
```

### 16.2 Bundled runtime integrity

可新增：

```text
bundled_dependency_unavailable
bundled_dependency_origin_mismatch
bundled_dependency_integrity_error
bundle_runtime_error
```

正式原則：

- integrity failure不可fallback到host同名package。
- bundled core dependency壞掉時必須fail closed。
- error response不得輸出Python traceback給一般runtime request。

### 16.3 Unknown location不再回`location_resolution_required`

當使用者已提供`birth_place`，但offline registry沒有命中且network disabled時，語意應是：

```text
location_not_resolved
```

`location_resolution_required`可保留給真正缺少location basis或legacy internal path，但不再作一般offline miss的主要error。

---

## 十七、Bundle Size Guard

新增hard guard：

```text
metaphysics_lab.py <= 5 MiB
```

目的不是追求極小體積，而是防止意外把：

- 全球完整geodata dump
- tests
- qualification corpus
- 重複vendor內容
- 不必要大型dependency

打進mobile-first distribution。

如果正式需求超過5 MiB，必須重新做architecture review，不允許implementation直接提高guard。

---

## 十八、Reproducibility Contract

同一個git source tree，在相同Python major/minor compatibility範圍內執行builder，必須產生byte-identical三個distribution artifacts。

不得把下列動態資訊打入bundle：

- build timestamp
- temp path
- absolute repo path
- current machine hostname
- network response
- local pip metadata結果

vendor與registry的變更必須反映在：

- source digest
- dependency / registry manifest
- generated bundle bytes

---

## 十九、Qualification Plan Requirements

本spec不直接寫implementation task order，但明確定義implementation完成前必須具備的qualification surface。

### 19.1 Clean Environment Qualification

核心release gate必須至少驗證：

1. temp directory只放generated `metaphysics_lab.py`。
2. 使用`python -S`。
3. `runtime-info`成功。
4. bundled lunar-python顯示available。
5. bundled tzdata顯示available。
6. 不需要site-packages。
7. 不需要network。
8. 台北出生資料可完整`build_natal`。
9. result包含Bazi pillars。
10. result包含12 Ziwei palaces。
11. result包含Normalized Natal Model。

### 19.2 Host Pollution Qualification

至少測試：

```text
host沒有lunar_python / tzdata
host有舊版lunar_python
host有新版lunar_python
host有fake tzdata
host同名module已先import
```

所有Project結果必須與clean baseline一致。

### 19.3 Network Block Qualification

測試過程主動阻斷network socket。

offline-supported location仍必須完整PASS。

### 19.4 Location Qualification

最低fixture：

```text
台北
臺北
台北市
臺北市
Taipei
Taipei City
```

必須依registry設計解析到同一canonical record。

另需：

- ambiguous fixture → `ambiguous_birth_place`
- unknown fixture → `location_not_resolved`
- invalid coordinates → `invalid_resolved_location`
- explicit resolved location → backward-compatible PASS
- offline miss + network enabled → external resolver path

### 19.5 Bundle Integrity Qualification

至少驗證：

- source digest tamper → fail
- vendor file checksum tamper → fail
- registry tamper → fail
- path traversal record → fail
- duplicate record path → fail
- binary tzdata extract後checksum一致

### 19.6 Modular / Bundle Parity

同一fixture：

```text
modular runtime
vs
generated bundle
```

必須比較完整structured output，不只比某一個四柱欄位。

### 19.7 Existing Regression

本階段完成後仍需執行現有：

- calendar tests
- birth tests
- bazi natal tests
- ziwei natal tests
- distribution tests
- forecast tests
- historical calibration tests
- case export / migration tests

portable work不得破壞其他能力。

---

## 二十、既有測試契約需要正式反轉的項目

目前generated bundle測試有一條既有expectation：

```text
python -S
+
build_natal
→ dependency_unavailable
```

Portable Offline Natal Pipeline完成後，這條不再是正確產品契約。

正式改成：

```text
python -S
+
build_natal
+
offline-registry-supported birth_place
→ success
```

這不是單純新增另一個happy-path test；舊「缺核心dependency為合理狀態」的contract必須被移除或改寫。

`runtime_info`在`python -S`下仍要成功，但對bundled core dependencies應顯示available，而不是missing。

---

## 二十一、Backward Compatibility

本階段採additive-first。

### 21.1 保留

- `build_natal` action name
- 現有birth payload shape
- `resolved_location`
- explicit network config
- ProjectNatalView schema
- NormalizedNatalChart核心schema
- reconciliation semantics
- Case schema 1.1
- 三個對外distribution artifact名稱

### 21.2 行為變更

原本：

```text
no resolved_location
+
no network
→ location_resolution_required
```

新行為：

```text
no resolved_location
        ↓
offline registry unique
→ success

offline registry ambiguous
→ ambiguous_birth_place

offline registry miss + network disabled
→ location_not_resolved

offline registry miss + network enabled
→ external network resolver
```

### 21.3 Legacy host dependency diagnostics

舊client若讀`external_dependencies`，至少一個runtime schema generation內仍可讀到相容view，但文件必須說明該欄位不再代表core dependency authority。

---

## 二十二、README / User-facing Documentation Contract

implementation完成後，文件需同步收斂成準確產品承諾。

README可以正式說：

> 對Metaphysics Lab offline registry已支援的出生地，只需要三個distribution檔案與出生資料，即可建立Project原生命盤；不需額外安裝Python套件，也不需網路。

但不得說：

> 全球所有城市都可offline自動辨識。

文件需清楚說明：

- offline registry coverage是有限、版本化的
- 未收錄地點可以提供pre-resolved location
- 或explicit enable network resolver
- ambiguity會要求使用者選擇，不會自動猜

---

## 二十三、Release / Migration Strategy

### 23.1 v1.3.0 不可修改

本階段不得：

- 移動v1.3.0 tag
- 替換既有Release assets
- 改寫既有Release provenance

### 23.2 新功能走unreleased cycle

流程：

```text
design approval
↓
written spec approval
↓
implementation plan
↓
feature branch
↓
TDD implementation
↓
clean-environment qualification
↓
full regression
↓
review
↓
human merge approval
↓
merge main
↓
independent release decision
```

### 23.3 Merge不等於Release

即使portable implementation合併main，也不自動：

- 建tag
- 發GitHub Release
- 升Stable

Release版本號與發版時點必須在實作與qualification完成後另案決定。

---

## 二十四、Component Responsibility

### Private Vendor Layer

唯一責任：保存與載入固定第三方runtime bytes。

不得負責命理解讀或location matching。

### Vendor Manifest

唯一責任：dependency version、source、checksum、license與runtime authority。

### Distribution Builder

唯一責任：deterministically封裝owned runtime、vendor、registry與固定Markdown artifacts。

不得自行下載dependency。

### Offline Birth Place Registry

唯一責任：保存canonical location records與aliases。

### Offline Resolver

唯一責任：deterministic normalize、lookup、ambiguity handling。

### Network Resolver

唯一責任：explicit opt-in external location resolution。

### Calendar Layer

唯一責任：使用bundled lunar / timezone authority建立calendar context。

### Natal Orchestration

唯一責任：沿用既有birth→calendar→Bazi/Ziwei→Normalized Natal pipeline。

### `runtime_info`

唯一責任：公開真實deployment capability、version與dependency authority。

### Qualification

唯一責任：證明「單檔、no pip、no internet」是事實，不是README假設。

---

## 二十五、Non-goals

本階段明確不做：

1. 重寫`lunar-python`演算法。
2. 建立Metaphysics Lab自有完整農曆引擎取代現有provider。
3. 建立完整全球地址資料庫。
4. 建立offline街道／門牌geocoder。
5. 使用LLM fuzzy geocoding。
6. 自動簡繁轉換後猜location。
7. 把`geopy`與`timezonefinder`強制bundle成核心依賴。
8. 變更Astralium資料權重。
9. 改寫Bazi／Ziwei本命規則。
10. 改變問事盲判／事件校準治理。
11. 升Project Natal Stable。
12. 修改v1.3.0 Release。
13. 在本階段自動建立新Release。

---

## 二十六、Implementation Plan 必須回答的問題

下一階段implementation plan必須把本spec拆成可驗證tasks，且至少明確回答：

1. private vendor source實際目錄。
2. 如何對`lunar-python`做private namespace packaging。
3. 如何bundle`tzdata.zoneinfo` binary resources。
4. mixed byte payload record schema。
5. vendor manifest schema與checksum算法。
6. offline registry exact schema。
7. registry v1收錄哪些canonical places與aliases。
8. location resolver新增在哪個module boundary。
9. `build_natal`如何接offline resolver而不破壞pre-resolved path。
10. `runtime_info`1.1 migration細節。
11. clean-environment test如何真正隔離repo與site-packages。
12. host pollution fixtures如何建立。
13. vendor license / attribution如何進repo與distribution。
14. 5 MiB size guard在哪個build gate執行。
15. 哪些舊測試要反轉、哪些只新增。
16. full regression與qualification command清單。

implementation plan不得跳過上述項目直接開始coding。

---

## 二十七、Final Acceptance Criteria

本階段實作只有同時滿足以下條件才可宣稱完成。

### A. Portable是真的portable

```text
只有metaphysics_lab.py
+
Python standard library
+
offline-supported birth data
→ 完整Project Natal成功
```

### B. Deterministic是真的deterministic

host installed package state不得影響Project core Natal結果。

### C. Offline不等於猜測

只有registry明確資料可以offline resolve；ambiguous或unknown都fail closed。

### D. Astralium真的optional

沒有Astralium仍可建立Project原生Bazi＋Ziwei＋Normalized Natal。

### E. Existing metaphysical truth不漂移

本階段只改dependency與location deployment architecture；既有已qualified calendar / natal規則輸出對固定fixtures不得無理由漂移。

### F. Bundle可稽核

vendor source、version、checksum、license、registry provenance與generated digest都可追溯。

---

## 二十八、設計結論

Portable Offline Natal Pipeline的正式策略不是把更多host dependency藏在README，而是把核心execution authority真正收進distribution。

最終責任邊界固定為：

```text
Bundled private calendar dependencies
+
Bundled deterministic location registry
+
Existing Natal Foundation
=
Portable Offline Natal Pipeline
```

外部network resolver只作optional fallback。

Astralium只作External Natal cross-check。

命理核心演算法、Project maturity與既有evidence governance不因本階段自動變更。

本spec獲使用者final approval後，下一步才進入implementation plan；在此之前不得開始runtime implementation。
