
#####################
# 
# mrbacco04@gmail.com 
# copyright 2026 onwards
# number predictor 
# 
#####################

import csv
import datetime as dt
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

# Source page for Lotto history data.
URL = "https://www.lottery.ie/results/lotto/history"
# Output file consumed by app.py.
CSV_FILE = "irish_lotto_results.csv"

# define the logger
def bac_log(message: str) -> None:
    # Uniform log prefix for easier terminal scanning.
    print(f"BAC_LOG: {message}")

# fetching data from the website and writing to csv file
def fetch_html(url: str) -> str:
    # Browser-like headers reduce risk of blocked non-browser requests.
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        },
    )
    with urlopen(req, timeout=30) as response:
        status = getattr(response, "status", 200)
        if status != 200:
            raise RuntimeError(f"Unexpected HTTP status: {status}")
        # Decode safely so a few malformed characters do not crash parsing.
        return response.read().decode("utf-8", errors="replace")

# extract the embedded JSON data from the HTML page
def extract_next_data_json(raw_html: str) -> dict:
    # Next.js embeds the page state in __NEXT_DATA__; this is the most stable source.
    script_match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">([\s\S]*?)</script>',
        raw_html,
        flags=re.IGNORECASE,
    )
    if not script_match:
        raise RuntimeError("Could not locate __NEXT_DATA__ payload in page HTML.")

    payload = script_match.group(1)
    return json.loads(payload)


def parse_lotto_rows_from_next_data(next_data: dict) -> list[dict[str, int | str]]:
    # Draw entries for this page are nested under props.pageProps.list.
    page_props = next_data.get("props", {}).get("pageProps", {})
    entries = page_props.get("list", [])

    rows: list[dict[str, int | str]] = []
    for entry in entries:
        # "standard" holds the base Lotto game for each date.
        standard = entry.get("standard", {})
        grids = standard.get("grids", [])
        draw_dates = standard.get("drawDates", [])

        if not grids or not draw_dates:
            continue

        first_grid = grids[0] if grids else {}
        standard_lines = first_grid.get("standard", [])
        additional_lines = first_grid.get("additional", [])

        if not standard_lines or len(standard_lines[0]) != 6:
            continue

        numbers = [int(x) for x in standard_lines[0]]
        # Bonus can be missing in edge cases; keep empty string when absent.
        bonus = int(additional_lines[0][0]) if additional_lines and additional_lines[0] else ""
        draw_date = dt.datetime.fromisoformat(draw_dates[0].replace("Z", "+00:00")).date().isoformat()

        row: dict[str, int | str] = {
            "draw_date": draw_date,
            "n1": numbers[0],
            "n2": numbers[1],
            "n3": numbers[2],
            "n4": numbers[3],
            "n5": numbers[4],
            "n6": numbers[5],
            "bonus": bonus,
        }
        rows.append(row)

    # Deduplicate by date while preserving the first parsed draw for each date.
    deduped: list[dict[str, int | str]] = []
    seen_dates: set[str] = set()

    for row in rows:
        draw_date = str(row["draw_date"])
        if draw_date in seen_dates:
            continue
        seen_dates.add(draw_date)
        deduped.append(row)

    deduped.sort(key=lambda r: str(r["draw_date"]))
    return deduped


def write_csv(rows: list[dict[str, int | str]], output_path: Path) -> None:
    # Keep column order aligned with predictor expectations.
    fieldnames = ["draw_date", "n1", "n2", "n3", "n4", "n5", "n6", "bonus"]
    with output_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    bac_log(f"Fetching lotto history from {URL}")
    raw_html = fetch_html(URL)
    bac_log("Page fetched successfully: HTTP 200")

    bac_log("Extracting embedded __NEXT_DATA__ payload")
    next_data = extract_next_data_json(raw_html)

    bac_log("Parsing Lotto draw rows from payload")
    rows = parse_lotto_rows_from_next_data(next_data)
    if not rows:
        raise RuntimeError(
            "No Lotto rows parsed from __NEXT_DATA__. The website payload may have changed."
        )

    output_path = Path(__file__).resolve().parent / CSV_FILE
    bac_log(f"Writing {len(rows)} rows to {output_path.name}")
    write_csv(rows, output_path)

    bac_log("CSV population complete")

if __name__ == "__main__":
    main()
