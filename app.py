
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
NUMBER_MIN = 1
NUMBER_MAX = 47
PICKS_PER_LINE = 6
TOP_K = 20
ITERATIONS = 50000
# Set a fixed seed for reproducible runs; change this value to explore alternatives.
RANDOM_SEED = 20260712


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
skipped_rows = 0
with csv_path.open("r", newline="", encoding="utf-8") as fp:
    reader = csv.DictReader(fp)
    for row_idx, row in enumerate(reader, start=2):
        try:
            nums = [int(row[col]) for col in number_cols]
        except (TypeError, ValueError, KeyError):
            skipped_rows += 1
            bac_log(f"Skipping malformed row {row_idx}")
            continue

        # Ignore impossible rows that would corrupt frequency and pair stats.
        if len(set(nums)) != PICKS_PER_LINE or any(n < NUMBER_MIN or n > NUMBER_MAX for n in nums):
            skipped_rows += 1
            bac_log(f"Skipping invalid row {row_idx}: {nums}")
            continue

        # Keep each historical draw as six integers.
        draws.append(sorted(nums))

if len(draws) < 10:
    raise RuntimeError("Not enough valid historical draws to generate output. Refresh CSV data first.")
if len(draws) < 100:
    bac_log(
        f"Warning: only {len(draws)} valid draws loaded. Output stability improves with more history."
    )

bac_log(f"CSV loaded with {len(draws)} rows")
if skipped_rows:
    bac_log(f"Skipped {skipped_rows} malformed or invalid rows")
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

freq_values = [freq[n] for n in range(NUMBER_MIN, NUMBER_MAX + 1)]
last_seen_values = [last_seen[n] for n in range(NUMBER_MIN, NUMBER_MAX + 1)]

def minmax(value, values):
    low = min(values)
    high = max(values)
    if high == low:
        return 0.0
    return (value - low) / (high - low)

for num in range(NUMBER_MIN, NUMBER_MAX + 1):
    hot = freq[num]
    cold = last_seen[num]

    # Normalize components so no single metric dominates over time as data grows.
    hot_n = minmax(hot, freq_values)
    cold_n = minmax(cold, last_seen_values)

    # Blend hot and overdue behavior into one weight.
    score = hot_n * 0.6 + cold_n * 0.4

    # bonus for >31 to avoid birthday-heavy lines
    if num > 31:
        score *= 1.05

    # Keep all weights positive for robust weighted sampling.
    score += 0.01

    scores[num] = score

bac_log(f"Score calculation complete for {len(scores)} numbers")

# Deterministic RNG makes output repeatable for the same data and parameters.
rng = random.Random(RANDOM_SEED)
bac_log(f"Random seed set to {RANDOM_SEED}")

# -------------------------
# Weighted random draw
# -------------------------
def weighted_pick():
    # Weighted sample without replacement avoids duplicate re-roll bias.
    population = list(scores.keys())
    selected = []

    while len(selected) < PICKS_PER_LINE:
        weights = [scores[n] for n in population]
        pick = rng.choices(population, weights=weights, k=1)[0]
        selected.append(pick)
        population.remove(pick)

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
    score = 0.0

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

iterations = ITERATIONS
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

if not candidates:
    raise RuntimeError("No valid candidates generated. Relax filter rules or increase iterations.")

# Remove duplicates
seen = set()
best = []
bac_log(f"Removing duplicate tickets and selecting top {TOP_K}")

for score, ticket in candidates:
    t = tuple(ticket)

    # Keep first occurrence of each ticket after score sort.
    if t not in seen:
        seen.add(t)
        best.append((score, ticket))

    if len(best) == TOP_K:
        break

bac_log(f"Final ticket set prepared with {len(best)} lines")

# -------------------------
# Output
# -------------------------
bac_log("Printing final optimized lines")
print(f"\nTop {TOP_K} Optimized Lines:\n")

for i, (score, ticket) in enumerate(best, 1):
    print(f"{i:02d}. {ticket}   score={score:.2f}")