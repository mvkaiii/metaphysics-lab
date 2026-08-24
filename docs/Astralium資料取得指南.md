# Astralium 資料取得指南

Astralium 是 Metaphysics Lab 可以使用的**可選第三方排盤來源**之一。你可以提供 Astralium 的八字資料、紫微資料，或兩者一起提供；沒有 Astralium 也可以使用 Metaphysics Lab。

Metaphysics Lab 不隸屬 Astralium，也不把 Astralium 當成必要 runtime dependency。

Astralium 官方網站：

https://getastralium.com/

## 一、什麼情況適合提供 Astralium？

你可以選擇：

- **只有出生資料**：由 Metaphysics Lab 建立 Project 原生命盤。
- **出生資料 + Astralium**：Project 自算一份，再用 Astralium 做交叉校驗。
- **只有第三方排盤**：先保存 Astralium 的 External 資料，等 Project 計算條件完整時再比較。

如果已經有 Astralium 八字與紫微資料，兩份都可以提供，不需要二選一。

## 二、Astralium 八字建議保留什麼

若來源有提供，建議保留：

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
- 流年資料
- 排盤版本／產出日期（若有）

如果來源另外提供格局、身強弱、喜用、神煞或干支互動，也可以保存，但標清楚「來源提供」，不要先改寫成自己的結論。

來源只提供部分欄位時，就只匯入那些欄位，不自行補齊。

## 三、Astralium 紫微建議保留什麼

若來源有提供，建議保留：

- 十二宮
- 各宮星曜
- 命宮
- 身宮
- 生年四化
- 自化／飛化
- 大限
- 小限
- 流年命宮
- 流年四化／飛化
- 排盤系統與時間口徑

第三方原始資料應盡量完整保存。Project 是否能自行建立某個紫微時間層，技術上仍以當次 `runtime_info` 為準；不要因 Project 可以計算某項資料，就刪掉 External 原始來源。

## 四、不知道出生時間怎麼辦

不要為了讓 Astralium 或 Project 排出完整盤而隨便填一個時辰。

如果來源已經提供明確四柱或部分命盤，可以先保存為 External view；但「來源有四柱」不等於「已知唯一 civil 出生時間」，也不能自動推出完整紫微本命。

缺少出生時間時，Project 能否建立 Candidate Envelope 或 partial Case，依目前 `runtime_info` 與[命盤資料準備指南](命盤資料準備指南.md)處理。

## 五、怎麼放進私人 Project

可以把第三方原始資料另存成清楚標示來源的 Markdown，例如：

```text
八字_原始資料_Astralium.md
紫微_原始資料_Astralium.md
```

檔案開頭可以記：

```text
來源：Astralium
網址：https://getastralium.com/
產出日期：YYYY-MM-DD
命主：私人標籤
時間口徑：來源實際設定
```

PDF 或截圖也可以保留，但結構化文字通常比較方便做欄位級比較。

## 六、External / Project / Resolved

Astralium 進入 Project 後仍然是第三方來源，不會自動變成 Project 自己算出的命盤。

固定保留：

```text
External / Project / Resolved
```

比較結果使用：

```text
MATCH / EQUIVALENT / CONFLICT / NOT_COMPARABLE
```

- **External**：Astralium 或其他第三方實際提供的資料。
- **Project**：Metaphysics Lab 依固定算法建立的資料。
- **Resolved**：經校驗後記錄目前採用來源及差異狀態。

若兩邊不同，保留差異；不得為了讓結果看起來一致而覆寫任一方 raw view。

## 七、八種資料類型

分析時固定區分：

1. **原始盤面事實**：Astralium 或其他第三方直接提供的欄位。
2. **已校驗資料**：External / Project reconciliation、Historical Calibration evaluation 等校驗結果。
3. **Project 原生盤面**：由出生資料經固定 Natal Engine 建立的本命資料。
4. **Project 推導盤面**：由本命／運限／目標時間按固定算法建立的時間層。
5. **已驗證事件**：使用者確認真正發生過的事情。
6. **命理推論**：AI 對盤面的趨勢、事件與策略解讀。
7. **研究假說**：尚未正式納入已校驗規則的研究想法。
8. **當次現實背景**：當次提供的工作、財務、家庭與決策條件。

Astralium raw chart 不會因為進入 Project 就變成 **Project 原生盤面**；Project 自算資料也不會因為與 Astralium 一致，就冒充 Astralium 直接輸出。

## 八、Historical Blind Calibration

建立 Base Case 後可以先做本命分析。第一次進入個人化未來趨勢、流年或重大決策時，若需要 Historical Blind Calibration，應先完成未受歷史答案污染的 Stage 1，再讓使用者驗證事件。

其中：

- `blind_prediction`＝命理推論
- `user_confirmed_actual`＝**已驗證事件**
- `evaluation`＝**已校驗資料**

不得把已知事件反寫成原本就預測到，也不得為了讓 Astralium 或 Project 看起來更準而修改原始盤面。

## 九、Astralium 不是唯一選項

其他排盤網站、命理軟體、命理師提供的 PDF 或結構化資料也可以作為 External source。

至少保留：

- 資料來源
- 出生資料
- 排盤時間口徑
- 產出日期／版本（若有）
- 原始盤面內容

不同來源先做 comparison，不要把不同來源的欄位直接拼成一張不存在的「綜合原始盤」。

## 十、隱私

出生年月日時、出生地、第三方 raw chart、Historical Calibration 回答與人生事件都屬私人 Case 資料。

GitHub repo 只保存共用規則、程式、測試與非私人模板；實際命主資料留在私人 ChatGPT Project、Claude Project 或其他受控環境。
