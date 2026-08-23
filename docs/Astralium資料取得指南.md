# Astralium 資料取得指南

本文件說明如何把 Astralium 當作 Metaphysics Lab 的結構化 external chart 來源之一，以及它與 Project deterministic chart 的資料邊界。

Astralium 官方網站：

https://getastralium.com/

截至 2026-08-20，Astralium 官方說明其定位為 AI 術數排盤資料平台，可先排盤，再產生可交給 ChatGPT／Claude 的結構化資料包。

Metaphysics Lab 不隸屬 Astralium，也不把 Astralium 視為唯一或必要來源。它是可選的第三方 external source；實際能否由 Project 自行建立某個 deterministic capability，一律以當次 `runtime_info` 為準。

---

## 一、為什麼建議保存結構化原始資料

Metaphysics Lab 的設計把來源資料、Project 計算與 AI 解讀分開：

```text
第三方排盤來源
↓
External raw view／原始盤面事實
↓
Project 依出生資料獨立建立 deterministic natal（若 required inputs 完整）
↓
External / Project reconciliation
↓
Resolved view
↓
需要時建立 Project 推導盤面
↓
AI 命理解讀
↓
Historical Blind Calibration／事件校準
```

這樣做的重點不是「一定要第三方先排盤」，而是任何來源都要保留 provenance，不讓原始資料、Project 計算與 AI 推論混成一層。

---

## 二、建立八字 external data

若使用 Astralium 八字資料包，至少確認並保存來源實際提供的：

- 性別
- 西元出生年月日
- 出生時間
- 出生地
- 時區、真太陽時、子時換日或其他時間口徑
- 四柱
- 日主
- 藏干
- 十神
- 大運
- 來源提供的流年資料
- 排盤系統版本／產出日期（若可取得）

若資料包另外提供格局、身強弱、喜用、神煞或干支互動，也可以保留，但要維持來源原貌，不要先人工改寫成自己的結論。

如果來源只提供部分欄位，就只匯入那些欄位。不得因為「通常八字應該還有某欄」而自行補值。

### 不知道出生時間時

不要為了讓 Astralium 或 Project 能排出完整盤而隨便填一個時辰。

若使用者已有來源明確的四柱或部分八字資料，可以把實際提供內容保存為 External view；但已知四柱不等於已知唯一 civil 出生時間，也不能用來自動重建完整 Ziwei natal。

目前 Project natal required inputs 與可執行狀態請看 `runtime_info`。若缺少出生時間而 runtime 回報 missing field，就保留未知，不假裝已建立完整 Project 本命。

---

## 三、建立紫微 external data

若要使用第三方紫微資料，優先保存來源實際提供的：

- 十二宮
- 各宮星曜
- 命宮
- 身宮
- 生年四化
- 自化／飛化（若來源有提供）
- 大限
- 小限
- 流年命宮
- 流年四化／飛化（若來源有提供）
- 排盤系統與時間口徑

不要因為 Project runtime 可能具備某些紫微 natal、流月、流日、流時、四化、飛化或流曜能力，就省略 external source 的原始資料；兩者的角色不同。

同樣地，也不要在本文件把「目前能算哪些紫微細層」寫死。需要建立某一時間層時，先讀 `runtime_info`，只使用當次 runtime 宣告可用且 required inputs 已滿足的 capability。

---

## 四、把 Astralium 原始資料放進私人 Project

建議把 Astralium 原始資料另存成清楚標示來源的文字／Markdown，例如：

```text
八字_原始資料_Astralium.md
紫微_原始資料_Astralium.md
```

檔案開頭可保留：

```text
來源：Astralium
網址：https://getastralium.com/
產出日期：YYYY-MM-DD
命主：私人標籤
時間口徑：來源實際設定
```

PDF 或截圖也可以保留，但結構化文字通常更方便做欄位級 comparison。

不要把真實命主的出生資料、Astralium raw chart 或人生事件提交到 Metaphysics Lab 公開／共用 GitHub repo。

---

## 五、第一次匯入後先做 natal reconciliation

不要拿到資料包後直接把它視為 Project 自己算出的結果。

若 required inputs 完整且 runtime 能建立 Project natal，應保留：

```text
External / Project / Resolved
```

至少核對：

1. 出生資料與時間口徑是否一致。
2. 八字四柱、日主與大運是否可比較。
3. 紫微命宮、身宮、十二宮、大限等可比較欄位是否一致。
4. 真太陽時、子時換日或其他 time profile 是否造成 material difference。
5. 不可比較的欄位是否明確標記 NOT_COMPARABLE，而不是猜值。
6. comparison 結果是否保留 MATCH / EQUIVALENT / CONFLICT / NOT_COMPARABLE 與 severity。

建立私人 Case 後，校驗資料寫入：

```text
00_專案索引.md
01_命盤核心摘要.md
02_命盤資料校驗紀錄.md
03_八字結構化資料包.md
04_紫微基礎資料包.md
```

新 Case 第一次只 materialize 00～04；05～08 依後續實際使用情境建立，不預先建立空檔。

---

## 六、Astralium 與 Metaphysics Lab 的八種資料層級

分析時固定區分：

1. **原始盤面事實**：Astralium 或其他第三方直接提供的欄位。
2. **已校驗資料**：External / Project reconciliation、Historical Calibration evaluation 等校驗結果。
3. **Project 原生盤面**：Project 由出生資料經固定 Natal Engine 建立的本命 deterministic facts。
4. **Project 推導盤面**：Project 由本命／運限／目標時間固定推導出的時間層與 Historical Activation selection。
5. **已驗證事件**：使用者確認真正發生過的事情。
6. **命理推論**：AI 對盤面做出的趨勢、事件與策略解讀。
7. **研究假說**：尚未正式納入已校驗 deterministic contract 的研究性想法。
8. **當次現實背景**：使用者當次提供的真實工作、財務、家庭與決策條件。

Astralium raw chart 不會因為進入 Project 就變成 Project 原生盤面；Project 自算的 natal 也不會因為與 Astralium 一致就變成 Astralium 直接輸出。

---

## 七、Historical Blind Calibration 與驗證事件

新使用者建立 Base Case 後，可以先做本命分析。

第一次進入個人化未來趨勢、流年或重大決策，而 `00_專案索引.md` 顯示 Historical Calibration 尚未完成時，依目前 Project Contract 先鎖定該問題的 Stage 1，再做 Historical Blind Calibration。

校準完成後才首次需要 materialize `05_驗證事件紀錄.md`。其中：

- `blind_prediction`＝命理推論
- `user_confirmed_actual`＝已驗證事件
- `evaluation`＝已校驗資料

不得把已知事件反寫成原本就預測到，也不得為了讓 external chart 看起來更準而修改原始盤面。

---

## 八、不是一定要用 Astralium

其他排盤網站、命理軟體、命理師提供的 PDF 或結構化資料也可以作為 external source。

至少保留：

- 資料來源
- 出生資料
- 排盤時間口徑
- 產出日期／版本（若有）
- 原始盤面內容

來源不同時先做 comparison，不要把不同來源的欄位直接拼成一張不存在的「綜合原始盤」。

---

## 九、隱私提醒

出生年月日時、出生地、external raw chart、Historical Calibration 回答與人生事件都屬私人 Case 資料。

GitHub repo 只保存共用規則、runtime、測試、qualification 與非私人模板；實際命主資料應留在私人 ChatGPT Project 或其他受控環境中。