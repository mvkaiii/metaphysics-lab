# Metaphysics Lab 版本

## 最新正式發布

- Metaphysics Lab Core：**v1.2.0**
- 發布日期：**2026-08-21**
- Release baseline：`main` post-merge verified

主要元件：

- 命理推導計算規則：v1.2
- Project Bazi Calendar Engine：v1.0.0
- 紫微流月定位引擎：v1.0.0
- 紫微流日定位引擎：v1.0.0-exp
- 紫微流時定位引擎：v1.0.0-exp
- Calendar Resolver：v1.0.0
- Ziwei Transformation Core：v1.0.0
- Ziwei Flying Core：v1.0.0
- 問事追蹤制度：v1.0

---

## v1.2.0 Capability 狀態

| Capability | Implementation | Maturity | Routing / Role |
|---|---|---|---|
| 八字流年／流月／流日／流時 | implemented | stable | default |
| 紫微流月定位 | implemented | stable | default |
| 紫微流日定位 | implemented | experimental | on_demand |
| 紫微流時定位 | implemented | experimental | on_demand |
| Calendar Resolver v1 | implemented | stable infrastructure | upstream |
| Ziwei Calendar Adapter | implemented | stable infrastructure | adapter |
| Ziwei Transformation Core v1 | implemented | stable | on_demand |
| Ziwei Flying Core v1 | implemented | stable | on_demand |
| 紫微流月／流日／流時四化與飛化 | planned | — | on_demand |
| 紫微流曜 | planned | — | on_demand |
| Cross-System Validation | planned | — | — |
| 奇門自動排盤引擎 | planned | — | — |

`Experimental / On-demand` 代表能力已有可執行 Python 與驗證紀錄，但一般年度／月份問事不預設執行，分析時也必須降權。

`Stable / On-demand` 代表能力已通過既定 promotion gate，但仍不代表每次問事都要預設執行。

---

## v1.2.0 Qualification / Regression Baseline

### Ziwei Transformation & Flying Core

```text
pinned iztro 十干四化             40/40 PASS
私有 Astralium 十干四化           40/40 PASS
Astralium 本命飛化                48/48 PASS
Astralium 大限飛化                 4/4 PASS
Astralium 2023–2029 流年飛化      28/28 PASS
Astralium flying total             80/80 PASS
Astralium-compatible presentation  11/11 PASS
```

### main post-merge regression

```text
Phase 2A internal  43/43 PASS
Ziwei              83/83 PASS
Calendar           35/35 PASS
Bazi               10/10 PASS
Full repository   132/132 PASS
```

Private Astralium raw chart 與 normalized qualification input 不存 repo；repo 只保存 aggregate evidence 與 digest。

---

## Runtime / Compatibility

- Python：3.9 以上
- Calendar Resolver lunar provider：`lunar-python==1.4.8`
- Timezone provider：`tzdata==2026.3` / IANA `2026c`
- Calendar Resolver Gregorian→Lunar HKO validated range：`1901-01-01..2100-12-31`
- `2057-09-28..2057-10-27`：`boundary_conflict`
- `2089-09-04`、`2097-08-07`：`boundary_caution`
- 23:00 已屬子時，但 Resolver civil date 只在 00:00 換日
- 八字 23:00 early-Zi 仍由八字引擎負責
- 紫微 23:00 命理日界尚未固定，不自動沿用八字規則

---

## 版本治理規則

`VERSION.md` 只回答「目前正式有效的是什麼」。歷史變更請看 `CHANGELOG.md`，升級操作請看 `docs/更新與版本同步.md`。

以下變更必須留下版本歷程並重新跑對應 gate：

- 會改變命盤計算結果的規則
- 時間／日期邊界
- rule profile
- schema / data contract
- capability implementation / maturity / routing
- qualification source 或 promotion gate

建議版本語意：

- patch：不改演算法語意的修正、文件錯誤、測試補強
- minor：新增正式 capability、啟用新的可執行規則層
- major：破壞性 schema／API／核心規則相容性變更

正式 Git tag / GitHub Release 應在 release 文件 merge、main regression 完成後建立，避免 tag 指向尚未收斂的中間狀態。

---

## 歷史版本

### v1.1.0｜2026-08-20

- 正式加入 Project 紫微流月定位。
- 建立流年斗君、流月命宮、流月十二宮重排。
- 建立安裝、資料準備、更新同步與快速開始文件。

### v1.0.0｜2026-08-20

- 建立 Metaphysics Lab 共用核心架構。
- 建立問事「先盲判、後事件校準」制度。
- 建立八字流年、流月、流日、流時固定算法與測試基線。
