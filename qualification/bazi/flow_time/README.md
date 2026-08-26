# Bazi Flow Day / Hour Qualification

本目錄保存八字 **流日／流時** deterministic algorithm 的可重現 qualification 證據。

本批 qualification **不修改** `core/命理推導計算規則.md` 已固定的公式，也**不提升 capability maturity**。Normative rule 與 qualification evidence 保持分層：

- 規則：`core/命理推導計算規則.md` §2.3–2.4
- 實作：`engine/bazi/calendar.py`
- 可重跑 qualifier：`tools/build_bazi_flow_time_qualification.py`
- 公開證據：`public-lunar-python-1.4.8.json`
- 回歸／邊界測試：`tests/test_bazi_flow_time_qualification.py`

## Oracle

公開 oracle 固定為：

```text
lunar-python==1.4.8
source revision = 000c8a3d74eed098d6256a28fdd51b869324c559
EightChar sect = 1
```

`sect = 1` 的用途是對齊 Project Bazi 已固定的 **23:00 early-Zi** 口徑：23:00 起日柱按下一個有效日期計算，流時日干也跟著使用新日干。

Oracle 只作 qualification comparison，不成為 runtime authority；Project runtime 仍由 `engine/bazi/calendar.py` 與已版本化規則負責。

## 2026-08-26 qualification result

公開 evidence 由 GitHub Actions runner 在 Python 3.9、實際安裝 pinned dependencies 的環境產生。

結果：

```text
PASS
mismatch_count = 0
```

Coverage：

| Gate | Cases | Result |
|---|---:|---|
| 1980-01-01 ～ 2050-12-31 deterministic day samples（每97日） | 268 | PASS |
| 23:00 boundary：22:59 / 23:00 / 23:59 / 次日00:00 × 4 IANA zones | 16 | PASS |
| Gregorian year/month/leap-day transitions | 13 | PASS |
| 五鼠遁：10日干 × 12時支 | 120 | PASS |
| 連續日六十甲子 +1 property | 730 pairs | PASS |
| DST nonexistent / ambiguous local-time responsibility | integration tests | PASS |
| modular ↔ generated single-file daily/hourly parity（ordinary + 23:xx） | 2 targets | PASS |

Boundary zones：

- `Asia/Taipei`
- `Asia/Tokyo`
- `America/New_York`
- `Europe/London`

## DST responsibility boundary

Bazi flow-time calculator 不自行建立第二套 timezone / DST resolver。

責任固定為：

```text
Calendar Resolver
  -> resolve local civil time / IANA timezone / DST ambiguity or gap
  -> produce valid timezone-aware local datetime
Bazi flow-time
  -> apply Project Bazi 23:00 effective-day rule
  -> calculate day pillar / hour pillar
```

New York spring-forward nonexistent time 必須先由 Calendar Resolver fail closed；fall-back ambiguous time 必須先回報兩個候選或使用 explicit offset hint 選定候選。

同一個合法 local civil `01:30` 即使因 fall-back 對應兩個不同 UTC instants，Bazi 流日／流時結果仍相同，因為命理時間算法消費的是已確認的 local civil fields，而不是偷用 UTC instant 重新換日。

## Reproducibility

重新產生 evidence：

```bash
python tools/build_bazi_flow_time_qualification.py
```

驗證 committed evidence 沒有 drift：

```bash
python tools/build_bazi_flow_time_qualification.py --check
```

PR validation workflow 會執行 `--check`；任何 oracle version、公式輸出、coverage contract 或 committed evidence 的 drift 都會使 CI fail。

## TDD evidence

第一個 RED gate 在 qualification builder／evidence 尚不存在時提交；該 exact-head CI：

```text
run 32947625348
job 98111702174
709 tests
1 failure
reason: missing reproducible flow-time qualification builder
```

原有 708 tests 沒有失敗。

完成 qualifier、evidence、DST 與 bundle parity tests 後，GREEN exact-head evidence（文件化前 checkpoint）：

```text
run 32948170035
job 98113369302
focused historical/progressive suite: 114/114 PASS
full regression: 715/715 PASS
AI distribution rebuild / --check: PASS
Python 3.9 compile: PASS
clean tree: PASS
artifact upload: PASS
```

## Interpretation limit

這批證據支持：

- 目前 Project 流日 JDN 映射在本次公開抽樣／邊界範圍內與 pinned oracle 一致。
- 23:00 early-Zi 規則在四個時區的指定 boundary vectors 與 pinned oracle sect 1 一致。
- 五鼠遁 120 組完整日干 × 時支矩陣與 pinned oracle 一致。
- DST responsibility boundary 與 generated runtime parity 沒有發現新缺口。

這批證據**不代表**：

- 所有歷史年份、所有 timezone database edge case 都已窮舉。
- `lunar-python` 是 Project runtime authority。
- 流日／流時的命理解讀必然準確。
- 任何 Experimental capability 因本次 qualification 自動升 Stable。
