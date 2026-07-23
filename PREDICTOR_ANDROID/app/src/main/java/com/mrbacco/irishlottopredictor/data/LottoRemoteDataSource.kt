// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor.data

import com.mrbacco.irishlottopredictor.core.BacLog
import com.mrbacco.irishlottopredictor.core.PredictorConfig
import com.mrbacco.irishlottopredictor.domain.LottoDraw
import java.net.HttpURLConnection
import java.net.URL
import java.time.LocalDate
import org.json.JSONObject

/**
 * Downloads and parses the public Irish National Lottery history page.
 */
class LottoRemoteDataSource(
    private val sourceUrl: String = PredictorConfig.SOURCE_URL,
) {
    fun fetchDraws(): List<LottoDraw> {
        BacLog.info("Fetching remote Lotto history", "remote", "source_url" to sourceUrl)
        val connection = (URL(sourceUrl).openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = PredictorConfig.REQUEST_TIMEOUT_MILLIS
            readTimeout = PredictorConfig.REQUEST_TIMEOUT_MILLIS
            instanceFollowRedirects = true
            setRequestProperty(
                "User-Agent",
                "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36",
            )
        }

        try {
            val status = connection.responseCode
            if (status != HttpURLConnection.HTTP_OK) {
                error("The history server returned HTTP $status.")
            }
            val html = connection.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
            BacLog.info(
                "Remote history downloaded",
                "remote",
                "characters_received" to html.length,
                "http_status" to status,
            )
            return parseHistoryPage(html)
        } finally {
            connection.disconnect()
        }
    }

    fun parseHistoryPage(html: String): List<LottoDraw> {
        val match = NEXT_DATA_PATTERN.find(html)
            ?: error("The Lottery page no longer contains its expected data payload.")
        return parseNextData(JSONObject(match.groupValues[1]))
    }

    fun parseNextData(root: JSONObject): List<LottoDraw> {
        val entries = root
            .getJSONObject("props")
            .getJSONObject("pageProps")
            .getJSONArray("list")
        val drawsByDate = linkedMapOf<LocalDate, LottoDraw>()
        var skippedEntries = 0

        for (index in 0 until entries.length()) {
            try {
                val standard = entries.getJSONObject(index).getJSONObject("standard")
                val firstGrid = standard.getJSONArray("grids").getJSONObject(0)
                val mainNumbers = firstGrid
                    .getJSONArray("standard")
                    .getJSONArray(0)
                    .toIntList()
                    .sorted()
                require(mainNumbers.size == PredictorConfig.PICKS_PER_LINE)
                require(mainNumbers.distinct().size == PredictorConfig.PICKS_PER_LINE)
                require(mainNumbers.all {
                    it in PredictorConfig.NUMBER_MIN..PredictorConfig.NUMBER_MAX
                })

                val additional = firstGrid.optJSONArray("additional")
                val bonusText = additional
                    ?.optJSONArray(0)
                    ?.optString(0)
                    ?.trim()
                    .orEmpty()
                val dateText = standard.getJSONArray("drawDates").getString(0)
                val bonus = bonusText.takeIf(String::isNotEmpty)?.toInt()
                require(bonus == null || bonus in PredictorConfig.NUMBER_MIN..PredictorConfig.NUMBER_MAX)
                require(bonus == null || bonus !in mainNumbers)
                val draw = LottoDraw(
                    drawDate = LocalDate.parse(dateText.take(10)),
                    numbers = mainNumbers,
                    bonus = bonus,
                )
                drawsByDate.putIfAbsent(draw.drawDate, draw)
            } catch (exception: Exception) {
                skippedEntries += 1
                BacLog.warning(
                    "Skipping unsupported remote history entry",
                    "remote",
                    "entry" to index,
                    "reason" to (exception.message ?: exception.javaClass.simpleName),
                )
            }
        }

        val draws = drawsByDate.values.sortedBy(LottoDraw::drawDate)
        check(draws.isNotEmpty()) {
            "No Lotto draws could be parsed; the Lottery page structure may have changed."
        }
        BacLog.info(
            "Remote history parsed",
            "remote",
            "draw_count" to draws.size,
            "skipped_entries" to skippedEntries,
        )
        return draws
    }

    private fun org.json.JSONArray.toIntList(): List<Int> =
        (0 until length()).map { getInt(it) }

    private companion object {
        val NEXT_DATA_PATTERN = Regex(
            """<script[^>]*id=["']__NEXT_DATA__["'][^>]*>([\s\S]*?)</script>""",
            RegexOption.IGNORE_CASE,
        )
    }
}
