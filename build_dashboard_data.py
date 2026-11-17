"""
Build pre-processed JSON/JS dataset (docs/data.js) for the GitHub Pages
election analytics dashboard from the 4 scraped CSV files in output/.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

PARTY_MAP = {
    "中國國民黨": "國民黨",
    "民主進步黨": "民進黨",
    "台灣民眾黨": "民眾黨",
    "時代力量": "時代力量",
    "台灣基進": "台灣基進",
    "親民黨": "親民黨",
    "無黨籍及未經政黨推薦": "無黨籍",
}

PARTY_ORDER = [
    "國民黨",
    "民進黨",
    "民眾黨",
    "時代力量",
    "台灣基進",
    "親民黨",
    "無黨籍",
    "其他政黨",
]

PARTY_COLORS = {
    "國民黨": "#0052A5",
    "民進黨": "#1B9431",
    "民眾黨": "#28C8C8",
    "時代力量": "#F9B600",
    "台灣基進": "#A73F24",
    "親民黨": "#F37021",
    "無黨籍": "#78909C",
    "其他政黨": "#9C27B0",
}

CITIES = ["台北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市"]
YEARS = ["2014", "2018", "2022"]


def to_int(val: str) -> int:
    val = (val or "").strip().replace(",", "")
    if not val or val == "--":
        return 0
    return int(val)


def to_pct(val: str) -> float:
    val = (val or "").strip().rstrip("%")
    if not val or val == "--":
        return 0.0
    return float(val)


def norm_party(raw: str) -> str:
    return PARTY_MAP.get((raw or "").strip(), "其他政黨")


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    root = Path(__file__).resolve().parent
    out_dir = root / "output"
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    mayor_ov_raw = load_csv(out_dir / "mayor_overview.csv")
    mayor_ca_raw = load_csv(out_dir / "mayor_candidates.csv")
    councilor_ov_raw = load_csv(out_dir / "councilor_overview.csv")
    councilor_ca_raw = load_csv(out_dir / "councilor_candidates.csv")
    ref_nat_raw = load_csv(out_dir / "nuclear_referendum_national.csv")
    ref_cnt_raw = load_csv(out_dir / "nuclear_referendum_counties.csv")

    mayor_overview = [
        {
            "year": r["年度"],
            "city": r["直轄市"],
            "pop": to_int(r["人口數"]),
            "voters": to_int(r["選舉人數"]),
            "cand": to_int(r["候選人數_計"]),
            "cand_m": to_int(r["候選人數_男"]),
            "cand_f": to_int(r["候選人數_女"]),
            "win": to_int(r["當選人數_計"]),
            "votes": to_int(r["投票數_合計"]),
            "valid": to_int(r["投票數_有效票數"]),
            "invalid": to_int(r["投票數_無效票數"]),
            "turnout": to_pct(r["投票數對選舉人數"]),
        }
        for r in mayor_ov_raw
    ]

    mayor_candidates = [
        {
            "year": r["年度"],
            "city": r["直轄市"],
            "name": r["姓名"],
            "no": r["號次"],
            "gender": r["性別"],
            "birth": to_int(r["出生年次"]),
            "raw_party": r["推薦政黨"],
            "party": norm_party(r["推薦政黨"]),
            "votes": to_int(r["得票數"]),
            "pct": to_pct(r["得票率"]),
            "elected": r["當選否"] == "Y",
            "incumbent": r["是否現任"] == "Y",
        }
        for r in mayor_ca_raw
    ]

    # Aggregate councilor overview to city-year level as well as keeping constituency rows
    councilor_overview = [
        {
            "year": r["年度"],
            "city": r["直轄市"],
            "type": r["選區類型"],
            "const": r["選區"],
            "pop": to_int(r["人口數"]),
            "voters": to_int(r["選舉人數"]),
            "cand": to_int(r["候選人數_計"]),
            "cand_m": to_int(r["候選人數_男"]),
            "cand_f": to_int(r["候選人數_女"]),
            "win": to_int(r["當選人數_計"]),
            "win_m": to_int(r["當選人數_男"]),
            "win_f": to_int(r["當選人數_女"]),
            "votes": to_int(r["投票數_合計"]),
            "valid": to_int(r["投票數_有效票數"]),
            "invalid": to_int(r["投票數_無效票數"]),
            "turnout": to_pct(r["投票數對選舉人數"]),
        }
        for r in councilor_ov_raw
    ]

    councilor_candidates = [
        {
            "year": r["年度"],
            "city": r["直轄市"],
            "type": r["選區類型"],
            "const": r["選區"],
            "name": r["姓名"],
            "no": r["號次"],
            "gender": r["性別"],
            "birth": to_int(r["出生年次"]),
            "raw_party": r["推薦政黨"],
            "party": norm_party(r["推薦政黨"]),
            "votes": to_int(r["得票數"]),
            "pct": to_pct(r["得票率"]),
            "elected": r["當選否"] == "Y",
            "incumbent": r["是否現任"] == "Y",
        }
        for r in councilor_ca_raw
    ]

    def parse_ref_rows(raw_rows: list[dict[str, str]]) -> list[dict]:
        return [
            {
                "year": r["年度"],
                "date": r["投票日期"],
                "case_no": to_int(r["案號"]),
                "name": r["簡稱"],
                "result": r["審定結果"],
                "area": r["地區"],
                "voters": to_int(r["投票權人數"]),
                "votes": to_int(r["投票數"]),
                "valid": to_int(r["有效票數"]),
                "invalid": to_int(r["無效票數"]),
                "agree": to_int(r["同意票數"]),
                "agree_pct": to_pct(r["同意率(%)"]),
                "disagree": to_int(r["不同意票數"]),
                "disagree_pct": to_pct(r["不同意率(%)"]),
                "turnout_pct": to_pct(r["投票率(%)"]),
                "threshold_pct": to_pct(r["同意票佔投票權人(%)"]),
            }
            for r in raw_rows
        ]

    payload = {
        "meta": {
            "years": YEARS,
            "cities": CITIES,
            "partyOrder": PARTY_ORDER,
            "partyColors": PARTY_COLORS,
        },
        "mayorOverview": mayor_overview,
        "mayorCandidates": mayor_candidates,
        "councilorOverview": councilor_overview,
        "councilorCandidates": councilor_candidates,
        "referendums": {
            "national": parse_ref_rows(ref_nat_raw),
            "counties": parse_ref_rows(ref_cnt_raw),
        },
    }

    js_path = docs_dir / "data.js"
    js_content = "window.ELECTION_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    js_path.write_text(js_content, encoding="utf-8")
    print(f"Wrote {js_path} ({js_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
