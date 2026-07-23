// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor

import android.app.Application
import com.mrbacco.irishlottopredictor.core.BacLog

/** Application process owner and dependency-container lifetime boundary. */
class PredictorApplication : Application() {
    val container by lazy { AppContainer(this) }

    override fun onCreate() {
        super.onCreate()
        BacLog.info("Android application started", "application", "version" to "1.0.0")
    }
}
