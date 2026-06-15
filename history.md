# 專案上傳變更紀錄

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
