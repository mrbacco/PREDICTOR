// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor.data

import android.content.Context
import com.mrbacco.irishlottopredictor.core.BacLog
import com.mrbacco.irishlottopredictor.core.PredictorConfig
import com.mrbacco.irishlottopredictor.domain.LottoDraw
import java.io.File
import java.io.FileOutputStream
import java.nio.file.AtomicMoveNotSupportedException
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

/**
 * Offline-first draw repository backed by app-private storage.
 *
 * The bundled CSV makes first launch independent of the network. A successful manual
 * refresh atomically replaces the private copy; a failed refresh leaves it untouched.
 */
class LotteryRepository(
    context: Context,
    private val remoteDataSource: LottoRemoteDataSource = LottoRemoteDataSource(),
) {
    private val appContext = context.applicationContext
    private val dataFile = File(appContext.filesDir, PredictorConfig.LOCAL_DATA_FILE)
    private val accessMutex = Mutex()

    suspend fun loadDraws(): List<LottoDraw> = withContext(Dispatchers.IO) {
        accessMutex.withLock {
            ensureLocalData()
            BacLog.info("Loading local draw history", "repository", "file" to dataFile.name)
            DrawCsvCodec.decode(dataFile.readText(Charsets.UTF_8))
        }
    }

    suspend fun refreshDraws(): List<LottoDraw> = withContext(Dispatchers.IO) {
        BacLog.info("Dataset refresh started", "repository")
        val remoteDraws = remoteDataSource.fetchDraws()
        require(remoteDraws.size >= PredictorConfig.MIN_HISTORY_REQUIRED) {
            "The refreshed dataset contains too few valid draws."
        }

        accessMutex.withLock {
            writeAtomically(DrawCsvCodec.encode(remoteDraws))
        }
        BacLog.info(
            "Dataset refresh completed",
            "repository",
            "latest_date" to remoteDraws.last().drawDate,
            "rows_written" to remoteDraws.size,
        )
        remoteDraws
    }

    private fun ensureLocalData() {
        if (dataFile.exists() && dataFile.length() > 0L) return

        BacLog.info("Installing bundled draw history", "repository", "file" to dataFile.name)
        val bundledCsv = appContext.assets
            .open(PredictorConfig.LOCAL_DATA_FILE)
            .bufferedReader(Charsets.UTF_8)
            .use { it.readText() }
        writeAtomically(bundledCsv)
    }

    private fun writeAtomically(csvText: String) {
        val temporaryFile = File(dataFile.parentFile, "${dataFile.name}.tmp")
        FileOutputStream(temporaryFile).use { output ->
            val writer = output.writer(Charsets.UTF_8)
            writer.write(csvText)
            writer.flush()
            output.fd.sync()
        }

        try {
            try {
                Files.move(
                    temporaryFile.toPath(),
                    dataFile.toPath(),
                    StandardCopyOption.ATOMIC_MOVE,
                    StandardCopyOption.REPLACE_EXISTING,
                )
            } catch (_: AtomicMoveNotSupportedException) {
                Files.move(
                    temporaryFile.toPath(),
                    dataFile.toPath(),
                    StandardCopyOption.REPLACE_EXISTING,
                )
            }
        } catch (exception: Exception) {
            temporaryFile.delete()
            throw IllegalStateException("The local history could not be activated.", exception)
        }
    }
}
