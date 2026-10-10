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
import androidx.compose.animation.togetherWith
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
import kotlinx.coroutines.launch
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
    val used by androidx.compose.runtime.produceState(0L, notes.size) { value = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) { Notes.bytesUsed() } }
    var confirmDeleteAll by remember { mutableStateOf(false) }
    var showPrivacy by remember { mutableStateOf(false) }
    val privacy = remember { context.resources.openRawResource(R.raw.privacy).bufferedReader().readText() }
    val scope = androidx.compose.runtime.rememberCoroutineScope()
    val export = androidx.activity.compose.rememberLauncherForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.CreateDocument("text/plain")) { uri ->
        if (uri != null) scope.launch(kotlinx.coroutines.Dispatchers.IO) {
            val ok = runCatching { context.contentResolver.openOutputStream(uri)!!.use { it.write(Notes.exportAll().toByteArray()) } }.isSuccess
            com.whispercppdemo.ui.Messages.flow.tryEmit(if (ok) "Notes exported" else "Couldn't save the file")
        }
    }

    if (showPrivacy) AlertDialog(
        onDismissRequest = { showPrivacy = false },
        title = { Text("Privacy policy") },
        text = { Text(privacy, Modifier.verticalScroll(rememberScrollState()), style = MaterialTheme.typography.bodySmall) },
        confirmButton = { TextButton(onClick = { showPrivacy = false }) { Text("Close") } },
    )

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

    // Settings in groups: a short list first, each group on its own page (no endless scrolling).
    var page by androidx.compose.runtime.saveable.rememberSaveable { mutableStateOf<String?>(null) }
    androidx.activity.compose.BackHandler(enabled = page != null) { page = null }
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(SettingsGroups.firstOrNull { it.id == page }?.title ?: "Settings") },
                navigationIcon = { IconButton(onClick = { if (page != null) page = null else onBack() }) {
                    Icon(Icons.Filled.ArrowBack, contentDescription = "Back") } },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { pad ->
        androidx.compose.animation.AnimatedContent(page, Modifier.padding(pad), label = "settings page", transitionSpec = {
            val dir = if (targetState != null) 1 else -1  // into a group slides left, back slides right
            (androidx.compose.animation.slideInHorizontally { it * dir / 4 } + androidx.compose.animation.fadeIn()) togetherWith
                (androidx.compose.animation.slideOutHorizontally { -it * dir / 4 } + androidx.compose.animation.fadeOut())
        }) { shown ->
        if (shown == null) {
            val bubbleOn = remember { com.whispercppdemo.overlay.BubbleService.enabled(context) }
            val summary = mapOf(
                "look" to theme.label,
                "dictation" to (if (bubbleOn) "Floating mic on" else "Keyboard and floating mic"),
                "ai" to (com.whispercppdemo.ui.aiTargets(context).joinToString(", ") { com.whispercppdemo.ui.aiTargetName(it).substringBefore(" (") }
                    .ifEmpty { "Share list" }),
                "fixes" to (if (fixes.isEmpty()) "None yet" else "${fixes.size} fix${if (fixes.size == 1) "" else "es"}"),
                "storage" to "${notes.size} notes · ${Formatter.formatShortFileSize(context, used)}",
                "about" to "indite ${BuildConfig.VERSION_NAME}",
            )
            LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(vertical = 8.dp)) {
                items(SettingsGroups) { g ->
                    Row(Modifier.fillMaxWidth().clickable(role = Role.Button, onClickLabel = "Open ${g.title}") { page = g.id }
                        .padding(horizontal = 20.dp, vertical = 16.dp), verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(g.title, style = MaterialTheme.typography.titleMedium)
                            Text(summary[g.id] ?: "", style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        Text("›", style = MaterialTheme.typography.headlineSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        } else
        LazyColumn(
            Modifier.fillMaxSize(),
            contentPadding = PaddingValues(start = 16.dp, end = 16.dp, bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            if (shown == "look") item {
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
            if (shown == "dictation") item {
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
            if (shown == "dictation") item {
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
            if (shown == "dictation") item {
                Section("Floating mic button") {
                    var on by remember { mutableStateOf(com.whispercppdemo.overlay.BubbleService.enabled(context)) }
                    var allowed by remember { mutableStateOf(android.provider.Settings.canDrawOverlays(context)) }
                    LaunchedEffect(Unit) {  // re-check after the user comes back from the phone's permission screen
                        while (true) {
                            val now = android.provider.Settings.canDrawOverlays(context)
                            if (now && !allowed && on) com.whispercppdemo.overlay.BubbleService.setEnabled(context, true)
                            allowed = now; delay(1000)
                        }
                    }
                    Text("A small mic bubble on top of every app. Tap it, talk, tap again. When it turns green, tap it to copy the text. " +
                        "Hold it while recording to cancel. Drag it to the bottom edge to hide it. " +
                        "If you use the indite keyboard, use its mic instead: it types the text in directly.",
                        style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Row(Modifier.fillMaxWidth().padding(top = 10.dp), verticalAlignment = Alignment.CenterVertically) {
                        Text(if (on && allowed) "On" else "Off", Modifier.weight(1f), style = MaterialTheme.typography.bodyLarge)
                        androidx.compose.material3.Switch(checked = on && allowed, onCheckedChange = { want ->
                            on = want
                            if (want && !allowed) context.startActivity(Intent(android.provider.Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                                android.net.Uri.parse("package:" + context.packageName)))
                            com.whispercppdemo.overlay.BubbleService.setEnabled(context, want)
                        })
                    }
                    if (on && !allowed) Text("Allow \"Display over other apps\" for indite, then come back.", Modifier.padding(top = 6.dp),
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.primary)
                    // The switch = the feature is on. Dragged away, it's hidden: say so, with one tap to show it again.
                    var hiddenNow by remember { mutableStateOf(com.whispercppdemo.overlay.BubbleService.hidden) }
                    LaunchedEffect(Unit) { while (true) { hiddenNow = com.whispercppdemo.overlay.BubbleService.hidden; delay(700) } }
                    if (on && allowed && hiddenNow) Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Hidden (you dragged it away)", Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant)
                        TextButton(onClick = { com.whispercppdemo.overlay.BubbleService.setEnabled(context, true) }) { Text("Show") }
                    }
                    var auto by remember { mutableStateOf(com.whispercppdemo.overlay.BubbleService.autoCopy(context)) }
                    Row(Modifier.fillMaxWidth().padding(top = 6.dp), verticalAlignment = Alignment.CenterVertically) {
                        Text("Copy automatically (no green button)", Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium)
                        androidx.compose.material3.Switch(checked = auto, onCheckedChange = {
                            auto = it; com.whispercppdemo.overlay.BubbleService.setAutoCopy(context, it)
                        })
                    }
                    if (com.whispercppdemo.overlay.AutoPaste.available) {
                        var typing by remember { mutableStateOf(com.whispercppdemo.overlay.AutoPaste.enabled()) }
                        var disclose by remember { mutableStateOf(false) }
                        LaunchedEffect(Unit) { while (true) { typing = com.whispercppdemo.overlay.AutoPaste.enabled(); delay(1000) } }
                        Row(Modifier.fillMaxWidth().padding(top = 6.dp), verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text("Type into the box for me", style = MaterialTheme.typography.bodyMedium)
                                Text(if (typing) "On: text goes straight into the box you were typing in"
                                    else "Off: tap the green button to copy", style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant)
                                // Android's accessibility shortcut can only switch this on/off, not the floating mic.
                                Text("The phone's accessibility shortcut turns this on and off, not the floating mic. You don't need the " +
                                    "shortcut: turn it off in Accessibility settings.", style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(top = 4.dp))
                            }
                            TextButton(onClick = { if (typing) context.startActivity(Intent(android.provider.Settings.ACTION_ACCESSIBILITY_SETTINGS)) else disclose = true }) {
                                Text(if (typing) "Turn off" else "Turn on")
                            }
                        }
                        // Google Play requires this disclosure before sending people to the accessibility settings.
                        if (disclose) AlertDialog(
                            onDismissRequest = { disclose = false },
                            title = { Text("Let indite type into text boxes?") },
                            text = { Text("indite uses Android's accessibility service only to paste your dictation into the text box " +
                                "you were typing in. It looks for that box only when you start and finish a dictation, and skips " +
                                "password boxes. It does not read or save anything on your screen, and nothing leaves your phone.\n\n" +
                                "Next: in the list, tap \"indite: type into the box\" and turn it on.") },
                            confirmButton = { TextButton(onClick = { disclose = false
                                context.startActivity(Intent(android.provider.Settings.ACTION_ACCESSIBILITY_SETTINGS)) }) { Text("Agree") } },
                            dismissButton = { TextButton(onClick = { disclose = false }) { Text("Not now") } },
                        )
                    }
                    // Some phones (OnePlus, Xiaomi, Vivo…) stop background apps to save battery; this opens the phone's own list.
                    TextButton(onClick = { runCatching { context.startActivity(Intent(android.provider.Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)) } }) {
                        Text("Bubble disappears? Allow indite in battery settings")
                    }
                }
            }
            if (shown == "ai") item {
                Section("Where AI requests go") {
                    var targets by remember { mutableStateOf(com.whispercppdemo.ui.aiTargets(context).toSet()) }
                    Text("Make notes, Action items and Translate go here. Tick one to go straight there, or several to choose each time. " +
                        "None ticked: your phone's share list." +
                        if (com.whispercppdemo.ai.MacCompanion.configured(context)) " Your Mac is set up, so answers come from Claude on your Mac." else "",
                        style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    val options = (if (com.whispercppdemo.ai.OpenRouter.available) listOf(com.whispercppdemo.ui.IN_APP) else emptyList()) +
                        com.whispercppdemo.ui.AiApps.map { it.first }
                    Column(Modifier.padding(top = 6.dp)) {
                        options.forEach { t ->
                            val on = t in targets
                            Row(Modifier.fillMaxWidth().clickable(role = Role.Checkbox) {
                                targets = if (on) targets - t else targets + t
                                com.whispercppdemo.ui.setAiTargets(context, targets)
                            }.padding(vertical = 6.dp), verticalAlignment = Alignment.CenterVertically) {
                                androidx.compose.material3.Checkbox(checked = on, onCheckedChange = null)
                                Text(com.whispercppdemo.ui.aiTargetName(t), Modifier.padding(start = 12.dp), style = MaterialTheme.typography.bodyLarge)
                            }
                        }
                    }
                }
            }
            if (shown == "ai" && com.whispercppdemo.ai.OpenRouter.available) item {
                Section("Your OpenRouter key") {
                    var key by remember { mutableStateOf(com.whispercppdemo.ai.OpenRouter.key(context)) }
                    var model by remember { mutableStateOf(com.whispercppdemo.ai.OpenRouter.model(context)) }
                    var models by remember { mutableStateOf<List<String>>(emptyList()) }
                    var result by remember { mutableStateOf<String?>(null) }
                    Text("Answers are written inside indite and saved with the note. Only the text is sent, never audio. " +
                        "Free models: about 50 requests a day. Get a key at openrouter.ai → Keys.",
                        style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    OutlinedTextField(key, { key = it }, Modifier.fillMaxWidth().padding(top = 8.dp), singleLine = true,
                        label = { Text("Key (starts with sk-or-)") },
                        visualTransformation = androidx.compose.ui.text.input.PasswordVisualTransformation())
                    OutlinedTextField(model, { model = it }, Modifier.fillMaxWidth().padding(top = 8.dp), singleLine = true,
                        label = { Text("Model") })
                    Row(Modifier.padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        OutlinedButton(onClick = {
                            com.whispercppdemo.ai.OpenRouter.save(context, key, model)
                            result = "Loading free models…"
                            scope.launch {
                                result = try { models = com.whispercppdemo.ai.OpenRouter.freeModels(context); "${models.size} free models. Tap one." }
                                catch (e: Exception) { e.message }
                            }
                        }, enabled = key.isNotBlank()) { Text("Show free models") }
                        FilledTonalButton(onClick = {
                            com.whispercppdemo.ai.OpenRouter.save(context, key, model)
                            result = "Checking…"
                            scope.launch {
                                result = try {
                                    com.whispercppdemo.ai.OpenRouter.ask(context, "Reply with just: OK", "test")
                                    if (com.whispercppdemo.ui.IN_APP !in com.whispercppdemo.ui.aiTargets(context))
                                        com.whispercppdemo.ui.setAiTargets(context, com.whispercppdemo.ui.aiTargets(context).toSet() + com.whispercppdemo.ui.IN_APP)
                                    "✓ Working. \"Answer inside indite\" is now ticked above."
                                } catch (e: Exception) { e.message }
                            }
                        }, enabled = key.isNotBlank() && model.isNotBlank()) { Text("Save and test") }
                    }
                    result?.let { Text(it, Modifier.padding(top = 6.dp), style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.primary) }
                    models.take(30).forEach { m ->
                        Text(m, Modifier.fillMaxWidth().clickable { model = m; com.whispercppdemo.ai.OpenRouter.save(context, key, m) }
                            .padding(vertical = 8.dp), style = MaterialTheme.typography.bodyMedium,
                            color = if (m == model) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface)
                    }
                }
            }
            if (shown == "ai" && com.whispercppdemo.ai.MacCompanion.available) item {
                Section("Your Mac (personal build)") {
                    var url by remember { mutableStateOf(com.whispercppdemo.ai.MacCompanion.url(context)) }
                    var token by remember { mutableStateOf(com.whispercppdemo.ai.MacCompanion.token(context)) }
                    var result by remember { mutableStateOf<String?>(null) }
                    val scope = androidx.compose.runtime.rememberCoroutineScope()
                    Text("Ask my AI uses Claude on your own Mac, on your own plan. On the Mac: start indite, run " +
                        "`tailscale serve --bg --set-path /api/ask http://127.0.0.1:8000/api/ask`, then paste the ts.net address and the token indite prints.",
                        style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    OutlinedTextField(url, { url = it }, Modifier.fillMaxWidth().padding(top = 8.dp), singleLine = true,
                        label = { Text("Your Mac's Tailscale link, e.g. https://my-mac.tail1234.ts.net") })
                    OutlinedTextField(token, { token = it }, Modifier.fillMaxWidth().padding(top = 8.dp), singleLine = true,
                        label = { Text("Token from the Mac") })
                    Row(Modifier.padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        FilledTonalButton(onClick = {
                            com.whispercppdemo.ai.MacCompanion.save(context, url, token)
                            result = "Checking…"
                            scope.launch {
                                result = try {
                                    com.whispercppdemo.ai.MacCompanion.ask(context, "Reply with just: OK", "test")
                                    "✓ Connected to Claude on your Mac"
                                } catch (e: Exception) { e.message }
                            }
                        }, enabled = url.isNotBlank() && token.isNotBlank()) { Text("Save and test") }
                    }
                    result?.let { Text(it, Modifier.padding(top = 6.dp), style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.primary) }
                }
            }
            if (shown == "fixes") item {
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
            if (shown == "storage") item {
                Section("Storage") {
                    Text("${notes.size} notes use ${Formatter.formatShortFileSize(context, used)} on this phone.",
                        style = MaterialTheme.typography.bodyLarge)
                    if (notes.isNotEmpty()) OutlinedButton(onClick = { export.launch("indite notes.txt") }, Modifier.padding(top = 8.dp)) {
                        Text("Export all notes as text")
                    }
                    if (notes.isNotEmpty()) OutlinedButton(onClick = { confirmDeleteAll = true }, Modifier.padding(top = 8.dp)) {
                        Text("Delete all notes", color = MaterialTheme.colorScheme.error)
                    }
                }
            }
            if (shown == "storage") item {
                Section("Privacy") {
                    Text(if (com.whispercppdemo.ai.MacCompanion.available)
                        "Personal build: speech-to-text happens on this phone. When you use Ask my AI, the note's text goes to your own Mac " +
                            "over Tailscale, nowhere else. Nothing is backed up to the cloud."
                    else "Everything happens on this phone. indite has no internet access, and nothing is backed up to the cloud. " +
                        "Your audio and text leave the phone only if you copy or share them.", style = MaterialTheme.typography.bodyMedium)
                    Text("When recording other people, ask them first.", Modifier.padding(top = 8.dp),
                        style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    TextButton(onClick = { showPrivacy = true }, Modifier.padding(top = 4.dp)) { Text("Privacy policy") }
                }
            }
            if (shown == "about") item {
                Section("About") {
                    Text("indite ${BuildConfig.VERSION_NAME} (build ${BuildConfig.VERSION_CODE} · ${BuildConfig.GIT} · ${BuildConfig.FLAVOR})",
                        style = MaterialTheme.typography.bodyLarge)
                    Text("Speech model: Oriserve Hindi2Hinglish-Apex (Apache-2.0), run with whisper.cpp (MIT). " +
                        "Speech detection: Silero VAD (MIT).", style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Row {
                        TextButton(onClick = { showLicences = true }, Modifier.padding(top = 4.dp)) { Text("Licences") }
                        TextButton(onClick = { scope.launch { shareDebugInfo(context, notes) } }, Modifier.padding(top = 4.dp)) { Text("Share debug info") }
                    }
                }
            }
        }
        }
    }
}

private class SettingsGroup(val id: String, val title: String)
private val SettingsGroups = listOf(SettingsGroup("look", "Look & feel"), SettingsGroup("dictation", "Dictation"),
    SettingsGroup("ai", "AI"), SettingsGroup("fixes", "Word fixes"), SettingsGroup("storage", "Storage & privacy"),
    SettingsGroup("about", "About"))

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

/** For bug reports: phone, app, speed numbers and app warnings. Never audio or note text (only exceptions are logged). */
private suspend fun shareDebugInfo(context: android.content.Context, notes: List<com.whispercppdemo.notes.Note>) {
    val text = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
        val cpu = runCatching { java.io.File("/proc/cpuinfo").readLines().firstOrNull { it.startsWith("Features") } }.getOrNull() ?: "?"
        val log = runCatching {
            Runtime.getRuntime().exec(arrayOf("logcat", "-d", "-t", "300", "*:W")).inputStream.bufferedReader().readText()
        }.getOrDefault("(no log)")
        buildString {
            appendLine("indite ${BuildConfig.VERSION_NAME} (${BuildConfig.FLAVOR})")
            appendLine("${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}, Android ${android.os.Build.VERSION.RELEASE}, ${Runtime.getRuntime().availableProcessors()} cores")
            appendLine("CPU $cpu")
            appendLine("Free space ${Notes.freeBytes() / 1_000_000} MB, ${notes.size} notes")
            appendLine("Recent speeds:")
            notes.take(10).forEach { appendLine("  ${(it.seconds / 60).toInt()} min, ${it.pieces.size} parts: ${it.speed ?: "-"}") }
            appendLine()
            appendLine("Warnings:")
            append(log.takeLast(30_000))
        }
    }
    context.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).setType("text/plain")
        .putExtra(Intent.EXTRA_SUBJECT, "indite debug info").putExtra(Intent.EXTRA_TEXT, text), "Share debug info")
        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
}
