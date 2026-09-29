# 大運reference預註冊準備紀錄

Methodology：`APPROVED WITH CONSTRAINTS`。Comparator contract：`ENGINEERING_READY`。Pre-oracle packet：`SEALED`。Oracle：`NOT_STARTED`。Comparison：`NOT_STARTED`。Task3：`NEEDS_EVIDENCE`。

依據：[人工決策](../superpowers/phase-gates/2026-09-27-review-decisions.md)與
`bazi-decadal-domain-review-decision.v1.json`。此文件不是reference結果或PASS證據。

## 已完成的事前封存

| 項目 | 已封存狀態 |
| --- | --- |
| 規格 | `bazi-decadal-independent-profile-spec.v1.md`，SHA256=`0757d1275e55b84e2424d6131e9dbdc73e029e1b619f900147be928cc7e5e01d` |
| D1 Jie等值 | current Jie inclusive；forward取first Jie >= birth、reverse取last Jie <= birth；exact equality => interval=0 |
| D2 endpoint | 每段直接由birth + absolute age × 365.2425 civil days計算；表示語意`[start,end)` |
| D3 HKO精度 | 分鐘顯示保守視為±60秒；start-age tolerance=`0.0002314814814814815`；datetime/endpoint tolerance=`7304.85`秒 |
| D4來源 | HKO 2015＋2016兩個靜態24節氣頁 |
| 2015 raw bytes | 16070 bytes；SHA256=`60a45ab889ef436936571a04a49387c6f9ce8d43243fb21c64e3fcb0331c8320` |
| 2016 raw bytes | 12079 bytes；SHA256=`84beb01553646b807a7c15d6efebdd7550af1ac6d7f06e07bfdd124dab9e443b` |
| 案例 | 12-case census；bundle SHA256=`ab7ebd72671c3020d67444f720c6f3645111005348efd56efe91ffd2ee699d3f` |
| 比較欄位 | direction、first pillar、start age、start datetime、subsequent endpoint均已事前固定 |
| Pre-oracle seal | `bazi-decadal-preoracle-seal.v1.json`；seal SHA256=`db32a95bc41a54531907e7e059655c094b1b1234a533770a88f2e3a52712874e` |
| Oracle | 尚未執行；目前implementation/review context不具clean-room資格 |
| Expected values | 0；尚未建立 |
| Comparison | 尚未執行 |

Exact raw source acquisition由GitHub Actions run `36563577026`完成；
artifact `11030359726`已驗證raw bytes、`SHA256SUMS`與
`source-bindings.json`三者一致。後續run `36563905095`再次取得相同兩個raw
source SHA256，證明本次封存期間來源bytes穩定；ZIP artifact digest因封裝metadata而不同，
不影響已封存的原始HTML SHA256。

## 相關治理artifact

- 原始review proposal：`bazi-decadal-preoracle-review-packet.v1.json`
- D1–D4人工決策：`bazi-decadal-domain-review-decision.v1.json`
- 核准規格：`bazi-decadal-independent-profile-spec.v1.md`
- synthetic oracle inputs：`bazi-decadal-oracle-case-inputs.v1.json`
- external source acquisition receipt：`bazi-decadal-source-acquisition-receipt.v1.json`
- pre-oracle seal：`bazi-decadal-preoracle-seal.v1.json`
- 狀態checkpoint：`bazi-decadal-domain-review-checkpoint.v1.json`
- independent oracle handoff boundary：`bazi-decadal-independent-oracle-handoff.md`

## Engineering contracts

`tools/seal_bazi_decadal_reference_inputs.py`只負責封存pre-oracle輸入；
`tools/finalize_bazi_decadal_reference_packet.py`只負責將獨立oracle輸出綁回exact
pre-oracle seal；`tools/compare_bazi_decadal_reference.py`只做封存後comparison。

三者均不得產生oracle expected values，也不得自動做qualification / maturity promotion。

## 目前唯一下一個gate

由**未接觸production實作／production output／comparison結果**的獨立executor，
只取得已核准handoff材料，獨立實作written contract並產生expected values與
oracle-code SHA256。

獨立oracle必須先封存自己的output bundle，再交回本context使用finalizer與comparator。
不得讓oracle先看到production actual bundle或comparison結果。

Exact-equality-at-Jie規則已核准，但由於目前HKO來源只有分鐘解析度，
本12-case packet未納入「精確相等」證據；此項記錄為coverage gap，不允許事後修改規則。

Task3因此仍為`NEEDS_EVIDENCE`，不做maturity promotion。
