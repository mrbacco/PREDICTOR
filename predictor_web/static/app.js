//
// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

// Cache the fixed dashboard elements once instead of querying on every render.
const dom = {
    statusMessage: document.querySelector("#status-message"),
    predictionMeta: document.querySelector("#prediction-meta"),
    totalDraws: document.querySelector("#total-draws"),
    historyWindow: document.querySelector("#history-window"),
    latestDraw: document.querySelector("#latest-draw"),
    hotNumbers: document.querySelector("#hot-numbers"),
    drawsTableBody: document.querySelector("#draws-table-body"),
    predictionsList: document.querySelector("#predictions-list"),
    predictionForm: document.querySelector("#prediction-form"),
    generateButton: document.querySelector("#generate-button"),
    refreshButton: document.querySelector("#refresh-button"),
    topK: document.querySelector("#top-k"),
    iterations: document.querySelector("#iterations"),
    seed: document.querySelector("#seed"),
};

// All API calls share consistent JSON parsing and error handling.
async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    const payload = await response.json();

    if (!response.ok) {
        throw new Error(payload.error || "Request failed.");
    }

    return payload;
}

// Summary values are intentionally rendered as text to avoid HTML injection.
function renderSummary(summary) {
    dom.totalDraws.textContent = summary.total_draws;
    dom.historyWindow.textContent = summary.earliest_draw_date && summary.latest_draw_date
        ? `${summary.earliest_draw_date} to ${summary.latest_draw_date}`
        : "No data";
    dom.latestDraw.textContent = summary.latest_draw_numbers.length
        ? summary.latest_draw_numbers.join(" - ")
        : "No data";
    dom.hotNumbers.textContent = summary.hottest_numbers.length
        ? summary.hottest_numbers.join(", ")
        : "No data";
}

// Draw rows come from the validated repository API.
function renderDraws(draws) {
    if (!draws.length) {
        dom.drawsTableBody.innerHTML = "<tr><td colspan='3'>No draw rows available.</td></tr>";
        return;
    }

    dom.drawsTableBody.innerHTML = draws.map((draw) => `
        <tr>
            <td>${draw.draw_date}</td>
            <td>${draw.numbers.join(" - ")}</td>
            <td>${draw.bonus ?? "-"}</td>
        </tr>
    `).join("");
}

// Prediction rendering verifies the backend schema before building any cards.
function renderPredictions(report) {
    if (!report.lines.length) {
        dom.predictionsList.innerHTML = `
            <article class="prediction-card empty-state">
                <p>No prediction lines were generated.</p>
            </article>
        `;
        return;
    }

    // An old Python process may serve a stale schema after frontend files change.
    const invalidLine = report.lines.find((line) => (
        !Number.isInteger(line.bonus)
        || line.bonus < 1
        || line.bonus > 47
        || line.numbers.includes(line.bonus)
    ));
    if (invalidLine) {
        throw new Error(
            "The prediction server is outdated. Restart the Python app and generate again."
        );
    }

    // The API supplies numeric values only; cards keep the result compact and scannable.
    dom.predictionsList.innerHTML = report.lines.map((line) => `
        <article class="prediction-card">
            <h3>Rank ${line.rank}</h3>
            <p class="ticket-line">${line.numbers.join(" - ")}</p>
            <p class="ticket-bonus">Bonus <strong>${line.bonus}</strong></p>
            <p class="ticket-score">Score: ${line.score.toFixed(2)}</p>
        </article>
    `).join("");

    dom.predictionMeta.textContent =
        `Generated ${report.lines.length} lines from ${report.candidate_count} valid candidates using `
        + `${report.iterations.toLocaleString()} iterations and seed ${report.random_seed}.`;
}

// Load independent dashboard resources concurrently for a faster first render.
async function loadDashboard() {
    dom.statusMessage.textContent = "Loading dashboard data...";

    try {
        const [summary, drawsResponse] = await Promise.all([
            fetchJson("/api/summary"),
            fetchJson("/api/draws?limit=12"),
        ]);

        renderSummary(summary);
        renderDraws(drawsResponse.items);
        dom.statusMessage.textContent = "Dashboard ready.";
    } catch (error) {
        dom.statusMessage.textContent = error.message;
    }
}

// Translate form values into the query parameters accepted by the prediction API.
async function handlePredictionSubmit(event) {
    event.preventDefault();
    dom.generateButton.disabled = true;
    dom.predictionMeta.textContent = "Generating ranked lines...";

    const query = new URLSearchParams({
        top_k: dom.topK.value,
        iterations: dom.iterations.value,
        seed: dom.seed.value,
    });

    try {
        const report = await fetchJson(`/api/predictions?${query.toString()}`);
        renderPredictions(report);
        dom.statusMessage.textContent = "Prediction run completed.";
    } catch (error) {
        dom.predictionMeta.textContent = error.message;
    } finally {
        dom.generateButton.disabled = false;
    }
}

// Remote refresh is explicit because it replaces the local CSV repository contents.
async function handleRefreshClick() {
    dom.refreshButton.disabled = true;
    dom.statusMessage.textContent = "Refreshing remote lotto dataset...";

    try {
        const result = await fetchJson("/api/refresh-data", { method: "POST" });
        dom.statusMessage.textContent =
            `Dataset refreshed with ${result.rows_written} rows. Latest draw: ${result.latest_draw_date}.`;
        await loadDashboard();
    } catch (error) {
        dom.statusMessage.textContent = error.message;
    } finally {
        dom.refreshButton.disabled = false;
    }
}

// Attach behavior after the static document has defined all target elements.
dom.predictionForm.addEventListener("submit", handlePredictionSubmit);
dom.refreshButton.addEventListener("click", handleRefreshClick);
loadDashboard();
