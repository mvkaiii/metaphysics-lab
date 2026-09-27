# Prospective pilot最終人工送審表

框架：`APPROVED FOR FINALIZATION`。本表：`ALL_ITEMS_APPROVED`。Protocol decisions：`HUMAN_APPROVED_PENDING_SEAL`。Pilot：`READY_FOR_START_AUTHORIZATION`。

依據：[2026-09-27人工決策](../superpowers/phase-gates/2026-09-27-review-decisions.md)。本表補充[protocol](prospective-pilot-protocol.md)，不是啟動許可；不代填人名、資料權限、樣本數或研究結果。

D01–D12 已由 human decision owner 於 `2026-09-27T17:55:00+08:00` 明確核准；公開 repo 只保存去識別化摘要。涉及個資、私人儲存位置或實際權限文件的內容仍保存在經核准的私人位置。此核准只完成 protocol decision gate，不是 pilot start authorization。

| ID／決策 | 最終送審內容／建議 | 仍須人工填定的值 | 狀態 |
| --- | --- | --- | --- |
| D01 Study owner | 明確問責並分離執行、資料保管及判讀角色 | owner、custodian、executor、adjudicator及利益衝突處理 | APPROVED |
| D02 資料權限 | 僅處理明確授權用途；未授權不得收案 | 資料來源、使用依據／同意、存取角色、儲存位置、保存期限、退出權利 | APPROVED |
| D03 Target population | 保留完整census與排除原因，不事後挑案例 | 母群、納入／排除、單位、重複處理、census截止時間 | APPROVED |
| D04 Claim universe | 先固定可操作定義，不允許事後換事件家族 | claim families、粒度、方向、期間、禁止claim、固定模板 | APPROVED |
| D05 Arms | 建議單一arm流程可行性；不推論比較優越性 | 是否採單一arm；每arm exact SHA、package／manifest digest、profile及設定 | APPROVED |
| D06 Time scope | lock先於outcome window；不回填時間 | timezone、query/cutoff、起訖及端點、精度、資料成熟等待期 | APPROVED |
| D07 Outcome | 先封存客觀資料，再用事前規則比對claim | 來源優先序、support/contradiction/indeterminate/out-of-universe規則、爭議裁決 | APPROVED |
| D08 Blinding | executor不可見outcome；資料收集者不可見預測；比對者可見必要claim但不見arm標籤 | 角色存取矩陣、揭盲時機、封存順序、違規判定及處理 | APPROVED |
| D09 Metrics | 建議主要指標為有效事前鎖定率；provenance完整率、資料完整率、blind violation與deviation為次要流程指標 | 主指標、分子／分母、缺失與退出處理、成功／失敗門檻；所有嘗試均留痕 | APPROVED |
| D10 Sample/stopping | 固定目標或固定收案截止，不依結果有利而提前停止 | 樣本數或截止日、成熟期、行政／安全停止及中止後報告規則 | APPROVED |
| D11 Withdrawal/deviation | 不靜默刪除、補答案或重寫失敗 | 退出、遲到、無法判定、缺失、偏離分類、撤回資料與計數可保留範圍 | APPROVED |
| D12 Publication/privacy | 僅核准的去識別化彙總，避免small-cell及hash洩漏 | 公開欄位、抑制規則、披露審查者、審查程序與保存期限 | APPROVED |

## Pilot-1具體建議值

已完成逐項具體化，見
[`prospective-pilot-proposed-values.md`](prospective-pilot-proposed-values.md)。

重要修正：早期討論中的「7天 window／12 attempts」不採用。Fresh review 顯示既有
`prospective_window_scope` research contract 只接受 calendar-aligned、same-year、
multi-month window，並映射為 yearly claim authority + monthly timing；因此 Pilot-1
proposal 改為單一 end-to-end case，建議 window 為
`2026-11-01T00:00:00+08:00` → `2026-12-31T23:59:59+08:00`。

上述值已由 human decision owner 正式核准。Committed decision receipt 的 D01-D12 已逐列改成 `APPROVED`，overall protocol decision status 為 `ALL_ITEMS_APPROVED`，pilot status 為 `READY_FOR_START_AUTHORIZATION`。這仍不等於 pilot start。

## Decision receipt工程契約

已新增公開、去識別化 decision receipt template：
`docs/research/prospective-pilot-decision-receipt.template.json`，以及 validator：
`tools/validate_prospective_pilot_decision.py`。

此契約只檢查治理完整性，不證明核准人的真實身份或法律權限。D01–D12 即使全部
`APPROVED`，最多讓 `pilot_status` 進到 `READY_FOR_START_AUTHORIZATION`；仍須另有
`pilot_start_authorization.authorized=true`，並綁定 exact candidate commit、package、
manifest、protocol SHA256 與另一次人工授權時間，才會讓 `pilot_start_allowed()`
回傳 true。現在 committed receipt 的 D01–D12 全部為 `APPROVED`；`protocol_decision_status=ALL_ITEMS_APPROVED`；`pilot_status=READY_FOR_START_AUTHORIZATION`；start authorization 仍為 false。

公開 receipt 禁止放 case ID、出生資料、prediction lock、outcome、source record 或
其他 private payload；真實權限／人名／私人資料仍留在核准的私人位置。

## 待核准的分析界線

主要目的、具體流程值、metric 與門檻已依 `prospective-pilot-proposed-values.md` 核准。有效lock須同時滿足時間、source/claim/candidate binding及blindness，不能只以檔案存在算成功。分母須保留所有事前定義的嘗試，並明示失敗、缺失、退出與排除；不同指標可有不同、預先固定的分母，不混用。

無機率輸出則不做機率校準。Outcome符合率最多為另經核准的描述性結果，不作本輪命理效度、一般化或promotion結論。Target population 與 claim-universe governance 已核准；但 exact candidate/package/manifest、final sealed protocol digest 與私人 storage/access record 尚未綁定，因此仍不能啟動真實 pilot。

## 啟動前最後確認

十二列已核准。下一步仍須封存最終 protocol 版本及 digest、確認私人 storage/access record、固定 exact candidate/package/manifest，並完成既定 governance 測試／整合審查。最後由人類另外明確授權啟動；D01–D12 核准本身不等於 pilot start。

目前不接受正式case、不產生正式prediction lock、不存取outcome/oracle、不scoring。未開始pilot，也沒有pilot結果。
