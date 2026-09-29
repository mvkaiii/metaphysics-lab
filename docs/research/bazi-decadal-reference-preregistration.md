# 大運reference預註冊準備紀錄

Methodology：`APPROVED WITH CONSTRAINTS`。Comparator contract：`ENGINEERING_READY`。Packet：`NOT_SEALED`。Comparison：`NOT_STARTED`。Task3：`NEEDS_EVIDENCE`。

依據：[人工決策](../superpowers/phase-gates/2026-09-27-review-decisions.md)。此文件不是reference結果、完整預註冊或PASS證據。

## 必須先封存的項目

| 項目 | 目前狀態／下一個動作 |
| --- | --- |
| 規格 | 已建立`bazi-decadal-independent-profile-spec.candidate.md`作domain-review candidate；仍為`DRAFT_PENDING_DOMAIN_REVIEW`，不得直接當oracle規格 |
| 外部來源 | 已事前選定HKO 2015＋2016靜態24節氣頁作source proposal，以common/leap-year coverage為選擇理由；exact raw bytes SHA256仍未取得，因此不可seal |
| 案例 | 已建立12-case proposal，覆蓋男女順逆、節氣前後、跨年、閏年／閏日；未依production結果挑案例；節氣「相等」案例仍因來源精度與規則未決而BLOCKED |
| 比較欄位 | 已提案方向、首段干支、起運連續年數、首段起點；後續endpoint因生成規則尚未由domain reviewer固定而維持NOT_COMPARABLE |
| 容差 | 已依HKO分鐘顯示粒度＋既有3日=1年／365.2425公式提出事前誤差傳播值；仍待domain reviewer核准，不可視為final tolerance |
| 判定規則 | 每欄MATCH／MISMATCH／NOT_COMPARABLE／MISSING_REFERENCE；缺口不能計入通過；整包仍待人工review |
| Oracle | 尚未建立；須有未接觸production實作／輸出的獨立實作者，先固定程式與expected值，再交比較者 |
| 封存 | profile review、equality-at-Jie、endpoint formula、source precision semantics、spec digest、source raw-byte digests尚未全部完成；seal維持禁止 |

Review packet：
`docs/research/bazi-decadal-preoracle-review-packet.v1.json`

Validator：
`tools/validate_bazi_decadal_preoracle_review_packet.py`

目前該packet刻意固定：
`status=DRAFT_PENDING_DOMAIN_REVIEW`、
`seal_allowed=false`、
`task3_status=NEEDS_EVIDENCE`。

## Comparator工程狀態

已新增 `tools/compare_bazi_decadal_reference.py` 與
`tests/test_bazi_decadal_reference_comparison.py`。比較器只驗證 sealed packet 與逐欄
JSON Pointer comparison，不產生 expected values、不呼叫 production 算法，也不作
qualification / promotion 決策。完整 oracle 交接邊界見
[`bazi-decadal-independent-oracle-handoff.md`](bazi-decadal-independent-oracle-handoff.md)。

比較器完成只代表後續證據有固定消費契約；不代表 reference packet 已封存。

## Pre-oracle seal工程狀態

已新增 `tools/seal_bazi_decadal_reference_inputs.py` 與
`tests/test_bazi_decadal_preoracle_seal.py`。這個工具只負責在oracle產生expected values
之前封存：

- 經領域reviewer核准後的文字規格SHA256；
- 實際外部來源bytes的SHA256與公布精度；
- 事前case census及其input digest／coverage tags；
- 每個case的比較JSON Pointer、comparison kind與容差；
- oracle不得接觸production code、production output或pre-seal comparison result的隔離旗標。

pre-oracle seal明確拒絕任何 `expected` value，並以canonical SHA256偵測封存後修改。
它不選擇實際年份、不下載或替代外部來源、不產生八字結果，也不構成independent
oracle或qualification evidence。

另已新增 `tools/finalize_bazi_decadal_reference_packet.py`，用於oracle完成後把expected
values綁回exact pre-oracle seal，禁止case、input digest、comparison path或tolerance漂移。
finalizer本身不計算命理值。

因此目前仍是：實際packet `NOT_SEALED`、oracle `NOT_CREATED`、
comparison `NOT_STARTED`、Task3 `NEEDS_EVIDENCE`。

## 獨立性與暴露紀錄

目前Codex執行者已讀過production及既有synthetic輸出，不能以同一上下文直接建立並宣稱獨立oracle。Reference實作者只能接收核准的規格與外部資料，不取得production、synthetic expected output或comparison結果。若未提供可隔離角色，本部分維持BLOCKED；不得偷偷降級為同源而宣稱independent。

每一比較欄位分別列`independent`、`partially_shared`或`same_source_reproduction`及理由。共用Project文字規格是契約驗證的必要前提，但共用production程式或資料計算鏈必須另揭露，不可把多個同源套件當多份獨立證據。

天文來源只支持節氣／時間輸入；獨立oracle支持被覆蓋的Project契約，不證明命理事件預測有效性。Visualization的半開區間是核准表示契約，不是外部天文資料能證明的engine原始語意。尚無結果，不修改既有qualification packet。
