"""
Scraper for Taiwan's national nuclear power referendums from CEC Election Database
(https://db.cec.gov.tw/):
  - Case 16 (2018-11-24): 以核養綠
  - Case 17 (2021-12-18): 重啟核四
  - Case 21 (2025-08-23): 核三延役
Outputs national summary and 22-county breakdown to UTF-8-SIG CSV files.
"""

from __future__ import annotations

import csv
import json
import urllib.request
from pathlib import Path

HEADERS = {"User-Agent": "Mozilla/5.0"}

CASES = [
    {
        "case_no": 16,
        "year": "2018",
        "vote_date": "2018-11-24",
        "short_name": "以核養綠",
        "theme_id": "91859c73ed7acc136fc669e6f4285391",
        "topic": "廢除電業法第95條第1項（2025非核家園條文）",
        "result": "通過",
    },
    {
        "case_no": 17,
        "year": "2021",
        "vote_date": "2021-12-18",
        "short_name": "重啟核四",
        "theme_id": "646d6bb5509d5345dc68a93e861ef2ca",
        "topic": "您是否同意核四啟封商轉發電？",
        "result": "不通過",
    },
    {
        "case_no": 21,
        "year": "2025",
        "vote_date": "2025-08-23",
        "short_name": "核三延役",
        "theme_id": "67e0b4764145bc1edb0eb02f11b383ff",
        "topic": "您是否同意第三核能發電廠經主管機關同意確認無安全疑慮後，繼續運轉？",
        "result": "不通過",
    },
]


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_level(theme_id: str, level: str) -> list[dict]:
    prof_url = f"https://db.cec.gov.tw/static/referendums/data/profiles/N/{theme_id}/{level}/00_000_00_000_0000.json"
    tckt_url = f"https://db.cec.gov.tw/static/referendums/data/tickets/N/{theme_id}/{level}/00_000_00_000_0000.json"
    prof_rows = fetch_json(prof_url)["00_000_00_000_0000"]
    tckt_rows = fetch_json(tckt_url)["00_000_00_000_0000"]

    tckt_by_code = {
        (r["prv_code"], r["city_code"]): r for r in tckt_rows
    }

    merged = []
    for p in prof_rows:
        key = (p["prv_code"], p["city_code"])
        t = tckt_by_code.get(key, {})
        merged.append({
            "area_name": p["area_name"],
            "votable_population": p["votable_population"],
            "vote_ticket": p["vote_ticket"],
            "valid_ticket": p["valid_ticket"],
            "invalid_ticket": p["invalid_ticket"],
            "agree_ticket": p["agree_ticket"],
            "agree_pct": t.get("agree_ticket_percent", 0),
            "disagree_ticket": p["disagree_ticket"],
            "disagree_pct": t.get("disagree_ticket_percent", 0),
            "turnout_pct": p["vote_to_votable"],
            "agree_to_votable_pct": p["agree_to_votable"],
        })
    return merged


def write_csv(path: Path, headers: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"Saved {len(rows)} rows -> {path}")


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "output"
    nat_rows = []
    county_rows = []

    for c in CASES:
        print(f"Fetching 第{c['case_no']}案 ({c['year']} {c['short_name']})...")
        for r in fetch_level(c["theme_id"], "N"):
            nat_rows.append([
                c["year"], c["vote_date"], c["case_no"], c["short_name"], c["result"],
                r["area_name"], r["votable_population"], r["vote_ticket"], r["valid_ticket"],
                r["invalid_ticket"], r["agree_ticket"], r["agree_pct"],
                r["disagree_ticket"], r["disagree_pct"], r["turnout_pct"], r["agree_to_votable_pct"],
            ])
        for r in fetch_level(c["theme_id"], "C"):
            county_rows.append([
                c["year"], c["vote_date"], c["case_no"], c["short_name"], c["result"],
                r["area_name"], r["votable_population"], r["vote_ticket"], r["valid_ticket"],
                r["invalid_ticket"], r["agree_ticket"], r["agree_pct"],
                r["disagree_ticket"], r["disagree_pct"], r["turnout_pct"], r["agree_to_votable_pct"],
            ])

    headers = [
        "年度", "投票日期", "案號", "簡稱", "審定結果",
        "地區", "投票權人數", "投票數", "有效票數", "無效票數",
        "同意票數", "同意率(%)", "不同意票數", "不同意率(%)",
        "投票率(%)", "同意票佔投票權人(%)",
    ]
    write_csv(out_dir / "nuclear_referendum_national.csv", headers, nat_rows)
    write_csv(out_dir / "nuclear_referendum_counties.csv", headers, county_rows)


if __name__ == "__main__":
    main()
