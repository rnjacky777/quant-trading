# 封存驗證紀錄（data/sealed-btc-2020-2021）

規則：AGENTS §1 的資料用途。候選必須先通過開發期 walk-forward，再事前登記，才能評估一次。每次評估都要記錄在這裡，不論結果好壞；每季最多 3 次。

## 封存（2026-10-29）

- **來源**：Binance `data.binance.vision`，包括 BTCUSDT 永續 1h K 線、mark price、現貨 1h K 線，都以 `.CHECKSUM` 驗證；funding 來自 `/fapi/v1/fundingRate`。工具是 `scripts/fetch_sealed_btc_2020_2021.py`，每個檔案的 SHA256 都記在 `manifest.json`。
- **期間**：2020-01-01 到 2021-09-30。Binance 永續的歷史檔從 2020-01 才開始提供，所以 2020-01 只當暖身，**評估期間為 2020-02-01 到 2021-09-30**。
- **完整性**（只檢查數量，沒有看價格或報酬）：

|資料|小時數或筆數|缺漏|
|---|---:|---|
|永續 K 線|15,336|0|
|永續 mark|15,336|0|
|現貨 K 線|15,306|30 小時，Binance 現貨的維護或停機時段，時間點列在 manifest|
|funding|1,917 筆|1,917 筆全部沒有 mark price|

- **評估時要事先寫進登記的處理方式**：
  - 30 個現貨缺漏小時要列為已知停機。不能交易現貨，估值沿用前一小時。
  - funding 的 mark price 用同一小時 mark K 線的開盤價補上。

## 評估紀錄

### 第 1 次（2026-10-30）：BTC 現貨 50 日均線濾網

- 登記：`2026-10-30-btc-trend-filter-sealed-registration.md`（使用者同意，本季第 1 次）。
- 執行：`python -m scripts.sealed_eval_btc_trend_filter`，輸出 `data/sealed-eval-1-btc-trend-filter.json`。執行前已比對封存檔案和 manifest 的 checksum。
- **結果：通過**，四項判定標準在兩段期間都符合。詳見 `2026-10-30-btc-trend-filter-sealed-results.md`。
- 封存驗證累計：1 次（本季 1/3）。
