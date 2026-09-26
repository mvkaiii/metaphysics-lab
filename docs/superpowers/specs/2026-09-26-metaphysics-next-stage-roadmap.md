# Metaphysics Lab：下一階段12週Roadmap

規劃日期：2026-09-26，Asia/Taipei。狀態：**Roadmap方向已接受；本輪僅Task 0–2獲准交接Luna執行。Task 3–10仍是後續提案，不是qualification evidence。**

適用repo：`mvkaiii/metaphysics-lab`。研究baseline：`872c60b2e959ea48d25524b74686e488f576ec6f`(v1.7.1)。搭配[Luna執行計畫](../plans/2026-09-26-metaphysics-next-stage-execution.md)閱讀。

證據限制：本次以GitHub API、固定SHA原始碼、tree/blob比對、release metadata與既有qualification文件進行唯讀調查。沒有重新執行baseline測試、下載驗證Release二進位檔、實測GitHub寫入權限或宣告新的sandbox PASS。文件中的PASS若指既有資料，均是「repo內紀錄」，不是本次fresh verification。遠端狀態會變，執行前必須重新確認。

## 1. Executive recommendation

### 本輪已確認的決策邊界(2026-09-26更新)

使用者接受v1.8方向，僅授權Luna從fresh main執行Execution Plan的Task 0–2：baseline確認、Capability Evidence Index／Qualification Matrix、repo與research branch現況盤點。**Task 2完成後必須停下回報，取得下一階段明確授權才能繼續。** 下述12週順序與Top 5 next actions是長期roadmap，不是本輪連續執行授權。

- baseline維持`872c60b2e959ea48d25524b74686e488f576ec6f`；執行前fresh verify。若main前進，先停止實作並回報差異，不能默換baseline或reset main。
- 不提前進Task 3 qualification實作；Visualization Data Contract是**Task 4**，不在Task 0–2 checkpoint內；大運時間軸同樣不在本輪。
- 不做Stable promotion、Case Schema migration、selector／interpretation default變更、research branch直接merge或歷史Release修改。
- `plan/v1.7-reliability-guided-inquiry`與`ci/v17-artifact-lifecycle-20260915`先保留；須待歷史文件歸檔與version-neutral governance tooling正式承接後，再由另一工作流評估去留，不預先授權刪除。
- 舊qualification分支的代表性核心blob相同，只能支持局部內容已承接；刪除前仍需完整residual／blob audit與明確授權。沒有完整承接證據一律保留。
- PR #219／#221按第8.1節的missing-base狀態處理，不能自行retarget、merge或刪head branch。
- 本次文件同步只允許commit到`docs/next-stage-roadmap-20260926`；不是Luna產品變更的commit／push／merge授權。既有qualification evidence保持不變；Task 0–2只新增索引與現況紀錄，不改寫PASS。

下一個產品目標建議為**v1.8.0：Capability Evidence + Explainable Visualization**，不是v2.0，也不把新增視覺化塞進v1.7.2。

- v1.7.2只保留給獨立、必要、向後相容的修正；目前沒有為了roadmap而必須發patch的理由。
- v1.8.0採向後相容、on-demand新增能力：先建立可稽核的能力證據，再交付大運時間軸。**零項Stable promotion也可以是合格結果**，不能用升級數量當KPI。
- v2.0 research track只保留重大契約／算法研究的可能性；本輪沒有Case migration或破壞性重構理由，不啟動v2產品工程。

12週必要交付：統一Capability Qualification Matrix、首批細時間層qualification補強、prospective預註冊與證據治理、Visualization Data Contract v1草案到凍結、大運時間軸靜態MVP、版本中立的唯讀artifact inventory／cleanup selection、歷史設計歸檔。

不承諾交付：完整dashboard、五種圖表全部上線、流日／流時整套Stable、預測準確率提升、selector／interpretation default promotion、Case Schema升版、自動cleanup或自動發布。

優先順序：**矩陣與authority契約 → 大運資料可用性／細時間層邊界證據 → 大運MVP → 有條件的第二張圖**。研究線與產品線可以並行，但研究結果不能自動成為正式capability truth。

## 2. Current architecture assessment

### 2.1 已核對的正式baseline

GitHub查核時，`main`、`v1.7.1` tag與正式Release的target均為`872c60b2e959ea48d25524b74686e488f576ec6f`。[Release](https://github.com/mvkaiii/metaphysics-lab/releases/tag/v1.7.1)

| 項目 | 值 |
| --- | --- |
| Release | v1.7.1 |
| 發布時間 | 2026-09-24T16:52:05Z，即台灣2026-09-25 |
| Distribution Runtime | 1.2-exp |
| Project Contract／Runtime Schema／Case Schema | 1.2／1.1／1.1 |
| Capability Manifest | 1.0 |
| User Package | `Metaphysics-Lab-v1.7.1-User-Package.zip`，812,869 bytes |
| Package SHA256(API metadata) | `771f8493cd07b298c7971f38c601ce17a8acfcce5dab43c72e245f7b282943e8` |

正式Release列有package及三個release assets。API提供的SHA256如下；執行者下載時仍須自行驗證，不得把metadata讀取說成已驗證下載bytes。

| Asset | SHA256 |
| --- | --- |
| `metaphysics_lab.py` | `4fcede84857f9ce5160cc35ca0d4dfdf9a9c68a59ff0ace310010a2d1bda36c1` |
| `metaphysics_core.md` | `44109890558bb58875e097def8335131f5c50210c14152ceab608d0c41bdc388` |
| `project_instructions.txt` | `e67abf88c3d6e899daa46ad1479c7ccb0abe3975abd9ec54be57bc61ee81de48` |

v1.7.1的metadata-only定位與版本常數一致。歷史v1.7.1／v1.7.0／v1.6.0必須依專案政策保持immutable；本次Release API的`immutable`欄位為false，**政策禁止改寫不等於平台已強制鎖定**。本計畫不調整該平台設定。[版本常數](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/engine/distribution/constants.py)

### 2.2 架構判斷

1. 已有合理分層：`engine/birth`、`calendar`、`bazi`、`ziwei`、`natal`提供計算與整合，`engine/distribution`提供runtime orchestration；`core`承載AI操作契約，`dist/ai`是生成產物。不要重造release架構，也不要手改dist來繞過builder。
2. capability truth已存在：六份`capabilities.py`經`engine/distribution/manifest.py`整合成排序、可digest的manifest。矩陣必須引用此處，不另建一份可自行宣稱maturity的registry。[Manifest](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/engine/distribution/manifest.py)
3. implementation、maturity、routing是三個獨立軸。Stable不等於default；implemented不等於Stable；deterministic不等於對人生事件具有預測效度。
4. `build_natal`已有structured output；`project_natal.bazi.decadal_periods`已序列化index、pillar、起訖年齡、起訖datetime。**不需要重寫大運算法才能開始圖表**。但這個serializer沒有大運專屬十神／五行欄位，不得在renderer自行補算法或挪用四柱十神。[序列化](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/engine/natal/orchestration.py)
5. 既有qualification檔案屬不同歷史階段，狀態與scope不能混讀。例：`qualification/natal/phase2c0-summary.json`仍是PENDING_FINAL_ACCEPTANCE，並保留當時flowing stars為planned的歷史描述；現行registry卻已implemented。應加上版本／scope索引，不覆寫歷史檔使其看似當代證據。
6. #219的年度Ziwei實作與多個測試，以及三條flow-time／month-boundary分支的qualification核心檔案，已與main有相同blob。分支ahead commit數不能直接當成待移植功能數。
7. 本輪沒有執行CI可靠性診斷。過去v1.7 quota事件不能當作今天仍不能發布的證據；後續需要fresh check，但不得以local成功替代正式hosted gate。

### 2.3 本次查核與本機的差異

規劃文件存放的本機checkout仍是`release/v1.6.0-integration@c70ff83498298342b31d96ac0ece1bee6792adf8`，不是v1.7.1。這次只新增交接文件，沒有切branch或更新產品。**Luna不得在此舊release branch直接實作；須以fresh main驗證後建立隔離工作線。**

## 3. Capability maturity matrix

### 3.1 現行registry完整盤點

六份registry共30個capability：全部implemented，5個stable、25個experimental；僅`ziwei.flow_month_palaces`為default，其餘on_demand。下表忠實保留現況，不是promotion建議。簡寫：S=stable、E=experimental、D=default、O=on_demand；「未對齊」不是斷言沒有測試，而是尚無本次確認的完整scope-bound promotion packet。

| Capability ID | Maturity／Routing | rule_version | 證據／限制／下一步 |
| --- | --- | --- | --- |
| birth.input_resolution | E／O | 1.0-exp | 輸入不確定性與候選分支須保留；W1對齊範圍與tests |
| birth.location_resolution | E／O | 1.0-exp | 歷史summary有live provider PENDING；離線資料不等於線上provider已qualified |
| birth.true_solar_time | E／O | 1.0-exp | 校正、時區、DST與來源差異須分profile；不可隱性換時間基準 |
| bazi.natal_chart | E／O | 1.0-exp | 有公私reference摘要，private摘要promotion_allowed=false；大運scope需另外對齊 |
| natal.candidate_envelope | E／O | 1.0-exp | 聚合相依E能力；不可圖表化成單一確定命盤 |
| natal.reconciliation | S／O | 1.0 | 已有Stable宣告；回歸保護，不藉本輪擴大權限 |
| natal.markdown_export | S／O | 1.0 | 已有Stable宣告；視覺化不可混淆來源盤與推導盤 |
| historical.activation_selector | E／O | 1.0-exp | main已支援v2／2.1-exp profile，非default；#200需查殘餘差異 |
| distribution.prospective_forecast_governance | E／O | lin_tianji_v1.5-exp | governance可測，不等於預測已有效；接WS3 |
| distribution.prospective_validation | E／O | prospective-validation-v2-exp | 保留blind／retrospective分類；真實未來outcome不得合成 |
| distribution.structural_interpretation | E／O | lin_tianji_structural_v1-exp | 結構推導不是verified event |
| distribution.evidence_engine | E／O | lin_tianji_v1.5-exp | registry有ranking_authority=true，但仍E；分數不是客觀機率 |
| distribution.historical_personalization | E／O | lin_tianji_historical_personalization_v1-exp | 歷史污染／overfit風險；不可混入blind chart |
| distribution.interpretation_contract | E／O | lin_tianji_interpretation_contract_v1-exp | 已支援v2 profile，不提升default或maturity |
| ziwei.flow_month_palaces | S／D | 1.0 | 月界qualified範圍／閏月政策仍須明示；不推出全部月層Stable |
| ziwei.flow_day_palaces | E／O | 1.0-exp | 月宮相依＋日界組合；流日天干reference不涵蓋此宮位算法 |
| ziwei.flow_hour_palaces | E／O | 1.0-exp | 依賴流日宮位；日界／子時／DST組合先補證據 |
| ziwei.transformations | S／O | 1.0 | 基礎四化函式；不代表每個時間層組合Stable |
| ziwei.flying | S／O | 1.0 | 基礎飛化函式；不代表日／時飛化Stable |
| ziwei.natal_chart | E／O | 1.0-exp | 有pinned iztro等qualification；不能由參考一致自動promote |
| ziwei.flow_month_stem | E／O | 1.0-exp | 月界與天干為不同qualification問題；優先釐清scope |
| ziwei.flow_day_stem | E／O | 1.0-exp | 首批promotion評估候選；main已有flow-time reference packet |
| ziwei.flow_hour_stem | E／O | 1.0-exp | 首批候選；需補日界與跨時區profile可追溯性 |
| ziwei.flow_month_transformations | E／O | 1.0-exp | 相依month stem＋transformations；不沿用基礎函式標示 |
| ziwei.flow_day_transformations | E／O | 1.0-exp | 先鎖day stem，再驗證組合reference與失敗行為 |
| ziwei.flow_hour_transformations | E／O | 1.0-exp | 先鎖hour stem；日界組合驗證不可省略 |
| ziwei.flow_month_flying | E／O | 1.0-exp | 相依月四化＋flying；private fine-cycle來源不足 |
| ziwei.flow_day_flying | E／O | 1.0-exp | private fine-cycle來源不足；維持E |
| ziwei.flow_hour_flying | E／O | 1.0-exp | 相依鏈更長且reference不足；維持E |
| ziwei.flowing_stars | E／O | 1.0-exp | 支援decadal/yearly/monthly/daily/hourly；須五個scope子列，不能整包promote |

來源：[birth](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/engine/birth/capabilities.py)、[bazi](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/engine/bazi/capabilities.py)、[natal](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/engine/natal/capabilities.py)、[historical](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/engine/historical/capabilities.py)、[distribution](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/engine/distribution/capabilities.py)、[ziwei](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/engine/ziwei/capabilities.py)。

### 3.2 已有證據究竟能證明什麼

| Evidence | repo紀錄 | 不可推論 |
| --- | --- | --- |
| Bazi flow-time | pinned lunar-python 1.4.8；268 samples、16 boundary samples、13 calendar transitions等；包含DST及模組／bundle parity | 所有profile皆正確、人生預測有效、Bazi全能力Stable |
| Ziwei flow-time | day/hour stems，指定late-zi profile；有Five-Rat與day-pair checks | 流日宮位、日／時四化、飛化全部被驗證；月層問題已解 |
| Ziwei month-boundary | 平月／閏月1–15、16後、閏十二月政策；23:00 neutral月界 | 所有reference引擎都有相同閏十二月覆蓋；月天干已升級 |
| Phase2B private fine-cycle | PENDING，fine_cycle_source_not_available | private reference已取得 |
| Phase2C flowing stars | public PASS：600 source cases／6,120 placements；private PENDING、0 cases、promotion_allowed=false | 五個時間scope全部具備私有reference或prospective效度 |
| Bazi private natal | PASS，1 case，promotion_allowed=false | 樣本充分、允許Stable promotion |

來源：[Bazi flow-time](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/qualification/bazi/flow_time/README.md)、[Ziwei flow-time](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/qualification/ziwei/flow_time/README.md)、[月界](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/qualification/ziwei/month_boundary/README.md)、[Phase2B](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/qualification/ziwei/phase2b/private-astralium-summary.json)、[Phase2C](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/qualification/ziwei/phase2c/phase2c-summary.json)、[Bazi private](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/qualification/bazi/natal/private-summary.json)。

### 3.3 Qualification Matrix設計

**應先建立統一矩陣**。新建`qualification/capabilities/evidence-index.v1.json`作證據索引；`tools/build_capability_qualification_matrix.py`讀現行manifest，生成`docs/qualification/capability-matrix.md`。索引不得另存可覆寫registry的maturity／routing／implementation。

每列key為`capability_id + scope + profile_id`，保留rule_version精確binding；必備欄位：

- implementation／maturity／routing／rule_version／dependencies：由manifest取得。
- deterministic_contract、boundary_cases、fixture_refs、regression_refs、reference_qualification、prospective_evidence、failure_modes、known_limitations、promotion_criteria、promotion_decision。
- 每份證據包含source SHA、rule/profile、測試scope、檔案或run URL、內容SHA256、狀態與適用限制；禁止只寫「有tests」。
- prospective狀態使用`not_applicable_with_rationale`、`not_started`、`locked_pending_outcome`、`observed`等明確分類。純干支計算可不適用事件預測驗證，但必須有理由；問事／排序／事件claim不能用N/A逃過驗證。
- scope不明、缺hash、版本不符、歷史摘要過時、私有證據不可稽核，一律標示`needs_verification`，不能自動PASS。

Action coverage另列附表：Case Doctor、Guided Inquiry及runtime actions對應哪個capability或明確的「action-only contract」。檢查`calendar.resolve`等dependency reference是否有既有獨立契約；不能因不在六份registry就自行新增能力或刪除依賴。

### 3.4 Promotion優先順序與共同門檻

1. **最值得先評估**：`ziwei.flow_day_stem`、`ziwei.flow_hour_stem`，已有明確profile和reference packet；以及Bazi大運輸出所需的起運／區間子scope，服務MVP但仍可保留Experimental。
2. 第二順位：flow_day_palaces，再到flow_hour_palaces；月界是shared prerequisite／既有Stable能力的邊界補強，不是新的「升Stable成果」。
3. 日／時四化待stem gates完成才評估；日／時飛化、日／時流曜、整體natal、selector v2、interpretation v2與預測優勢目前不應承諾升Stable。yearly Y1僅可延續qualification／prospective，不以retrospective提升當產品效度。

每次promotion必須：deterministic algorithm contract、邊界清單、固定fixtures、regression、pinned且辨明獨立性的cross-source/reference、適用時真實prospective、failure modes與未涵蓋範圍、明確人類決策。零unexpected mismatch；所有預期profile差異逐項列明；抽樣數、效度指標與停止規則必須在看結果前核准，不能事後挑門檻。

Promotion gate評估「某rule/profile/scope的軟體可信度」，不授予命理因果真實性。依賴能力仍E時，只能提出受限scope決策；不得以Stable子函式漂白整個組合。registry無法精確表達受限promotion時，先提契約變更審查，保持原E，不直接整包升級。Routing與default變更不在本輪授權內。

## 4. 12-week roadmap

假設一位主要實作者(Luna)、一位領域／證據審查者，最多兩個同時在做的工作項目。週次以2026-09-28起算，可整體順延；不是deadline-driven promotion。預留約20%容量給現有回歸與資料缺口。prospective觀察時間不可壓縮。

| 週次 | Workstreams與主要輸出 | 決策／驗收點 |
| --- | --- | --- |
| W1 09/28–10/04 | WS1現況矩陣、WS6 branch residual inventory；固定baseline、source與缺口 | G0：identity一致、無產品改動；矩陣涵蓋30項及scope/action coverage |
| W2 10/05–10/11 | WS1證據index／validator；WS3選定prospective protocol | G1：SSOT、hash／scope mismatch會FAIL；不更動maturity |
| W3 10/12–10/18 | WS2 day/hour stems及Bazi大運區間qualification；WS4 Data Contract草案 | G2：時間基準、authority、unsupported策略人工確認 |
| W4 10/19–10/25 | WS2邊界／reference gaps；WS3 pre-registration／arm lock；WS6歸檔設計 | 預註冊先於outcome；缺真實來源則PENDING，不造資料 |
| W5 10/26–11/01 | WS4 JSON schema、validator、projection；WS6唯讀artifact inventory | Contract測試、privacy、盲測隔離；cleanup不執行 |
| W6 11/02–11/08 | WS4 deterministic projection完成；WS2首批promotion packet | G3：可拒絕promotion但仍交付合格E資料；renderer不得偷算 |
| W7 11/09–11/15 | WS5大運SVG＋文字替代、authority圖例；WS3持續觀察 | 同輸入同bytes；E badge與unsupported清楚可見 |
| W8 11/16–11/22 | WS5可用性／可及性／boundary QA；WS6 lifecycle policy tests | G4：大運MVP必交；零authority混淆的測試情境 |
| W9 11/23–11/29 | WS5有條件大運×流年矩陣；WS2 day/hour palace研究 | 只在G4通過且有合格interaction資料時啟動第二圖 |
| W10 11/30–12/06 | WS3 outcome接收／缺失分類；WS6 retention提案與release evidence保護 | outcome未到可結案治理功能，但不能宣稱預測qualified |
| W11 12/07–12/13 | 跨WS integration、exact candidate回歸、package與正式qualification | G5：不降低既有hosted／sandbox gate，不代填PASS |
| W12 12/14–12/20 | promotion decisions、文件、候選交接；必要時延後發布 | G6：READY FOR HUMAN RELEASE REVIEW，非自動發布 |

六條workstream的owner與成果：WS1=能力矩陣(E1)；WS2=qualification(E2)；WS3=prospective(E3)；WS4=資料契約(E4)；WS5=圖表(E5)；WS6=治理(E6/E7)。Luna負責程式、fixtures與可重現檢查；人類負責reference適用性、隱私授權、預註冊、promotion與release決策。

縮減順序：先砍第二圖、互動Web與新研究scope，再延後promotion；不砍authority、privacy、candidate identity或必需release gates。若W6仍無足夠大運區間來源契約，只交付schema／validator／synthetic renderer demo，不把demo標為可用的正式命盤圖。

## 5. Epics / milestones

### E1／WS1：Capability Qualification Matrix

- **Goal**：可由現行manifest追溯每個capability／scope的證據、限制與promotion決策。
- **Why now**：目前有多階段summary、研究branch與現行registry並存，易把局部PASS放大。
- **Scope**：30項完整coverage、scope/profile子列、action/dependency附表、evidence index、唯讀validator與生成矩陣。
- **Out of scope**：新增第二份capability truth、自動promotion、改defaults。
- **Dependencies**：G0 baseline、六份registries、existing qualification資料。
- **Affected modules**：讀`engine/distribution/manifest.py`與registries；新增`qualification/capabilities/`、矩陣builder、tests、`docs/qualification/`。
- **Research required**：historical evidence的scope／source lineage、缺reference與未登記action辨識。
- **Tests**：registry覆蓋、重複key、未知ID、hash篡改、rule mismatch、歷史summary不能取代新scope、輸出determinism、check模式不寫檔。
- **Qualification gate**：每列都有證據或明確缺口；沒有由索引反向修改runtime的路徑。
- **Acceptance criteria**：30項無遺漏；所有待查欄明示；同baseline產出一致；讀者可分辨測試通過與promoted。
- **Risk**：metadata drift及未經授權公開private source。
- **Promotion / release condition**：治理工具可獨立交付，不綁任何能力升級；registry變更另提審查。

### E2／WS2：有限scope Experimental qualification

- **Goal**：先完成day/hour stems與Bazi大運區間的可稽核qualification packet。
- **Why now**：已有public reference基礎，可先補缺口，而不是增加新算法。
- **Scope**：pinned profile、子時／DST／跨日年／節氣／閏月相依、出生精度不足、起運順逆與區間端點；次順位day/hour palaces；每scope獨立decision。
- **Out of scope**：承諾全細時間層Stable、改Y1／selector／interpretation算法與default、增加reference相容性捷徑。
- **Dependencies**：E1、既有qualification builder與可合法取得的reference。
- **Affected modules**：既有三個flow-time／month-boundary builders與tests；新增Bazi大運scope packet；除已證實且另外核准的bug外不改算法。
- **Research required**：共同library造成的非獨立reference、端點語意、學派差異、未支持日期範圍；private fine-cycle缺來源維持PENDING。
- **Tests**：boundary固定vectors、順逆大運、跨年閏日、23:00/00:00、DST gap/fold、invalid/ambiguous input、模組與dist parity、reference差異白名單。
- **Qualification gate**：共同promotion八項條件全部滿足；未通過的scope保持E，不能用大樣本掩蓋missing boundary。
- **Acceptance criteria**：每個首批scope產出PASS／BLOCKED／NEEDS_EVIDENCE決策及原因；無需為進度製造Stable。
- **Risk**：reference並非ground truth；單一profile被泛化；研究修正引發semantic drift。
- **Promotion / release condition**：人類確認scope後才另開maturity變更；計算qualification不宣稱事件預測效度。

### E3／WS3：Prospective validation / evidence governance

- **Goal**：把#221與arm-freeze研究收斂成可前置鎖定、可追溯、不能事後改答案的研究流程。
- **Why now**：功能可運作之後，最大的證據缺口不是更多retrospective故事，而是合格future observations。
- **Scope**：authority、claim universe、window、arm、source/version hashes、lock timestamp、outcome cutoff、indeterminate與withdrawal、protocol deviation；只選一個有實際資料owner的pilot。
- **Out of scope**：未來outcome造假、回填時間、以少數例子證明命理有效、把ranking分數當機率、自動合併研究branch。
- **Dependencies**：E1；#221／arm-freeze exact delta審查；人類資料授權與reference/scoring protocol。
- **Affected modules**：既有`engine/distribution/prospective.py`、`prospective_validation.py`；研究模組先隔離於`research/`或tools，通過契約review再決定是否進engine，不預先強迫合併。
- **Research required**：來源獨立性、outcome操作定義、blindness、sample size／停止規則／缺失率／基準組與多重比較。
- **Tests**：lock後mutation拒絕、wrong candidate拒絕、重複outcome、不足精度、retrospective誤標、oracle先曝光、held-out污染、partial window。
- **Qualification gate**：protocol與arm先鎖定，真實觀察晚於鎖定；任何偏離保留紀錄，不rescue改寫失敗。
- **Acceptance criteria**：治理測試通過＋一份合法預註冊或明確「無資料owner，未啟動」；outcome未到不能宣稱pilot驗證通過。
- **Risk**：12週不足觀察；selection bias；private資料洩漏。
- **Promotion / release condition**：governance可交付而empirical status仍PENDING；事件推論promotion必須另經預先核准的效度分析。

### E4／WS4：Visualization Data Contract

- **Goal**：建立與renderer無關、可重現、逐元素標示authority的JSON contract。
- **Why now**：先防止視覺化放大資料權威，再談UI。
- **Scope**：schema、validator、pure projection、schema/rule/provenance binding、能力與precision gates、blindness、日期與age語意、unsupported回應。
- **Out of scope**：Case Schema升版、重算命盤、raw Case傳給renderer、DOM藏資料、預測分數模型。
- **Dependencies**：E1；E2的大運欄位與端點確認；既有build_natal輸出。
- **Affected modules**：新`engine/visualization/`只含schema projection／validation；新`schemas/visualization/`、fixtures與tests；必要的runtime入口須獨立review後才加入。
- **Research required**：engine時間interval是否可無損投影、缺大運十神／五行時的降級、authority與confidence語意。
- **Tests**：JSON Schema、field source缺漏、E標示不可移除、unknown schema fail-closed、no wall-clock、no IO、blind denylist／allowlist、NaN/Infinity拒絕、source hash mismatch。
- **Qualification gate**：G2人工確認契約後才寫projection；schema golden與projection一致。
- **Acceptance criteria**：同輸入／as_of／versions得到相同canonical JSON；不能由inference變成fact；無隱藏歷史資料。
- **Risk**：新增registry truth或無意把單一候選當唯一真相。
- **Promotion / release condition**：Visualization schema版本獨立；MVP可E/on-demand；不擴大源能力maturity。

### E5／WS5：大運timeline MVP與conditional矩陣

- **Goal**：使用者能看懂目前大運、起訖時間、流年位置及來源限制。
- **Why now**：現有engine已產生必要核心資料，效益高於全新dashboard。
- **Scope**：stdlib SVG靜態renderer、文字替代、色彩之外的authority標記；合格來源才加十神／五行／流年；第二圖僅在G4後評估。
- **Out of scope**：完整Web App、登入／儲存、喜忌分數、工作財運客觀分數、問事事件預告、未qualified紫微細時間層圖。
- **Dependencies**：E4 G3；E2 source-bound limits；人類可用性review。
- **Affected modules**：新`renderers/svg/`、`tools/render_visualization.py`、golden fixtures；renderer不可import計算模組。
- **Research required**：年齡與西元雙軸可理解性、重疊密度、色盲／黑白可讀性、繁中標籤；先以synthetic fixtures評估。
- **Tests**：SVG XML escaping、無script／外部fetch、stable IDs、byte determinism、E badge、空／多段／窄畫面、跨年interval、文字替代與圖一致；人工檢視代表性render。
- **Qualification gate**：必須通過語意assertion與人工視覺QA；漂亮截圖不等於source正確。
- **Acceptance criteria**：使用者可辨識「算法推導、外部盤面、已驗證事件、推論」差異；MVP不需要任何事件overlay即可使用；缺欄位顯示未提供。
- **Risk**：顏色傳達吉凶暗示；SVG/HTML注入；中文字型環境差異。
- **Promotion / release condition**：JSON與SVG byte可重現；PNG僅選配並固定字型／renderer環境，不承諾跨環境pixel一致；runtime合併前保留原package與release gates。

### E6／WS6：Version-neutral artifact lifecycle governance

- **Goal**：把有價值的唯讀inventory與fail-closed selection變成repo maintenance工具。
- **Why now**：舊工具已實作保護精神，但綁定v1.7舊candidate，直接沿用有誤刪風險。
- **Scope**：`artifact_inventory.py`、`artifact_lifecycle_policy.py`、explicit protection config、read-only workflow提案、usage reporting、retention分類。
- **Out of scope**：刪artifact／branch、寫billing設定、自動cleanup、減少正式hosted artifact gate、發布或替換歷史release assets。
- **Dependencies**：branch exact code review、E1 provenance原則、當前candidate與全部frozen release inventory。
- **Affected modules**：從artifact branch擇取兩tools與三tests重構；只新增maintenance workflow；正式validation retention修改須另列精確allowlist審查。
- **Research required**：artifact filename與run SHA／attempt關係、缺失API資料、owner-level storage與repo inventory差異、既有workflow retention需求。
- **Tests**：unknown provenance、name/run SHA conflict、incomplete pagination、protected current／historical／evidence、approval snapshot過期、非法repo、零網路DELETE、有限retention。
- **Qualification gate**：不完整inventory不能產生可執行cleanup清單；每筆候選需exact provenance與獨立approval；policy本身沒有刪除路徑。
- **Acceptance criteria**：能報repo artifact bytes與分類，但不聲稱這是account quota；未知資料只報告／保護；不變動Release assets。
- **Risk**：`retention=None`被誤解為GitHub永久保存；執行時候選改變；只保護v1.6漏掉v1.7.1。
- **Promotion / release condition**：工具可進main且version-neutral，不隨產品版本升maturity；自動刪除executor不屬於本12週交付。

### E7／WS6：Architecture archive與branch residual ledger

- **Goal**：保留設計決策，但不讓歷史計畫變成現行truth。
- **Why now**：分支已housekeeping，需分清「證據／架構資產」與「已落地舊計畫」。
- **Scope**：v1.7設計歸檔、current crosswalk、研究branch逐檔residual對照、bounded portable review。
- **Out of scope**：刪branch、bulk merge／cherry-pick、重做已完成Guided Inquiry、重建offline pipeline。
- **Dependencies**：fixed branch SHAs、main blob比較；E1 action/registry mapping。
- **Affected modules**：`docs/archive/v1.7/`、`docs/research/branch-disposition.md`；不動runtime。
- **Research required**：設計原則是否仍適用、已完成API改名、portable殘餘差異是否仍有獨立價值。
- **Tests**：archive來源SHA／hash、歷史標題／警語、links、current mapping；確保沒有把舊NOT STARTED搬成當前待辦。
- **Qualification gate**：每份文件明示historical、不具current authority；每分支結論有逐檔依據，不用commit數推導。
- **Acceptance criteria**：所有指定分支都有保留／重用／延後建議與原因；branch保持原狀。
- **Risk**：舊規格覆蓋新runtime；把等價實作當遺失功能。
- **Promotion / release condition**：純文件治理，可獨立審查；不改版本identity。

## 6. Visualization architecture proposal

### 6.1 選Hybrid，但先做最小static client

| 選項 | 優點 | 成本／限制 | 本輪決策 |
| --- | --- | --- | --- |
| Static：Python／SVG／PNG | 適合ChatGPT檔案、報告、export；容易留證據 | 無hover／zoom；PNG字型與backend需固定 | SVG＋文字先做；PNG/matplotlib選配 |
| Web：JSON＋HTML/JS/SVG | hover／filter／zoom可用性佳 | 新依賴、XSS、資料外洩、瀏覽器QA、dashboard scope | 不作必要交付；後續共用contract |
| Hybrid：engine projection＋多renderer | 計算與呈現分離、可重用、不鎖client | 需先定schema與跨renderer語意測試 | 採用；不表示本輪同時做兩個client |

SVG適合可縮放的結構圖；matplotlib可export多種格式，但不是MVP必需依賴。依repo既有Python floor選相容版本，不以最新matplotlib強迫runtime升級。[SVG規格](https://www.w3.org/TR/SVG2/)、[savefig文件](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html)

```text
既有deterministic engine → allowlisted EngineView envelope
                                ↓
                     engine/visualization/ projection + validator
                                ↓
                     Visualization Data Contract(JSON)
                                ↓
                     renderers/svg/ + 文字替代
                                └→ 未來Web/PNG client

Case／事件／現實背景 → 另行授權的annotation adapter(非MVP)
                     → visibility／lock gate → annotations
```

`engine/visualization/`只放pure projection、authority checks與contract validation，不含matplotlib、DOM、CSS、Case storage、網路或命理算法。`renderers/svg/`只讀validated chart，不import`engine/bazi`、`engine/ziwei`、calendar或Case parser。schema放`schemas/visualization/chart.v1.schema.json`，獨立於Case Schema。

**Visualization不直接讀Case。** orchestration可以從既有Case流程取得已計算的engine output，但輸入projection之前只保留欄位allowlist、版本、來源、precision與visibility metadata。私有事件與known reality不能藏在JSON、HTML data attributes、SVG metadata或tooltip裡，再靠前端隱藏。

既有runtime若要提供新action，應在核心contract與MVP通過後另做小型integration task：新action名稱、SUPPORTED_ACTIONS、manifest映射、dist builder、core使用說明必須一起review。不能為了新增renderer先重組正式三資產交付架構。

### 6.2 Visualization Authority

每個有語意的element／field以`authority_refs`引用下列分類；不能只在整張圖寫一個「資料來源」。

| Authority | 適用例 | 顯示／限制 |
| --- | --- | --- |
| original_chart_fact | 外部盤面原文中的宮位／干支 | 標「原始盤面記載」及來源；不是自然界真實性保證 |
| verified_data | 已按指定程序核對的輸入資料 | 顯示核對範圍；不外推成命理效度 |
| project_derived | engine算出的大運干支／時間區間 | 標「Project推導」、rule/profile與E狀態 |
| verified_event | 有來源支持的已發生事件 | 另軌呈現、需授權；blind mode禁用 |
| metaphysical_inference | 某年可能工作壓力高 | 明示推論、虛線／文字標籤；不得當客觀分數 |
| research_hypothesis | 尚待驗證的時間窗假說 | 研究標記；不得導向Stable結論 |
| current_real_world_context | 使用者已揭露的工作／家庭背景 | 標提供時間與來源；blind mode禁用 |

顏色僅為輔助，不將紅／綠預設為吉凶；每元素有文字／圖例標識。混合來源的推導保留lineage，輸出仍標project_derived或inference，不能繼承verified_data標籤而「洗白」。confidence預設null；若有值需method、scale、scope及evidence，不能把interaction count、rule coverage或演算法可重現性換算成事件機率。

### 6.3 五種候選MVP取捨

| 模組 | 決策 | 安全邊界／啟動條件 |
| --- | --- | --- |
| 八字大運時間軸 | 第一優先，必要交付 | 西元、年齡、干支、engine區間、固定as_of；十神／五行缺來源則null，不補算 |
| 大運×流年矩陣 | W9 conditional stretch | 只呈現已有rule-qualified干支／十神互動與刑沖合害；「五行壓力」若屬推論須另軌，不創造量化分數 |
| 流年節奏圖 | contract先保留，不列必交 | 月份區間由engine供給；structural activation須可追溯，count先去重與定義分母；domain tags是推導，confidence無模型則null |
| 紫微運限 | 本輪研究spike／schema mapping，可延後 | 本命十二宮、大限、流年命宮／四化只用已核對scope；natal本身E照樣標示；不引入流月／日／時visual authority |
| 問事時間窗 | 後續研究，不做正式MVP | 進攻／觀察／防守／停損是建議或推論，不是盤面事實；要evidence/context/lock/expiry且不得事後改blind claim |

## 7. 大運圖表MVP schema

狀態：**proposed Visualization Schema 1.0**，須G2確認，不是現有runtime API。採JSON Schema 2020-12描述；外加Python語意validator檢查cross-field／source binding。不要把JSON Schema形式通過當成數值正確。[JSON Schema](https://json-schema.org/draft/2020-12)

### 7.1 欄位契約

| 區塊／欄位 | 型態與要求 | 原則 |
| --- | --- | --- |
| chart_type／schema_version | 固定`bazi_decadal_timeline`／`1.0` | 未知版本拒絕，不猜相容 |
| status／reason_codes | `ready`或`unsupported`；code陣列 | 來源缺必需欄、端點語意未知、候選不唯一時unsupported |
| view_context | as_of(帶offset ISO8601)、timezone、visibility_mode、locale | as_of由caller提供，不讀今天；locale先限定zh-TW |
| source_capabilities | capability_id、scope、profile_id、rule_version、maturity、routing | 與manifest snapshot核對；大運是bazi.natal_chart子scope，不捏造目前registry ID |
| data.age_basis | id、description、rounding_policy | 保留engine age；未確認實歲／虛歲／起運換算則不顯示誤導年齡軸 |
| data.time_basis | calendar、boundary_policy、interval_convention、source_timezone | 西元年label不等於立春流年；只接受確認後的區間契約 |
| data.direction | forward／reverse／null | 只投影engine值 |
| data.periods[] | id、index、pillar、age_start_years、age_end_years、start_at、end_at | 保留原始精度，不把小數起運年齡四捨五入後拿來排序 |
| periods[].ten_god／elements | nullable objects＋reason | 使用既有engine合格輸出；目前serializer未含大運專屬值，MVP可null |
| periods[].authority_refs | JSON-pointer→authority ID陣列的map | 每個semantic欄位皆覆蓋，索引／ID等純布局欄位可免 |
| data.current_period_id | string或null | 依明確as_of與已確認區間判斷；範圍外為null，不選最近一段 |
| data.year_overlays[] | id、year_label、pillar、start_at、end_at、period_ids、authority_refs | engine提供流年interval；跨大運可連兩段；未提供時空陣列 |
| annotations[] | target_id、text、authority_refs、visibility、evidence_refs | MVP預設空；不接受任意Case內容；未支持的annotation fail-closed |
| authorities | authority ID→classification、source_refs、transformation、confidence | 不只靠顏色；confidence預設null |
| provenance | repo、source_commit、release_version、distribution_runtime_version、manifest_sha256、source_payload_sha256、projection_version | SHA256須canonical bytes；不以Windows CRLF working-tree identity冒充release |
| limitations[] | code、message、scope | experimental、unsupported optional fields、validated range等不可被renderer移除 |

source SHA及digest屬資料來源身份；新程式的candidate SHA與source release SHA可能不同，兩者不能互相冒充。source payload是經allowlist及去識別化的deterministic envelope；hash也可能具有可連結性，不放可反查出生資料的公開索引。

### 7.2 正規化與時間語意

- JSON canonicalization v1固定UTF-8、key sorting、compact separators、禁止NaN／Infinity、固定數字序列化策略；跨JS client只消費JSON，不自行重算不同版本digest。
- 建議圖表使用半開區間`[start_at, end_at)`，但**必須先證明engine的end語意可無損對映**。不能自行end+1天或+1年；若有inclusive source，先出明確adapter契約與邊界tests，否則unsupported。
- `as_of == end_at`不得仍落前一段；相鄰區間交界應只有一個current period。合法空隙／重疊須有source解釋，不能補齊或裁切以讓圖好看。
- Gregorian year只作軸label；流年起點使用engine提供的節氣／profile區間。年齡與西元位置皆依source interval，不用`birth_year + age`替代。
- 無性別／出生時間不精確／多候選時，先回unsupported；多候選facet視圖不在MVP。不得默選第一個候選或輸出平均盤。
- birth raw input、姓名、歷史ledger、known reality、freeform Case文字不進MVP envelope。標籤也採allowlist與長度限制。

### 7.3 可解析的unsupported示例

以下只示範降級形狀，不是qualification evidence，也不是含完整provenance的ready chart。schema應使用ready／unsupported分支：unsupported禁止資料元素，並允許無法取得的digest為null；ready所有必要digest須完整且可驗證。

```json
{
  "chart_type": "bazi_decadal_timeline",
  "schema_version": "1.0",
  "status": "unsupported",
  "reason_codes": ["AMBIGUOUS_NATAL_CANDIDATE"],
  "view_context": {
    "as_of": "2026-09-26T12:00:00+08:00",
    "timezone": "Asia/Taipei",
    "visibility_mode": "blind",
    "locale": "zh-TW"
  },
  "source_capabilities": [],
  "data": null,
  "annotations": [],
  "authorities": {},
  "provenance": {
    "repo": "mvkaiii/metaphysics-lab",
    "source_commit": null,
    "release_version": null,
    "distribution_runtime_version": null,
    "manifest_sha256": null,
    "source_payload_sha256": null,
    "projection_version": "1.0-exp"
  },
  "limitations": [
    {
      "code": "INPUT_NOT_RESOLVED",
      "message": "尚未確定唯一命盤，未產生大運圖。",
      "scope": "chart"
    }
  ]
}
```

G2後建立真正ready的synthetic golden fixture：來源為固定engine輸出，包含至少兩段相鄰大運、剛好交界as_of、跨界流年overlay、null十神／五行及E badge。不要在規劃階段發明大運事件或捏造ready值來假裝已完成驗證。

## 8. Research branches disposition

### 8.1 分支快照與建議

下列均為本次讀取時的head，執行前fresh verify。ahead／behind不作去留依據；沒有任何刪branch授權。

**2026-09-26補充查核：PR仍open不表示原base branch存在。** GitHub PR API仍保存base ref／SHA作歷史metadata；branch清單共12項，不包含下列兩個base，對各base的Git ref直接查詢也均回傳404。兩個head branches仍在清單中；因此本輪按missing-base的research/archive evidence保留，不直接修PR拓樸。

| PR | 原base ref(API metadata) | 歷史base SHA | 處理限制 |
| --- | --- | --- | --- |
| #219 | `impl/v1.6-legacy-adapter-paired-evaluation` | `eaf03116bf5e02b08b4b51caed2cb2c31f796686` | 不retarget、不merge、不刪`research/v1.6-yearly-ziwei-transformations-y1` |
| #221 | `research/v1.6-prospective-window-scope-v1` | `c2d111b3e1b410a7208b8d4ba0585e8000d30a87` | 不retarget、不merge、不刪`research/v1.6-prospective-claim-authority-set` |

查核來源：[PR #219 metadata](https://api.github.com/repos/mvkaiii/metaphysics-lab/pulls/219)、[PR #221 metadata](https://api.github.com/repos/mvkaiii/metaphysics-lab/pulls/221)、[branch inventory](https://api.github.com/repos/mvkaiii/metaphysics-lab/branches?per_page=100)。這是時間點快照，不保證未來狀態相同；Task 0–2須重新查核並保存結果。若歷史base commit無法讀取，標示證據缺口，不以main替代舊base來重建原PR語意。

| 線／固定head | 查核結果 | Roadmap處置 |
| --- | --- | --- |
| #221 `e28a51e9cb60961838300b8a0aea8e25696e9fb4` | claim authority／universe／window等模組不在main；PR描述qualified，但PRIVATE_S1_NOT_YET_LOCKED、ORACLE_NOT_CREATED、PRIVATE_SCORING_NOT_EXECUTED、promotion_allowed=false | WS3高優先：擇取governance契約、先補TDD與main相容性；不整包merge，不把PR文字當fresh evidence |
| #219 `3d6bba9efa37b105aee198215f90f00e3ed99229` | forecast.py、yearly_cycle.py與相關Y1測試有main相同blob；獨有benchmarks/docs/workflows仍有研究價值 | WS2/3：保留benchmark與限制；年度prospective候選，**不重做已落地Y1** |
| #200 `842bb3b75eb9b8f03ae90180f1b98cfa3bd19a13` | PR描述舊compat WIP；main registry已含2.1-exp支持，且有compat tests | WS1/6先做semantic residual audit；只有獨有且仍適用的calibration/control測試才提移植；不promote default |
| prospective-arm-freeze `dc95050640addf31e57ec637fdcf8e1483c42fb5` | 部分Y1 code已main等價；arm-freeze與authority模組仍獨立 | 與#221共同WS3，避免兩套claim authority；保留sealed provenance |
| Bazi flow-time `4319964291f2acd6f535042c70a2b2e3e9da076e` | qualification README/JSON、builder、test與main同blob | WS2直接基於main補缺口；分支作歷史來源，不bulk merge |
| Ziwei flow-time `df26e7eaf8718deef380b3e04194c2f625cba62b` | 核心qualification packet／builder／test與main同blob | 同上；scope主要是day/hour stems，不擴張為全部細時間層 |
| Ziwei month-boundary `38d8509f46a2c1121e147c563d571a7ce85d1967` | 核心qualification與tests已main等價 | WS2共享邊界前提，檢查reference盲點，不重新引入舊core檔 |
| portable offline natal `c6771cde49b0a8936841d98a6ae7b7c4a3f4eca9` | branch有大量獨有commits，但離線registry/data、calendar、distribution natal/dependencies、vendor及多項portable tests已有main相同blob | W1最多兩個工作日做殘餘semantic inventory；必要bug另案，其餘研究保留；不重建整條pipeline、不刪branch |

PR來源：[#221](https://github.com/mvkaiii/metaphysics-lab/pull/221)、[#219](https://github.com/mvkaiii/metaphysics-lab/pull/219)、[#200](https://github.com/mvkaiii/metaphysics-lab/pull/200)。Y1 PR中retrospective coverage提升及大量indeterminate不構成預測優勢；本輪不沿用舊run數作新candidate qualification。

完整residual audit應記錄固定main/head/base、所有branch-specific路徑的blob比對、不同內容的語意承接、獨有tests/docs/evidence與未解缺口。patch／commit數及抽樣相同blob不能替代完整比對。Task 0–2可交付部分盤點，但必須標`PARTIAL／NOT SAFE TO DELETE`，不得藉checkpoint產生刪除建議或執行housekeeping。

### 8.2 v1.7 planning branch歸檔

來源：`plan/v1.7-reliability-guided-inquiry@0d7370eb54fb77c9f4f788ad838a78d06217d24b`。以下八份文件當時未完整存在main；**不是八項未完成產品工作**。

| 原文件(皆在docs/superpowers下) | 建議 |
| --- | --- |
| `specs/2026-09-08-v1.7-reliability-guided-inquiry-design.md` | 正式archive進`docs/archive/v1.7/`；保留原文與來源SHA，另加導讀／現況crosswalk |
| `plans/2026-09-08-v1.7-planning-index.md` | archive作歷史導航；明示其PLANNED/NOT IMPLEMENTED為當時狀態，不能覆蓋現況 |
| `plans/2026-09-08-v1.7-capability-manifest-v1.md` | 萃取SSOT決策引用到archive index；完整執行步驟可留原branch，不必納入active docs |
| `plans/2026-09-08-v1.7-case-doctor-reconciliation.md` | 保留append-only／不暗改Case原則；步驟已完成部分不轉成新待辦 |
| `plans/2026-09-08-v1.7-prospective-validation-2.md` | 保留blind／retrospective分類、證據邊界；現行API名稱以main為準 |
| `plans/2026-09-08-v1.7-guided-inquiry.md` | 保留不污染blind／非限制性導航／不誇大能力；不重做Guided Inquiry |
| `plans/2026-09-08-v1.7-integration-release.md` | 歷史release checklist可索引，不作v1.8現行發布命令 |
| `plans/2026-09-08-v1.7-direct-implementation-ledger.md` | 保留歷史source/hash；不作當前status ledger，避免把STARTING／NOT STARTED誤讀為未落地 |

歸檔minimum：design原文、planning index原文、來源manifest與current crosswalk。其餘六份以固定SHA連結＋內容hash保留；若未來branch housekeeping會使來源不可保證可達，先另案授權完整archive bundle再處置branch。本輪不刪文件／branch。

延續的是治理原則，而非舊待辦：capability truth單一來源、Case不暗改、prediction boundary、authority分離、自由問事不受導航綁架。Visualization與新evidence matrix需要繼承這些原則。

### 8.3 Artifact lifecycle branch

來源：`ci/v17-artifact-lifecycle-20260915@9872223aac6d2bc2d607d716c4490c5cd47651d0`。

應保留的五檔：`tools/v17_artifact_inventory.py`、`tools/v17_artifact_lifecycle_policy.py`、`tests/test_v17_artifact_inventory.py`、`tests/test_v17_artifact_inventory_workflow.py`、`tests/test_v17_artifact_lifecycle_policy.py`。歷史transport payload不帶入main。

結論：**值得成為maintenance capability，而非只屬v1.7 staging**，但需E6重構。原工具固定舊candidate `7c9c4a3...`及v1.6 protection，asset names也綁v1.6/v1.7；不能只rename。新版以repo-scoped explicit config列出所有current candidates、frozen release SHAs、protected evidence IDs／digests與正式Release asset名稱；來源不完整或身份衝突一律保護。

原policy的provenance完整性檢查不等於filename SHA與run SHA一致性驗證；新版必補衝突tests。retention策略建議：intermediate 1日、failure debug 3日、已核准superseded candidate 7日；current candidate／正式evidence不得由cleanup選中。**policy中的None只表示不選刪，不代表Actions永不過期**。正式evidence需在平台到期前依既有合格保存機制保留；不藉此重發或覆蓋歷史Release assets。[Artifact保存與下載說明](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts)

正式validation workflow不可為省空間移除contract要求的hosted artifact。先盤點每個upload步驟的用途、bytes／run與retention，再逐workflow審查：非必要intermediate可不upload；failure bundle只失敗時upload；正式candidate package／evidence仍按gate保留。Repo inventory只能報repo bytes，不能斷言owner billing quota已恢復。

## 9. Release strategy

### 9.1 分離交付與成熟度

- 維持v1.7.1／v1.7.0／v1.6.0 identity，不重建覆蓋任何歷史產物。
- v1.8 feature branch從經fresh verify的main開始；新candidate依semantic／契約變更另建，不把v1.7.1 SHA拿來代表新軟體。
- Visualization schema自有version；Case Schema 1.1不因新增圖表而bump。若runtime公開欄位需version調整，先提出相容性決策，不偷改。
- SSOT矩陣與maintenance工具可以獨立PR；capability promotion、runtime integration、正式release各有獨立review gate。registry保持E不阻礙如實標示的E視覺化交付。
- 未完成promotion不等於發布失敗；宣稱的功能、限制、測試與實際artifact一致才是release要件。

### 9.2 正式驗證與停止條件

每個implementation task遵循systematic debugging → TDD(確認RED原因) → minimal implementation → verification-before-completion。以既有workflow實際命令為準，保持受支持Python與platform矩陣，不使用本機依賴缺失作修改production的理由。

新candidate至少fresh verify：focused tests、完整repository regression、release-surface、deterministic dist／package、compile、contamination/privacy、dry-run maintenance無write、clean tree、exact SHA與hosted artifacts存在。正式sandbox若依現行contract要求，必須在hosted qualification合格後使用新exact assets，不能套用v1.7.0舊transcript或預填PASS。

以下停止受影響實作並回報：baseline不一致；dirty tree與本次改動重疊；缺reference／合法private資料；algorithm結果需改但未另核准；需要Case migration／default promotion；authority無法正確標示；source區間語意不明；regression失敗；GitHub gate／artifact不可驗證；候選freeze後出現非允許變動。

Github無write時仍可LOCAL VERIFIED，但清楚標REMOTE NOT APPLIED，不能稱正式qualification完成。本計畫未授權commit／push／merge／tag／release或cleanup；由使用者在執行階段明確指定可做的外部操作。

### 9.3 Rollback

各epic隔離小批次，避免混入算法與研究資料。尚未合併可保留分支停用；已合併的新功能以經授權的revert或關閉on-demand入口回復，不force push、不reset歷史、不移tag。Evidence append-only，撤銷決策另加紀錄，不修改既有觀察或lock。任何新asset發布前都不影響v1.7.1可用性。

## 10. Top 5 next actions

1. **先做E1**：fresh核對main／tag／Release，建立30項capability與scope／profile evidence index；不改任何maturity。
2. **選首批qualification**：day/hour stems＋Bazi大運區間，先確認profile／boundary／reference independence；其餘保持E。
3. **凍結Visualization Contract草案**：決定端點與age語意、逐欄authority、blind allowlist、unsupported策略；沒有十神／五行source時接受null。
4. **開始大運SVG MVP**：使用固定engine輸出與synthetic fixtures做projection／renderer TDD，先不加事件與Web UI。
5. **把治理線小量落地**：#221／arm-freeze做一個預註冊pilot；artifact做唯讀version-neutral工具；archive設計原則，不bulk merge或刪branch。

交付判準不是功能數，而是：能力狀態不說謊、證據可定位、圖表不增加不當權威、研究和正式產品有清楚邊界，且下次release仍可重現。
