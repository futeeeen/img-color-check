# 專案上傳變更紀錄

## 2026.06.16_11:10:26
* 新增參數說明 tooltip，讓每個 UI 參數旁的小問號可顯示該參數會影響的選色或版型行為。
* 將 `局部色彩保護` 從開關改為 `關 / 弱 / 中 / 強` 四段滑桿，並在後端轉換為對應的局部色彩保護強度。
* 更新 README，補充 tooltip 與局部色彩保護分級功能。
* Validation: 執行 `python -m compileall app.py palette_generator.py`、`node --check static\app.js`，確認 Web UI 首頁回傳 `200`，並用 `local_protection=3` 呼叫 `/generate` 成功產生圖片。

## 2026.06.15_18:28:09
* 優化 `重到輕` 排序，改為以明度為主並加入色相與彩度連續性的平滑排序，降低食物照片色票中綠色或低彩度色插入造成的斷層感。
* 統一 UI 尺寸標示邏輯，左側原圖與右側輸出預覽皆使用 `寬 x 高 px`，並將右側預覽標示改為 `輸出：寬 x 高 px`。
* 修正右側版型預覽的數值讀取，讓外框粗細與分隔粗細設定為 `0` 時也能正確反映在預覽尺寸。
* Validation: 執行 `python -m compileall app.py palette_generator.py`、`node --check static\app.js`、`python palette_generator.py valid-used\S__100302857_0.jpg --output-dir output\history-check --crop-source auto-palette --order luminance`，並確認 Web UI 首頁回傳 `200`。

## 2026.06.15_11:47:26
* 優化預設 cinematic 色票排序，改為深色錨點加連續色相帶，降低紅綠或明暗來回穿插造成的跳動感。
* 新增 hue-band 排序邏輯，讓色票更接近 `valid-used` 參考圖的重到輕或重、輕、重視覺節奏。
* 更新 README 的 MVP 管線描述，補上新的連續色相帶排序策略。
* Validation: 執行 `python -m compileall palette_generator.py`，以及 `python palette_generator.py valid-used --output-dir output\valid-used --crop-source auto-palette --json`。

## 2026.06.15_11:36:49
* 建立第一版照片主色提取 CLI，可從單張圖片或資料夾批次產生上圖下色票的 PNG。
* 實作 sRGB 到 OKLab/OKLCH 的感知色彩管線、權重式 MiniBatchKMeans、相近色合併、10 色選取與 cinematic/luminance/hue 排序。
* 加入以中心偏重、飽和度、局部對比、邊緣細節與曝光品質組成的 MVP 顯著性權重，並支援 `--crop-source auto-palette` 供 `valid-used` 參考圖裁切驗證。
* 新增 README、requirements、.gitignore，說明開發工具、使用方式、開源方案評估與驗證流程。
* Validation: 執行 `python -m compileall palette_generator.py`，以及 `python palette_generator.py valid-used --output-dir output\valid-used --crop-source auto-palette --json`。
