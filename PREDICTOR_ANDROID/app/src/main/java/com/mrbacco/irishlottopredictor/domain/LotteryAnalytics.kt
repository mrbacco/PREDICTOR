// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor.domain

import com.mrbacco.irishlottopredictor.core.BacLog
import com.mrbacco.irishlottopredictor.core.PredictorConfig

/**
 * Pure historical analysis operations used by both predictions and dashboard summaries.
 */
object LotteryAnalytics {
    fun buildFrequency(draws: List<LottoDraw>): IntArray {
        BacLog.debug("Building number frequency table", "analytics", "draw_count" to draws.size)
        val frequency = IntArray(PredictorConfig.NUMBER_MAX + 1)
        draws.forEach { draw -> draw.numbers.forEach { frequency[it] += 1 } }
        return frequency
    }

    fun buildBonusFrequency(draws: List<LottoDraw>): IntArray {
        val frequency = IntArray(PredictorConfig.NUMBER_MAX + 1)
        draws.mapNotNull(LottoDraw::bonus).forEach { frequency[it] += 1 }
        return frequency
    }

    /**
     * Pair keys are encoded as `first * 100 + second`; the number range makes this
     * collision-free while avoiding thousands of temporary pair objects.
     */
    fun buildPairFrequency(draws: List<LottoDraw>): Map<Int, Int> {
        val frequency = mutableMapOf<Int, Int>()
        draws.forEach { draw ->
            for (firstIndex in 0 until draw.numbers.lastIndex) {
                for (secondIndex in firstIndex + 1 until draw.numbers.size) {
                    val key = pairKey(draw.numbers[firstIndex], draw.numbers[secondIndex])
                    frequency[key] = frequency.getOrDefault(key, 0) + 1
                }
            }
        }
        BacLog.debug("Pair frequency table ready", "analytics", "pair_count" to frequency.size)
        return frequency
    }

    fun buildOverdue(draws: List<LottoDraw>): IntArray {
        val unseenDistance = draws.size
        val overdue = IntArray(PredictorConfig.NUMBER_MAX + 1) { unseenDistance }

        // The first hit in reverse order is the number's most recent appearance.
        draws.asReversed().forEachIndexed { distance, draw ->
            draw.numbers.forEach { number ->
                if (overdue[number] == unseenDistance) overdue[number] = distance
            }
        }
        return overdue
    }

    fun calculateNumberScores(frequency: IntArray, overdue: IntArray): DoubleArray {
        val range = PredictorConfig.NUMBER_MIN..PredictorConfig.NUMBER_MAX
        val frequencyValues = range.map { frequency[it] }
        val overdueValues = range.map { overdue[it] }
        val scores = DoubleArray(PredictorConfig.NUMBER_MAX + 1)

        range.forEach { number ->
            val hotScore = minMax(frequency[number], frequencyValues)
            val coldScore = minMax(overdue[number], overdueValues)
            var score = hotScore * 0.6 + coldScore * 0.4
            if (number > 31) score *= 1.05
            scores[number] = score + 0.01
        }

        val highest = range.sortedByDescending { scores[it] }.take(6)
        BacLog.info("Number weights ready", "analytics", "highest_weighted" to highest)
        return scores
    }

    fun summarize(draws: List<LottoDraw>): DatasetSummary {
        if (draws.isEmpty()) return DatasetSummary.Empty

        val frequency = buildFrequency(draws)
        val latestDraw = draws.last()
        val hottest = (PredictorConfig.NUMBER_MIN..PredictorConfig.NUMBER_MAX)
            .sortedWith(compareByDescending<Int> { frequency[it] }.thenBy { it })
            .take(6)

        return DatasetSummary(
            totalDraws = draws.size,
            earliestDrawDate = draws.first().drawDate,
            latestDrawDate = latestDraw.drawDate,
            latestDrawNumbers = latestDraw.numbers,
            hottestNumbers = hottest,
            uniqueNumbersSeen = frequency.count { it > 0 },
        )
    }

    fun pairKey(first: Int, second: Int): Int = first * 100 + second

    private fun minMax(value: Int, values: List<Int>): Double {
        val low = values.min()
        val high = values.max()
        return if (low == high) 0.0 else (value - low).toDouble() / (high - low)
    }
}
