// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

plugins {
    id("com.android.application") version "9.2.1" apply false
    // AGP 9.2 provides Kotlin 2.3.10 directly; Compose must use the matching compiler.
    id("org.jetbrains.kotlin.plugin.compose") version "2.3.10" apply false
}
