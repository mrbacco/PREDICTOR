// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor

import android.content.Context
import com.mrbacco.irishlottopredictor.data.LotteryRepository
import com.mrbacco.irishlottopredictor.domain.PredictorEngine

/**
 * Small dependency container that keeps construction out of activities and view models.
 */
class AppContainer(context: Context) {
    val repository = LotteryRepository(context)
    val predictorEngine = PredictorEngine()
}
