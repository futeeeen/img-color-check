# 專案上傳變更紀錄

## 2026.06.15_11:36:49
* 建立第一版照片主色提取 CLI，可從單張圖片或資料夾批次產生上圖下色票的 PNG。
* 實作 sRGB 到 OKLab/OKLCH 的感知色彩管線、權重式 MiniBatchKMeans、相近色合併、10 色選取與 cinematic/luminance/hue 排序。
* 加入以中心偏重、飽和度、局部對比、邊緣細節與曝光品質組成的 MVP 顯著性權重，並支援 `--crop-source auto-palette` 供 `valid-used` 參考圖裁切驗證。
* 新增 README、requirements、.gitignore，說明開發工具、使用方式、開源方案評估與驗證流程。
* Validation: 執行 `python -m compileall palette_generator.py`，以及 `python palette_generator.py valid-used --output-dir output\valid-used --crop-source auto-palette --json`。
