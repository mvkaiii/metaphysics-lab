from pathlib import Path

p = Path("VERSION.md")
s = p.read_text(encoding="utf-8")
s = s.replace("- 紫微細部四化／流曜／細層飛化：`planned / on_demand`", "- Ziwei Transformation Core：`implemented / stable / on_demand`\n- Ziwei Flying Core：`implemented / stable / on_demand`\n- 紫微流月／流日／流時四化與細層飛化：`planned / on_demand`\n- 紫微流曜：`planned / on_demand`")
s = s.replace("- 紫微細部四化／流曜／細層飛化：尚未實作", "- Ziwei Transformation Core：v1.2 開發線已實作為 Stable / On-demand\n- Ziwei Flying Core：v1.2 開發線已實作為 Stable / On-demand\n- 紫微流月／流日／流時四化、細層飛化與流曜：尚未實作")
p.write_text(s, encoding="utf-8")

p = Path("README.md")
s = p.read_text(encoding="utf-8")
needle = "- Ziwei Calendar Adapter：`implemented`，第一個正式 adapter；Bazi refactor 不包含在本次變更\n"
insert = needle + "- Ziwei Transformation Core：`implemented / stable / on_demand`，固定十干四化 profile，不處理流月／流日／流時天干\n- Ziwei Flying Core：`implemented / stable / on_demand`，只依已校驗本命星曜位置建立飛化 edge / natal graph\n- Phase 2A qualification：pinned iztro 十干四化 `40/40`、私人 Astralium 十干四化 `40/40`、飛化 `80/80`；repo 不保存私人 raw chart\n"
if "Ziwei Transformation Core：`implemented / stable / on_demand`" not in s:
    s = s.replace(needle, insert)
s = s.replace("- 紫微細部四化／流曜／細層飛化", "- 紫微流月／流日／流時四化與細層飛化\n- 紫微流曜")
if "紫微十干四化核心 = implemented / stable / on_demand" not in s:
    s = s.replace("紫微流時定位 = implemented / experimental / on_demand\n", "紫微流時定位 = implemented / experimental / on_demand\n紫微十干四化核心 = implemented / stable / on_demand\n紫微飛化核心 = implemented / stable / on_demand\n")
if "engine.ziwei.transformations" not in s:
    s = s.replace("engine.ziwei.capabilities\n", "engine.ziwei.capabilities\nengine.ziwei.transformations\nengine.ziwei.flying\n")
p.write_text(s, encoding="utf-8")

p = Path("docs/架構說明.md")
s = p.read_text(encoding="utf-8")
needle = "- Ziwei Calendar Adapter：`implemented`，以成功的 `CalendarContext` 原樣傳遞 lunar month/day/leap 與 hour branch 給既有 core。\n"
insert = needle + "- 十干四化核心：`implemented / stable / on_demand`；只處理天干→祿／權／科／忌，不自行解析細運天干。\n- 飛化核心：`implemented / stable / on_demand`；使用已校驗 natal star location 建立 cycle edges 與 48-edge `NatalFlyingGraph`。\n- 流月／流日／流時四化與細層飛化：`planned / on_demand`。\n- 流曜：`planned / on_demand`。\n"
if "- 十干四化核心：`implemented / stable / on_demand`" not in s:
    s = s.replace(needle, insert)
if "│   ├── transformation_profiles.py" not in s:
    s = s.replace("│   ├── hour.py\n│   └── calendar_adapter.py", "│   ├── hour.py\n│   ├── transformation_profiles.py\n│   ├── transformations.py\n│   ├── basis.py\n│   ├── flying.py\n│   ├── composition.py\n│   └── calendar_adapter.py")
needle2 = "- `engine/ziwei/calendar_adapter.py`：把可用 `CalendarContext` 原樣傳入既有 Ziwei core；不重算日期或套用命理日界。\n"
insert2 = needle2 + "- `engine/ziwei/transformation_profiles.py` / `transformations.py`：版本化十干四化規則與純規則 core。\n- `engine/ziwei/basis.py`：先驗 duplicate/conflict，再物化 immutable natal star / palace-stem indexes。\n- `engine/ziwei/flying.py`：四化落宮、12×4 natal flying graph 與中性的宮位幾何 relation；`↑/↓` 僅屬 presentation mapping。\n- `engine/ziwei/composition.py`：birth-year / decadal / yearly layer composition；不同 scope 不覆寫，同一 LayerIdentity 衝突 fail closed。\n"
if "`engine/ziwei/transformation_profiles.py` / `transformations.py`" not in s:
    s = s.replace(needle2, insert2)
s = s.replace("後續仍未實作的是紫微細部四化、流曜、細層飛化、Cross-System Validation 正式引擎與 Qimen 自動排盤；", "後續仍未實作的是紫微流月／流日／流時四化與細層飛化、流曜、Cross-System Validation 正式引擎與 Qimen 自動排盤；")
if "## Ziwei Transformation & Flying Core v1 Qualification" not in s:
    s += "\n\n## Ziwei Transformation & Flying Core v1 Qualification\n\nPhase 2A 核心已通過：pinned iztro 十干四化 40/40、私人 Astralium 十干四化 40/40、本命 48/48、大限 4/4、2023–2029 流年 28/28，飛化合計 80/80；Astralium-compatible `↑/↓` presentation 另記錄 11/11。私人 raw chart 與 normalized qualification input 不進 repo，repo 只保存 aggregate summary 與 digest。\n"
p.write_text(s, encoding="utf-8")

p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
insert = """
### Ziwei Transformation & Flying Core v1

- 新增版本化 `metaphysics-lab-common-v1` 十干四化核心：`ziwei.transformations = implemented / stable / on_demand`。
- 新增 natal basis record-first builders，duplicate/conflict 在 mapping materialization 前 fail closed。
- 新增 `FlyingEdge`、12×4 `NatalFlyingGraph`、same/opposite/normal 幾何 relation 與獨立 `↑/↓` presentation mapping。
- 新增 birth-year / decadal / yearly Composition；不同 scope 共存且不覆寫，同一 `LayerIdentity` 衝突 fail closed。
- `ziwei.flying = implemented / stable / on_demand`；stable 不代表 default routing。
- Public qualification 固定 iztro revision `814b77e6371e1050cac31bbf674db3c3138fcfde`：十干四化 40/40。
- Private Astralium qualification：十干四化 40/40、本命飛化 48/48、大限 4/4、2023–2029 流年 28/28，飛化合計 80/80；presentation 11/11。
- 私人 raw chart 與 normalized qualification input 不提交 repo；只保存 aggregate summary 與 source digest。
- 流月／流日／流時四化與細層飛化、流曜仍為 `planned / on_demand`，Phase 2A 未啟用。
"""
if "### Ziwei Transformation & Flying Core v1" not in s:
    s = s.replace("\n### 證據權重\n", insert + "\n### 證據權重\n")
s = s.replace("- 紫微細部四化、流曜與細層飛化算法。", "- 紫微流月／流日／流時四化與細層飛化算法。\n- 紫微流曜算法。")
p.write_text(s, encoding="utf-8")
