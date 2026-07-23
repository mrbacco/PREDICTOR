// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor.core

import android.util.Log

/**
 * Structured Android logger matching the BAC_LOG format used by the web application.
 *
 * Events appear in Android Studio's Logcat window under the `BAC_LOG` tag. Context
 * values are sorted to keep repeated events easy to compare.
 */
object BacLog {
    private const val TAG = "BAC_LOG"

    fun debug(message: String, component: String, vararg context: Pair<String, Any?>) {
        write(Log.DEBUG, message, component, null, context)
    }

    fun info(message: String, component: String, vararg context: Pair<String, Any?>) {
        write(Log.INFO, message, component, null, context)
    }

    fun warning(message: String, component: String, vararg context: Pair<String, Any?>) {
        write(Log.WARN, message, component, null, context)
    }

    fun error(
        message: String,
        component: String,
        throwable: Throwable? = null,
        vararg context: Pair<String, Any?>,
    ) {
        write(Log.ERROR, message, component, throwable, context)
    }

    private fun write(
        priority: Int,
        message: String,
        component: String,
        throwable: Throwable?,
        context: Array<out Pair<String, Any?>>,
    ) {
        val contextText = context
            .sortedBy { it.first }
            .joinToString(separator = " ") { (key, value) -> "$key=${format(value)}" }
        val suffix = if (contextText.isBlank()) "" else " | $contextText"
        Log.println(priority, TAG, "$component | $message$suffix")

        if (throwable != null) {
            Log.println(priority, TAG, Log.getStackTraceString(throwable))
        }
    }

    private fun format(value: Any?): String = when (value) {
        null -> "null"
        is Number, is Boolean -> value.toString()
        else -> "\"${value.toString().replace("\"", "\\\"")}\""
    }
}
