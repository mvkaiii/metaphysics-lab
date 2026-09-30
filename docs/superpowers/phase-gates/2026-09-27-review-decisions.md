# 人工review決策與分離gate

日期：2026-09-27。來源：使用者於本次Codex對話明確核准以下三項；不是測試結果或成果驗收。

- main baseline：`872c60b2e959ea48d25524b74686e488f576ec6f`，本輪透過遠端ref查核一致。
- 變更前feature HEAD：`26176b15e23897b37e30a1bc615a33d9d93ccb63`。
- 計畫來源：`docs/next-stage-roadmap-20260926@0bdd2f41fe78ba192b4ae0e31fcbba6fba0c9741`。

## Task3 reference methodology

`APPROVED WITH CONSTRAINTS`。接受獨立天文資料加獨立契約計算/oracle，作為`bazi-natal-project-v1`契約／實作qualification的一部分，不是事件預測有效性證明。

外部天文資料僅支持其覆蓋的節氣／時間輸入，不是獨立大運算法reference。Oracle須依事前核准的Project profile獨立實作，不呼叫、複製production，也不從production輸出回推expected values。來源版本、原始bytes/digest、案例集合、比較欄位、容差與判定規則須在查看比較結果前固定。分別標示`independent`、`partially_shared`、`same_source_reproduction`。

`[start,end)`仍是Visualization表示契約，不宣稱外部reference證明engine原始endpoint語意。部分欄位通過不得宣告整包PASS。Reference packet完成並經人工review前，Task3保持`NEEDS_EVIDENCE`，不做maturity promotion。

執行限制：目前執行者已讀取production實作與既有輸出，不具未暴露的clean-room條件；不得將其直接產出的oracle標為獨立。後續由未接觸production/output的獨立實作者，只取得已核准規格與固定外部來源；先封存oracle及expected值，再由另一角色比較。沒有隔離實作者時停止oracle部分，不以重新開檔案或自述獨立取代來源證據。

## Task9 protocol framework

`APPROVED FOR FINALIZATION`；`PILOT NOT AUTHORIZED`。第一輪定位為prospective流程可行性，不建立預測優越性或一般化有效性。重點為有效事前鎖定、source/claim/candidate provenance、outcome-blind隔離、資料完整率、blind violation、protocol deviation與缺失處理。

所有pre-run decisions仍須逐項人工核准，詳見[最終送審表](../../research/prospective-pilot-review.md)。Protocol維持`DRAFT_PENDING_HUMAN_APPROVAL`，pilot維持`NOT_STARTED`。不得接受正式case、產生正式prediction lock、存取outcome/oracle或scoring。此處pilot oracle與Task3數學reference oracle是不同用途，不混用授權。

## Windows portability

`APPROVED AS SEPARATE ENGINEERING FIX`。先建立跨平台RED fixture；canonical排序為relative POSIX path string，大小寫不折疊。Windows/Linux相同raw bytes須得到相同digest；lunar-python與tzdata分別驗證。

不修改vendor bytes、manifest預期digest、歷史Release assets或qualification evidence以配合測試。修改若產生新candidate bytes，重新取得該candidate的工程驗證；舊SHA的CI不適用。

## Review邊界

Task3研究證據、Task9 pilot與Experimental engineering delivery是不同gate。未來工程PR依實際delivery claims及原G3/G4另行review；研究尚未完成不表示永遠不可merge，工程CI也不能取代研究qualification。

整體維持人工review checkpoint及`NOT READY FOR MERGE/RELEASE`。本決策不授權merge、tag、release、publish、Stable promotion或修改歷史release identity。
