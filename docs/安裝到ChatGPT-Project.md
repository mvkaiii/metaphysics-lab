# 安裝到 ChatGPT Project

本文件說明如何把 Metaphysics Lab v1.2.0 的共用核心安裝到新的 ChatGPT Project，並與私人命盤資料分開管理。

核心原則：

> GitHub 保存系統核心；ChatGPT Project 保存實際分析環境與私人 Case。

GitHub 更新不應直接覆蓋命主私人資料。

---

## 一、設定 Project Instructions

開啟：

```text
core/核心提示詞.md
```

把內容同步到 ChatGPT Project 的 Instructions／專案指示。

這份提示詞負責：

- 資料讀取順序
- 問事先盲判、後事件校準
- 八字／紫微／奇門分工
- 七種資料類型區分
- 高風險領域邊界
- 輸出格式與信心標示

若核心提示詞更新，Project Instructions 也要同步更新。

---

## 二、基礎規則

一般 Project 至少加入：

```text
core/命理分析作業規範.md
core/命理推導計算規則.md
core/紫微流月推導規則.md
```

用途：

- `命理分析作業規範.md`：最高層分析流程與資料治理。
- `命理推導計算規則.md`：八字流年／流月／流日／流時固定算法與邊界。
- `紫微流月推導規則.md`：紫微斗君、流月命宮、十二宮與月份邊界。

---

## 三、Compatibility wrapper 與正式 package

相容入口：

```text
engine/project_bazi_calendar.py
engine/project_ziwei_month.py
engine/project_ziwei_day.py
engine/project_ziwei_hour.py
```

這些檔案保留既有呼叫路徑，但不是完全獨立的單檔引擎。

若只是讓 AI 閱讀正式入口，可以把 wrapper 當作索引；若環境要實際執行，必須同步對應 package modules。

---

## 四、八字執行環境

同步：

```text
engine/bazi/__init__.py
engine/bazi/calendar.py
engine/project_bazi_calendar.py
```

八字正式能力包含流年、流月、流日、流時與天干十神等 Project 推導。

八字 23:00 early-Zi 規則仍由八字引擎負責，不由 Calendar Resolver 代替。

---

## 五、紫微流月／流日／流時定位

共用：

```text
engine/ziwei/__init__.py
engine/ziwei/common.py
engine/ziwei/capabilities.py
```

流月：

```text
core/紫微流月推導規則.md
engine/project_ziwei_month.py
engine/ziwei/month.py
```

流日：

```text
core/紫微流日推導規則.md
engine/project_ziwei_day.py
engine/ziwei/day.py
```

流時：

```text
core/紫微流時推導規則.md
engine/project_ziwei_hour.py
engine/ziwei/hour.py
```

v1.2.0 狀態：

```text
紫微流月 = implemented / stable / default
紫微流日 = implemented / experimental / on_demand
紫微流時 = implemented / experimental / on_demand
```

流日／流時目前只做宮位定位。Experimental 能力可執行，但分析時必須降權。

---

## 六、Calendar Resolver v1

若要從 structured civil datetime + IANA timezone 建立 `CalendarContext`，同步：

```text
requirements.txt
engine/calendar/__init__.py
engine/calendar/precision.py
engine/calendar/models.py
engine/calendar/timezone.py
engine/calendar/lunar.py
engine/calendar/resolver.py
engine/ziwei/calendar_adapter.py
```

並安裝：

```bash
pip install -r requirements.txt
```

v1.2.0 exact runtime dependencies：

```text
lunar-python==1.4.8
tzdata==2026.3
```

Resolver 只接受 structured local civil datetime、IANA timezone 與可選 `utc_offset_hint`。

Resolver 不負責：

- 自然語言日期解析
- timezone 猜測
- 真太陽時
- 八字換日 policy
- 紫微 23:00 命理日界 school policy

23:00 已屬子時，但 civil date 只在 00:00 換日。

---

## 七、Ziwei Transformation & Flying Core v1

若要在 Python 環境執行十干四化、本命宮干飛化、生年／大限／流年四化飛化與 Composition，至少同步：

```text
engine/ziwei/errors.py
engine/ziwei/models.py
engine/ziwei/basis.py
engine/ziwei/transformation_profiles.py
engine/ziwei/transformations.py
engine/ziwei/flying.py
engine/ziwei/composition.py
```

並保持同版：

```text
engine/ziwei/__init__.py
engine/ziwei/common.py
engine/ziwei/capabilities.py
```

v1.2.0 狀態：

```text
Ziwei Transformation Core = implemented / stable / on_demand
Ziwei Flying Core = implemented / stable / on_demand
```

已支援：

- 十天干四化
- 本命十二宮宮干飛化
- 生年四化
- 大限四化／飛化
- 流年四化／飛化
- layer no-overwrite / fail-closed conflict handling

仍未支援：

- 流月四化／飛化
- 流日四化／飛化
- 流時四化／飛化
- 流曜

這些細運能力仍需要 Fine Cycle Stem Resolver 與獨立 qualification。

---

## 八、建議的完整 Python 環境

若目標不是只讓 AI 閱讀，而是要真正執行 v1.2.0 已有能力，建議至少同步：

```text
requirements.txt

engine/bazi/__init__.py
engine/bazi/calendar.py
engine/project_bazi_calendar.py

engine/calendar/__init__.py
engine/calendar/precision.py
engine/calendar/models.py
engine/calendar/timezone.py
engine/calendar/lunar.py
engine/calendar/resolver.py

engine/ziwei/__init__.py
engine/ziwei/common.py
engine/ziwei/capabilities.py
engine/ziwei/month.py
engine/ziwei/day.py
engine/ziwei/hour.py
engine/ziwei/calendar_adapter.py
engine/ziwei/errors.py
engine/ziwei/models.py
engine/ziwei/basis.py
engine/ziwei/transformation_profiles.py
engine/ziwei/transformations.py
engine/ziwei/flying.py
engine/ziwei/composition.py

engine/project_ziwei_month.py
engine/project_ziwei_day.py
engine/project_ziwei_hour.py
```

wrapper、package 與 requirements 應保持同版。

---

## 九、Capability 語意

```text
implementation = planned / implemented
maturity       = experimental / stable
routing        = default / on_demand
```

目前正式狀態：

```text
紫微流月定位 = implemented / stable / default
紫微流日定位 = implemented / experimental / on_demand
紫微流時定位 = implemented / experimental / on_demand
Ziwei Transformation Core = implemented / stable / on_demand
Ziwei Flying Core = implemented / stable / on_demand
流月／流日／流時四化與飛化 = planned / on_demand
流曜 = planned / on_demand
Cross-System Validation = planned
```

`implemented` 代表程式能力存在；`on_demand` 代表一般問事不預設跑；`planned` 代表尚不能執行。

---

## 十、建立私人 Case

從 `templates/` 複製空白模板，建立自己的：

```text
命盤核心摘要.md
命盤資料校驗紀錄.md
驗證事件紀錄.md
流年追蹤紀錄.md
問事追蹤紀錄.md
重大決策紀錄.md
```

優先順序：

1. 出生資料與正式命盤來源
2. 命盤資料校驗
3. 命盤核心摘要
4. 已確認的重要事件
5. 再累積流年、問事與重大決策追蹤

私人資料不要提交回共用 repo。

---

## 十一、第一次啟動 Project

先做命盤建立／校驗，不要直接跳到未來預測。

建議確認：

- 是否成功讀到 `命理分析作業規範.md`
- 出生年月日時與出生地是否正確
- 八字四柱、日主、大運是否一致
- 紫微十二宮、大限、流年是否可讀
- 不同來源是否有時間口徑差異
- 哪些欄位是原始來源，哪些是 Project 推導
- capability registry 是否能區分 Stable / Experimental / Planned 與 Default / On-demand

完成後再建立 `命盤核心摘要.md`。

---

## 十二、Python 檔案放進 Project 代表什麼

把 `.py` 放進 Project，代表保存正式算法來源。

**不代表每一個 ChatGPT 對話都會自動執行 Python。**

若當次環境能執行 Python，可依正式程式計算；若無法執行，AI 只能閱讀規則與程式內容，不得假裝已執行。

回答若宣稱「程式已計算」「測試已通過」，必須真的有執行證據。

---

## 十三、驗證資料

若 Project 檔案空間允許，可加入對應測試案例作知識參考；Python 單元測試主要供開發與回歸使用，不是一般問事的必要檔案。

v1.2.0 Phase 2A qualification 與 main regression 基線請看：

- `VERSION.md`
- `CHANGELOG.md`
- `qualification/ziwei/phase2a/`

---

## 十四、更新時不要覆蓋私人資料

日後更新 Metaphysics Lab 時，只同步共用核心：

- `core/`
- `engine/`
- `requirements.txt`
- 必要的 `tests/`
- Project Instructions

不要用 GitHub 版本覆蓋自己的：

- 命盤核心摘要
- 命盤資料校驗紀錄
- 驗證事件紀錄
- 流年追蹤紀錄
- 問事追蹤紀錄
- 重大決策紀錄
- 原始八字／紫微資料
- 個人命盤 PDF／截圖

完整升級流程請看 [更新與版本同步](更新與版本同步.md)。
