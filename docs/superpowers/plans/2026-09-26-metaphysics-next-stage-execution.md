# Metaphysics Lab下一階段 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans執行；若使用者另外選擇subagent-driven方式，使用superpowers:subagent-driven-development。所有實作依systematic debugging → TDD → implementation → verification-before-completion。以下checkbox均未完成；本文件不是實作或測試成果。

**Goal:** 以v1.7.1為研究baseline，先建立可稽核能力矩陣，再交付authority-safe大運視覺化及版本中立maintenance治理，不承諾自動Stable promotion。

**Architecture:** 既有manifest仍是capability truth；evidence index只補證據。engine projection輸出版本化JSON，獨立SVG renderer只呈現資料。研究／promotion／runtime integration分開審查。

**Tech Stack:** 沿用repo受支持Python(目前v1.7 workflow為3.9)、unittest、stdlib JSON／XML、JSON Schema 2020-12；MVP不新增matplotlib或Web framework到runtime dependencies。

**Spec:** [12週Roadmap與完整設計](../specs/2026-09-26-metaphysics-next-stage-roadmap.md)。執行者先完整讀spec，再讀本計畫；兩份一起交接。

狀態：**Task 0–2 APPROVED FOR LUNA EXECUTION；Task 3–10 NOT AUTHORIZED。** 使用者已接受roadmap方向，但本輪只做到Capability Evidence Index／Qualification Matrix與repo現況盤點。Task 2完成後強制停下回報，取得下一階段明確授權才能繼續；不是通過G1就自動開始Task 3，也不是依G2自動進入Task 4。Luna Max為使用者選定的實作者；本次文件更新沒有執行Task 0–2，也不冒充已切換模型。

### 本輪checkpoint與共用現況

- baseline：`872c60b2e959ea48d25524b74686e488f576ec6f`，fresh verify後從main建立隔離工作線；若main不再等於baseline，停止實作並回報差異，不能默換受測版本。
- 允許：Task 0–2的index／builder／validator／tests、生成矩陣、source snapshot、branch residual ledger；TDD只針對這些治理工具。
- 不允許：Task 3 qualification實作、Task 4 Visualization Data Contract、Task 5–6大運projection／renderer、Task 7–9治理工具移植／archive／pilot實作。可記錄缺口與後續建議，不提前寫其程式。
- 現況依相連roadmap第8.1節：PR #219、#221原base refs缺失，head branches仍保留。不得retarget／merge／重建base／刪head；API內base SHA只是歷史metadata。
- planning／artifact lifecycle分支先保留，等正式承接後由另一工作流評估。三條flow-time／month-boundary線須完整residual／blob audit才有去留討論依據；局部相同不能代表可刪。
- 本次同步文件的docs分支commit授權僅限文件更新，不延伸至Luna產品／工具變更的commit或push；本機完成時如實回報LOCAL VERIFIED／REMOTE NOT APPLIED。

## Global Constraints

- 唯一repo：`mvkaiii/metaphysics-lab`；參考baseline：`872c60b2e959ea48d25524b74686e488f576ec6f`。
- 本機放文件的checkout仍是v1.6舊branch；不得在那裡實作v1.8。從fresh main建立隔離workspace，遵守using-git-worktrees。
- 不改歷史v1.7.1／v1.7.0／v1.6.0 tag、Release或assets；不force push，不刪branch。
- 不改Case Schema 1.1、不提升selector／interpretation default、不因implemented而升Stable。
- 不重造命理算法、release架構或offline pipeline；新發現algorithm bug另報證據與變更範圍。
- Git stage／commit／push／PR／Actions寫入、安裝依賴與cleanup需使用者明確授權。本計畫本身不授予這些操作。未授權時留local diff及建議commit單元。
- 不自動發布；即使所有gate綠燈也只交接READY FOR HUMAN RELEASE REVIEW。
- 每個task要記錄RED命令及真正失敗原因、GREEN結果與實際test count；import／環境失敗不能冒充功能RED。
- 不公開private出生資料、ledger、oracle、outcomes；真實prospective需人類授權，無資料則PENDING。
- 任何候選身份／authority／reference缺口都fail-closed。不能用local成功替代正式hosted qualification。

## Review Focus

1. 歷史summary PASS卻對不上當前rule/profile/scope：Task 1測試拒絕promotion evidence binding。
2. 大運交界剛好等於as_of或來源end語意不明：Task 4–5測試唯一current或unsupported，不自行加一天。
3. 多候選、birth精度不足或缺大運欄位：Task 5回unsupported／明確null，不挑第一盤、不補算法。
4. blind chart中的隱藏Case事件／HTML／tooltip資料：Task 4–6的allowlist、annotation與SVG安全測試拒絕。
5. artifact已被保護、inventory缺頁或filename與run SHA衝突：Task 7只報告／保護，不產生可執行刪除候選。

## 工作單元與介面

以下新路徑是計畫，不是宣稱repo已有。若fresh main已有同責任模組，先比較再重用，不重複建第二套。

| Task | 新增或修改 | 責任／對外介面 |
| --- | --- | --- |
| 1 | `qualification/capabilities/evidence-index.v1.json`；`tools/build_capability_qualification_matrix.py`；`tests/test_capability_qualification_matrix.py` | `build_matrix(manifest: dict, evidence_index: dict, repo_root: Path) -> dict`；`validate_evidence_index(...) -> list[str]`，回傳按key排序errors，不改registry |
| 2 | `docs/qualification/capability-matrix.md`；`docs/research/branch-disposition.md`；`qualification/capabilities/source-snapshot.v1.json` | 人可讀矩陣、source與branch residual ledger；不內嵌private source |
| 3 | 既有三個qualification builders/tests；新`qualification/bazi/decadal/README.md`、`public-reference-summary.json`與`tests/test_bazi_decadal_qualification.py`(取得reference後) | 小scope證據包，不動算法；reference不足只寫gap記錄，不產生PASS summary |
| 4 | `schemas/visualization/chart.v1.schema.json`；`engine/visualization/__init__.py`、`contract.py`；`tests/test_visualization_contract.py` | `validate_chart(chart: dict) -> list[str]`；ready／unsupported discriminated contract |
| 5 | `engine/visualization/bazi_decadal.py`；`tests/test_visualization_bazi_decadal.py`；`tests/fixtures/visualization/` | `project_bazi_decadal(engine_view: dict, manifest: dict, *, as_of: str, timezone: str, visibility_mode: str) -> dict` |
| 6 | `renderers/__init__.py`、`renderers/svg/__init__.py`、`renderers/svg/bazi_decadal.py`；`tools/render_visualization.py`；`tests/test_visualization_svg.py` | `render_bazi_decadal_svg(chart: dict) -> str`；`render_bazi_decadal_text(chart: dict) -> str`；只收validated chart |
| 7 | `tools/artifact_inventory.py`、`tools/artifact_lifecycle_policy.py`；`config/artifact-protection.json`；三個對應tests | 唯讀inventory與純selection policy；不含delete executor |
| 8 | `docs/archive/v1.7/README.md`、`sources.json`與兩份歷史原文 | historical archive＋current crosswalk；不改active capability truth |
| 9 | `docs/research/prospective-pilot-protocol.md`與經review的governance delta/tests | 先protocol再確定研究模組移植範圍；沒有protocol不開始真實run |
| 10 | `docs/qualification/next-candidate-checklist.md`；必要runtime integration另經review | verification manifest；不是sandbox PASS evidence |

Task 1–2、4–6、7、8、9各為可獨立review的工作單元；不把所有研究branch混成一個PR。Task 3和9的研究結論不能在寫測試前預定。

## Task 0：Baseline與安全工作環境

**Read:** 現行AGENTS／README、六份capability registries、manifest、相關workflow；不要只照本文件假設環境。

- [ ] 讀取repo remote、branch、HEAD、status；用GitHub API確認main／v1.7.1 tag／release target與資產清單。若main已前進，列出與baseline差異並停止實作，等待baseline決策；不可reset遠端或把新main當成同一baseline。
- [ ] 記錄v1.7.1、v1.7.0、v1.6.0各自tag解析後commit與release assets metadata，作之後只讀比對。遇到歷史identity改變就停止。
- [ ] 依已授權範圍建立隔離worktree。確認不是`release/v1.6.0-integration`；保留原工作區的未提交文件。
- [ ] 唯讀檢查Python／依賴；缺套件先回報。不改production來繞過套件缺失；需要安裝時說明隔離環境與取得授權。
- [ ] 執行既有manifest focused tests，建立baseline結果。不把本次source inspection說成已重跑全部CI。

```powershell
git remote -v
git branch --show-current
git rev-parse HEAD
git status --short
python -m unittest tests.test_v17_capability_manifest tests.test_v17_capability_distribution_parity -v
```

**Gate G0：** exact source與本機一致、環境可重現、沒有錯repo／dirty overlap；否則只做不受影響的唯讀盤點。

## Task 1：TDD evidence index與矩陣builder

**Consumes:** `engine.distribution.manifest.load_capability_manifest(engine_root: Optional[Path] = None) -> dict`。實作前讀實際返回shape，不自行假設capabilities為list或dict。

**Produces:** 表格前述三個新檔。index row以`capability_id/scope/profile_id`唯一；rule_version與source SHA綁定。缺證據為needs_verification，不使工具無法產生gap報告；偽造／衝突／無效索引才是validation error。`--check`不得寫檔。

- [ ] 建立小型synthetic manifest/index測試：`test_matrix_takes_maturity_only_from_manifest` assert矩陣maturity等於manifest，index提供maturity override應被拒絕。
- [ ] 增加`test_rule_scope_hash_mismatch_rejected`、`test_missing_evidence_is_visible_gap`、`test_unknown_and_duplicate_keys_rejected`、`test_historical_pass_is_not_current_promotion`、`test_private_payload_not_embedded`。
- [ ] 跑`python -m unittest tests.test_capability_qualification_matrix -v`，確認因尚未實作的介面／行為失敗；若只是測試發現不了先修runner配置。
- [ ] 最小實作validator／builder；只讀來源，digest針對實際證據bytes；不得把markdown複製的PASS當source proof。
- [ ] 加`test_deterministic_order_and_output`、`test_check_mode_does_not_write`並跑GREEN。
- [ ] 加main manifest contract test：baseline30項、5 stable／25 experimental是snapshot斷言，不是永遠固定數；future manifest變更必須review更新snapshot，不能硬編碼runtime。
- [ ] 交接diff、RED/GREEN與建議commit：`feat: add capability qualification evidence index`。未授權不commit。

**Gate G1：** 沒有新增capability truth，PASS證據能定位scope，缺口可見；registry／dist／core無差異。

## Task 2：填入查核結果，而不是預填PASS

**Consumes:** Task 1 builder。**Produces:** matrix docs、branch residual ledger、source snapshot。

- [ ] 從六registry填全部30項，flowing_stars展開五scope、selector／interpretation展開supported profiles；action-only與dependency references另表記錄。
- [ ] 精讀並綁定現有flow-time、month-boundary、natal、phase2b/phase2c、prospective evidence；不得只讀摘要status欄。
- [ ] 用固定source SHA與Git blob比較記錄「相同、不同、不在main、未查」；區分三dot compare的分支歷史和main→branch真正內容差異。
- [ ] fresh核對PR #219／#221 metadata、原base ref存在性與head SHA，記錄missing-base狀態；不retarget／merge／重建base或刪head。不把404單獨當全repo不可讀，也不把PR保存的base SHA當ref存在證明。
- [ ] 對#219、portable、三條flow-time／month-boundary及#200記錄residual／blob audit覆蓋範圍。完整audit須逐檔列main/head blob、different/missing內容、tests/docs/evidence承接與未解缺口；尚未完成則明示PARTIAL／NOT SAFE TO DELETE。不得從抽樣或commit數推定可刪，不merge分支來取得文件。
- [ ] 生成人可讀matrix；`--check`零差異、invalid source fixtures會FAIL、private資料scan無洩漏。
- [ ] 列出首批qualification scope、不適用prospective的理由及需要人類決定的事項，僅作下一階段提案，不執行Task 3或修改maturity。

**Task 0–2 STOP CHECKPOINT(強制)：** 回報fresh baseline與docs來源SHA、changed files、index／matrix coverage、實際RED/GREEN與focused regression結果、證據缺口、PR missing-base狀態、各branch audit完整度、Git狀態及local/remote分界。既有qualification evidence、production／core／dist、Case Schema、defaults與歷史release皆不可因本輪而變動。完成後停止，等待使用者授權下一階段；下列Task 3–10保留作roadmap，不能自動執行。

## Task 3：首批qualification與promotion packet

**Existing files:** `tools/build_bazi_flow_time_qualification.py`、`tools/build_ziwei_flow_time_qualification.py`、`tools/build_ziwei_month_boundary_qualification.py`及同名tests；新Bazi大運scope按表列路徑。

- [ ] 先重跑現有三份builder的`--check`與focused tests，記錄baseline；builder check不可覆蓋frozen evidence。
- [ ] 提出首批gap清單：day/hour stems profile、跨日/DST boundary、Bazi decadal endpoints/age/direction/reference。任何reference共用相同底層library都標註非完全獨立。
- [ ] 寫尚未涵蓋的boundary RED測試；expected值來自已核對reference／規範，不從待測函式回算。
- [ ] 若現有engine正確而缺測試，加入fixture／qualification生成與validator，保留算法。若確有算法錯誤，停止該scope，回報minimal reproduction與預期來源，另取變更確認。
- [ ] GREEN後生成新scope packet，綁source SHA/rule/profile、fixture digest、命令、環境、count、failures、limitations。歷史summary不覆寫成新PASS。
- [ ] 產出promotion decision草案，保持registry原值；人類才能核准受限scope的promotion。若資料不足，結果為BLOCKED／NEEDS_EVIDENCE，不能補假reference。

```powershell
python tools/build_bazi_flow_time_qualification.py --check
python tools/build_ziwei_flow_time_qualification.py --check
python tools/build_ziwei_month_boundary_qualification.py --check
python -m unittest tests.test_bazi_flow_time_qualification tests.test_ziwei_flow_time_qualification tests.test_ziwei_month_boundary_qualification -v
```

**Gate G2輸入：** 明確確認大運interval語意、age basis、optional fields來源、可接受的reference scope。未確認不能讓projection猜。

## Task 4：TDD Visualization Contract

**Consumes:** spec第6–7節。**Produces:** schema、`validate_chart(chart: dict) -> list[str]`及tests。

- [ ] 人類確認G2：半開區間能否無損對映、age語意、blind allowlist、E標示、unsupported形狀。若需要更改這些核心決策，先更新plan，不邊做邊猜。
- [ ] 寫`test_unknown_schema_rejected`、`test_ready_requires_provenance_and_field_authority`、`test_inference_cannot_claim_verified_event`、`test_experimental_badge_cannot_be_dropped`、`test_nonfinite_numbers_rejected`、`test_unsupported_has_no_data`。
- [ ] 跑`python -m unittest tests.test_visualization_contract -v`確認RED。
- [ ] 實作兩個分支schema與Python語意validator；authority使用spec七個精確enum，errors排序可重現。未知欄位／未知authority拒絕；ready digest為64位hex。
- [ ] 加blind fixture含ledger／known reality／current context／event annotations，assert全部拒絕；非blind也不能任意接受不支持的annotation。
- [ ] GREEN並做schema與語意validator一致性測試；若需新增JSON Schema dev依賴，先取得安裝授權，不把它加入production bundle。

## Task 5：TDD pure Bazi projection

**Consumes:** allowlisted `engine_view` envelope與manifest；不得直接收Case。envelope明定`project_natal.bazi`、`source_capabilities`、`provenance`、`input_status`；只接受唯一resolved candidate及已確認profile。未知必需資訊回unsupported，非法／污染資料回validation error。

**Produces:** `project_bazi_decadal(engine_view: dict, manifest: dict, *, as_of: str, timezone: str, visibility_mode: str) -> dict`；輸出須通過Task 4。

- [ ] 用現有engine產生固定synthetic source fixture，另存來源版本與digest；不加入真實事件。取兩段相鄰大運及邊界，保留原始起運年齡精度。
- [ ] 寫`test_projection_preserves_engine_period_values`、`test_as_of_at_boundary_selects_next_period_once`、`test_outside_range_has_no_current_period`、`test_unknown_interval_semantics_is_unsupported`。
- [ ] 加`test_ambiguous_candidate_is_unsupported`、`test_missing_optional_ten_god_is_null_not_calculated`、`test_source_maturity_matches_manifest`、`test_no_case_or_event_payload_leaks`、`test_same_input_same_canonical_bytes`。
- [ ] 跑`python -m unittest tests.test_visualization_bazi_decadal -v`確認RED。
- [ ] 最小實作欄位映射、ISO datetime比較與source validation。禁止重新計算干支、起運、十神、四化或以西元年猜流年起點；禁止wall-clock／network／filesystem副作用。
- [ ] optional overlays只消費已有engine輸出；無合格來源空陣列。十神／五行null帶reason，renderer不得補值。
- [ ] GREEN後測試fixture在不同as_of、timezone offset、DST交界的穩定性；沒有source-bound timezone契約的輸入unsupported。

**Gate G3：** schema+projection合格，可保留Experimental。若唯一缺口是optional欄位，MVP降級而不重寫算法；若必需時間語意缺口，停止ready chart交付。

## Task 6：TDD SVG renderer與文字替代

**Consumes:** Task 5 validated chart。**Produces:** `render_bazi_decadal_svg(chart: dict) -> str`及`render_bazi_decadal_text(chart: dict) -> str`，CLI `python tools/render_visualization.py --input <chart.json> --output <chart.svg>`；CLI只寫明確指定新output，既有檔預設拒絕覆寫。

- [ ] 寫`test_svg_has_same_labels_and_current_period_as_contract`、`test_experimental_and_authority_labels_visible`、`test_text_alternative_preserves_limitations`、`test_unsupported_renders_no_fake_timeline`。
- [ ] 加`test_script_and_external_href_cannot_be_injected`、`test_renderer_has_no_engine_algorithm_imports`、`test_svg_bytes_deterministic`、`test_long_labels_do_not_hide_authority`、`test_existing_output_requires_explicit_overwrite`。
- [ ] 跑`python -m unittest tests.test_visualization_svg -v`確認RED；使用stdlib XML escape，不拼接未驗證HTML。
- [ ] 最小實作SVG timeline與純文字替代；stable元素ID、固定layout、無外部字型fetch、無script、無隱藏payload。圖表有年份／年齡／干支／optional欄位狀態／as_of。
- [ ] GREEN後人工檢視正常、多段、交界、空值、unsupported、長繁中標籤與黑白列印情境；保留synthetic輸出而非private個案截圖。
- [ ] 記錄QA缺陷與修正；不以pixel snapshot單獨宣稱語意通過。

**Gate G4：** 一張可用且不誤導的圖優先。大運×流年矩陣另補小型TDD plan後才做；須有可追溯interaction dataset，沒有就延後。Web renderer、紫微細時間圖、問事時間窗不自動啟動。

## Task 7：Version-neutral artifact inventory／policy

**Source:** `ci/v17-artifact-lifecycle-20260915@9872223aac6d2bc2d607d716c4490c5cd47651d0`的兩tools與三tests；不帶transport payload。

**Interfaces(新版規劃)：**

- `collect_inventory(fetch_json: Callable[[str], dict], repository: str) -> dict`：所有HTTP操作由注入函式負責，只允許GET；回`complete`、`artifacts`、`errors`、`total_bytes`。
- `classify_artifact(artifact: dict, protection: dict) -> dict`：回classification／protected／reasons，unknown一律protected。
- `select_cleanup_candidates(inventory: dict, protection: dict, approval: dict) -> dict`：回`selection_allowed`、`candidate_ids`、`blocked_reasons`；無網路、無刪除。approval綁repository、完整inventory digest、每個candidate ID及provenance，空approval不能選。

- [ ] 先跑舊tests作行為參考；重新確認它們是否支持fresh releases，不能因舊測試GREEN就直接rename。
- [ ] 寫RED：protected v1.6／v1.7／v1.7.1、current多candidate、release evidence、unknown provenance、SHA衝突、缺run/attempt資訊、incomplete pagination、stale approval、foreign repo、零DELETE。
- [ ] 跑`python -m unittest tests.test_artifact_inventory tests.test_artifact_lifecycle_policy -v`確認RED。
- [ ] 最小移植唯讀inventory與pure policy；刪除舊hardcoded release identities，改explicit config。沒有足夠證據比對artifact origin時保護，不推測。
- [ ] retention建議1／3／7日只作分類策略；protected不被cleanup挑中不代表平台永久保存。保護所有frozen release，不只v1.6。
- [ ] GREEN後才提`.github/workflows/artifact-inventory.yml`：`contents: read`、`actions: read`、不upload intermediate、不含delete API。加`tests/test_artifact_inventory_workflow.py`先RED後GREEN。
- [ ] Hosted啟用／正式workflow retention調整需另確認GitHub權限及精確diff；無權限只LOCAL VERIFIED，不宣稱remote applied。

## Task 8：歷史設計歸檔

**Consumes:** spec第8.2節八份文件與固定SHA。**Produces:** design原文、index原文、source hashes、current crosswalk。

- [ ] 固定SHA取得原文並hash，不用目前branch浮動內容替代；保留原文bytes，歷史警語放README／sidecar，不偷偷重寫原設計。
- [ ] 新README明示「historical，不是current capability truth」；把原planned API與main現行API對齊，未知的列needs_verification。
- [ ] 其餘六份用固定SHA連結與hash索引，不把舊ledger的NOT STARTED轉成待辦。
- [ ] 驗證檔名、links、hash與來源，檢查只改docs；不刪branch、不改舊release docs來暗示重新qualification。

文件歸檔採source/hash驗證，不需要虛構TDD RED；若新增archive validator程式，該程式仍須TDD。

## Task 9：Prospective pilot設計與研究delta

這是**研究決策gate**，不是讓Luna自行發明empirical protocol的空白授權。可與Task 3並行調查，真實觀察前必須核准。

- [ ] 對#221與arm-freeze只做獨有模組／schema／tests對照，提出單一claim authority收斂方案；確認不與main prospective_validation重複。
- [ ] 完成protocol：一個pilot、資料owner、合法來源、claim universe、arms、lock/cutoff、outcome定義、indeterminate、withdrawal、baseline/control、評估指標、樣本／停止規則、偏離處理與privacy。
- [ ] 交人類核准protocol與資料授權；無資料或未核准時標NOT_STARTED並繼續其他workstreams，不能合成真實outcome。
- [ ] 核准後先寫`tests/test_prospective_pilot_governance.py`：lock後改claim／candidate／window拒絕；exposed oracle非blind；duplicate outcome拒絕；未成熟window不能scored；retrospective不能換標。
- [ ] 依已核准delta另寫精確模組移植subplan，再RED→minimal implementation→GREEN；不整包merge #221或arm-freeze。
- [ ] 保存protocol與lock provenance，持續等待實際outcome；到W12仍未到觀察期限，report PENDING，不縮短window或重寫失敗scenario。

## Task 10：Integration與verification-before-completion

**Precondition:** G1/G3/G4通過；維持每項Experimental標示與default原值。runtime公開action或額外圖表需要已確認的小型integration spec，不能靠本task擴scope。

- [ ] 核對本次changed files：只包含批准的epics，沒有研究raw data、歷史tag／asset、Case migration或defaults變更。
- [ ] 跑新增focused suites及既有release contract tests；記錄exact candidate SHA與環境。若未commit，只能稱working-tree verification，不捏造candidate SHA。
- [ ] 讀fresh workflow命令再跑完整回歸、dist check、release-surface、package、compile與contamination。以下是已讀取v1.7 workflow的baseline命令，**不是未來v1.8工作流已存在的宣告**。

```powershell
python -m unittest tests.test_v17_release_contract tests.test_v17_release_surface_validation tests.test_v17_release_package -v
python tools/build_ai_distribution.py --check
python tools/run_v17_release_surface_validation.py --json
python -m unittest discover -s tests -p 'test_*.py' -v
python -m compileall -q engine tools tests
python -c "from pathlib import Path; compile(Path('dist/ai/metaphysics_lab.py').read_text(encoding='utf-8'), 'dist/ai/metaphysics_lab.py', 'exec')"
git diff --check
git status --short
```

- [ ] deterministic package依已review的候選版本，以`python tools/build_release_package.py --verify --output <隔離暫存的新candidate ZIP路徑>`驗證。先讀CLI與版本來源；不沿用舊workflow的v1.7.0 ZIP檔名冒充v1.8、不覆寫歷史ZIP。必要dist rebuild只在新feature worktree執行、review生成diff。
- [ ] 保留既有workflow的private filename scan，另加內容層blind/privacy與unexpected asset檢查；原scan只檢查檔名，不代表全部內容無污染。
- [ ] 新renderers列入compile／test coverage；untracked檔也納入交接inventory。未獲commit授權時如實報dirty tree，不為通過clean-tree而偷偷commit或刪檔。
- [ ] 若GitHub操作已另授權，檢查exact candidate workflows、job conclusions、artifact existence/digests；不得只看command exit 0。GitHub失敗要分permission、quota與product regression，不混為一談。
- [ ] 依當前release contract準備新candidate sandbox；正式run由使用者批准後進行。未執行保持PENDING，舊證據不能冒用。
- [ ] 比對Task 0歷史tag／release資產identity仍一致；列release allowlist與無unexpected資產的證據。
- [ ] 最終報：已完成檔案、RED/GREEN、full test count、exact SHA、package/hash、仍E能力、pending evidence、local/remote分界、clean/dirty tree、protected history。到READY FOR HUMAN RELEASE REVIEW即停，不merge/tag/release。

## Rollback與停止條件

每task保留可review的local diff；有commit授權才建立獨立commit。回復使用新feature分支的經授權revert，不改frozen refs；禁止reset使用者既有修改。Evidence不刪除，撤銷以新紀錄表達。

任一baseline不一致、來源不明、實證需要未授權private資料、算法修正超scope、Case/default breaking change、無法保留authority、hosted gate失敗，停止受影響工作並回報Status／已知原因／缺口／下一步。其他安全且不依賴缺口的task可以繼續。

## 建議交給Luna的起始指令

> 請完整讀取本計畫及相連roadmap，僅執行已批准的Task 0–2。只操作mvkaiii/metaphysics-lab，fresh verify main與baseline 872c60b2e959ea48d25524b74686e488f576ec6f一致後建立隔離工作線，不在v1.6舊branch實作。完成Capability Evidence Index／Qualification Matrix與repo現況盤點後，回報實際RED/GREEN、證據缺口、PR #219／#221 missing-base狀態、branch audit完整度、Git狀態，然後強制停止等候下一階段授權。不要提前進Task 3；Visualization Data Contract是Task 4，不在本輪範圍。不要promotion、改Case Schema/default、修改既有qualification evidence、retarget/merge研究PR、刪branch/artifact、commit/push、tag或release。planning／artifact lifecycle與未完整稽核的qualification分支一律保留。main若已前進，先回報，不自行換baseline。

本計畫自我檢查：六workstreams映射到Task 1–10；全部七epics的門檻在spec第5節；五個Review Focus各有對應tests；future research未假設PASS；SVG與projection簽名一致；歷史release及production semantics保持保護。
