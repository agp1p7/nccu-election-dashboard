"""
Scraper for NCCU Election Study Center (https://vote.nccu.edu.tw/cec/)
Extracts 2014, 2018, 2022 Special Municipality Mayor (直轄市長) and
Councilor (直轄市議員) overview and candidate vote details into 4 UTF-8-SIG CSV files.
"""

from __future__ import annotations

import csv
import html
import re
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

BASE_URL = "https://vote.nccu.edu.tw/cec/"
TARGET_YEARS = ("2014", "2018", "2022")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
REQUEST_DELAY_SEC = 0.15

OVERVIEW_FIELDS = [
    "人口數",
    "選舉人數",
    "候選人數_計",
    "候選人數_男",
    "候選人數_女",
    "當選人數_計",
    "當選人數_男",
    "當選人數_女",
    "投票數_合計",
    "投票數_有效票數",
    "投票數_無效票數",
    "選舉人數對人口數",
    "投票數對選舉人數",
    "當選人數對候選人數",
]

CANDIDATE_FIELDS = [
    "姓名",
    "號次",
    "性別",
    "出生年次",
    "推薦政黨",
    "得票數",
    "得票率",
    "當選否",
    "是否現任",
]


class TableParser(HTMLParser):
    """Lightweight HTML table parser extracting (text, links) per cell."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[tuple[str, list[str]]]]] = []
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._cur_table: list[list[tuple[str, list[str]]]] = []
        self._cur_row: list[tuple[str, list[str]]] = []
        self._cur_text: list[str] = []
        self._cur_links: list[str] = []
        self._cur_link: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_d = dict(attrs)
        if tag == "table":
            self._in_table = True
            self._cur_table = []
        elif tag == "tr" and self._in_table:
            self._in_row = True
            self._cur_row = []
        elif tag in ("td", "th") and self._in_row:
            self._in_cell = True
            self._cur_text = []
            self._cur_links = []
        elif tag == "a" and self._in_cell:
            self._cur_link = attrs_d.get("href") or ""

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a" and self._in_cell and self._cur_link is not None:
            self._cur_links.append(self._cur_link)
            self._cur_link = None
        elif tag in ("td", "th") and self._in_cell:
            text = re.sub(r"\s+", " ", html.unescape("".join(self._cur_text))).strip()
            self._cur_row.append((text, self._cur_links))
            self._in_cell = False
        elif tag == "tr" and self._in_row:
            if self._cur_row:
                self._cur_table.append(self._cur_row)
            self._in_row = False
        elif tag == "table" and self._in_table:
            if self._cur_table:
                self.tables.append(self._cur_table)
            self._in_table = False

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cur_text.append(data)


def fetch_tables(url: str, retries: int = 3) -> list[list[list[tuple[str, list[str]]]]]:
    """Fetch a page relative to BASE_URL and parse all HTML tables."""
    full_url = urljoin(BASE_URL, url)
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            time.sleep(REQUEST_DELAY_SEC)
            req = urllib.request.Request(full_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read()
                charset = resp.headers.get_content_charset() or "utf-8"
                text = raw.decode(charset, errors="replace")
            parser = TableParser()
            parser.feed(text)
            return parser.tables
        except (urllib.error.URLError, TimeoutError) as exc:
            last_err = exc
            time.sleep(0.5 * attempt)
    raise RuntimeError(f"Failed to fetch {full_url}: {last_err}")


def get_election_links(election_code: str) -> dict[str, tuple[str, str]]:
    """Return {year: (overview_url, candidates_url)} for TARGET_YEARS."""
    tables = fetch_tables(f"ceclist.asp?t={election_code}")
    links: dict[str, tuple[str, str]] = {}
    for row in tables[-1]:
        if len(row) >= 4 and row[0][0] in TARGET_YEARS:
            year = row[0][0]
            ov_links = row[2][1]
            ca_links = row[3][1]
            if ov_links and ca_links:
                links[year] = (ov_links[0], ca_links[0])
    return links


def extract_overview_rows(tables: list[list[list[tuple[str, list[str]]]]]) -> list[list[tuple[str, list[str]]]]:
    """Extract 15-column overview data rows from parsed tables."""
    rows = []
    for table in tables:
        for row in table:
            if len(row) == 15 and row[0][0] not in ("地區別", "計", ""):
                rows.append(row)
    return rows


def extract_candidate_rows(tables: list[list[list[tuple[str, list[str]]]]]) -> list[list[tuple[str, list[str]]]]:
    """Extract 10-column candidate data rows from parsed tables."""
    rows = []
    for table in tables:
        for row in table:
            if len(row) == 10 and row[0][0] not in ("地區", "地區別", ""):
                rows.append(row)
    return rows


def scrape_mayor(mayor_links: dict[str, tuple[str, str]]) -> tuple[list[list[str]], list[list[str]]]:
    """Scrape mayor overview and candidate rows across TARGET_YEARS."""
    overview_out: list[list[str]] = []
    candidates_out: list[list[str]] = []

    for year in sorted(mayor_links):
        ov_url, ca_url = mayor_links[year]
        print(f"[直轄市長] {year} 選舉概況表...")
        for row in extract_overview_rows(fetch_tables(ov_url)):
            overview_out.append([year] + [cell[0] for cell in row])

        print(f"[直轄市長] {year} 候選人得票明細...")
        for row in extract_candidate_rows(fetch_tables(ca_url)):
            candidates_out.append([year] + [cell[0] for cell in row])

    return overview_out, candidates_out


def first_link(row: list[tuple[str, list[str]]]) -> str | None:
    """Return the first href found in any cell of a table row."""
    return next((cell[1][0] for cell in row if cell[1]), None)


def scrape_councilor(councilor_links: dict[str, tuple[str, str]]) -> tuple[list[list[str]], list[list[str]]]:
    """Scrape councilor overview and candidate rows (constituency level) across TARGET_YEARS."""
    overview_out: list[list[str]] = []
    candidates_out: list[list[str]] = []

    for year in sorted(councilor_links):
        ov_url, ca_url = councilor_links[year]

        # 1. Councilor overview: city -> type -> (optional) constituency
        print(f"[直轄市議員] {year} 選舉概況表...")
        for city_row in extract_overview_rows(fetch_tables(ov_url)):
            city_name = city_row[0][0]
            city_link = first_link(city_row)
            if not city_link:
                continue
            for type_row in extract_overview_rows(fetch_tables(city_link)):
                type_name = type_row[0][0]
                type_link = first_link(type_row)
                if type_link:
                    for const_row in extract_overview_rows(fetch_tables(type_link)):
                        const_name = const_row[0][0]
                        overview_out.append(
                            [year, city_name, type_name, const_name] + [c[0] for c in const_row[1:]]
                        )
                else:
                    overview_out.append(
                        [year, city_name, type_name, type_name] + [c[0] for c in type_row[1:]]
                    )

        # 2. Councilor candidates: city selector -> type selector -> candidate rows
        print(f"[直轄市議員] {year} 候選人得票明細...")
        city_tables = fetch_tables(ca_url)
        for row in city_tables[-1]:
            city_ca_url = first_link(row)
            if len(row) >= 2 and row[0][0] == year and city_ca_url:
                city_name = row[1][0]
                type_tables = fetch_tables(city_ca_url)
                for trow in type_tables[-1]:
                    type_ca_url = first_link(trow)
                    if len(trow) >= 2 and trow[0][0] == year and type_ca_url:
                        type_name = trow[1][0]
                        for cand_row in extract_candidate_rows(fetch_tables(type_ca_url)):
                            const_name = cand_row[0][0]
                            candidates_out.append(
                                [year, city_name, type_name, const_name] + [c[0] for c in cand_row[1:]]
                            )

    return overview_out, candidates_out


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    """Write rows to a UTF-8 with BOM CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows -> {path}")


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "output"

    mayor_links = get_election_links("DM")
    councilor_links = get_election_links("EM")

    mayor_ov, mayor_ca = scrape_mayor(mayor_links)
    councilor_ov, councilor_ca = scrape_councilor(councilor_links)

    write_csv(out_dir / "mayor_overview.csv", ["年度", "直轄市"] + OVERVIEW_FIELDS, mayor_ov)
    write_csv(out_dir / "mayor_candidates.csv", ["年度", "直轄市"] + CANDIDATE_FIELDS, mayor_ca)
    write_csv(
        out_dir / "councilor_overview.csv",
        ["年度", "直轄市", "選區類型", "選區"] + OVERVIEW_FIELDS,
        councilor_ov,
    )
    write_csv(
        out_dir / "councilor_candidates.csv",
        ["年度", "直轄市", "選區類型", "選區"] + CANDIDATE_FIELDS,
        councilor_ca,
    )


if __name__ == "__main__":
    main()
