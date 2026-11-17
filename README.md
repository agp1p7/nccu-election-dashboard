# 臺灣六都選舉數據爬蟲與分析儀表板（2014–2022）

資料來源：[國立政治大學選舉研究中心歷屆公職選舉資料庫](https://vote.nccu.edu.tw/cec/cechead.asp)

## 專案結構

- `scrape.py`：爬取 2014、2018、2022 三屆直轄市長與直轄市議員的「選舉概況表」與「候選人得票明細」（僅使用 Python 標準函式庫）。
- `output/`：產出的 4 份 UTF-8 with BOM (`utf-8-sig`) CSV 檔：
  - `mayor_overview.csv`
  - `mayor_candidates.csv`
  - `councilor_overview.csv`
  - `councilor_candidates.csv`
- `build_dashboard_data.py`：將 4 份 CSV 彙整轉換為 `docs/data.js`。
- `docs/`：純靜態互動式視覺化儀表板（`index.html` + `data.js`），可直接部署至 GitHub Pages。

## 本機重新執行

```bash
python scrape.py
python build_dashboard_data.py
```

可直接雙擊開啟 `docs/index.html` 預覽儀表板。

## 部署到 GitHub Pages

1. 將本專案推送至 GitHub Repository。
2. 進入 Repository 的 **Settings → Pages**。
3. **Source** 選擇 **Deploy from a branch**，Branch 選 `main`，資料夾選 `/docs`，按 **Save** 即可上線。
