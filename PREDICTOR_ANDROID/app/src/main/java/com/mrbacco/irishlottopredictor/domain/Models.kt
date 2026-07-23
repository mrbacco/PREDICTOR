// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor.domain

import java.time.Instant
import java.time.LocalDate

/** One validated historical Irish Lotto draw. */
data class LottoDraw(
    val drawDate: LocalDate,
    val numbers: List<Int>,
    val bonus: Int?,
)

/** One ranked prediction with a bonus that is distinct from its six main numbers. */
data class PredictionLine(
    val rank: Int,
    val numbers: List<Int>,
    val bonus: Int,
    val score: Double,
)

/** Complete output and reproducibility metadata for one prediction run. */
data class PredictionReport(
    val lines: List<PredictionLine>,
    val iterations: Int,
    val topK: Int,
    val randomSeed: Long,
    val candidateCount: Int,
    val generatedAt: Instant,
)

/** Compact historical statistics displayed above the prediction controls. */
data class DatasetSummary(
    val totalDraws: Int,
    val earliestDrawDate: LocalDate?,
    val latestDrawDate: LocalDate?,
    val latestDrawNumbers: List<Int>,
    val hottestNumbers: List<Int>,
    val uniqueNumbersSeen: Int,
) {
    companion object {
        val Empty = DatasetSummary(
            totalDraws = 0,
            earliestDrawDate = null,
            latestDrawDate = null,
            latestDrawNumbers = emptyList(),
            hottestNumbers = emptyList(),
            uniqueNumbersSeen = 0,
        )
    }
}
