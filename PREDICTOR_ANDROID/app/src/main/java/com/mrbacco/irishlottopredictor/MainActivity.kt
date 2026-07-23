// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.viewmodel.compose.viewModel
import com.mrbacco.irishlottopredictor.core.BacLog
import com.mrbacco.irishlottopredictor.ui.PredictorRoute
import com.mrbacco.irishlottopredictor.ui.PredictorViewModel
import com.mrbacco.irishlottopredictor.ui.theme.PredictorTheme

/** Single-activity host for the lifecycle-aware Compose application. */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        BacLog.info("Main activity created", "activity")

        val container = (application as PredictorApplication).container
        setContent {
            PredictorTheme {
                val predictorViewModel: PredictorViewModel = viewModel(
                    factory = PredictorViewModel.factory(container),
                )
                PredictorRoute(predictorViewModel)
            }
        }
    }
}
