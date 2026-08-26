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
2. `lunar-python==1.4.8` 與 `tzdata==2026.3` 仍由 Python execution environment 提供，而不是由 distribution 自己提供。
3. `build_natal` 在 `python -S` 或缺少 site-packages 的乾淨環境中無法完成核心 calendar resolution。
4. 出生地若沒有預先提供 `resolved_location`，目前只能走 explicit network resolver 或 fail closed。

這表示目前「只有一支 `metaphysics_lab.py` 就能完成 Natal」並未成為真正的 deployment contract。

本階段要修正的是 **portable execution architecture**，不是重寫命理規則。

### 1.1 Execution environment 術語定義

本 spec 統一使用以下術語：

```text
execution environment
= 實際執行 metaphysics_lab.py 的 Python 環境
= 例如 ChatGPT / Claude 提供的隔離 Python sandbox
= 也包含本機 CLI fallback 所使用的 Python interpreter
```

```text
environment-provided package
= execution environment 原本就存在的 Python package / module / data resource
= 不屬於 metaphysics_lab.py bundled vendor bytes
```

因此，本 spec 所防範的是：

```text
AI 平台 sandbox 或本機 Python 環境預裝套件
影響 Project 核心計算結果
```

而不是假設 ChatGPT／Claude 可以直接存取使用者電腦、作業系統或其他外部主機。

另外：

```text
package availability
≠
network availability
```

即使某個 execution environment 內存在 `geopy` 或 `timezonefinder`，也不代表該環境允許 outbound network access。ChatGPT／Claude 等平台若封鎖網路，network resolver 可以維持 unavailable；這不得影響 offline core Natal path。

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

### 4.1 Core dependency authority 不得來自 execution environment

對核心 Natal path：

```text
lunar-python
+
tzdata
```

計算 authority 必須永遠來自 Metaphysics Lab bundled vendor bytes。

execution environment / sandbox：

- 沒有同名套件
- 有相同版本
- 有舊版本
- 有新版本
- 已先 import 同名 environment-provided package

都不得改變 Project 結果。

### 4.2 不使用 environment-provided top-level vendor import name

Project-owned runtime 不得把核心計算依賴繼續視為：

```python
import lunar_python
import tzdata
```

private vendor 必須有不與 execution environment-provided package 共用的 namespace。

建議 namespace：

```text
_metaphysics_lab_vendor.lunar_python
_metaphysics_lab_vendor.tzdata
```

實際 module root 若 implementation plan 有充分理由可微調，但必須維持：

- private namespace
- execution environment-provided package 不可覆蓋 bundled authority
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

正式 error code 沿用既有：

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

repo test execution 與 generated bundle 不得一邊使用 environment-provided package、一邊使用 vendor package。

兩者都必須由同一份 committed vendor source / binary bytes 建立，以維持真正的 parity。

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

Project timezone provider 必須讀 bundled zoneinfo resource，不依賴：

- execution environment OS 的 `/usr/share/zoneinfo`
- execution environment-installed `tzdata`
- execution environment 的 IANA version

### 5.4 Private import compatibility qualification

vendor refresh 必須對 vendored package 執行 import graph / source scan，確認：

- package internal imports 不會跳回 execution environment-provided top-level package
- 沒有意外 dependency on undeclared third-party package
- package 可以從 private namespace 載入

不得只靠抽查一兩個檔案推定全 package 安全。

---

## 六、Vendor Manifest 與 Supply-chain Contract

### 6.1 Manifest 最低欄位

每個 bundled dependency 至少保存：

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

而不是 `execution_environment` 或其他外部 package authority。

### 6.2 Build-time verification

正式 build 前必須驗證：

1. manifest 存在。
2. license file 存在。
3. declared vendor tree 存在。
4. tree checksum 符合 manifest。
5. package metadata 符合 expected pin。
6. private import scan 通過。
7. 不含 symlink escape。
8. 不含超出 allowlist 的 vendor path。

任一失敗：

```text
build fail closed
```

### 6.3 Vendor refresh

vendor refresh 是 maintenance action，不是 distribution build 的一部分。

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

refresh tool 若需要 network 可以接受，但必須：

- explicit command
- deterministic input
- 固定 version
- 驗 checksum
- 不在 runtime 執行

---

## 七、Generated Bundle Payload Format

### 7.1 現況問題

目前 distribution builder 只適合 UTF-8 文字檔：

- `engine/**/*.py`
- `templates/**/*.tmpl`

但 `tzdata.zoneinfo` 包含 binary TZif resource。

因此舊 payload format 無法成為 portable timezone runtime 的正式基礎。

### 7.2 Build format upgrade

正式要求：

```text
BUILD_FORMAT_VERSION 1.0 → 1.1
```

新 payload 必須是 byte-oriented。

每筆 record 最低包含：

```text
path
sha256
encoding
content
```

其中：

- `encoding` 可為固定 `base64`，或其他經 spec 明確定義的 byte-safe encoding。
- `content` 解碼後必須逐檔驗 `sha256`。
- 第一方文字檔可在進 payload 前沿用既有 newline normalization。
- vendor source 與 binary resource 必須 byte-for-byte 保存。

### 7.3 Extraction security

bundle extract 時必須拒絕：

- absolute path
- `..`
- duplicate target path
- invalid path component
- payload record checksum mismatch
- overall source digest mismatch

不得讓 embedded payload 寫出 runtime temp root 之外。

### 7.4 SOURCE_DIGEST

現有整體 `SOURCE_DIGEST` 概念保留。

新 digest authority 必須涵蓋：

- owned runtime source
- templates
- bundled dependencies
- bundled registry
- vendor manifest
- required third-party notices

這樣同一 source tree 才能產生可稽核的同一 distribution。

---

## 八、Offline Birth Place Registry

### 8.1 定位

本階段不建立全球地址搜尋引擎。

Offline registry 只負責：

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

實際檔名可在 implementation plan 微調，但 registry 必須是：

- committed
- versioned
- deterministic
- reviewable
- bundled

### 8.3 Canonical record schema

每筆 record 至少包含：

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

`aliases` 必須是明確清單，不依賴 runtime NLP 猜測。

### 8.4 v1 coverage policy

v1 正式保證：

1. 台灣縣市層級完整 offline coverage。
2. 常見台灣繁體中文與英文別名。
3. Project 明確收錄的國際主要城市。
4. 實際 coverage 以 registry 內容為準，不做「全球城市皆支援」的產品承諾。

### 8.5 Geographic source policy

正式 registry 資料不得由 AI 自由生成。

每筆 canonical data 必須能回溯來源。

允許使用有明確授權與版本資訊的 geographic dataset 作為 source，例如 GeoNames；但本階段只 bundle 經 Project 篩選的必要 records，不 bundle 整套全球 database。

如果採用 GeoNames 或其他第三方 geodata，必須把其 license / attribution 納入 vendor／data notice 治理。

---

## 九、Alias Normalization Contract

### 9.1 Runtime normalization 只做有限、可重現轉換

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

### 9.2 Alias equality 由資料宣告，不由演算法猜

例如：

```text
台北
臺北
台北市
臺北市
Taipei
Taipei City
```

是否相等，必須因為 registry 明確列為同一 canonical record 的 aliases，而不是 resolver 自行推理。

### 9.3 Ambiguous alias

normalized query 若命中多個 record：

```text
ambiguous_birth_place
```

details 最低包含：

```text
query
candidate_count
candidates[]
```

candidate 應提供足以讓 AI 或使用者選擇的識別資訊，例如：

```text
canonical_name
country_code
admin_area
record_id
```

不得自動選第一筆。

### 9.4 Unknown alias

完全沒有 record：

```text
location_not_resolved
```

若 network fallback 沒有 explicit enable，流程在此停止。

---

## 十、Location Resolution Precedence

正式 precedence 固定為：

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

`provider_reference` 保持 optional。

### 10.2 Project Offline Registry

offline 唯一命中時，產生標準 `ResolvedBirthPlace`。

建議 provenance：

```text
provider_name = metaphysics_lab_offline_registry
provider_version = 1.0
provider_reference = <source-id / record-id>
resolution_status = resolved
```

### 10.3 Ambiguous offline result 不可 fall through network

若 offline registry 已知道此 query 存在多個 candidate，這代表使用者輸入不夠精確。

此時即使 network resolver 已 enable，也必須：

```text
ambiguous_birth_place
```

不得讓 network provider 替使用者偷偷做 disambiguation。

### 10.4 Offline miss 才可進 network fallback

只有：

```text
offline candidate count = 0
+
network_location.enabled = true
```

才進現有 Nominatim＋TimezoneFinder external path。

如果 network 沒有 enable：

```text
location_not_resolved
```

---

## 十一、External Network Location Boundary

### 11.1 Network resolver 保持 optional

`geopy` 與 `timezonefinder` 不進核心 portable dependency。

理由：

- offline Natal 不需要它們
- `geopy` 本身需要 network provider
- `timezonefinder` 相對大型，且只為 external network geocode 後補 timezone

### 11.2 Network 依賴可由 execution environment 提供，但 network access 不作保證

這兩者是 optional external integrations，因此可以維持 execution-environment dependency model。

正式必須清楚區分：

```text
Bundled Core Dependencies
vs
Optional External Dependencies
```

且必須再區分：

```text
optional package available
vs
outbound network available
```

AI 平台 sandbox 若封鎖 outbound network，即使 optional package 已存在，network resolver 仍可回 unavailable／structured error；不得因此影響 offline Natal。

### 11.3 Network provenance 不得偽裝成 offline

Nominatim／TimezoneFinder 輸出的 location 不得寫成 Project offline provider。

同理，user-supplied `resolved_location` 也保留其自身 provider provenance。

---

## 十二、Calendar Runtime Refactor Boundary

### 12.1 `lunar-python`

現有 calendar provider 應從 environment-dependent provider 改為 bundled provider。

正式要求：

- 使用 private bundled lunar source
- 版本 metadata 讀 vendor authority
- 不再以 execution environment 的 `importlib.metadata.version("lunar_python")` 作核心計算資格判斷

### 12.2 `tzdata`

現有 `PinnedTzdataProvider` 概念保留：

- pinned package version
- pinned IANA version
- explicit resource load

但 resource authority 改為 private bundled tzdata package。

### 12.3 Existing calendar qualification 不因 bundling 失效

本階段不可因「套件現在變成 vendor」就刪除既有：

- Gregorian / lunar validation range
- HKO validation profile
- known conflict window
- caution boundary
- timezone ambiguity / nonexistent local time 處理

portable architecture 只改 provider source，不改已核准的 calendar correctness contract。

---

## 十三、Natal Pipeline Contract

### 13.1 Offline happy path

正式最小 input：

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

若 `台北市` 在 offline registry 唯一命中，`build_natal` 必須在：

- no site-packages
- no network
- no Astralium
- no explicit `resolved_location`

條件下完成。

### 13.2 Output shape

本階段不要求破壞現有 `build_natal` output shape。

仍回：

```text
input_resolution
resolved_location
project_natal
normalized_natal
```

`resolved_location` 增加 offline provenance，但維持既有資料模型。

### 13.3 Candidate Envelope

`natal.candidate_envelope` 目前要求 pre-resolved location。

本階段設計允許 implementation 將它接入相同 offline resolver，前提是：

- 不改 Candidate Envelope 核心精度規則
- ambiguity 同樣 fail closed
- output schema 不發生無理由 breaking change

若 implementation plan 判斷 Candidate Envelope 接入 offline resolver 會擴大 scope，可保留既有 explicit resolved location 要求；但核心 `build_natal` offline path 必須完成。

---

## 十四、`runtime_info` 新 Dependency Contract

### 14.1 問題

目前所有 runtime dependency 都被集中在：

```text
external_dependencies
```

portable architecture 完成後，這已不能表達真正 execution authority。

### 14.2 Canonical schema

`runtime_info.data` 新增：

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
runtime_uses_environment_package
source_revision
artifact_sha256
vendored_tree_sha256
license
role
required_for
```

`lunar-python` 與 `tzdata` 必須：

```text
bundled = true
available = true
runtime_uses_environment_package = false
```

在 `python -S` 下仍成立。

### 14.4 `optional_external_dependencies`

保留 execution-environment package inspection semantics 給：

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

但明確標示它們不是核心 Natal dependency；其 installed 狀態也不代表 execution environment 具有 outbound network access。

### 14.5 `offline_location_registry`

最低回：

```text
version
record_count
coverage_profile
source_profiles
bundled
```

不得在 runtime_info 裡回整份 aliases 或大量資料。

### 14.6 Backward compatibility

舊 `external_dependencies` 保留至少一個 runtime schema generation 作 compatibility view。

其語意調整為：

```text
execution environment dependency diagnostics
```

不得再作 core execution authority。

文件需標示 deprecated。

新 canonical 欄位固定為：

```text
runtime_uses_environment_package
```

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

- AI 治理契約不發生 breaking change。
- Case Markdown schema 不需要改。
- runtime dependency schema 與 location behavior 發生正式變更。
- bundle payload format 因 binary support 而變更。

如果 implementation 中發現 Case schema 或 Project Contract 真的需要 breaking change，必須停止並回到 design review，不得自行順手升版。

---

## 十六、Error Semantics

正式沿用／新增以下 machine-readable errors。

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

- integrity failure 不可 fallback 到 execution environment-provided 同名 package。
- bundled core dependency 壞掉時必須 fail closed。
- error response 不得輸出 Python traceback 給一般 runtime request。

### 16.3 Unknown location 不再回 `location_resolution_required`

當使用者已提供 `birth_place`，但 offline registry 沒有命中且 network disabled 時，語意應是：

```text
location_not_resolved
```

`location_resolution_required` 可保留給真正缺少 location basis 或 legacy internal path，但不再作一般 offline miss 的主要 error。

---

## 十七、Bundle Size Guard

新增 hard guard：

```text
metaphysics_lab.py <= 5 MiB
```

目的不是追求極小體積，而是防止意外把：

- 全球完整 geodata dump
- tests
- qualification corpus
- 重複 vendor 內容
- 不必要大型 dependency

打進 mobile-first distribution。

如果正式需求超過 5 MiB，必須重新做 architecture review，不允許 implementation 直接提高 guard。

---

## 十八、Reproducibility Contract

同一個 git source tree，在相同 Python major/minor compatibility 範圍內執行 builder，必須產生 byte-identical 三個 distribution artifacts。

不得把下列動態資訊打入 bundle：

- build timestamp
- temp path
- absolute repo path
- current machine name
- network response
- local environment package metadata 結果

vendor 與 registry 的變更必須反映在：

- source digest
- dependency / registry manifest
- generated bundle bytes

---

## 十九、Qualification Plan Requirements

本 spec 不直接寫 implementation task order，但明確定義 implementation 完成前必須具備的 qualification surface。

### 19.1 Clean Environment Qualification

核心 release gate 必須至少驗證：

1. temp directory 只放 generated `metaphysics_lab.py`。
2. 使用 `python -S`。
3. `runtime-info` 成功。
4. bundled lunar-python 顯示 available。
5. bundled tzdata 顯示 available。
6. 不需要 site-packages。
7. 不需要 network。
8. 台北出生資料可完整 `build_natal`。
9. result 包含 Bazi pillars。
10. result 包含 12 Ziwei palaces。
11. result 包含 Normalized Natal Model。

### 19.2 Sandbox / Execution Environment Package Isolation Qualification

至少測試：

```text
execution environment 沒有 lunar_python / tzdata
execution environment 有舊版 lunar_python
execution environment 有新版 lunar_python
execution environment 有 fake tzdata
execution environment 同名 module 已先 import
```

所有 Project 結果必須與 clean baseline 一致。

### 19.3 Network Block Qualification

測試過程主動阻斷 network socket。

offline-supported location 仍必須完整 PASS。

### 19.4 Location Qualification

最低 fixture：

```text
台北
臺北
台北市
臺北市
Taipei
Taipei City
```

必須依 registry 設計解析到同一 canonical record。

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
- binary tzdata extract 後 checksum 一致

### 19.6 Modular / Bundle Parity

同一 fixture：

```text
modular runtime
vs
generated bundle
```

必須比較完整 structured output，不只比某一個四柱欄位。

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

portable work 不得破壞其他能力。

---

## 二十、既有測試契約需要正式反轉的項目

目前 generated bundle 測試有一條既有 expectation：

```text
python -S
+
build_natal
→ dependency_unavailable
```

Portable Offline Natal Pipeline 完成後，這條不再是正確產品契約。

正式改成：

```text
python -S
+
build_natal
+
offline-registry-supported birth_place
→ success
```

這不是單純新增另一個 happy-path test；舊「缺核心 dependency 為合理狀態」的 contract 必須被移除或改寫。

`runtime_info` 在 `python -S` 下仍要成功，但對 bundled core dependencies 應顯示 available，而不是 missing。

---

## 二十一、Backward Compatibility

本階段採 additive-first。

### 21.1 保留

- `build_natal` action name
- 現有 birth payload shape
- `resolved_location`
- explicit network config
- ProjectNatalView schema
- NormalizedNatalChart 核心 schema
- reconciliation semantics
- Case schema 1.1
- 三個對外 distribution artifact 名稱

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

### 21.3 Legacy execution-environment dependency diagnostics

舊 client 若讀 `external_dependencies`，至少一個 runtime schema generation 內仍可讀到相容 view，但文件必須說明該欄位不再代表 core dependency authority。

---

## 二十二、README / User-facing Documentation Contract

implementation 完成後，文件需同步收斂成準確產品承諾。

README 可以正式說：

> 對 Metaphysics Lab offline registry 已支援的出生地，只需要三個 distribution 檔案與出生資料，即可建立 Project 原生命盤；不需額外安裝 Python 套件，也不需網路。

但不得說：

> 全球所有城市都可 offline 自動辨識。

文件需清楚說明：

- offline registry coverage 是有限、版本化的
- 未收錄地點可以提供 pre-resolved location
- 或 explicit enable network resolver
- ambiguity 會要求使用者選擇，不會自動猜
- AI 平台是否允許 outbound network 屬平台 execution environment 能力，不是 Metaphysics Lab portable core 的必要條件

---

## 二十三、Release / Migration Strategy

### 23.1 v1.3.0 不可修改

本階段不得：

- 移動 v1.3.0 tag
- 替換既有 Release assets
- 改寫既有 Release provenance

### 23.2 新功能走 unreleased cycle

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

### 23.3 Merge 不等於 Release

即使 portable implementation 合併 main，也不自動：

- 建 tag
- 發 GitHub Release
- 升 Stable

Release 版本號與發版時點必須在實作與 qualification 完成後另案決定。

---

## 二十四、Component Responsibility

### Private Vendor Layer

唯一責任：保存與載入固定第三方 runtime bytes。

不得負責命理解讀或 location matching。

### Vendor Manifest

唯一責任：dependency version、source、checksum、license 與 runtime authority。

### Distribution Builder

唯一責任：deterministically 封裝 owned runtime、vendor、registry 與固定 Markdown artifacts。

不得自行下載 dependency。

### Offline Birth Place Registry

唯一責任：保存 canonical location records 與 aliases。

### Offline Resolver

唯一責任：deterministic normalize、lookup、ambiguity handling。

### Network Resolver

唯一責任：explicit opt-in external location resolution。

### Calendar Layer

唯一責任：使用 bundled lunar / timezone authority 建立 calendar context。

### Natal Orchestration

唯一責任：沿用既有 birth→calendar→Bazi/Ziwei→Normalized Natal pipeline。

### `runtime_info`

唯一責任：公開真實 deployment capability、version 與 dependency authority。

### Qualification

唯一責任：證明「單檔、no pip、no internet」是事實，不是 README 假設。

---

## 二十五、Non-goals

本階段明確不做：

1. 重寫 `lunar-python` 演算法。
2. 建立 Metaphysics Lab 自有完整農曆引擎取代現有 provider。
3. 建立完整全球地址資料庫。
4. 建立 offline 街道／門牌 geocoder。
5. 使用 LLM fuzzy geocoding。
6. 自動簡繁轉換後猜 location。
7. 把 `geopy` 與 `timezonefinder` 強制 bundle 成核心依賴。
8. 變更 Astralium 資料權重。
9. 改寫 Bazi／Ziwei 本命規則。
10. 改變問事盲判／事件校準治理。
11. 升 Project Natal Stable。
12. 修改 v1.3.0 Release。
13. 在本階段自動建立新 Release。

---

## 二十六、Implementation Plan 必須回答的問題

下一階段 implementation plan 必須把本 spec 拆成可驗證 tasks，且至少明確回答：

1. private vendor source 實際目錄。
2. 如何對 `lunar-python` 做 private namespace packaging。
3. 如何 bundle `tzdata.zoneinfo` binary resources。
4. mixed byte payload record schema。
5. vendor manifest schema 與 checksum 算法。
6. offline registry exact schema。
7. registry v1 收錄哪些 canonical places 與 aliases。
8. location resolver 新增在哪個 module boundary。
9. `build_natal` 如何接 offline resolver 而不破壞 pre-resolved path。
10. `runtime_info` 1.1 migration 細節。
11. clean-environment test 如何真正隔離 repo 與 site-packages。
12. sandbox / execution-environment package isolation fixtures 如何建立。
13. vendor license / attribution 如何進 repo 與 distribution。
14. 5 MiB size guard 在哪個 build gate 執行。
15. 哪些舊測試要反轉、哪些只新增。
16. full regression 與 qualification command 清單。

implementation plan 不得跳過上述項目直接開始 coding。

---

## 二十七、Final Acceptance Criteria

本階段實作只有同時滿足以下條件才可宣稱完成。

### A. Portable 是真的 portable

```text
只有 metaphysics_lab.py
+
Python standard library
+
offline-supported birth data
→ 完整 Project Natal 成功
```

### B. Deterministic 是真的 deterministic

execution environment-provided package state 不得影響 Project core Natal 結果。

### C. Offline 不等於猜測

只有 registry 明確資料可以 offline resolve；ambiguous 或 unknown 都 fail closed。

### D. Astralium 真的 optional

沒有 Astralium 仍可建立 Project 原生 Bazi＋Ziwei＋Normalized Natal。

### E. Existing metaphysical truth 不漂移

本階段只改 dependency 與 location deployment architecture；既有已 qualified calendar / natal 規則輸出對固定 fixtures 不得無理由漂移。

### F. Bundle 可稽核

vendor source、version、checksum、license、registry provenance 與 generated digest 都可追溯。

---

## 二十八、設計結論

Portable Offline Natal Pipeline 的正式策略不是把更多 execution-environment dependency 藏在 README，而是把核心 execution authority 真正收進 distribution。

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

外部 network resolver 只作 optional fallback。

Astralium 只作 External Natal cross-check。

ChatGPT／Claude 等 AI 平台是否允許 outbound network，不是 portable core 成立的前提；核心 offline Natal 必須在封網 sandbox 仍成立。

命理核心演算法、Project maturity 與既有 evidence governance 不因本階段自動變更。

本 spec 獲使用者 final approval 後，下一步才進入 implementation plan；在此之前不得開始 runtime implementation。