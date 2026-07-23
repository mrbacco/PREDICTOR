// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor.domain

import java.time.LocalDate
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PredictorEngineTest {
    private val draws = (0 until 24).map { drawIndex ->
        val numbers = (0 until 6)
            .map { offset -> ((drawIndex * 3 + offset * 7) % 47) + 1 }
            .sorted()
        val bonus = (1..47).first { it !in numbers && it > drawIndex % 47 }
        LottoDraw(
            drawDate = LocalDate.of(2026, 1, 1).plusDays(drawIndex.toLong()),
            numbers = numbers,
            bonus = bonus,
        )
    }

    @Test
    fun generateReturnsFiveUniqueLinesWithDistinctBonuses() {
        val report = PredictorEngine().generate(
            draws = draws,
            topK = 5,
            iterations = 3_000,
            randomSeed = 20260723L,
        )

        assertEquals(5, report.lines.size)
        assertEquals(5, report.lines.map(PredictionLine::numbers).distinct().size)
        report.lines.forEach { line ->
            assertEquals(6, line.numbers.distinct().size)
            assertTrue(line.numbers.all { it in 1..47 })
            assertTrue(line.bonus in 1..47)
            assertFalse(line.bonus in line.numbers)
        }
    }

    @Test
    fun sameSeedReproducesTheSameRankedLines() {
        val engine = PredictorEngine()

        val first = engine.generate(draws, 5, 2_000, 42L)
        val second = engine.generate(draws, 5, 2_000, 42L)

        assertEquals(first.lines, second.lines)
    }
}
