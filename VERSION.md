# Metaphysics Lab 版本

> `VERSION.md` 是給開發、驗證與版本治理看的**技術版本表**。第一次使用請先看 `README.md` 或 `docs/快速開始.md`；一般使用者版 v1.3.0 發布說明見 `docs/發布說明-v1.3.0.md`。
>
> 本文件的「v1.3.0」區塊保存正式 Release snapshot。已合併 `main`、但尚未成為下一個正式 Release 的 Project Contract / Case Schema 1.1 變更，記錄在 `CHANGELOG.md` 的 Unreleased 區，不回寫改造 v1.3.0 歷史快照。

## 最新正式發布

- Metaphysics Lab Core：**v1.3.0**
- 發布日期：**2026-08-23**
- Release baseline：`main` post-merge verified + v1.3.0 release gate

主要元件：

- 命理推導計算規則：v1.2
- 八字時間推導引擎：v1.0.0
- 紫微流月定位引擎：v1.0.0
- 紫微流日定位引擎：v1.0.0-exp
- 紫微流時定位引擎：v1.0.0-exp
- Calendar Resolver：v1.0.0
- Ziwei Transformation Core：v1.0.0
- Ziwei Flying Core：v1.0.0
- Natal Foundation：v1.0-exp
- Ziwei Fine Cycle：v1.0-exp
- Ziwei Flowing Stars：v1.0-exp
- AI Distribution Runtime：v1.0-exp
- Project Contract：v1.0
- Case Schema：v1.0
- 問事追蹤制度：v1.0

---

## v1.3.0 Capability 狀態

目前執行能力的權威來源是 `runtime_info`。以下是本次正式 release snapshot；release 本身不改變 capability maturity。

| Capability / Layer | Implementation | Maturity | Routing / Role |
|---|---|---|---|
| 八字時間推導（流年／流月／流日／流時） | implemented | stable | default |
| Birth input / location / true solar time | implemented | experimental | on_demand |
| `bazi.natal_chart` | implemented | experimental | on_demand |
| `ziwei.natal_chart` | implemented | experimental | on_demand |
| `natal.reconciliation` | implemented | stable | on_demand |
| `natal.markdown_export` | implemented | stable | on_demand |
| `ziwei.flow_month_palaces` | implemented | stable | default |
| `ziwei.flow_day_palaces` | implemented | experimental | on_demand |
| `ziwei.flow_hour_palaces` | implemented | experimental | on_demand |
| `ziwei.transformations` | implemented | stable | on_demand |
| `ziwei.flying` | implemented | stable | on_demand |
| 紫微流月／流日／流時 stem | implemented | experimental | on_demand |
| 紫微流月／流日／流時 transformations | implemented | experimental | on_demand |
| 紫微流月／流日／流時 flying | implemented | experimental | on_demand |
| `ziwei.flowing_stars` | implemented | experimental | on_demand |
| Cross-System Validation | planned | — | — |
| 奇門自動排盤引擎 | planned | — | — |

`Experimental / On-demand` 代表能力已有可執行 Python 與驗證紀錄，但一般問事不預設執行，分析時必須依 evidence / qualification 降權。

`Stable / On-demand` 代表能力已通過既定 promotion gate，但仍不代表每次問事都要預設執行。

---

## v1.3.0 Qualification / Regression Baseline

### AI Distribution Pack / main acceptance

```text
Focused AI Distribution   56/56 PASS
Deterministic build check       PASS
Full repository           488/488 PASS
Python 3.9 compileall            PASS
```

### Natal Foundation private aggregate qualification

```text
Bazi private case       PASS：6 direct matches / 3 explicit profile differences / 0 unexpected mismatch
Ziwei private case      PASS：129 matches / 1 equivalent / 0 unexpected mismatch
promotion_allowed       false
```

單一 private case 不構成 capability promotion 依據；`bazi.natal_chart` 與 `ziwei.natal_chart` 仍為 Experimental。

### Ziwei Fine Cycle

```text
pinned lunar-lite 1d104fff...   18/18 PASS
pinned iztro 814b77e6...        integration PASS
Astralium fine-cycle             PENDING
```

`leap_twelfth_month_second_half` 目前只有 synthetic internal coverage，仍為 not externally qualified。

### Ziwei Flowing Stars

```text
pinned iztro 2.6.0 / 814b77e6...   600/600 source cases PASS
placements                         6120
unexpected mismatch                0
Astralium flowing-stars            PENDING
promotion_allowed                  false
```

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

Private Astralium raw chart、raw birth input、完整住址與 normalized private qualification input 不存共用 repo；repo 只保存 aggregate evidence、digests、versions 與 statuses。

---

## AI Distribution Pack

v1.3.0 正式提供 mobile-first AI release surface：

```text
dist/ai/metaphysics_lab.py
dist/ai/METAPHYSICS_CORE.md
dist/ai/PROJECT_INSTRUCTIONS.md
```

一般使用者不需要理解 repo modules。前兩個檔案上傳到 ChatGPT / Claude Project，`PROJECT_INSTRUCTIONS.md` 內容貼入 Project Instructions；完整分析若平台提供，可優先使用較高推理強度模式。

Runtime 更新預設只替換 `metaphysics_lab.py`。Project Contract 或 Case Schema 只有在明確 migration 通知時才同步。

AI Distribution Runtime 目前版本仍為 `1.0-exp`；本次 GitHub Release 不把它或任何 experimental metaphysics capability 自動升 Stable。

---

## Runtime / Compatibility

- Python：3.9 以上
- Calendar Resolver lunar provider：`lunar-python==1.4.8`
- Timezone provider：`tzdata==2026.3` / IANA `2026c`
- Optional location packages：`geopy==2.5.0`、`timezonefinder==8.2.0`
- Calendar Resolver Gregorian→Lunar HKO validated range：`1901-01-01..2100-12-31`
- `2057-09-28..2057-10-27`：`boundary_conflict`
- `2089-09-04`、`2097-08-07`：`boundary_caution`
- 23:00 已屬子時，但 Resolver civil date 只在 00:00 換日
- 八字 23:00 early-Zi 仍由八字引擎負責
- 紫微 fine-cycle 日界採其固定 profile，不讓 Calendar Resolver 代替決定命理日界

---

## 版本治理規則

`VERSION.md` 只回答「目前正式有效的是什麼」。歷史與尚未發布變更請看 `CHANGELOG.md`，升級操作請看 `docs/更新與版本同步.md`。

以下變更必須留下版本歷程並重新跑對應 gate：

- 會改變命盤計算結果的規則
- 時間／日期邊界
- rule profile
- schema / data contract
- capability implementation / maturity / routing
- qualification source 或 promotion gate
- Project Contract / Distribution Runtime release surface

建議版本語意：

- patch：不改演算法語意的修正、文件錯誤、測試補強
- minor：新增正式 capability、啟用新的可執行規則層或正式 distribution surface
- major：破壞性 schema／API／核心規則相容性變更

正式 Git tag / GitHub Release 應在 release 文件 merge、main regression 完成後建立，避免 tag 指向尚未收斂的中間狀態。

---

## 歷史版本

### v1.2.0｜2026-08-21

- 引擎正式模組化為 `engine/bazi/`、`engine/ziwei/` 與 `engine/calendar/`。
- 建立 Calendar Resolver v1。
- 收斂 Ziwei Transformation Core / Flying Core v1。
- 正式建立 implementation / maturity / routing 三軸 capability 模型。

### v1.1.0｜2026-08-20

- 正式加入紫微流月定位。
- 建立流年斗君、流月命宮、流月十二宮重排。
- 建立安裝、資料準備、更新同步與快速開始文件。

### v1.0.0｜2026-08-20

- 建立 Metaphysics Lab 共用核心架構。
- 建立問事「先盲判、後事件校準」制度。
- 建立八字流年、流月、流日、流時固定算法與測試基線。
