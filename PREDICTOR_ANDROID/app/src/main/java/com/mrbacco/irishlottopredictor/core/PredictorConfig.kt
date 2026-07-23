// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor.core

/**
 * Central configuration for limits shared by the UI, data, and prediction layers.
 */
object PredictorConfig {
    const val NUMBER_MIN = 1
    const val NUMBER_MAX = 47
    const val PICKS_PER_LINE = 6
    const val DEFAULT_TOP_K = 5
    const val DEFAULT_ITERATIONS = 50_000
    const val MIN_HISTORY_REQUIRED = 10
    const val MAX_TOP_K = 50
    const val MAX_ITERATIONS = 200_000
    const val REQUEST_TIMEOUT_MILLIS = 30_000
    const val LOCAL_DATA_FILE = "irish_lotto_results.csv"
    const val SOURCE_URL = "https://www.lottery.ie/results/lotto/history"
}
