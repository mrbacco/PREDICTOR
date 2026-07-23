// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor.domain

import com.mrbacco.irishlottopredictor.core.BacLog
import com.mrbacco.irishlottopredictor.core.PredictorConfig
import java.time.Instant
import kotlin.math.round
import kotlin.random.Random

/**
 * Deterministic Monte Carlo engine ported from the Python web application.
 *
 * Supplying the same history, settings, and seed repeats an Android result. A new
 * seed explores a different deterministic sequence.
 */
class PredictorEngine {
    fun generate(
        draws: List<LottoDraw>,
        topK: Int = PredictorConfig.DEFAULT_TOP_K,
        iterations: Int = PredictorConfig.DEFAULT_ITERATIONS,
        randomSeed: Long,
        onProgress: (Int) -> Unit = {},
    ): PredictionReport {
        require(draws.size >= PredictorConfig.MIN_HISTORY_REQUIRED) {
            "At least ${PredictorConfig.MIN_HISTORY_REQUIRED} historical draws are required."
        }
        require(topK in 1..PredictorConfig.MAX_TOP_K) {
            "Predictions must be between 1 and ${PredictorConfig.MAX_TOP_K}."
        }
        require(iterations in 1..PredictorConfig.MAX_ITERATIONS) {
            "Iterations must be between 1 and ${PredictorConfig.MAX_ITERATIONS}."
        }

        BacLog.info(
            "Prediction run started",
            "predictor",
            "draw_count" to draws.size,
            "iterations" to iterations,
            "random_seed" to randomSeed,
            "top_k" to topK,
        )

        val frequency = LotteryAnalytics.buildFrequency(draws)
        val bonusFrequency = LotteryAnalytics.buildBonusFrequency(draws)
        val pairFrequency = LotteryAnalytics.buildPairFrequency(draws)
        val overdue = LotteryAnalytics.buildOverdue(draws)
        val scores = LotteryAnalytics.calculateNumberScores(frequency, overdue)
        val random = Random(randomSeed)
        val candidates = ArrayList<Candidate>(iterations)
        val progressInterval = maxOf(1, iterations / 5)

        repeat(iterations) { index ->
            val ticket = weightedMainPick(random, scores)
            if (isValidTicket(ticket)) {
                val bonus = weightedBonusPick(random, scores, bonusFrequency, ticket)
                candidates += Candidate(scoreTicket(ticket, scores, pairFrequency), ticket, bonus)
            }

            val completed = index + 1
            if (completed % progressInterval == 0 || completed == iterations) {
                val progress = (completed * 100.0 / iterations).toInt()
                onProgress(progress)
                BacLog.info(
                    "Prediction generation progress",
                    "predictor",
                    "accepted_candidates" to candidates.size,
                    "completed_iterations" to completed,
                    "progress_percent" to progress,
                )
            }
        }

        check(candidates.isNotEmpty()) {
            "No valid candidates were generated. Increase the iteration count."
        }

        candidates.sortByDescending(Candidate::score)
        val seen = HashSet<List<Int>>()
        val lines = ArrayList<PredictionLine>(topK)
        candidates.forEach { candidate ->
            if (lines.size < topK && seen.add(candidate.numbers)) {
                lines += PredictionLine(
                    rank = lines.size + 1,
                    numbers = candidate.numbers,
                    bonus = candidate.bonus,
                    score = round(candidate.score * 100.0) / 100.0,
                )
            }
        }

        BacLog.info(
            "Prediction run completed",
            "predictor",
            "accepted_candidates" to candidates.size,
            "returned_lines" to lines.size,
        )
        return PredictionReport(
            lines = lines,
            iterations = iterations,
            topK = topK,
            randomSeed = randomSeed,
            candidateCount = candidates.size,
            generatedAt = Instant.now(),
        )
    }

    private fun weightedMainPick(random: Random, scores: DoubleArray): List<Int> {
        val available = (PredictorConfig.NUMBER_MIN..PredictorConfig.NUMBER_MAX).toMutableList()
        val selected = ArrayList<Int>(PredictorConfig.PICKS_PER_LINE)

        repeat(PredictorConfig.PICKS_PER_LINE) {
            val pickIndex = weightedIndex(random, available.map { scores[it] })
            selected += available.removeAt(pickIndex)
        }
        return selected.sorted()
    }

    private fun weightedBonusPick(
        random: Random,
        scores: DoubleArray,
        bonusFrequency: IntArray,
        excluded: List<Int>,
    ): Int {
        val available = (PredictorConfig.NUMBER_MIN..PredictorConfig.NUMBER_MAX)
            .filterNot(excluded::contains)
        val weights = available.map { number -> scores[number] + bonusFrequency[number] * 0.25 }
        return available[weightedIndex(random, weights)]
    }

    private fun weightedIndex(random: Random, weights: List<Double>): Int {
        val target = random.nextDouble(weights.sum())
        var cumulative = 0.0
        weights.forEachIndexed { index, weight ->
            cumulative += weight
            if (target < cumulative) return index
        }
        return weights.lastIndex
    }

    private fun isValidTicket(ticket: List<Int>): Boolean {
        if (ticket.count { it <= 31 } > 4) return false
        if (ticket.count { it % 2 == 1 } !in 2..4) return false
        return ticket.zipWithNext().count { (first, second) -> second - first == 1 } < 2
    }

    private fun scoreTicket(
        ticket: List<Int>,
        scores: DoubleArray,
        pairFrequency: Map<Int, Int>,
    ): Double {
        var total = ticket.sumOf { scores[it] }
        for (firstIndex in 0 until ticket.lastIndex) {
            for (secondIndex in firstIndex + 1 until ticket.size) {
                val key = LotteryAnalytics.pairKey(ticket[firstIndex], ticket[secondIndex])
                total += pairFrequency.getOrDefault(key, 0) * 2
            }
        }
        return total
    }

    private data class Candidate(
        val score: Double,
        val numbers: List<Int>,
        val bonus: Int,
    )
}
