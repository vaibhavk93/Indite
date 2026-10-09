package com.whispercppdemo.ui.main

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.widget.Toast
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.google.accompanist.permissions.ExperimentalPermissionsApi
import com.google.accompanist.permissions.isGranted
import com.google.accompanist.permissions.rememberPermissionState

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(vm: MainScreenViewModel) {
    Scaffold(topBar = {
        TopAppBar(title = {
            Column {
                Text("indite", fontWeight = FontWeight.Bold)
                Text("Phone speed test", style = MaterialTheme.typography.bodySmall)
            }
        })
    }) { pad ->
        Column(
            Modifier.padding(pad).padding(horizontal = 16.dp).verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                "Checks whether this phone can turn Hinglish speech into text on its own — " +
                    "no internet, no computer — fast enough for long recordings.",
                style = MaterialTheme.typography.bodyMedium,
            )
            StatusCard(vm)
            when (vm.phase) {
                Phase.RUNNING -> ProgressCard(vm)
                Phase.DONE -> vm.result?.let { ResultCard(it) }
                else -> {}
            }
            if (vm.phase != Phase.RUNNING) StepsCard(vm)
            if (vm.lines.isNotEmpty()) TranscriptCard(vm)
            if (vm.phase != Phase.RUNNING && vm.phase != Phase.LOADING && vm.phase != Phase.ERROR) VoiceCard(vm)
            Text(vm.device, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(16.dp))
        }
    }
}

@Composable
private fun StatusCard(vm: MainScreenViewModel) {
    val colors = when (vm.phase) {
        Phase.ERROR -> CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
        Phase.DONE -> CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)
        else -> CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
    }
    Card(colors = colors, modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                if (vm.phase == Phase.LOADING) CircularProgressIndicator(Modifier.size(20.dp), strokeWidth = 2.dp)
                Text(vm.status, style = MaterialTheme.typography.titleMedium)
            }
            when (vm.phase) {
                Phase.READY, Phase.STOPPED -> Button(onClick = vm::start, modifier = Modifier.fillMaxWidth()) {
                    Text("Start the 15-minute test")
                }
                Phase.DONE -> OutlinedButton(onClick = vm::start, modifier = Modifier.fillMaxWidth()) { Text("Run again") }
                Phase.RUNNING -> OutlinedButton(onClick = vm::stop, modifier = Modifier.fillMaxWidth()) { Text("Stop test") }
                Phase.ERROR -> Button(onClick = vm::load, modifier = Modifier.fillMaxWidth()) { Text("Try again") }
                else -> {}
            }
        }
    }
}

@Composable
private fun ProgressCard(vm: MainScreenViewModel) {
    val frac = if (vm.audioTotalSec > 0) (vm.audioDoneSec / vm.audioTotalSec).toFloat() else 0f
    val left = if (vm.audioDoneSec > 0) vm.elapsedSec / vm.audioDoneSec * (vm.audioTotalSec - vm.audioDoneSec) else null
    val speed = if (vm.elapsedSec > 0) vm.audioDoneSec / vm.elapsedSec else 0.0
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("${(frac * 100).toInt()}% done", style = MaterialTheme.typography.headlineSmall)
            LinearProgressIndicator(progress = frac, modifier = Modifier.fillMaxWidth().height(8.dp),
                trackColor = MaterialTheme.colorScheme.surface)
            Stat("Pieces", "${vm.piecesDone} of ${vm.piecesTotal}")
            Stat("Time so far", minSec(vm.elapsedSec))
            Stat("Time left (estimate)", left?.let { minSec(it) } ?: "working it out…")
            Stat("Speed", if (speed > 0) "%.2fx real time".format(speed) + if (speed >= PASS_SPEED) "  ✓" else "  (needs 1.0x)" else "—")
            Stat("Battery temperature", "${vm.temp} °C")
        }
    }
}

@Composable
private fun ResultCard(r: Result) {
    val ctx = LocalContext.current
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(if (r.passed) "✓ Passed" else "✗ Too slow", style = MaterialTheme.typography.headlineSmall,
                color = if (r.passed) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error)
            Text(
                if (r.passed) "This phone can transcribe a recording at least as fast as it plays. An offline app is worth building."
                else "This phone takes longer than the recording itself. A 1-hour interview would take over an hour.",
                style = MaterialTheme.typography.bodyMedium,
            )
            Stat("Audio", "%.1f min".format(r.audioMin))
            Stat("Time taken", "%.1f min".format(r.tookMin))
            Stat("Speed", "%.2fx real time (pass: 1.0x)".format(r.speed))
            Stat("Battery", "${r.startTemp} °C → ${r.endTemp} °C")
            Stat("Peak memory", r.peakMemory)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = {
                    ctx.startActivity(Intent.createChooser(
                        Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, r.shareText()), "Share result"))
                }) { Text("Share result") }
                OutlinedButton(onClick = { copy(ctx, r.shareText()) }) { Text("Copy") }
            }
        }
    }
}

@Composable
private fun StepsCard(vm: MainScreenViewModel) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("How to run the test", style = MaterialTheme.typography.titleMedium)
            Text("1.  Unplug the charger — charging heats the phone and skews the result.")
            Text("2.  Close other apps.")
            Text("3.  Tap Start. It transcribes ${vm.piecesTotal} short pieces (${"%.0f".format(vm.audioTotalSec / 60)} min of a real Hinglish interview).")
            Text("4.  Keep this screen open. The screen stays on by itself. Expect 5–30 minutes.")
            Text("5.  When it says Done, tap Share result and send it to Claude.")
        }
    }
}

@Composable
private fun TranscriptCard(vm: MainScreenViewModel) {
    val ctx = LocalContext.current
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Text so far", style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                TextButton(onClick = { copy(ctx, vm.lines.joinToString("\n")) }) { Text("Copy all") }
            }
            Text("Shows the last 5 pieces, newest at the bottom.", style = MaterialTheme.typography.bodySmall)
            SelectionContainer { Text(vm.lines.takeLast(5).joinToString("\n\n")) }
        }
    }
}

@OptIn(ExperimentalPermissionsApi::class)
@Composable
private fun VoiceCard(vm: MainScreenViewModel) {
    val mic = rememberPermissionState(android.Manifest.permission.RECORD_AUDIO) { if (it) vm.toggleRecord() }
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Optional: try your own voice", style = MaterialTheme.typography.titleMedium)
            Text("Speak for 10–30 seconds in Hindi, English or a mix, and see the text. Stays on this phone.",
                style = MaterialTheme.typography.bodySmall)
            OutlinedButton(onClick = { if (mic.status.isGranted) vm.toggleRecord() else mic.launchPermissionRequest() }) {
                Text(if (vm.isRecording) "Stop and transcribe" else "Record")
            }
            if (vm.voiceText.isNotEmpty()) SelectionContainer { Text(vm.voiceText) }
        }
    }
}

@Composable
private fun Stat(label: String, value: String) {
    Row(Modifier.fillMaxWidth()) {
        Text(label, modifier = Modifier.weight(1f), color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(value, fontWeight = FontWeight.Medium)
    }
}

private fun minSec(s: Double) = "%d min %02d s".format((s / 60).toInt(), (s % 60).toInt())

private fun copy(ctx: Context, text: String) {
    (ctx.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager).setPrimaryClip(ClipData.newPlainText("indite", text))
    Toast.makeText(ctx, "Copied", Toast.LENGTH_SHORT).show()
}
