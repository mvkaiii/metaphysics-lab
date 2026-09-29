# 大運reference預註冊準備紀錄

Methodology：`APPROVED WITH CONSTRAINTS`。Comparator contract：`ENGINEERING_READY`。Packet：`NOT_SEALED`。Comparison：`NOT_STARTED`。Task3：`NEEDS_EVIDENCE`。

依據：[人工決策](../superpowers/phase-gates/2026-09-27-review-decisions.md)。此文件不是reference結果、完整預註冊或PASS證據。

## 必須先封存的項目

| 項目 | 目前狀態／下一個動作 |
| --- | --- |
| 規格 | bazi-natal-project-v1與G2的age／Visualization端點契約已指定；需由領域reviewer確認不依production反推的完整算法文字規格，包含精度、節氣相等時的規則及日期運算 |
| 外部來源 | 候選為香港天文台節氣資料；尚未選定年份、版本或下載bytes，digest未取得，不可開始comparison |
| 案例 | 尚未封存；事前規劃順逆、節氣前後／相等、跨年／閏年及指定時區案例；不得依production結果挑案例 |
| 比較欄位 | 節氣時刻、方向、首段干支、起運連續年數、首段起點與後續endpoint；逐欄標適用性，未知不猜補 |
| 容差 | 尚未封存；依來源公布精度、規格數值精度與誤差傳播事前制定，不依觀察到的差異放寬 |
| 判定規則 | 每欄MATCH／MISMATCH／NOT_COMPARABLE／MISSING_REFERENCE；缺口不能計入通過；整包仍待人工review |
| Oracle | 尚未建立；須有未接觸production實作／輸出的獨立實作者，先固定程式與expected值，再交比較者 |
| 封存 | 來源bytes、案例、規格、oracle、expected值、容差與規則均須有版本／SHA256及先後順序紀錄 |

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

因此目前仍是：實際packet `NOT_SEALED`、oracle `NOT_CREATED`、
comparison `NOT_STARTED`、Task3 `NEEDS_EVIDENCE`。

## 獨立性與暴露紀錄

目前Codex執行者已讀過production及既有synthetic輸出，不能以同一上下文直接建立並宣稱獨立oracle。Reference實作者只能接收核准的規格與外部資料，不取得production、synthetic expected output或comparison結果。若未提供可隔離角色，本部分維持BLOCKED；不得偷偷降級為同源而宣稱independent。

每一比較欄位分別列`independent`、`partially_shared`或`same_source_reproduction`及理由。共用Project文字規格是契約驗證的必要前提，但共用production程式或資料計算鏈必須另揭露，不可把多個同源套件當多份獨立證據。

天文來源只支持節氣／時間輸入；獨立oracle支持被覆蓋的Project契約，不證明命理事件預測有效性。Visualization的半開區間是核准表示契約，不是外部天文資料能證明的engine原始語意。尚無結果，不修改既有qualification packet。
