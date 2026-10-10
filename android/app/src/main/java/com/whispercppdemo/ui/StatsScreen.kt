package com.whispercppdemo.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.whispercppdemo.notes.Note

/** Usage numbers, worked out on this phone from the notes themselves. Nothing is sent anywhere. */
internal class Stats(notes: List<Note>, reminders: Int, now: Long = System.currentTimeMillis()) {
    private fun words(n: Note) = n.allText().split(Regex("\\s+")).count { it.isNotBlank() }
    private val done = notes.filter { it.pieces.isNotEmpty() }
    val dictations = notes.count { it.name.startsWith("Dictation") }
    val recordings = notes.count { it.live && !it.name.startsWith("Dictation") }
    val imports = notes.count { !it.live }
    val minutes = notes.sumOf { it.seconds } / 60
    val words = done.sumOf { words(it) }
    val dayMs = 24 * 60 * 60 * 1000L
    /** Words per day for the last 7 days, oldest first. */
    val week: List<Int> = (6 downTo 0).map { d ->
        val start = startOfDay(now) - d * dayMs
        done.filter { it.created in start until start + dayMs }.sumOf { words(it) }
    }
    val wordsThisWeek = week.sum()
    val aiAnswers = notes.sumOf { it.ai.size }
    val labelled = notes.count { it.labelled }
    val upcomingReminders = reminders
    /** Typical speed of turning audio into text, from each note's speed log ("… (1.35x) …"). */
    val speed: Double? = notes.mapNotNull { it.speed?.let { s -> Regex("\\(([0-9.]+)x\\)").find(s)?.groupValues?.get(1)?.toDoubleOrNull() } }
        .sorted().let { if (it.isEmpty()) null else it[it.size / 2] }
    private fun startOfDay(t: Long) = java.util.Calendar.getInstance().apply {
        timeInMillis = t; set(java.util.Calendar.HOUR_OF_DAY, 0); set(java.util.Calendar.MINUTE, 0)
        set(java.util.Calendar.SECOND, 0); set(java.util.Calendar.MILLISECOND, 0)
    }.timeInMillis
}

@Composable
internal fun StatsPanel(s: Stats) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Big("%,d".format(s.words), "words written", Modifier.weight(1f))
            Big("%,.0f".format(s.minutes), "minutes of audio", Modifier.weight(1f))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Big("${s.recordings}", "recordings", Modifier.weight(1f))
            Big("${s.dictations}", "dictations", Modifier.weight(1f))
            Big("${s.imports}", "imports", Modifier.weight(1f))
        }
        Surface(shape = RoundedCornerShape(16.dp), color = MaterialTheme.colorScheme.surface) {
            Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("This week: %,d words".format(s.wordsThisWeek), style = MaterialTheme.typography.titleSmall)
                val bar = MaterialTheme.colorScheme.primary
                val faint = MaterialTheme.colorScheme.outline
                val max = (s.week.maxOrNull() ?: 0).coerceAtLeast(1)
                Canvas(Modifier.fillMaxWidth().height(90.dp)) {
                    val n = s.week.size; val gap = 10.dp.toPx(); val w = (size.width - gap * (n - 1)) / n
                    s.week.forEachIndexed { k, v ->
                        val h = if (v == 0) 3.dp.toPx() else size.height * v / max
                        drawRoundRect(if (v == 0) faint else bar, Offset(k * (w + gap), size.height - h), Size(w, h), CornerRadius(6.dp.toPx()))
                    }
                }
                val fmt = java.text.SimpleDateFormat("EEE", java.util.Locale.getDefault())
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    (6 downTo 0).forEach { d ->
                        Text(if (d == 0) "Today" else fmt.format(java.util.Date(System.currentTimeMillis() - d * s.dayMs)),
                            style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
        Surface(shape = RoundedCornerShape(16.dp), color = MaterialTheme.colorScheme.surface) {
            Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Line("Typical speed", s.speed?.let { "%.2fx real time".format(it) } ?: "after your first long recording")
                Line("AI answers saved", "${s.aiAnswers}")
                Line("Notes with speaker labels", "${s.labelled}")
                Line("Upcoming reminders", "${s.upcomingReminders}")
            }
        }
        Text("Counted on this phone from your notes. Nothing is sent anywhere.", style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun Big(value: String, label: String, modifier: Modifier) =
    Surface(shape = RoundedCornerShape(16.dp), color = MaterialTheme.colorScheme.surface, modifier = modifier) {
        Column(Modifier.padding(14.dp)) {
            Text(value, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold, color = MaterialTheme.colorScheme.primary)
            Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }

@Composable
private fun Line(label: String, value: String) = Row(Modifier.fillMaxWidth()) {
    Text(label, Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium)
    Text(value, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
}
