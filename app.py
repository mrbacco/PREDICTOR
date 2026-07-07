
#####################
# 
# mrbacco04@gmail.com 
# copyright 2026 onwards
# number predictor 
# 
#####################

import csv
import random
from pathlib import Path
from collections import Counter
from itertools import combinations

# Main dataset consumed by predictor and produced by scraper.
CSV_FILE = "irish_lotto_results.csv"


def bac_log(message):
    # Standardized terminal log prefix for easy filtering.
    print(f"BAC_LOG: {message}")

# -------------------------
# Load data
# -------------------------

bac_log("Loading CSV data")
# Predictor expects exactly these six columns for each draw.
number_cols = ["n1", "n2", "n3", "n4", "n5", "n6"]
bac_log(f"Using number columns: {number_cols}")

csv_path = Path(CSV_FILE)
# Fail fast with a clear message if scraper output is missing.
if not csv_path.exists():
    raise FileNotFoundError(
        f"CSV file not found: {CSV_FILE}. Run scrape_irish_lotto.py first to generate it."
    )

draws = []
with csv_path.open("r", newline="", encoding="utf-8") as fp:
    reader = csv.DictReader(fp)
    for row in reader:
        # Keep each historical draw as six integers.
        draws.append([int(row[col]) for col in number_cols])

bac_log(f"CSV loaded with {len(draws)} rows")
bac_log(f"Prepared draws list with {len(draws)} entries")


# -------------------------
# Frequency analysis
# -------------------------
bac_log("Starting frequency analysis")
freq = Counter()

for draw in draws:
    freq.update(draw)

bac_log(f"Frequency analysis complete with {len(freq)} unique numbers")


# -------------------------
# Pair analysis
# -------------------------
bac_log("Starting pair analysis")
pair_freq = Counter()

for draw in draws:
    # Pair frequencies capture number co-occurrence strength.
    for pair in combinations(sorted(draw), 2):
        pair_freq[pair] += 1

bac_log(f"Pair analysis complete with {len(pair_freq)} unique pairs")


# -------------------------
# Overdue analysis
# -------------------------
bac_log("Starting overdue analysis")
last_seen = {n: 999 for n in range(1, 48)}

for idx, draw in enumerate(reversed(draws)):
    # Reverse iteration makes idx represent "draws since last seen".
    for num in draw:
        if last_seen[num] == 999:
            last_seen[num] = idx

bac_log("Overdue analysis complete")


# -------------------------
# Weight score
# -------------------------
bac_log("Calculating number scores")
scores = {}

for num in range(1, 48):
    hot = freq[num]
    cold = last_seen[num]

    # Blend hot and overdue behavior into one weight.
    score = hot * 0.6 + cold * 0.4

    # bonus for >31 to avoid birthday-heavy lines
    if num > 31:
        score *= 1.05

    scores[num] = score

bac_log(f"Score calculation complete for {len(scores)} numbers")

# -------------------------
# Weighted random draw
# -------------------------
def weighted_pick():
    # Build population and probability weights once per ticket.
    population = list(scores.keys())
    weights = [scores[n] for n in population]

    selected = set()

    while len(selected) < 6:
        # Keep sampling until we have six unique values.
        pick = random.choices(population, weights=weights, k=1)[0]
        selected.add(pick)

    return sorted(selected)

# -------------------------
# Pattern filter
# -------------------------
def valid_line(line):

    # Rules are simple heuristics to avoid common weak patterns.

    # Avoid too many low numbers
    low_count = sum(1 for x in line if x <= 31)
    if low_count > 4:
        return False

    # Odd/even balance
    odd = sum(1 for x in line if x % 2)
    if odd < 2 or odd > 4:
        return False

    # Avoid consecutive numbers
    consecutive = 0
    for i in range(5):
        if line[i+1] - line[i] == 1:
            consecutive += 1

    if consecutive >= 2:
        return False

    return True

# -------------------------
# Score ticket by pair strength
# -------------------------
def score_ticket(line):
    # Start from individual number strengths.
    score = 0

    for n in line:
        score += scores[n]

    for pair in combinations(line, 2):
        # Reward historically common pairs more heavily.
        score += pair_freq[pair] * 2

    return score

# -------------------------
# Monte Carlo generation
# -------------------------
bac_log("Starting Monte Carlo generation")
candidates = []

iterations = 50000
bac_log(f"Configured iterations: {iterations}")

for idx in range(iterations):
    ticket = weighted_pick()

    if valid_line(ticket):
        ticket_score = score_ticket(ticket)
        candidates.append((ticket_score, ticket))

    # Progress heartbeat for long Monte Carlo runs.
    if (idx + 1) % 10000 == 0:
        bac_log(f"Monte Carlo progress: {idx + 1}/{iterations}")

candidates.sort(reverse=True)
bac_log(f"Monte Carlo complete with {len(candidates)} valid candidates")

# Remove duplicates
seen = set()
best = []
bac_log("Removing duplicate tickets and selecting top 0")

for score, ticket in candidates:
    t = tuple(ticket)

    # Keep first occurrence of each ticket after score sort.
    if t not in seen:
        seen.add(t)
        best.append((score, ticket))

    if len(best) == 10:
        break

bac_log(f"Final ticket set prepared with {len(best)} lines")

# -------------------------
# Output
# -------------------------
bac_log("Printing final optimized lines")
print("\nTop 20 Optimized Lines:\n")

for i, (score, ticket) in enumerate(best, 1):
    print(f"{i:02d}. {ticket}   score={score:.2f}")