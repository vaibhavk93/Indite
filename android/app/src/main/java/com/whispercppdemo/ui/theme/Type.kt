package com.whispercppdemo.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.ExperimentalTextApi
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontVariation
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.whispercppdemo.R

// indite type: Figtree (bundled; the app has no internet). One family, a clear scale, generous line height for reading.
@OptIn(ExperimentalTextApi::class)
private fun figtree(w: Int) = Font(R.font.figtree, FontWeight(w), variationSettings = FontVariation.Settings(FontVariation.weight(w)))

val Figtree = FontFamily(figtree(400), figtree(500), figtree(600), figtree(700), figtree(800))

private fun style(size: Int, line: Int, weight: Int, tracking: Double = 0.0) =
    TextStyle(fontFamily = Figtree, fontWeight = FontWeight(weight), fontSize = size.sp, lineHeight = line.sp, letterSpacing = tracking.sp)

val Typography = Typography(
    displaySmall = style(34, 40, 700, -0.5),
    headlineMedium = style(28, 34, 700, -0.3),
    headlineSmall = style(22, 28, 700, -0.2),
    titleLarge = style(20, 26, 600),
    titleMedium = style(17, 24, 600),
    titleSmall = style(15, 20, 600),
    bodyLarge = style(17, 27, 400),
    bodyMedium = style(15, 22, 400),
    bodySmall = style(13, 18, 400),
    labelLarge = style(15, 20, 600, 0.1),
    labelMedium = style(13, 16, 600, 0.2),
    labelSmall = style(11, 14, 600, 0.6),
)
