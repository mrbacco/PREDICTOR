// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor.data

import java.time.LocalDate
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class DrawCsvCodecTest {
    @Test
    fun decodeSkipsMetadataCommentsAndParsesOptionalBonus() {
        val csv = """
            # Author: mrbacco04@gmail.com
            # Month: July 2026
            draw_date,n1,n2,n3,n4,n5,n6,bonus
            2026-07-15,3,10,12,24,25,41,7
            2026-07-12,1,9,19,31,37,47,
        """.trimIndent()

        val draws = DrawCsvCodec.decode(csv)

        assertEquals(2, draws.size)
        assertEquals(LocalDate.of(2026, 7, 12), draws.first().drawDate)
        assertNull(draws.first().bonus)
        assertEquals(7, draws.last().bonus)
    }

    @Test
    fun encodeAndDecodePreserveValidatedDraws() {
        val original = DrawCsvCodec.decode(
            """
                draw_date,n1,n2,n3,n4,n5,n6,bonus
                2026-07-15,3,10,12,24,25,41,7
            """.trimIndent(),
        )

        val decodedAgain = DrawCsvCodec.decode(DrawCsvCodec.encode(original))

        assertEquals(original, decodedAgain)
    }
}
