// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor.data

import com.mrbacco.irishlottopredictor.core.BacLog
import com.mrbacco.irishlottopredictor.core.PredictorConfig
import com.mrbacco.irishlottopredictor.domain.LottoDraw
import java.time.LocalDate

/**
 * Converts between the portable project CSV format and validated domain records.
 */
object DrawCsvCodec {
    private val numberColumns = (1..PredictorConfig.PICKS_PER_LINE).map { "n$it" }

    fun decode(csvText: String): List<LottoDraw> {
        val dataLines = csvText.lineSequence()
            .map(String::trim)
            .filter { it.isNotBlank() && !it.startsWith("#") }
            .toList()
        require(dataLines.isNotEmpty()) { "The draw history CSV is empty." }

        val header = splitRow(dataLines.first())
        val columnIndexes = header.withIndex().associate { it.value to it.index }
        val requiredColumns = listOf("draw_date", *numberColumns.toTypedArray(), "bonus")
        require(requiredColumns.all(columnIndexes::containsKey)) {
            "The draw history CSV does not contain the expected columns."
        }

        var skippedRows = 0
        val draws = dataLines.drop(1).mapIndexedNotNull { index, line ->
            try {
                val values = splitRow(line)
                fun value(column: String): String = values.getOrNull(columnIndexes.getValue(column))
                    ?: error("Missing value for $column")

                val numbers = numberColumns.map { value(it).toInt() }.sorted()
                val bonus = value("bonus").trim().takeIf(String::isNotEmpty)?.toInt()
                validateNumbers(numbers, bonus)
                LottoDraw(
                    drawDate = LocalDate.parse(value("draw_date")),
                    numbers = numbers,
                    bonus = bonus,
                )
            } catch (exception: Exception) {
                skippedRows += 1
                BacLog.warning(
                    "Skipping malformed CSV row",
                    "repository",
                    "row" to index + 2,
                    "reason" to (exception.message ?: exception.javaClass.simpleName),
                )
                null
            }
        }

        // Keep one record per date and order the result for overdue calculations.
        val sorted = draws
            .associateBy(LottoDraw::drawDate)
            .values
            .sortedBy(LottoDraw::drawDate)
        BacLog.info(
            "Draw history decoded",
            "repository",
            "loaded_rows" to sorted.size,
            "skipped_rows" to skippedRows,
        )
        return sorted
    }

    fun encode(draws: List<LottoDraw>): String = buildString {
        appendLine("# Author: mrbacco04@gmail.com")
        appendLine("# Month: July 2026")
        appendLine("# Release Version: 1.0.0")
        appendLine("# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial")
        appendLine("draw_date,n1,n2,n3,n4,n5,n6,bonus")
        draws.sortedBy(LottoDraw::drawDate).forEach { draw ->
            append(draw.drawDate)
            draw.numbers.forEach { append(',').append(it) }
            append(',').append(draw.bonus ?: "").appendLine()
        }
    }

    private fun validateNumbers(numbers: List<Int>, bonus: Int?) {
        require(numbers.size == PredictorConfig.PICKS_PER_LINE) { "A draw needs six numbers." }
        require(numbers.distinct().size == PredictorConfig.PICKS_PER_LINE) {
            "Main numbers must be unique."
        }
        require(numbers.all { it in PredictorConfig.NUMBER_MIN..PredictorConfig.NUMBER_MAX }) {
            "A main number is outside the supported range."
        }
        require(bonus == null || bonus in PredictorConfig.NUMBER_MIN..PredictorConfig.NUMBER_MAX) {
            "The bonus number is outside the supported range."
        }
        require(bonus == null || bonus !in numbers) {
            "The bonus number must be distinct from the main numbers."
        }
    }

    // The project dataset is deliberately plain CSV and does not contain quoted commas.
    private fun splitRow(row: String): List<String> = row.split(',').map(String::trim)
}
