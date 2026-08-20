#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise RuntimeError(f"required replacement missing: {label}")


def ensure_after(text: str, anchor: str, addition: str, label: str) -> str:
    if addition.strip() in text:
        return text
    if anchor not in text:
        raise RuntimeError(f"anchor missing: {label}")
    return text.replace(anchor, anchor + addition, 1)


def append_section(path: str, marker: str, section: str) -> None:
    text = read(path)
    if marker not in text:
        text = text.rstrip() + "\n\n---\n\n" + section.strip() + "\n"
        write(path, text)


# Spec status
path = "docs/superpowers/specs/2026-08-20-紫微流時能力設計.md"
text = read(path)
text = re.sub(
    r"- 狀態：.*implementation plan.*",
    "- 狀態：書面 spec 已核准；implementation plan 已建立，進入實作與驗證",
    text,
    count=1,
)
write(path, text)

# core/命理分析作業規範.md
path = "core/命理分析作業規範.md"
text = read(path)
text = ensure_after(
    text,
    "- 紫微流日推導規則.md（涉及指定日期、日期比較或需要提高到日層解析度時）\n",
    "- 紫微流時推導規則.md（涉及指定時辰、時段比較或需要提高到時辰層解析度時）\n",
    "workflow read list flow-hour",
)
text = ensure_after(
    text,
    "- 若要按需使用紫微流日，先讀 `紫微流日推導規則.md` 並確認 capability 狀態。\n",
    "- 若要按需使用紫微流時，先讀 `紫微流時推導規則.md` 並確認 capability 狀態；民用時間必須先由可信上游解析為農曆日期與時辰地支。\n",
    "workflow blind flow-hour",
)
text = ensure_after(
    text,
    "- 紫微流日十二宮重排（Experimental / On-demand）\n",
    "- 紫微流時命宮（Experimental / On-demand）\n- 紫微流時十二宮重排（Experimental / On-demand）\n",
    "workflow project-derived flow-hour",
)
text = ensure_after(
    text,
    "- Project 紫微流日定位層（Experimental / On-demand）\n",
    "- Project 紫微流時定位層（Experimental / On-demand）\n",
    "workflow ziwei responsibilities flow-hour",
)
flow_hour_section = """## 已實作但預設不跑：紫微流時定位層

可依 `紫微流時推導規則.md` 建立：

- 流時命宮
- 流時十二宮重排

Capability：

```text
implemented / experimental / on_demand
```

使用原則：

- 只在使用者指定時辰、比較候選時段，或流日主軸確定後需要提高到時辰解析度時按需調用。
- 一般本命、年度、月份與一般單日問事不自動遍歷十二時辰。
- Experimental 流時可以參與時段比較，但必須降權，不能單獨支撐高度確信。
- 核心只接受已確認的農曆月、日、閏月狀態與時辰地支。
- 民用 datetime、timezone、DST、國曆轉農曆、23:00 日界與早子／晚子 policy 由未來 Calendar / Input Resolver 或可信上游處理，不由 `hour.py` 自行猜測。

"""
if "## 已實作但預設不跑：紫微流時定位層" not in text:
    text = text.replace("## 尚未實作\n", flow_hour_section + "## 尚未實作\n", 1)
text = text.replace("目前不得自行建立：\n\n- 紫微流時\n- 流月／流日／流時細部四化", "目前不得自行建立：\n\n- 流月／流日／流時細部四化", 1)
text = text.replace("不得因流月或流日定位已可執行", "不得因流月、流日或流時定位已可執行")
write(path, text)

# core/核心提示詞.md
path = "core/核心提示詞.md"
text = read(path)
text = ensure_after(
    text,
    "- 紫微流日推導規則.md（涉及指定日期、日期比較或需要日層解析度時）\n",
    "- 紫微流時推導規則.md（涉及指定時辰、時段比較或需要時辰層解析度時）\n",
    "prompt read list flow-hour",
)
text = ensure_after(
    text,
    "- 若使用紫微流日，先確認 `紫微流日推導規則.md` 與 capability 狀態\n",
    "- 若使用紫微流時，先確認 `紫微流時推導規則.md` 與 capability 狀態；民用時間先由可信上游解析\n",
    "prompt blind flow-hour",
)
text = ensure_after(
    text,
    "- 紫微流日命宮與十二宮（Experimental / On-demand）\n",
    "- 紫微流時命宮與十二宮（Experimental / On-demand）\n",
    "prompt project-derived flow-hour",
)
prompt_hour_section = """### Experimental / On-demand：紫微流時定位

可依 `紫微流時推導規則.md` 建立：

- 流時命宮
- 流時十二宮重排

只有在下列情況按需調用：

- 使用者指定某個時辰
- 比較候選時段
- 流日主軸已確認，需要提高到時辰層解析度
- 需要補充時辰層證據

一般本命、年度、月份或一般單日問事不自動遍歷十二時辰。

Experimental 流時可以執行與驗證，但分析時必須降權，不得單獨支撐高度確信。核心只接受已解析的農曆日期與時辰地支；Calendar Resolver、timezone、國曆轉農曆與 23:00 日界 policy 尚未實作。

"""
if "### Experimental / On-demand：紫微流時定位" not in text:
    text = text.replace("目前仍不得自行建立：\n", prompt_hour_section + "目前仍不得自行建立：\n", 1)
text = text.replace("目前仍不得自行建立：\n\n- 紫微流時\n- 流月／流日／流時細部四化", "目前仍不得自行建立：\n\n- 流月／流日／流時細部四化", 1)
text = text.replace("不得因紫微流月或流日已可執行", "不得因紫微流月、流日或流時已可執行")
write(path, text)

# core/命理推導計算規則.md
path = "core/命理推導計算規則.md"
text = read(path)
text = ensure_after(text, "- 紫微流日引擎：Metaphysics Lab 紫微流日定位引擎 v1.0.0-exp\n", "- 紫微流時引擎：Metaphysics Lab 紫微流時定位引擎 v1.0.0-exp\n", "calc header hour engine")
text = ensure_after(text, "- 紫微流日正式實作：`engine/ziwei/day.py`\n", "- 紫微流時正式實作：`engine/ziwei/hour.py`\n", "calc header hour module")
calc_hour_section = """## 已實作但按需調用：紫微流時定位層

依 `紫微流時推導規則.md` 可建立：

- 流時命宮
- 流時十二宮重排

Capability：

```text
implemented / experimental / on_demand
rule_version = 1.0-exp
```

固定公式：

```text
flow_hour_index = (flow_day_index + hour_branch_index) mod 12
```

核心只接受可信上游已確認的農曆月、農曆日、閏月狀態與時辰地支。它不提供國曆轉農曆、timezone、DST、民用時間解析或 23:00 日界判斷。只有指定時辰、時段比較或需要提高到時辰層解析度時才按需調用，Experimental 輸出必須降權。

"""
if "## 已實作但按需調用：紫微流時定位層" not in text:
    text = text.replace("## 尚未實作：其他紫微細運\n", calc_hour_section + "## 尚未實作：其他紫微細運\n", 1)
text = text.replace("目前不自行建立：\n\n- 紫微流時命盤\n- 流月／流日／流時細部四化", "目前不自行建立：\n\n- 流月／流日／流時細部四化", 1)
text = text.replace("不得因流月或流日定位已實作而自行延伸。", "不得因流月、流日或流時定位已實作而自行延伸到四化、流曜、飛化或 Resolver。")
text = ensure_after(text, "engine/ziwei/day.py\n", "engine/ziwei/hour.py\n", "calc module list hour")
text = ensure_after(text, "engine/project_ziwei_day.py\n", "engine/project_ziwei_hour.py\n", "calc wrapper list hour")
text = text.replace("紫微流月細節依 `紫微流月推導規則.md`；紫微流日細節依 `紫微流日推導規則.md`。", "紫微流月細節依 `紫微流月推導規則.md`；紫微流日細節依 `紫微流日推導規則.md`；紫微流時細節依 `紫微流時推導規則.md`。")
write(path, text)

# VERSION.md
path = "VERSION.md"
text = read(path)
text = text.replace("- 紫微流時：`planned / on_demand`", "- Metaphysics Lab 紫微流時定位引擎：v1.0.0-exp\n- 紫微流時推導規則：v1.0-exp\n- 紫微流時：`implemented / experimental / on_demand`")
text = text.replace("- 紫微流時：尚未實作", "- 紫微流時：v1.2 開發線已實作為 Experimental / On-demand")
write(path, text)

# README.md
path = "README.md"
text = read(path)
text = ensure_after(text, "- 紫微流日自動測試、人工回歸與外部來源交叉校驗紀錄\n", "- Project 紫微流時定位：`implemented / experimental / on_demand`\n- 流時命宮與流時十二宮重排\n", "readme v1.2 flow-hour")
text = text.replace("- 紫微流時 Project 推導\n", "")
text = text.replace("紫微流時定位 = planned / on_demand", "紫微流時定位 = implemented / experimental / on_demand")
text = ensure_after(text, "engine/project_ziwei_day.py\n", "engine/project_ziwei_hour.py\n", "readme wrapper hour")
text = ensure_after(text, "engine.ziwei.day\n", "engine.ziwei.hour\n", "readme module hour")
if "若要使用 v1.2 紫微流時 on-demand capability" not in text:
    anchor = "`project_ziwei_day.py` 同樣依賴 `engine/ziwei/` package，不是獨立單檔。\n"
    addition = "\n若要使用 v1.2 紫微流時 on-demand capability，再同步：\n\n```text\ncore/紫微流時推導規則.md\nengine/project_ziwei_hour.py\nengine/ziwei/hour.py\n```\n\n`project_ziwei_hour.py` 同樣依賴同版 `engine/ziwei/` package；一般問題不預設跑流時，只有指定時辰、時段比較或需要 hour-level precision 時才按需調用。\n"
    text = ensure_after(text, anchor, addition, "readme install hour")
write(path, text)

# CHANGELOG.md: append a scoped development entry if absent.
append_section(
    "CHANGELOG.md",
    "PR #3：紫微流時 on-demand capability",
    """## v1.2 開發線｜PR #3：紫微流時 on-demand capability

- 新增 `engine/ziwei/hour.py` 與 `engine/project_ziwei_hour.py`。
- 新增 `ziwei.flow_hour_palaces = implemented / experimental / on_demand`。
- 固定流時公式：流日命宮起子時，每時辰順行一宮。
- 新增 `core/紫微流時推導規則.md`、自動測試與人工回歸。
- 採 1.5 架構：flow-hour core 不處理民用 datetime、timezone、國曆轉農曆或 23:00 日界 policy；未來由 Calendar / Input Resolver 負責。
- 流時四化、流曜、細層飛化與 Cross-System Validation 仍未實作。
""",
)

# User-facing docs: normalize obvious old status phrases, then append a precise PR3 section.
user_docs = [
    "docs/架構說明.md",
    "docs/快速開始.md",
    "docs/安裝到ChatGPT-Project.md",
    "docs/更新與版本同步.md",
    "docs/設計/Metaphysics-Lab-v1.2-架構設計.md",
]
for path in user_docs:
    text = read(path)
    text = text.replace("紫微流時：planned / on_demand", "紫微流時：implemented / experimental / on_demand")
    text = text.replace("紫微流時宮位：planned / on_demand", "紫微流時宮位：implemented / experimental / on_demand")
    text = text.replace("紫微流時定位：planned / on_demand", "紫微流時定位：implemented / experimental / on_demand")
    text = text.replace("紫微流時：尚未實作", "紫微流時：implemented / experimental / on_demand")
    text = text.replace("紫微流時尚未實作", "紫微流時定位已實作為 Experimental / On-demand")
    text = text.replace("`hour.py`、`transformations.py`、`stars.py`、`flying.py` 與 `validation/cross_system.py` 仍是後續 capability PR。", "`hour.py` 已由 PR #3 實作為 Experimental / On-demand；`transformations.py`、`stars.py`、`flying.py` 與 `validation/cross_system.py` 仍是後續 capability PR。")
    write(path, text)
    append_section(
        path,
        "PR #3 流時 capability 狀態",
        """## PR #3 流時 capability 狀態

```text
紫微流月 = implemented / stable / default
紫微流日 = implemented / experimental / on_demand
紫微流時 = implemented / experimental / on_demand
紫微細部四化／流曜／細層飛化 = planned / on_demand
Cross-System Validation = planned
```

流時只提供命宮定位與十二宮重排。核心需由可信上游提供已解析的農曆日期與時辰地支；不自行處理國曆轉農曆、timezone、DST 或 23:00 日界 policy。一般問題不預設跑流時，只有指定時辰、時段比較或需要 hour-level precision 時才按需調用。

若要執行流時 capability，需保持以下檔案同版：

```text
core/紫微流時推導規則.md
engine/ziwei/hour.py
engine/project_ziwei_hour.py
engine/ziwei/day.py
engine/ziwei/month.py
engine/ziwei/common.py
engine/ziwei/capabilities.py
```
""",
    )

# Make the v1.2 architecture design's explicit hour section current.
path = "docs/設計/Metaphysics-Lab-v1.2-架構設計.md"
text = read(path)
text = text.replace("`hour.py`、`transformations.py`、`stars.py`、`flying.py` 與 `validation/cross_system.py` 仍是後續 capability PR。", "`hour.py` 已由 PR #3 實作為 Experimental / On-demand；`transformations.py`、`stars.py`、`flying.py` 與 `validation/cross_system.py` 仍是後續 capability PR。")
text = text.replace("紫微流時宮位：planned / on_demand", "紫微流時宮位：implemented / experimental / on_demand")
text = text.replace("紫微流時層仍為下一個獨立 capability PR。", "紫微流時定位層已由 PR #3 完成第一版正式 Python 實作。")
write(path, text)

# Guardrails: fail if top-level rules still say the whole flow-hour location capability is unavailable.
for path in ["core/命理分析作業規範.md", "core/核心提示詞.md", "core/命理推導計算規則.md"]:
    text = read(path)
    forbidden = [
        "- 紫微流時\n- 流月／流日／流時細部四化",
        "- 紫微流時命盤\n- 流月／流日／流時細部四化",
        "紫微流時：planned / on_demand",
        "紫微流時尚未實作",
    ]
    hits = [x for x in forbidden if x in text]
    if hits:
        raise RuntimeError(f"stale flow-hour prohibition remains in {path}: {hits}")

print("PR3 document sync complete")
