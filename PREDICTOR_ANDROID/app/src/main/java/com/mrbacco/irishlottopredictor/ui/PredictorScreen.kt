// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.mrbacco.irishlottopredictor.domain.LottoDraw
import com.mrbacco.irishlottopredictor.domain.PredictionLine
import com.mrbacco.irishlottopredictor.ui.theme.Amber
import com.mrbacco.irishlottopredictor.ui.theme.Canvas
import com.mrbacco.irishlottopredictor.ui.theme.DeepGreen
import com.mrbacco.irishlottopredictor.ui.theme.Hairline
import com.mrbacco.irishlottopredictor.ui.theme.Ink
import com.mrbacco.irishlottopredictor.ui.theme.IrishGreen
import com.mrbacco.irishlottopredictor.ui.theme.Mint
import com.mrbacco.irishlottopredictor.ui.theme.MutedInk
import com.mrbacco.irishlottopredictor.ui.theme.Paper
import com.mrbacco.irishlottopredictor.ui.theme.SoftAmber
import java.time.format.DateTimeFormatter

/** Connects lifecycle-aware state collection to the stateless screen renderer. */
@Composable
fun PredictorRoute(viewModel: PredictorViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    PredictorScreen(
        state = state,
        onPredictionCountChanged = viewModel::updatePredictionCount,
        onIterationsChanged = viewModel::updateIterations,
        onSeedChanged = viewModel::updateSeed,
        onGenerate = viewModel::generatePredictions,
        onNewSeed = viewModel::generateWithNewSeed,
        onRefresh = viewModel::refreshData,
    )
}

/**
 * Minimalist phone-first dashboard. All work is delegated through event callbacks so
 * this composable remains previewable and independently testable.
 */
@Composable
fun PredictorScreen(
    state: PredictorUiState,
    onPredictionCountChanged: (String) -> Unit,
    onIterationsChanged: (String) -> Unit,
    onSeedChanged: (String) -> Unit,
    onGenerate: () -> Unit,
    onNewSeed: () -> Unit,
    onRefresh: () -> Unit,
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(Canvas)
            .windowInsetsPadding(WindowInsets.safeDrawing),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item { AppHeader(state.dataSourceLabel) }
        item { StatusPanel(state) }
        item { SummaryGrid(state) }
        item {
            SettingsPanel(
                state = state,
                onPredictionCountChanged = onPredictionCountChanged,
                onIterationsChanged = onIterationsChanged,
                onSeedChanged = onSeedChanged,
                onGenerate = onGenerate,
                onNewSeed = onNewSeed,
                onRefresh = onRefresh,
            )
        }

        if (state.report != null) {
            item {
                SectionHeading(
                    eyebrow = "RANKED OUTPUT",
                    title = "Prediction lines",
                    detail = "${state.report.candidateCount} accepted candidates",
                )
            }
            items(state.report.lines, key = PredictionLine::rank) { line ->
                PredictionCard(line)
            }
            item {
                Text(
                    text = "Seed ${state.report.randomSeed} reproduces this Android run.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MutedInk,
                )
            }
        }

        if (state.recentDraws.isNotEmpty()) {
            item {
                SectionHeading(
                    eyebrow = "HISTORY",
                    title = "Recent draws",
                    detail = "Newest verified rows",
                )
            }
            items(state.recentDraws, key = LottoDraw::drawDate) { draw ->
                RecentDrawRow(draw)
            }
        }

        item {
            Text(
                text = "Statistical exploration only. Lottery results are random and predictions cannot guarantee a win.",
                modifier = Modifier.padding(vertical = 8.dp),
                style = MaterialTheme.typography.bodySmall,
                color = MutedInk,
                textAlign = TextAlign.Center,
            )
        }
    }
}

@Composable
private fun AppHeader(dataSourceLabel: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(
            modifier = Modifier
                .size(48.dp)
                .clip(RoundedCornerShape(14.dp))
                .background(DeepGreen),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = "IL",
                color = Color.White,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
        }
        Spacer(Modifier.width(13.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = "IRISH LOTTO / ANDROID",
                style = MaterialTheme.typography.labelSmall,
                color = IrishGreen,
                letterSpacing = 1.4.sp,
            )
            Text(
                text = "Predictor",
                style = MaterialTheme.typography.headlineMedium,
                color = Ink,
            )
            Text(
                text = dataSourceLabel,
                style = MaterialTheme.typography.bodySmall,
                color = MutedInk,
            )
        }
        Surface(
            color = Mint,
            shape = RoundedCornerShape(50),
        ) {
            Text(
                text = "OFFLINE",
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                style = MaterialTheme.typography.labelSmall,
                color = DeepGreen,
                letterSpacing = 0.8.sp,
            )
        }
    }
}

@Composable
private fun StatusPanel(state: PredictorUiState) {
    val isError = state.errorMessage != null
    val containerColor = if (isError) MaterialTheme.colorScheme.errorContainer else Paper
    val contentColor = if (isError) MaterialTheme.colorScheme.onErrorContainer else Ink

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(containerColor)
            .border(1.dp, if (isError) Color.Transparent else Hairline, RoundedCornerShape(14.dp))
            .padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                Modifier
                    .size(8.dp)
                    .clip(CircleShape)
                    .background(if (isError) MaterialTheme.colorScheme.error else IrishGreen),
            )
            Spacer(Modifier.width(9.dp))
            Text(
                text = state.errorMessage ?: state.statusMessage,
                modifier = Modifier.weight(1f),
                style = MaterialTheme.typography.bodyMedium,
                color = contentColor,
            )
        }
        if (state.isBusy) {
            LinearProgressIndicator(
                progress = { state.progressPercent / 100f },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(3.dp)
                    .clip(CircleShape),
                color = IrishGreen,
                trackColor = Mint,
            )
        }
    }
}

@Composable
private fun SummaryGrid(state: PredictorUiState) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            SummaryTile(
                label = "DRAW ROWS",
                value = state.summary.totalDraws.toString(),
                modifier = Modifier.weight(1f),
            )
            SummaryTile(
                label = "LATEST",
                value = state.summary.latestDrawDate?.format(SHORT_DATE) ?: "--",
                modifier = Modifier.weight(1f),
            )
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            SummaryTile(
                label = "NUMBERS SEEN",
                value = "${state.summary.uniqueNumbersSeen} / 47",
                modifier = Modifier.weight(1f),
            )
            SummaryTile(
                label = "HOT SIX",
                value = state.summary.hottestNumbers.joinToString(" ").ifBlank { "--" },
                modifier = Modifier.weight(1f),
            )
        }
    }
}

@Composable
private fun SummaryTile(label: String, value: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .background(Paper)
            .border(1.dp, Hairline, RoundedCornerShape(12.dp))
            .padding(13.dp),
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MutedInk,
            letterSpacing = 0.8.sp,
        )
        Spacer(Modifier.height(4.dp))
        Text(
            text = value,
            style = MaterialTheme.typography.titleMedium,
            color = Ink,
            maxLines = 1,
        )
    }
}

@Composable
private fun SettingsPanel(
    state: PredictorUiState,
    onPredictionCountChanged: (String) -> Unit,
    onIterationsChanged: (String) -> Unit,
    onSeedChanged: (String) -> Unit,
    onGenerate: () -> Unit,
    onNewSeed: () -> Unit,
    onRefresh: () -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Paper),
        shape = RoundedCornerShape(16.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Hairline),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            SectionHeading(
                eyebrow = "CONTROLS",
                title = "Run a model",
                detail = "Same seed, same Android result",
            )
            OutlinedTextField(
                value = state.predictionCountInput,
                onValueChange = onPredictionCountChanged,
                modifier = Modifier.fillMaxWidth(),
                enabled = !state.isBusy,
                label = { Text("Prediction lines") },
                supportingText = { Text("Default 5, maximum 50") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                shape = RoundedCornerShape(11.dp),
            )
            OutlinedTextField(
                value = state.iterationsInput,
                onValueChange = onIterationsChanged,
                modifier = Modifier.fillMaxWidth(),
                enabled = !state.isBusy,
                label = { Text("Iterations") },
                supportingText = { Text("More iterations search more candidates") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                shape = RoundedCornerShape(11.dp),
            )
            OutlinedTextField(
                value = state.seedInput,
                onValueChange = onSeedChanged,
                modifier = Modifier.fillMaxWidth(),
                enabled = !state.isBusy,
                label = { Text("Random seed") },
                supportingText = { Text("Change it to generate a different sequence") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                shape = RoundedCornerShape(11.dp),
            )
            Button(
                onClick = onGenerate,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(50.dp),
                enabled = !state.isBusy,
                shape = RoundedCornerShape(11.dp),
            ) {
                Text("Generate predictions")
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(
                    onClick = onNewSeed,
                    modifier = Modifier.weight(1f),
                    enabled = !state.isBusy,
                    shape = RoundedCornerShape(11.dp),
                ) {
                    Text("New seed")
                }
                OutlinedButton(
                    onClick = onRefresh,
                    modifier = Modifier.weight(1f),
                    enabled = !state.isBusy,
                    shape = RoundedCornerShape(11.dp),
                ) {
                    Text("Refresh data")
                }
            }
        }
    }
}

@Composable
private fun SectionHeading(eyebrow: String, title: String, detail: String) {
    Column {
        Text(
            text = eyebrow,
            style = MaterialTheme.typography.labelSmall,
            color = IrishGreen,
            letterSpacing = 1.2.sp,
        )
        Row(verticalAlignment = Alignment.Bottom) {
            Text(
                text = title,
                modifier = Modifier.weight(1f),
                style = MaterialTheme.typography.titleLarge,
                color = Ink,
            )
            Text(
                text = detail,
                style = MaterialTheme.typography.bodySmall,
                color = MutedInk,
                textAlign = TextAlign.End,
            )
        }
    }
}

@Composable
private fun PredictionCard(line: PredictionLine) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Paper),
        shape = RoundedCornerShape(15.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Hairline),
    ) {
        Column(
            modifier = Modifier.padding(15.dp),
            verticalArrangement = Arrangement.spacedBy(13.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "LINE ${line.rank.toString().padStart(2, '0')}",
                    modifier = Modifier.weight(1f),
                    style = MaterialTheme.typography.labelMedium,
                    color = IrishGreen,
                    letterSpacing = 1.sp,
                )
                Text(
                    text = "score ${"%.2f".format(line.score)}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MutedInk,
                )
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                line.numbers.forEach { NumberBall(it) }
            }
            HorizontalDivider(color = Hairline)
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "BONUS",
                    modifier = Modifier.weight(1f),
                    style = MaterialTheme.typography.labelSmall,
                    color = Amber,
                    letterSpacing = 1.sp,
                )
                NumberBall(number = line.bonus, isBonus = true)
            }
        }
    }
}

@Composable
private fun RecentDrawRow(draw: LottoDraw) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(13.dp))
            .background(Paper)
            .border(1.dp, Hairline, RoundedCornerShape(13.dp))
            .padding(13.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = draw.drawDate.format(LONG_DATE),
                modifier = Modifier.weight(1f),
                style = MaterialTheme.typography.titleSmall,
                color = Ink,
            )
            draw.bonus?.let {
                Text(
                    text = "Bonus $it",
                    style = MaterialTheme.typography.labelSmall,
                    color = Amber,
                )
            }
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            draw.numbers.forEach { NumberBall(number = it, compact = true) }
        }
    }
}

@Composable
private fun NumberBall(number: Int, isBonus: Boolean = false, compact: Boolean = false) {
    val size = if (compact) 31.dp else 36.dp
    Box(
        modifier = Modifier
            .size(size)
            .clip(CircleShape)
            .background(if (isBonus) SoftAmber else Mint)
            .border(1.dp, if (isBonus) Amber else Color.Transparent, CircleShape),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            text = number.toString(),
            style = if (compact) MaterialTheme.typography.labelMedium else MaterialTheme.typography.labelLarge,
            color = if (isBonus) Amber else DeepGreen,
            fontWeight = FontWeight.Bold,
        )
    }
}

private val SHORT_DATE: DateTimeFormatter = DateTimeFormatter.ofPattern("dd MMM yy")
private val LONG_DATE: DateTimeFormatter = DateTimeFormatter.ofPattern("EEE, dd MMM yyyy")
