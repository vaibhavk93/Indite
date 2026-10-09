package com.whispercppdemo.ui

import android.text.format.Formatter
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import android.content.Intent
import android.view.inputmethod.InputMethodManager
import androidx.compose.runtime.LaunchedEffect
import kotlinx.coroutines.delay
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import com.whispercppdemo.BuildConfig
import com.whispercppdemo.R
import com.whispercppdemo.notes.Notes
import com.whispercppdemo.notes.Settings
import com.whispercppdemo.notes.Theme

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(onBack: () -> Unit) {
    val theme by Settings.theme.collectAsState()
    var showLicences by remember { mutableStateOf(false) }
    val fixes by Settings.fixes.collectAsState()
    val notes by Notes.list.collectAsState()
    val context = LocalContext.current
    val licences = remember { context.resources.openRawResource(R.raw.licenses).bufferedReader().readText() }
    val used = remember(notes) { Notes.bytesUsed() }
    var confirmDeleteAll by remember { mutableStateOf(false) }

    if (showLicences) AlertDialog(
        onDismissRequest = { showLicences = false },
        title = { Text("Licences") },
        text = { Text(licences, Modifier.verticalScroll(rememberScrollState()), style = MaterialTheme.typography.bodySmall) },
        confirmButton = { TextButton(onClick = { showLicences = false }) { Text("Close") } },
    )

    if (confirmDeleteAll) AlertDialog(
        onDismissRequest = { confirmDeleteAll = false },
        title = { Text("Delete all notes?") },
        text = { Text("All ${notes.size} notes, their audio and text are removed from this phone. This can't be undone.") },
        confirmButton = { TextButton(onClick = { confirmDeleteAll = false; Notes.deleteAll() }) { Text("Delete all") } },
        dismissButton = { TextButton(onClick = { confirmDeleteAll = false }) { Text("Cancel") } },
    )

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings") },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Filled.ArrowBack, contentDescription = "Back") } },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { pad ->
        LazyColumn(
            Modifier.fillMaxSize().padding(pad),
            contentPadding = PaddingValues(start = 16.dp, end = 16.dp, bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item {
                Section("Appearance") {
                    Column(Modifier.selectableGroup()) {
                        Theme.values().forEach { t ->
                            Row(
                                Modifier.fillMaxWidth().selectable(selected = theme == t, role = Role.RadioButton) { Settings.setTheme(t) }
                                    .padding(vertical = 4.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                RadioButton(selected = theme == t, onClick = null)
                                Text(t.label, Modifier.padding(start = 12.dp), style = MaterialTheme.typography.bodyLarge)
                            }
                        }
                    }
                }
            }
            item {
                Section("Spelling") {
                    val chat by Settings.chatSpelling.collectAsState()
                    Column(Modifier.selectableGroup()) {
                        listOf(true to "Everyday spelling: achha, maine, kyunki", false to "As the model wrote it: achchha, mainne, kyonki").forEach { (v, label) ->
                            Row(Modifier.fillMaxWidth().selectable(selected = chat == v, role = Role.RadioButton) { Settings.setChatSpelling(v) }
                                .padding(vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                                RadioButton(selected = chat == v, onClick = null)
                                Text(label, Modifier.padding(start = 12.dp), style = MaterialTheme.typography.bodyLarge)
                            }
                        }
                    }
                }
            }
            item {
                Section("Voice keyboard") {
                    val imm = context.getSystemService(InputMethodManager::class.java)
                    var enabled by remember { mutableStateOf(false) }
                    LaunchedEffect(Unit) {  // re-check when you come back from the phone's settings
                        while (true) { enabled = imm.enabledInputMethodList.any { it.packageName == context.packageName }; delay(1000) }
                    }
                    Text("Dictate into any app: WhatsApp, Gmail, notes. Switch to the indite keyboard, tap the mic and talk. " +
                        "Each dictation is also saved here with its audio.", style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Row(Modifier.padding(top = 12.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        if (!enabled) FilledTonalButton(onClick = {
                            context.startActivity(Intent(android.provider.Settings.ACTION_INPUT_METHOD_SETTINGS))
                        }) { Text("1. Turn it on") }
                        else Text("✓ Turned on", Modifier.padding(vertical = 10.dp), style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.primary)
                        OutlinedButton(onClick = { imm.showInputMethodPicker() }, enabled = enabled) {
                            Text(if (enabled) "Switch keyboard" else "2. Switch to it")
                        }
                    }
                }
            }
            item {
                Section("Word fixes") {
                    Text("Words indite keeps getting wrong, fixed everywhere. The original text is kept.",
                        style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    fixes.forEach { (from, to) ->
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("$from  →  $to", Modifier.weight(1f), style = MaterialTheme.typography.bodyLarge)
                            IconButton(onClick = { Settings.removeFix(from) }) {
                                Icon(Icons.Filled.Close, contentDescription = "Remove fix for $from")
                            }
                        }
                    }
                    AddFix()
                }
            }
            item {
                Section("Storage") {
                    Text("${notes.size} notes use ${Formatter.formatShortFileSize(context, used)} on this phone.",
                        style = MaterialTheme.typography.bodyLarge)
                    if (notes.isNotEmpty()) OutlinedButton(onClick = { confirmDeleteAll = true }, Modifier.padding(top = 8.dp)) {
                        Text("Delete all notes", color = MaterialTheme.colorScheme.error)
                    }
                }
            }
            item {
                Section("Privacy") {
                    Text("Everything happens on this phone. indite has no internet access, and nothing is backed up to the cloud. " +
                        "Your audio and text leave the phone only if you copy or share them.", style = MaterialTheme.typography.bodyMedium)
                    Text("When recording other people, ask them first.", Modifier.padding(top = 8.dp),
                        style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            item {
                Section("About") {
                    Text("indite ${BuildConfig.VERSION_NAME}", style = MaterialTheme.typography.bodyLarge)
                    Text("Speech model: Oriserve Hindi2Hinglish-Apex (Apache-2.0), run with whisper.cpp (MIT). " +
                        "Speech detection: Silero VAD (MIT).", style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                    TextButton(onClick = { showLicences = true }, Modifier.padding(top = 4.dp)) { Text("Licences") }
                }
            }
        }
    }
}

@Composable
private fun AddFix() {
    var from by remember { mutableStateOf("") }
    var to by remember { mutableStateOf("") }
    Column(Modifier.padding(top = 8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedTextField(from, { from = it }, Modifier.fillMaxWidth(), label = { Text("Wrong word, e.g. PTM") }, singleLine = true)
        OutlinedTextField(to, { to = it }, Modifier.fillMaxWidth(), label = { Text("Right word, e.g. Paytm") }, singleLine = true)
        FilledTonalButton(onClick = { Settings.addFix(from, to); from = ""; to = "" },
            enabled = from.isNotBlank() && to.isNotBlank()) { Text("Add fix") }
    }
}

@Composable
private fun Section(title: String, content: @Composable () -> Unit) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.fillMaxWidth().padding(16.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold,
                modifier = Modifier.padding(bottom = 8.dp))
            content()
        }
    }
}
