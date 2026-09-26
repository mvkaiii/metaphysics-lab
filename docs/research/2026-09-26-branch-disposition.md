# Branch disposition audit

> 狀態：AUDIT ONLY／NOT SAFE TO DELETE。此文件只記錄Task 0-2的fresh branch與tree盤點，不執行retarget、merge、archive、delete或default promotion。

## Baseline

- Repository：`mvkaiii/metaphysics-lab`
- Compared against `main`：`872c60b2e959ea48d25524b74686e488f576ec6f`
- Immutable history：`v1.7.1`=`872c60b2e959ea48d25524b74686e488f576ec6f`、`v1.7.0`=`24760aa8766eb2691c8878f2cd8b97f0b37f8964`、`v1.6.0`=`c325d754112df71c6747e17262d2e781d2864441`
- Observation date：`2026-09-26`

## Fresh compare inventory

| Branch | HEAD | Ahead | Behind | Changed files | Disposition |
| --- | --- | ---: | ---: | ---: | --- |
| `research/v1.6-prospective-claim-authority-set` | `e28a51e9cb60961838300b8a0aea8e25696e9fb4` | 40 | 313 | 19 | 保留研究線；含prospective claim authority的獨有engine／workflow／tests，對應PR #221；不得直接merge或視為promotion evidence。 |
| `research/v1.6-yearly-ziwei-transformations-y1` | `3d6bba9efa37b105aee198215f90f00e3ed99229` | 22 | 313 | 14 | 保留研究線；含yearly transformation benchmark／validation的獨有內容，對應PR #219；prospective pending，不作Stable truth。 |
| `impl/v1.6-selector-v2-clean-control-21` | `842bb3b75eb9b8f03ae90180f1b98cfa3bd19a13` | 11 | 423 | 9 | 保留研究線；含selector 2.1／coordination policy v2的獨有內容；不得改變目前selector／interpretation default。 |
| `research/v1.6-prospective-arm-freeze-v1` | `dc95050640addf31e57ec637fdcf8e1483c42fb5` | 51 | 313 | 25 | 保留研究線；含arm-freeze與claim-authority治理內容；待獨立evidence review，不自動承接。 |
| `feature/bazi-flow-time-qualification` | `4319964291f2acd6f535042c70a2b2e3e9da076e` | 9 | 705 | 6 | 保留qualification分支；核心qualification檔案已在main可見，但仍需完整residual／blob audit後才可archive。 |
| `feature/ziwei-flow-time-qualification` | `df26e7eaf8718deef380b3e04194c2f625cba62b` | 8 | 704 | 5 | 保留qualification分支；核心qualification檔案已在main可見，但仍需完整residual／blob audit後才可archive。 |
| `feature/ziwei-month-boundary-qualification` | `38d8509f46a2c1121e147c563d571a7ce85d1967` | 13 | 703 | 9 | 保留qualification分支；核心qualification檔案已在main可見，且分支仍有UX／提示詞差異，不能直接刪除。 |
| `feature/portable-offline-natal-pipeline` | `c6771cde49b0a8936841d98a6ae7b7c4a3f4eca9` | 200 | 707 | 125 | 保留大型獨立功能線；200 commits／125 changed files且含core／engine／dist差異，不能以部分blob相同推論可刪除。 |
| `plan/v1.7-reliability-guided-inquiry` | `0d7370eb54fb77c9f4f788ad838a78d06217d24b` | 11 | 257 | 8 | 保留歷史planning branch；文件可作architecture／governance參考，archive進main需另案決策；不在Task 0-2實作。 |
| `ci/v17-artifact-lifecycle-20260915` | `9872223aac6d2bc2d607d716c4490c5cd47651d0` | 45 | 81 | 53 | 保留CI治理候選；含version-specific inventory／policy、tests與transport residue；是否version-neutral化另案處理，不在Task 0-2搬移。 |

## PR base integrity

| PR | Head | Declared base | Base SHA | Base ref lookup | Decision |
| ---: | --- | --- | --- | --- | --- |
| #219 | `research/v1.6-yearly-ziwei-transformations-y1` @ `3d6bba9efa37b105aee198215f90f00e3ed99229` | `impl/v1.6-legacy-adapter-paired-evaluation` | `eaf03116bf5e02b08b4b51caed2cb2c31f796686` | `404` | 保留；不retarget、不merge、不刪除head |
| #221 | `research/v1.6-prospective-claim-authority-set` @ `e28a51e9cb60961838300b8a0aea8e25696e9fb4` | `research/v1.6-prospective-window-scope-v1` | `c2d111b3e1b410a7208b8d4ba0585e8000d30a87` | `404` | 保留；不retarget、不merge、不刪除head |

## Task9 fresh GitHub revalidation

Observed on `2026-09-26` from read-only GitHub PR, branch, commit, and recursive tree endpoints. The complete recursive trees for the listed commits were not truncated. These exact tree comparisons supersede ambiguous earlier `Changed files` counts for these three research lines; they do not authorize branch cleanup.

| Ref | Fresh state / exact HEAD | PR file-list count | HEAD tree vs baseline `main@872c60b` | Finding |
| --- | --- | ---: | --- | --- |
| PR #219 | Open, draft; head `3d6bba9efa37b105aee198215f90f00e3ed99229`; declared base `impl/v1.6-legacy-adapter-paired-evaluation@eaf03116bf5e02b08b4b51caed2cb2c31f796686` has no current branch result | 14 | 8 paths absent from main; 34 existing paths have different blobs | PR body records retrospective Y1 pipeline status, `PROSPECTIVE_NOT_EXECUTED`, and `promotion_allowed=false`. The tree still has Y1-specific benchmark/docs/tools and differing existing files. Preserve the research evidence; do not retarget or merge. |
| PR #221 | Open, draft; head `e28a51e9cb60961838300b8a0aea8e25696e9fb4`; declared base `research/v1.6-prospective-window-scope-v1@c2d111b3e1b410a7208b8d4ba0585e8000d30a87` has no current branch result | 8 | 18 paths absent from main; 37 existing paths have different blobs | PR-specific files add the composite claim-authority set. Its PR body records `PRIVATE_S1_NOT_YET_LOCKED`, no oracle, no private scoring, and `promotion_allowed=false`. The larger tree delta also includes the stacked window-scope line; do not mistake it for the PR-only file list. |
| `research/v1.6-prospective-arm-freeze-v1` | Branch exists at `dc95050640addf31e57ec637fdcf8e1483c42fb5` | n/a | 21 paths absent from main; 36 existing paths have different blobs | Relative to PR #221's exact tree, this branch adds the arm-freeze workflow/module/test plus Y1 files and changes two existing paths. It is a separate research artifact, not a main capability or authorization to run private scoring. |

The two missing PR base branches were checked by branch search; their PR metadata still retains the historical base SHAs. No base was recreated, and no PR or branch was changed. Tree-level differences confirm residual content remains; they are not a branch-deletion audit or merge recommendation.

Sources: [PR #219](https://github.com/mvkaiii/metaphysics-lab/pull/219), [PR #221](https://github.com/mvkaiii/metaphysics-lab/pull/221), [arm-freeze branch](https://github.com/mvkaiii/metaphysics-lab/tree/research/v1.6-prospective-arm-freeze-v1), and exact baseline commit [`872c60b2e959ea48d25524b74686e488f576ec6f`](https://github.com/mvkaiii/metaphysics-lab/commit/872c60b2e959ea48d25524b74686e488f576ec6f).

## Selected target-blob findings

- Bazi flow-time、Ziwei flow-time與month-boundary的qualification README／fixtures／tests／builders，在本次selected target audit中已與main相同；這只能證明選定檔案的blob一致，不能取代完整residual audit。
- #219／#221與`research/v1.6-prospective-arm-freeze-v1`仍有claim-authority、prospective governance或yearly transformation的獨有engine／tests／workflow／docs；這些是研究內容，不是main的capability truth。
- `plan/v1.7-reliability-guided-inquiry`的八份planning／design文件在selected target audit中未顯示production target差異；是否archive進main仍需獨立文件治理決策。
- `ci/v17-artifact-lifecycle-20260915`的`tools/v17_artifact_inventory.py`在selected target audit中為branch-only；其餘lifecycle／transport內容也未在本Task承接。
- `feature/portable-offline-natal-pipeline`雖有offline registry／birth-place／vendor target blob相同，但仍有大量core／engine／dist／docs差異，不能視為可安全刪除。

## Disposition rules

1. 研究branch與qualification branch先保留；沒有完整承接證據不得刪除。
2. Branch／PR housekeeping不屬於Task 0-2；本checkpoint不retarget、不merge、不close、不delete。
3. `main`的capability manifest仍是implementation、maturity、routing與rule_version single source of truth；branch evidence不會覆寫它。
4. 研究branch的PASS、benchmark或workflow結果不等同Stable promotion，也不會寫入正式release evidence。

詳細機器可讀快照見`qualification/capabilities/source-snapshot.v1.json`。
