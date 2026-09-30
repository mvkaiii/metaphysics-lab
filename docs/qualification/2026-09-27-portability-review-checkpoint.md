# Portability與人工review checkpoint

本紀錄是未提交working-tree驗證，不是新candidate hosted qualification。歷史CI不能沿用。

## 範圍及進度

- 變更前HEAD：`26176b15e23897b37e30a1bc615a33d9d93ccb63`；branch：`local/task0-2-capability-matrix`。
- 遠端main已fresh verify為`872c60b2e959ea48d25524b74686e488f576ec6f`。
- 計畫來源：`0bdd2f41fe78ba192b4ae0e31fcbba6fba0c9741`；舊Task0–2限制依後續人工決策取代。
- 使用既有隔離worktree與`.venv-task3`，Windows/Python3.12；沒有安裝套件或修改全域Python。
- 人工決策、Task9十二項送審表已整理；Task3預註冊仍`NOT_SEALED`，沒有comparison。

## TDD

命令：`.venv-task3/Scripts/python.exe -B -m unittest tests.test_vendor_digest_portability -v`。

RED：4項全部以digest不符失敗，而非import／缺依賴。混合大小寫與目錄前綴fixture的canonical digest為`6ebb38a979d82f9ea999c21ad8abcff1c7cbe0d9d8b538129d24daa05e448f09`；Windows舊排序為`3b25976eedaf231ab79f6ea12478c5f8dec81e7f9c22feed6e28617b77af7d8b`。

最小修正：runtime與maintenance的tree digest改用relative POSIX path string排序，不casefold、不normalize payload bytes；既有manifest測試的獨立digest helper使用相同明定排序契約。未更動vendor manifest預期digest。

GREEN命令：`.venv-task3/Scripts/python.exe -B -m unittest tests.test_vendor_digest_portability tests.test_vendor_manifest tests.test_vendor_refresh tests.test_vendor_import_isolation tests.test_bazi_decadal_qualification -v`。

結果：41項通過；其中大運22項通過，但僅為結構／重現性，不改Task3 `NEEDS_EVIDENCE`。

分別重建及驗證的package tree符合原manifest：

- lunar-python：`4bdfa74a22952023d4613df223e1e87d010b472b78f0f809cc48b700ce842c07`。
- tzdata：`a36e10a120028b8adc4f1e5645987e31befe4a1282a63e29017cea13a8914fcc`。

## 環境診斷與生成產物

第一輪原Windows checkout回歸：1,365項，25 failures、7 errors。涉及舊bundle尚未同步、CP950編解碼及歷史summary來源bytes差異，不能宣告PASS。

同步Windows生成bundle並僅對測試程序設定`PYTHONUTF8=1`後：1,365項，剩1 failure：`test_natal_qualification_summary.NatalQualificationSummaryTests.test_committed_summary_matches_deterministic_builder`。四個被摘要引用的來源檔包含CRLF；逐檔比較Git raw blob確認LF bytes的digest與歷史summary完全一致。沒有修改qualification來源或摘要。

另發現Windows生成bundle除runtime修正外，會包含六個CRLF資源差異。因此不採該bundle為candidate；在新的暫存clone以`core.autocrlf=false` checkout變更前HEAD，僅套用五個工程檔，再用原builder重建。Bundle的`_SOURCE_FILES`映射與HEAD相比，唯一變更為`engine/vendor/materialize.py`。沒有改Git全域設定、套件版本或vendor內容。

Canonical checkout在正確bundle同步前執行1,365項，有6 failures，全為bundle parity／release-surface drift，沒有error。

同步canonical bundle後的最終完整回歸：**1,365項全部通過，190.101秒**。命令為既有隔離Python執行`-B -m unittest discover -s tests -p 'test_*.py'`，僅該程序設定`PYTHONUTF8=1`；環境為Windows/Python3.12.14及canonical LF checkout。原worktree與此checkout的五個工程檔及最終bundle一致。這不是Linux/Python3.9或hosted結果。

Vendor manifest與68個shards共69檔，working-tree raw bytes均與HEAD Git blob相同。`build_bazi_decadal_qualification.py --check`通過，沒有改寫packet。

## Canonical candidate-only產物

以下為未提交working-tree的候選產物，不是已發布v1.7.1資產。版本常數尚沿用既有值，不能以此覆蓋歷史Release或冒稱新正式版本。

- runtime SHA256：`dbcce29eb2c66759c869a7864691a305bb6a8cc3aa6ad41e10df418751fad62f`。
- distribution SOURCE_DIGEST：`89208e58eb8f199ae1a2efebf1fd2c1be5ace5a40012406b15e0a6dea9303a39`。
- User Package SHA256：`cb175e2d482fe9ca8e2d46d6c55c4b0237f1cbb9a631e0d3c50aef75f8e1e0c4`。
- canonical build `--check`：通過。
- canonical release-surface：13項通過。工具中的`python39_compile`檢查實際使用本機3.12，不宣稱已跑Python3.9。
- compile：394個source檔加bundle通過。
- 既有workflow檔名污染掃描：未發現禁止名稱；這不是全面私人資料審核。
- 新文件連結及含untracked內容的行尾空白檢查通過。

新runtime bytes不同，不能沿用舊SHA的CI、package identity或sandbox證據。尚無Linux/Python3.9及新SHA hosted驗證，不宣稱跨平台整體完成。

原Windows CRLF worktree不可作canonical build authority；直接重建仍會帶入資源line-ending差異，歷史summary的raw-byte檢查也會失敗。保留原證據檔，不提交normalization；後續採canonical checkout／hosted驗證。

## 獨立自我審查

無可用subagent reviewer；另行自我審查diff，不當成外部review。排序不使用casefold，raw bytes、symlink排除與既有manifest預期值不變；大小寫／目錄前綴fixture及兩套真實vendor tree可攔截排序回退。Generated source mapping只變更runtime materializer。獨立人工／hosted驗收仍待完成。

## Gate與review限制

Task3：`NEEDS_EVIDENCE`；獨立oracle角色待建立。Task9：`DRAFT_PENDING_HUMAN_APPROVAL`／`NOT_STARTED`。沒有正式case、prediction lock、outcome/oracle或scoring。

這裡的oracle存取禁令指Task9真實pilot；Task3另依reference methodology限制處理。工程修正與研究qualification分開。本次未merge、tag、release、publish或promotion。
