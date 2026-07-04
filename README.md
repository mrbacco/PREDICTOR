# Irish Lotto Predictor

A Python project that:

- Scrapes historical Irish Lotto draw data from lottery.ie
- Saves normalized results to CSV
- Runs a weighted Monte Carlo ticket generator
- Ranks and prints the top 20 candidate lines

## What This App Does

This repo contains two scripts:

- `scrape_irish_lotto.py`: downloads and parses Irish Lotto history data, then writes `irish_lotto_results.csv`
- `app.py`: reads the CSV and generates optimized ticket lines using frequency, pair, and overdue heuristics

### 1) Data Collection (Scraper)

The scraper:

- Requests https://www.lottery.ie/results/lotto/history with browser-like headers
- Extracts embedded `__NEXT_DATA__` JSON from the page
- Reads the Lotto draw list from `props.pageProps.list`
- Parses:
  - draw date
  - six main numbers (`n1`..`n6`)
  - bonus number (`bonus`, when present)
- Deduplicates rows by `draw_date`
- Sorts by date ascending
- Writes `irish_lotto_results.csv` with schema:

```csv
draw_date,n1,n2,n3,n4,n5,n6,bonus
```

### 2) Prediction Engine

The predictor in `app.py` uses the CSV to build candidate lines.

#### Inputs

- File: `irish_lotto_results.csv`
- Required columns consumed by predictor: `n1,n2,n3,n4,n5,n6`

#### Analysis Steps

1. Frequency analysis
- Counts how often each number (1..47) appears.

2. Pair analysis
- Counts co-occurrence frequency for every 2-number combination from historical draws.

3. Overdue analysis
- Tracks how many draws since each number last appeared.

4. Score calculation
- Number score formula:
  - `score = hot * 0.6 + cold * 0.4`
  - where `hot = frequency`, `cold = overdue distance`
- Applies a small bonus to numbers > 31:
  - `score *= 1.05`

5. Weighted random ticket generation
- Uses weighted random sampling based on number scores
- Ensures each ticket contains 6 unique numbers

6. Pattern filter (`valid_line`)
- Rejects lines with:
  - more than 4 numbers <= 31
  - odd count outside 2..4
  - 2 or more consecutive adjacent pairs

7. Ticket scoring (`score_ticket`)
- Adds individual number scores
- Adds pair strength bonus (`pair_freq[pair] * 2` for each pair in the line)

8. Monte Carlo search
- Runs 50,000 iterations
- Keeps valid lines and their scores
- Sorts by score descending
- Removes duplicate tickets
- Outputs top 20 unique lines

## Requirements

- Python 3.10+
- Standard library only (no third-party packages required)

## How To Run

From the project root:

1. Refresh data:

```powershell
python scrape_irish_lotto.py
```

2. Generate top lines:

```powershell
python app.py
```

## Example Output

```text
Top 20 Optimized Lines:

01. [.., .., .., .., .., ..]   score=...
...
20. [.., .., .., .., .., ..]   score=...
```

## Logging

Both scripts use prefixed logs for traceability:

- `BAC_LOG: ...`

This makes terminal output easy to scan and filter.

## Project Structure

```text
.
|-- app.py
|-- scrape_irish_lotto.py
|-- irish_lotto_results.csv
|-- README.md
|-- LICENSE-APACHE
|-- LICENSE-AGPL
|-- COMMERCIAL-LICENSE.md
```

## Notes

- This is a heuristic number-line generator for experimentation.
- Lottery draws are random; no method can guarantee winning results.
- Re-run the scraper before predictions to keep the dataset fresh.

## Licensing

This repository is set up with multiple licensing paths depending on use case:

1. Portfolio management, demos, and non-production/open usage
- Apache License 2.0: see `LICENSE-APACHE`

2. Serious commercial product use with open-source obligations
- GNU AGPL v3: see `LICENSE-AGPL`

3. Serious commercial product use without AGPL copyleft obligations
- Commercial license under a separate agreement: see `COMMERCIAL-LICENSE.md`

For commercial licensing requests, contact mrbacco04@gmail.com.

## Copyright

- Copyright 2026 onwards
- Contact: mrbacco04@gmail.com
