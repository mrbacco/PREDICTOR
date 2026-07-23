// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.mrbacco.irishlottopredictor.AppContainer
import com.mrbacco.irishlottopredictor.core.BacLog
import com.mrbacco.irishlottopredictor.core.PredictorConfig
import com.mrbacco.irishlottopredictor.data.LotteryRepository
import com.mrbacco.irishlottopredictor.domain.DatasetSummary
import com.mrbacco.irishlottopredictor.domain.LotteryAnalytics
import com.mrbacco.irishlottopredictor.domain.LottoDraw
import com.mrbacco.irishlottopredictor.domain.PredictionReport
import com.mrbacco.irishlottopredictor.domain.PredictorEngine
import kotlin.random.Random
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** Immutable render state for the complete predictor screen. */
data class PredictorUiState(
    val summary: DatasetSummary = DatasetSummary.Empty,
    val recentDraws: List<LottoDraw> = emptyList(),
    val report: PredictionReport? = null,
    val predictionCountInput: String = PredictorConfig.DEFAULT_TOP_K.toString(),
    val iterationsInput: String = PredictorConfig.DEFAULT_ITERATIONS.toString(),
    val seedInput: String = newSeed().toString(),
    val isBusy: Boolean = true,
    val progressPercent: Int = 0,
    val statusMessage: String = "Loading offline draw history...",
    val errorMessage: String? = null,
    val dataSourceLabel: String = "Bundled offline data",
)

/**
 * Coordinates repository work and CPU-heavy prediction runs outside the UI thread.
 */
class PredictorViewModel(
    private val repository: LotteryRepository,
    private val predictorEngine: PredictorEngine,
) : ViewModel() {
    private val _uiState = MutableStateFlow(PredictorUiState())
    val uiState: StateFlow<PredictorUiState> = _uiState.asStateFlow()
    private var loadedDraws: List<LottoDraw> = emptyList()

    init {
        loadInitialData()
    }

    fun updatePredictionCount(value: String) {
        if (value.all(Char::isDigit)) _uiState.update { it.copy(predictionCountInput = value) }
    }

    fun updateIterations(value: String) {
        if (value.all(Char::isDigit)) _uiState.update { it.copy(iterationsInput = value) }
    }

    fun updateSeed(value: String) {
        if (value.all(Char::isDigit)) _uiState.update { it.copy(seedInput = value) }
    }

    fun generatePredictions() {
        if (_uiState.value.isBusy) return
        viewModelScope.launch { runPrediction(loadedDraws) }
    }

    fun generateWithNewSeed() {
        if (_uiState.value.isBusy) return
        _uiState.update { it.copy(seedInput = newSeed().toString()) }
        viewModelScope.launch { runPrediction(loadedDraws) }
    }

    fun refreshData() {
        if (_uiState.value.isBusy) return
        viewModelScope.launch {
            setBusy("Refreshing from lottery.ie...")
            try {
                loadedDraws = repository.refreshDraws()
                publishDraws(loadedDraws, "Refreshed online")
                runPrediction(loadedDraws)
            } catch (exception: Exception) {
                reportFailure("Refresh failed. Your offline data is still available.", exception)
            }
        }
    }

    private fun loadInitialData() {
        viewModelScope.launch {
            try {
                loadedDraws = repository.loadDraws()
                publishDraws(loadedDraws, "Bundled offline data")
                runPrediction(loadedDraws)
            } catch (exception: Exception) {
                reportFailure("The bundled draw history could not be loaded.", exception)
            }
        }
    }

    private suspend fun runPrediction(draws: List<LottoDraw>) {
        val settings = parseSettings() ?: return
        if (draws.isEmpty()) {
            reportFailure("No draw history is available.", IllegalStateException("Empty history"))
            return
        }

        setBusy("Generating weighted predictions...")
        try {
            val report = withContext(Dispatchers.Default) {
                predictorEngine.generate(
                    draws = draws,
                    topK = settings.topK,
                    iterations = settings.iterations,
                    randomSeed = settings.seed,
                ) { progress ->
                    _uiState.update { it.copy(progressPercent = progress) }
                }
            }
            _uiState.update {
                it.copy(
                    report = report,
                    isBusy = false,
                    progressPercent = 100,
                    statusMessage = "${report.lines.size} predictions ready",
                    errorMessage = null,
                )
            }
        } catch (exception: Exception) {
            reportFailure("Prediction generation failed.", exception)
        }
    }

    private fun parseSettings(): PredictionSettings? {
        val state = _uiState.value
        val topK = state.predictionCountInput.toIntOrNull()
        val iterations = state.iterationsInput.toIntOrNull()
        val seed = state.seedInput.toLongOrNull()
        val error = when {
            (topK == null || topK !in 1..PredictorConfig.MAX_TOP_K) ->
                "Predictions must be between 1 and ${PredictorConfig.MAX_TOP_K}."
            (iterations == null || iterations !in 1..PredictorConfig.MAX_ITERATIONS) ->
                "Iterations must be between 1 and ${PredictorConfig.MAX_ITERATIONS}."
            seed == null -> "Enter a valid positive random seed."
            else -> null
        }

        if (error != null) {
            _uiState.update {
                it.copy(isBusy = false, errorMessage = error, statusMessage = "Check the settings")
            }
            BacLog.warning("Prediction settings rejected", "view_model", "reason" to error)
            return null
        }
        return PredictionSettings(topK!!, iterations!!, seed!!)
    }

    private fun publishDraws(draws: List<LottoDraw>, sourceLabel: String) {
        val summary = LotteryAnalytics.summarize(draws)
        _uiState.update {
            it.copy(
                summary = summary,
                recentDraws = draws.takeLast(8).asReversed(),
                dataSourceLabel = sourceLabel,
                errorMessage = null,
            )
        }
        BacLog.info(
            "Dashboard history ready",
            "view_model",
            "draw_count" to draws.size,
            "latest_date" to summary.latestDrawDate,
            "source" to sourceLabel,
        )
    }

    private fun setBusy(message: String) {
        _uiState.update {
            it.copy(
                isBusy = true,
                progressPercent = 0,
                statusMessage = message,
                errorMessage = null,
            )
        }
    }

    private fun reportFailure(userMessage: String, exception: Exception) {
        BacLog.error(
            userMessage,
            "view_model",
            exception,
            "reason" to (exception.message ?: exception.javaClass.simpleName),
        )
        _uiState.update {
            it.copy(
                isBusy = false,
                progressPercent = 0,
                statusMessage = "Action could not be completed",
                errorMessage = "$userMessage ${exception.message.orEmpty()}".trim(),
            )
        }
    }

    private data class PredictionSettings(
        val topK: Int,
        val iterations: Int,
        val seed: Long,
    )

    companion object {
        fun factory(container: AppContainer): ViewModelProvider.Factory = viewModelFactory {
            initializer {
                PredictorViewModel(container.repository, container.predictorEngine)
            }
        }
    }
}

private fun newSeed(): Long = Random.nextLong(1, Int.MAX_VALUE.toLong())
