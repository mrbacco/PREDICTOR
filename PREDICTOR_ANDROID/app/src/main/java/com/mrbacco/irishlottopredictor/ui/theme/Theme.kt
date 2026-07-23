// Author: mrbacco04@gmail.com
// Month: July 2026
// Release Version: 1.0.0
// License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

package com.mrbacco.irishlottopredictor.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.mrbacco.irishlottopredictor.R

val Ink = Color(0xFF17201B)
val MutedInk = Color(0xFF65706A)
val IrishGreen = Color(0xFF176B46)
val DeepGreen = Color(0xFF0D4D33)
val Mint = Color(0xFFE3F0E8)
val Canvas = Color(0xFFF4F6F3)
val Paper = Color(0xFFFCFDFB)
val Hairline = Color(0xFFD9DFDA)
val Amber = Color(0xFFB96D19)
val SoftAmber = Color(0xFFFFEED9)

private val AppColorScheme = lightColorScheme(
    primary = IrishGreen,
    onPrimary = Color.White,
    primaryContainer = Mint,
    onPrimaryContainer = DeepGreen,
    secondary = Amber,
    onSecondary = Color.White,
    secondaryContainer = SoftAmber,
    onSecondaryContainer = Color(0xFF5B330A),
    background = Canvas,
    onBackground = Ink,
    surface = Paper,
    onSurface = Ink,
    surfaceVariant = Color(0xFFEDF1ED),
    onSurfaceVariant = MutedInk,
    outline = Hairline,
    error = Color(0xFFB3261E),
)

private val RobotoCondensed = FontFamily(Font(R.font.roboto_condensed))

private val AppTypography = Typography(
    displayLarge = appTextStyle(57, 64, FontWeight.SemiBold),
    displayMedium = appTextStyle(45, 52, FontWeight.SemiBold),
    displaySmall = appTextStyle(36, 44, FontWeight.SemiBold),
    headlineLarge = appTextStyle(32, 40, FontWeight.SemiBold),
    headlineMedium = appTextStyle(28, 36, FontWeight.SemiBold),
    headlineSmall = appTextStyle(24, 32, FontWeight.SemiBold),
    titleLarge = appTextStyle(22, 28, FontWeight.SemiBold),
    titleMedium = appTextStyle(17, 24, FontWeight.SemiBold),
    titleSmall = appTextStyle(15, 20, FontWeight.SemiBold),
    bodyLarge = appTextStyle(16, 24, FontWeight.Normal),
    bodyMedium = appTextStyle(14, 20, FontWeight.Normal),
    bodySmall = appTextStyle(12, 16, FontWeight.Normal),
    labelLarge = appTextStyle(14, 20, FontWeight.SemiBold),
    labelMedium = appTextStyle(12, 16, FontWeight.SemiBold),
    labelSmall = appTextStyle(11, 16, FontWeight.Medium),
)

private fun appTextStyle(
    fontSize: Int,
    lineHeight: Int,
    weight: FontWeight,
) = TextStyle(
    fontFamily = RobotoCondensed,
    fontWeight = weight,
    fontSize = fontSize.sp,
    lineHeight = lineHeight.sp,
)

@Composable
fun PredictorTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = AppColorScheme,
        typography = AppTypography,
        content = content,
    )
}
