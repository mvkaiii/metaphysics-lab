# 下一階段G2決策與續作邊界

決策日期：2026-09-26。
決策狀態：`G2 APPROVED WITH CONSTRAINTS`。
決策來源：使用者在本次Codex對話明確回覆「確認寫入，但你幫我寫後續的prompt，我讓luna max執行」，核准前一則列出的12項G2契約及補充限制。

本文件記錄人工契約決策，不是測試結果、獨立算法qualification或Stable promotion證據。Task4可依本契約開始；後續Task仍須通過原計畫的相依gate。

## 正式來源與checkpoint

- Repository：`mvkaiii/metaphysics-lab`。
- 正式baseline：`872c60b2e959ea48d25524b74686e488f576ec6f`。
- 決策寫入前feature HEAD：`23262f7de85875d950040af2c5b70a87443d9e1e`。
- Feature branch：`local/task0-2-capability-matrix`。
- Draft PR：https://github.com/mvkaiii/metaphysics-lab/pull/233。
- 計畫branch：`docs/next-stage-roadmap-20260926`。執行者須讀取其最新版本並記錄SHA：
  - `docs/superpowers/specs/2026-09-26-metaphysics-next-stage-roadmap.md`
  - `docs/superpowers/plans/2026-09-26-metaphysics-next-stage-execution.md`
  - 該branch相關current-state／handoff文件(若有)。

## 核准契約

1. 區間採半開表示`[start_at, end_at)`。`as_of == end_at`不屬前段；只有存在下一段且符合其區間才屬下一段。這不代表原engine語意已獲外部證實。須確認來源欄位、時區、精度及endpoint可無損映射；相鄰值一致只是必要條件。不能確認即`unsupported`，禁止自行加一天或一年修補。
2. 年齡基準固定為`continuous_years_from_jie_interval`，不得稱為實歲、虛歲或傳統周歲。保留來源數值精度；顯示格式化結果不得反推區間。
3. Synthetic packet僅支持結構與重現性，可作Experimental Visualization的Project-derived來源。Task3 qualification維持`NEEDS_EVIDENCE`。未來qualification PASS／promotion仍須不共用同一底層算法的reference，核對方向、首段起點／年齡及endpoint profile，並符合原qualification gates。
4. Visualization只接受allowlisted deterministic engine view、canonical manifest metadata、provenance及caller提供的`as_of`、`timezone`、`visibility_mode`，不得直接讀Case。
5. 必須已有唯一resolved natal candidate。多候選、必要欄位缺失或區間語意無法確認時輸出`unsupported`，不得選第一個、平均或猜補。
6. 十神、五行等optional欄位沒有合格的大運專屬來源時使用`null`並附機器可讀原因；不得在projection或renderer重算。
7. Current period只依明確`as_of`與已確認區間判定；範圍外為`null`，不得選最近一段。Renderer不得重新推導current period。
8. Blind mode禁止帶入verified event、historical ledger、known reality、current real-world context及自由文字Case內容。第一版`annotations`預設空陣列；驗證器必須防止污染。
9. 有語意的欄位須能透過`authority_refs`追溯來源。大運時間、干支等engine推導結果屬`project_derived`；輸入經驗證不會使推導結果變成`verified_data`。
10. Maturity以canonical manifest為唯一真實來源。Experimental capability必須保留E／Experimental標示及limitations，renderer不得隱藏。G2不構成Stable promotion。
11. Renderer只呈現validated chart contract，不得排盤、重算區間、補十神五行、改authority或推導current period。
12. 使用`ready`／`unsupported`兩種discriminated status。`ready`須有完整必要data、authority及provenance，允許契約定義的optional null；它只表示符合Visualization契約。`unsupported`必須`data=null`、空annotations及機器可讀`reason_codes`，不得輸出看似正常的半套圖。

## 授權沿革

原Task0–2限定已被使用者後續明確授權取代：完成必要驗收後可依Execution Plan執行Task3–10；G2阻塞期間可繼續獨立的Task7、Task8、Task9。因此PR包含這些工作有既有授權依據，不能沿用舊範圍認定越界。

授權實作不等於人工驗收全部成果。Task7／8工程交付及Task9設計草案依各自證據審查；Task9仍為`DRAFT_PENDING_HUMAN_APPROVAL`，pilot為`NOT_STARTED`。本決策不批准真實pilot、參與者／資料／研究設計選擇或promotion。

本次只保存決策與交接，由Luna Max接續實作。Task4–10沿用既有執行授權，不需一般續作確認；必要人工研究決策、外部證據與後續gate不能跳過。

## 執行及停止條件

先fresh verify remote、branch、HEAD、完整working tree、main baseline、計畫版本與適用AGENTS.md。保留`.venv-task3/`及所有既有變更；本決策文件在提交前屬待保存的已核准成果。

採systematic debugging → TDD → implementation → verification-before-completion。依各Task實際內容及依賴順序執行，不猜Task編號。Windows Python3.12與bundled tzdata／vendor限制須如實回報；正式Python3.9 hosted驗證綁定新commit，不能沿用舊SHA結果。

允許專用feature branch的一般commit／push與更新Draft PR #233；不得force push或直接寫main。GitHub不可寫時可繼續本機授權工作，明確區分LOCAL VERIFIED與REMOTE NOT APPLIED。

Baseline偏離、使用者變更衝突、必要gate失敗、證據不足或新的指定人工決策點，停止受影響部分，繼續不依賴阻塞的已授權工作。

不得修改歷史v1.7.1／v1.7.0／v1.6.0 release identity、tag或Release assets；不得merge、tag、release、publish、Stable promotion、改selector／interpretation defaults、強迫Case Schema migration、直接merge研究branch、retarget／close／delete研究PR或branch。不得填入未執行的sandbox／qualification PASS。

最終交付停在review checkpoint，回報各Task狀態、exact SHA、changed files、fresh local／hosted結果、artifact存在性、evidence限制及待人工決策事項。
