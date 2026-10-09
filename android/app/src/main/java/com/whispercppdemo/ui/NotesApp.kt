package com.whispercppdemo.ui

import android.content.Context
import android.content.Intent
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.os.Build
import android.text.format.DateUtils
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.DismissDirection
import androidx.compose.material3.DismissValue
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.Surface
import androidx.compose.material3.SwipeToDismiss
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TextField
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.rememberDismissState
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.whispercppdemo.R
import com.whispercppdemo.notes.Guards
import com.whispercppdemo.notes.Note
import com.whispercppdemo.notes.Notes
import com.whispercppdemo.notes.PhoneCheck
import com.whispercppdemo.notes.Piece
import com.whispercppdemo.notes.Settings
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** For work that must outlive a screen or a rotation (imports, saving an edit as you leave). */
val AppScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

/** One-off messages for the snackbar (import errors, "Copied"). */
object Messages {
    val flow = MutableSharedFlow<String>(extraBufferCapacity = 4)
    /** "Always fix PTM -> Paytm?" after the same correction twice. */
    val suggest = MutableSharedFlow<Pair<String, String>>(extraBufferCapacity = 2)
}

/** Ready prompts for the user's own AI app (ChatGPT, Claude…). Only the text is shared, and only when the user taps. */
private val AskPrompts = listOf(
    "Summary" to "Summarise this in 5 short bullet points. Keep names, numbers and dates exactly. It is Hinglish (Hindi and English in Roman letters).",
    "To-do list" to "List every task, promise or follow-up in this, one per line, with who and when if mentioned. It is Hinglish (Hindi and English in Roman letters).",
    "In English" to "Translate this into clear, natural English. Keep names, numbers and dates exactly.",
    "Clean it up" to "Clean up this dictated Hinglish text: fix punctuation and obvious mistakes, remove fillers like umm, keep Hindi words in Roman letters, don't add anything new.",
)

private val Gutter = 20.dp

@Composable
fun NotesApp(openRequest: String?, onOpenHandled: () -> Unit, onOpenFile: () -> Unit, onRecord: () -> Unit, onStop: () -> Unit) {
    var selected by rememberSaveable { mutableStateOf<String?>(null) }
    var settings by rememberSaveable { mutableStateOf(false) }
    LaunchedEffect(openRequest) { if (openRequest != null) { selected = openRequest; settings = false; onOpenHandled() } }
    val notes by Notes.list.collectAsState()
    val snackbar = remember { SnackbarHostState() }
    LaunchedEffect(Unit) { Messages.flow.collect { snackbar.showSnackbar(it) } }
    LaunchedEffect(Unit) {
        Messages.suggest.collect { (from, to) ->
            val r = snackbar.showSnackbar("Always fix \"$from\" → \"$to\"?", actionLabel = "Always fix", withDismissAction = true)
            if (r == SnackbarResult.ActionPerformed) { Settings.addFix(from, to); Notes.refresh() }
        }
    }

    val note = notes.firstOrNull { it.id == selected }
    var onboarded by remember { mutableStateOf(Settings.onboarded) }
    when {
        !onboarded && selected == null -> Welcome(
            onTry = { Settings.setOnboarded(); onboarded = true; onRecord() },
            onSkip = { Settings.setOnboarded(); onboarded = true },
        )
        settings -> {
            BackHandler { settings = false }
            SettingsScreen(onBack = { settings = false })
        }
        note != null && note.recording -> {
            BackHandler { selected = null }
            RecordingScreen(note, onStop, onMinimise = { selected = null })
        }
        note != null -> {
            BackHandler { Player.stop(); selected = null }
            NoteScreen(note, snackbar, onBack = { Player.stop(); selected = null })
        }
        else -> HomeScreen(notes, snackbar, onOpenFile, onRecord, onSettings = { settings = true }, onOpen = { selected = it })
    }
}

// ---------------------------------------------------------------- Welcome (first open only)

@Composable
private fun Welcome(onTry: () -> Unit, onSkip: () -> Unit) {
    Scaffold(containerColor = MaterialTheme.colorScheme.background) { pad ->
        Column(Modifier.fillMaxSize().padding(pad).padding(horizontal = 28.dp).navigationBarsPadding(),
            verticalArrangement = Arrangement.spacedBy(18.dp)) {
            Spacer(Modifier.weight(1f))
            Text("indite", style = MaterialTheme.typography.displaySmall, color = MaterialTheme.colorScheme.primary)
            Text("Speak Hindi, English or both.\nGet it in writing.", style = MaterialTheme.typography.headlineMedium)
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Promise("Written the way you type: achha, kal milte hain, meeting at 3")
                Promise("Works without internet. Your voice never leaves this phone")
                Promise("Notes, voice notes, meetings, and a keyboard for any app")
            }
            Spacer(Modifier.weight(1f))
            Surface(shape = RoundedCornerShape(18.dp), color = MaterialTheme.colorScheme.surfaceVariant) {
                Text("Try saying: \"Kal 3 baje meeting hai, Rahul ko bata dena.\"", Modifier.padding(16.dp),
                    style = MaterialTheme.typography.bodyLarge)
            }
            Button(onClick = onTry, Modifier.fillMaxWidth().height(56.dp), shape = RoundedCornerShape(16.dp)) {
                Icon(painterResource(R.drawable.ic_mic), contentDescription = null, modifier = Modifier.size(20.dp))
                Text("  Try it now", style = MaterialTheme.typography.titleMedium)
            }
            TextButton(onClick = onSkip, Modifier.fillMaxWidth().padding(bottom = 12.dp)) { Text("Not now") }
        }
    }
}

@Composable
private fun Promise(text: String) = Row(verticalAlignment = Alignment.Top) {
    Text("✓", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.primary)
    Text(text, Modifier.padding(start = 12.dp), style = MaterialTheme.typography.bodyLarge)
}

// ---------------------------------------------------------------- Home

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun HomeScreen(notes: List<Note>, snackbar: SnackbarHostState, onOpenFile: () -> Unit, onRecord: () -> Unit,
                       onSettings: () -> Unit, onOpen: (String) -> Unit) {
    val context = LocalContext.current
    val status by Notes.status.collectAsState()
    val working by Notes.working.collectAsState()
    val problem = remember { PhoneCheck.problem() }
    val lowRam = remember { PhoneCheck.lowRam(context) }
    var query by rememberSaveable { mutableStateOf("") }
    val hidden = remember { mutableStateListOf<String>() }  // swiped away, waiting for Undo
    val scope = rememberCoroutineScope()
    val shown = notes.filter { it.id !in hidden }.filter { n ->
        query.isBlank() || n.name.contains(query, true) || n.pieces.indices.any { n.text(it).contains(query, true) }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {},
                actions = {
                    if (problem == null) TextButton(onClick = onOpenFile) {
                        Icon(Icons.Filled.Add, contentDescription = null, modifier = Modifier.size(18.dp))
                        Text(" Import")
                    }
                    IconButton(onClick = onSettings) { Icon(Icons.Filled.Settings, contentDescription = "Settings") }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
        bottomBar = { if (problem == null) RecordBar(onRecord) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { pad ->
        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(pad),
            contentPadding = PaddingValues(start = Gutter, end = Gutter, bottom = 24.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            item {
                Column(Modifier.padding(bottom = 6.dp)) {
                    Text("indite", style = MaterialTheme.typography.displaySmall)
                    Text("Speak in Hindi, English or both. Get it in writing.", style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            if (problem != null) item { Banner(problem, error = true) }
            else if (lowRam) item { Banner("This phone has under 6 GB of memory. Long recordings may be slow.", error = false) }
            if (status.isNotBlank()) item { StatusLine(status, working) }
            if (notes.isNotEmpty()) item { SearchField(query) { query = it } }
            if (notes.isEmpty()) item { EmptyState() }
            else if (shown.isEmpty()) item {
                Text("Nothing matches \"$query\".", Modifier.padding(vertical = 24.dp), style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            items(shown, key = { it.id }) { note ->
                val dismiss = rememberDismissState(confirmValueChange = {
                    if (it == DismissValue.DismissedToStart && !note.recording) {
                        hidden += note.id
                        scope.launch {
                            val r = snackbar.showSnackbar("Note deleted", actionLabel = "Undo", withDismissAction = true)
                            if (r == SnackbarResult.ActionPerformed) hidden -= note.id
                            else { withContext(Dispatchers.IO) { Notes.delete(note.id) }; hidden -= note.id }
                        }
                        true
                    } else false
                })
                SwipeToDismiss(
                    state = dismiss,
                    directions = setOf(DismissDirection.EndToStart),
                    background = {
                        Box(Modifier.fillMaxSize().clip(RoundedCornerShape(20.dp)).background(MaterialTheme.colorScheme.errorContainer)
                            .padding(horizontal = 24.dp), contentAlignment = Alignment.CenterEnd) {
                            Text("Delete", color = MaterialTheme.colorScheme.onErrorContainer, style = MaterialTheme.typography.labelLarge)
                        }
                    },
                    dismissContent = { NoteRow(note) { onOpen(note.id) } },
                )
            }
        }
    }
}

@Composable
private fun SearchField(query: String, onChange: (String) -> Unit) = TextField(
    value = query, onValueChange = onChange, singleLine = true,
    modifier = Modifier.fillMaxWidth(),
    placeholder = { Text("Search your notes") },
    leadingIcon = { Icon(Icons.Filled.Search, contentDescription = null) },
    trailingIcon = { if (query.isNotEmpty()) IconButton(onClick = { onChange("") }) { Icon(Icons.Filled.Close, contentDescription = "Clear search") } },
    shape = RoundedCornerShape(16.dp),
    colors = TextFieldDefaults.colors(
        focusedContainerColor = MaterialTheme.colorScheme.surfaceVariant, unfocusedContainerColor = MaterialTheme.colorScheme.surfaceVariant,
        focusedIndicatorColor = MaterialTheme.colorScheme.surfaceVariant, unfocusedIndicatorColor = MaterialTheme.colorScheme.surfaceVariant,
    ),
)

/** The one big action: a round mic button, always in the same place. */
@Composable
private fun RecordBar(onRecord: () -> Unit) {
    val haptics = LocalHapticFeedback.current
    Column(Modifier.fillMaxWidth().background(MaterialTheme.colorScheme.background).navigationBarsPadding().padding(top = 8.dp, bottom = 14.dp),
        horizontalAlignment = Alignment.CenterHorizontally) {
        Box(
            Modifier.size(76.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primary)
                .clickable(role = Role.Button, onClickLabel = "Start recording") {
                    haptics.performHapticFeedback(HapticFeedbackType.LongPress); onRecord()
                },
            contentAlignment = Alignment.Center,
        ) {
            Icon(painterResource(R.drawable.ic_mic), contentDescription = "Record", tint = MaterialTheme.colorScheme.onPrimary,
                modifier = Modifier.size(32.dp))
        }
        Text("Tap to speak", Modifier.padding(top = 8.dp), style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun EmptyState() {
    Column(Modifier.fillMaxWidth().padding(top = 28.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        Surface(shape = RoundedCornerShape(24.dp), color = MaterialTheme.colorScheme.surface,
            modifier = Modifier.border(1.dp, MaterialTheme.colorScheme.outline, RoundedCornerShape(24.dp))) {
            Column(Modifier.padding(22.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Step("1", "Tap the mic and talk, as long as you like.")
                Step("2", "Pause for a moment and that part turns into text.")
                Step("3", "Edit, copy or share it. The audio stays with it.")
            }
        }
        Text("Works without internet. Your voice never leaves this phone.", style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text("Have a voice note or recording? Share it to indite, or tap Import.", style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun Step(n: String, text: String) = Row(verticalAlignment = Alignment.CenterVertically) {
    Box(Modifier.size(28.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primaryContainer), contentAlignment = Alignment.Center) {
        Text(n, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onPrimaryContainer)
    }
    Text(text, Modifier.padding(start = 14.dp), style = MaterialTheme.typography.bodyLarge)
}

@Composable
private fun Banner(text: String, error: Boolean) = Surface(
    shape = RoundedCornerShape(16.dp),
    color = if (error) MaterialTheme.colorScheme.errorContainer else MaterialTheme.colorScheme.primaryContainer,
    contentColor = if (error) MaterialTheme.colorScheme.onErrorContainer else MaterialTheme.colorScheme.onPrimaryContainer,
) {
    Row(Modifier.padding(16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Icon(Icons.Filled.Warning, contentDescription = null)
        Text(text, style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
private fun StatusLine(text: String, working: Boolean) = Column(Modifier.animateContentSize(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
    Text(text, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    if (working || text.endsWith("…")) LinearProgressIndicator(Modifier.fillMaxWidth().clip(CircleShape))
}

@Composable
private fun NoteRow(note: Note, onClick: () -> Unit) {
    val context = LocalContext.current
    Surface(
        shape = RoundedCornerShape(20.dp), color = MaterialTheme.colorScheme.surface,
        modifier = Modifier.fillMaxWidth().border(1.dp, MaterialTheme.colorScheme.outline, RoundedCornerShape(20.dp))
            .clip(RoundedCornerShape(20.dp)).clickable(role = Role.Button, onClickLabel = "Open note", onClick = onClick),
    ) {
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(note.name, Modifier.weight(1f), style = MaterialTheme.typography.titleMedium, maxLines = 1, overflow = TextOverflow.Ellipsis)
                if (note.recording) LiveDot()
            }
            when {
                note.recording -> Text("Recording now", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.error)
                note.done && note.cuts.isEmpty() -> Text("No speech found.", style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
                note.pieces.isNotEmpty() -> Text(note.allText(), style = MaterialTheme.typography.bodyMedium, maxLines = 2,
                    overflow = TextOverflow.Ellipsis, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            if (note.pending && !note.recording) LinearProgressIndicator(note.pieces.size / note.cuts.size.toFloat(),
                Modifier.fillMaxWidth().padding(vertical = 4.dp).clip(CircleShape))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("${clock(note.seconds)}  ·  ${DateUtils.getRelativeTimeSpanString(context, note.created, true)}",
                    style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Spacer(Modifier.weight(1f))
                val toCheck = note.pieces.count { it.flags.isNotEmpty() }
                if (note.done && toCheck > 0) Chip(if (toCheck == 1) "1 to check" else "$toCheck to check")
                if (note.pending && !note.recording) Chip("Writing ${note.pieces.size}/${note.cuts.size}", accent = false)
            }
        }
    }
}

@Composable
private fun Chip(text: String, accent: Boolean = true) = Surface(
    shape = CircleShape, color = if (accent) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant,
    contentColor = if (accent) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurfaceVariant,
) { Text(text, Modifier.padding(horizontal = 10.dp, vertical = 4.dp), style = MaterialTheme.typography.labelMedium) }

@Composable
private fun LiveDot() {
    var on by remember { mutableStateOf(true) }
    LaunchedEffect(Unit) { while (true) { delay(600); on = !on } }
    val a by animateFloatAsState(if (on) 1f else 0.25f, label = "live")
    Box(Modifier.size(10.dp).clip(CircleShape).background(MaterialTheme.colorScheme.error.copy(alpha = a)))
}

// ---------------------------------------------------------------- Recording

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun RecordingScreen(note: Note, onStop: () -> Unit, onMinimise: () -> Unit) {
    val haptics = LocalHapticFeedback.current
    val level by Notes.level.collectAsState()
    val bars = remember { mutableStateListOf<Float>().apply { repeat(48) { add(0f) } } }
    var seconds by remember { mutableStateOf(0.0) }
    LaunchedEffect(note.created) {
        while (true) {
            seconds = (System.currentTimeMillis() - note.created) / 1000.0
            bars.removeAt(0); bars.add(Notes.level.value)
            delay(80)
        }
    }
    val listState = rememberLazyListState()
    LaunchedEffect(note.pieces.size) { if (note.pieces.isNotEmpty()) listState.animateScrollToItem(note.pieces.size) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(note.name, maxLines = 1, overflow = TextOverflow.Ellipsis, style = MaterialTheme.typography.titleMedium) },
                navigationIcon = { IconButton(onClick = onMinimise) { Icon(Icons.Filled.ArrowBack, contentDescription = "Back (keeps recording)") } },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { pad ->
        Column(Modifier.fillMaxSize().padding(pad)) {
            Column(Modifier.fillMaxWidth().padding(horizontal = Gutter), horizontalAlignment = Alignment.CenterHorizontally) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    LiveDot()
                    Text("  " + clock(seconds), style = MaterialTheme.typography.displaySmall)
                }
                Waveform(bars, Modifier.fillMaxWidth().height(64.dp).padding(vertical = 10.dp))
                Text(if (level > 0.08f) "Listening…" else "Pause for a moment to see the text",
                    style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            LazyColumn(Modifier.weight(1f).fillMaxWidth(), state = listState,
                contentPadding = PaddingValues(horizontal = Gutter, vertical = 16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                items(note.pieces, key = { it.i }) { p ->
                    Text(note.text(p.i), style = MaterialTheme.typography.bodyLarge,
                        color = if (p.junk) MaterialTheme.colorScheme.onSurfaceVariant else MaterialTheme.colorScheme.onBackground)
                }
                if (note.pending) item { Writing() }
            }
            Box(Modifier.fillMaxWidth().navigationBarsPadding().padding(bottom = 18.dp, top = 8.dp), contentAlignment = Alignment.Center) {
                Box(
                    Modifier.size(80.dp).clip(CircleShape).background(MaterialTheme.colorScheme.error)
                        .clickable(role = Role.Button, onClickLabel = "Stop recording") {
                            haptics.performHapticFeedback(HapticFeedbackType.LongPress); onStop()
                        },
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(painterResource(R.drawable.ic_stop), contentDescription = "Stop", tint = MaterialTheme.colorScheme.onError,
                        modifier = Modifier.size(30.dp))
                }
            }
        }
    }
}

@Composable
private fun Waveform(levels: List<Float>, modifier: Modifier) {
    val color = MaterialTheme.colorScheme.primary
    Canvas(modifier) {
        val n = levels.size
        val gap = 4.dp.toPx()
        val w = (size.width - gap * (n - 1)) / n
        levels.forEachIndexed { k, v ->
            val h = (size.height * (0.08f + 0.92f * v.coerceIn(0f, 1f)))
            drawRoundRect(color.copy(alpha = 0.35f + 0.65f * (k + 1f) / n), Offset(k * (w + gap), (size.height - h) / 2),
                Size(w, h), CornerRadius(w / 2, w / 2))
        }
    }
}

@Composable
private fun Writing() {
    var dots by remember { mutableStateOf(1) }
    LaunchedEffect(Unit) { while (true) { delay(400); dots = dots % 3 + 1 } }
    Text("Writing" + ".".repeat(dots), style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
}

// ---------------------------------------------------------------- Note

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun NoteScreen(note: Note, snackbar: SnackbarHostState, onBack: () -> Unit) {
    val context = LocalContext.current
    val clipboard = LocalClipboardManager.current
    val scope = rememberCoroutineScope()
    var menu by remember { mutableStateOf(false) }
    var confirmDelete by remember { mutableStateOf(false) }
    var renaming by remember { mutableStateOf(false) }
    var editing by remember { mutableStateOf<Int?>(null) }
    var playing by remember { mutableStateOf<Int?>(null) }
    var asking by remember { mutableStateOf(false) }
    val exportSrt = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/x-subrip")) { uri ->
        if (uri != null) AppScope.launch(Dispatchers.IO) {
            context.contentResolver.openOutputStream(uri)?.use { it.write(Notes.srt(note).toByteArray()) }
            Messages.flow.tryEmit("Subtitles saved")
        }
    }

    fun copy(text: String) {
        clipboard.setText(AnnotatedString(text))
        if (Build.VERSION.SDK_INT < 33) scope.launch { snackbar.showSnackbar("Copied") }  // Android 13+ shows its own confirmation
    }

    fun play(p: Piece) {
        if (playing == p.i) { Player.stop(); playing = null; return }
        playing = p.i
        if (!Player.play(note.id, p.start, p.end) { playing = null }) {
            playing = null
            scope.launch { snackbar.showSnackbar("Couldn't play this part.") }
        }
    }

    if (confirmDelete) AlertDialog(
        onDismissRequest = { confirmDelete = false },
        title = { Text("Delete this note?") },
        text = { Text("The audio and text are removed from this phone. This can't be undone.") },
        confirmButton = { TextButton(onClick = { confirmDelete = false; Player.stop(); onBack(); Notes.delete(note.id) }) { Text("Delete") } },
        dismissButton = { TextButton(onClick = { confirmDelete = false }) { Text("Cancel") } },
    )
    if (asking) AlertDialog(
        onDismissRequest = { asking = false },
        title = { Text("Ask my AI") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("Opens your own ChatGPT, Claude or other AI app with this text and a ready request. Only the text is shared.",
                    style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(bottom = 8.dp))
                AskPrompts.forEach { (label, prompt) ->
                    TextButton(onClick = { asking = false; share(context, prompt + "\n\n---\n" + note.allText()) },
                        modifier = Modifier.fillMaxWidth()) { Text(label, Modifier.fillMaxWidth()) }
                }
            }
        },
        confirmButton = { TextButton(onClick = { asking = false }) { Text("Cancel") } },
    )
    if (renaming) RenameDialog(note.name, onDone = { renaming = false; if (it != null) Notes.rename(note.id, it) })
    editing?.let { i -> if (i < note.pieces.size) EditSheet(note, i, playing == i, onPlay = { play(note.pieces[i]) },
        onCopy = { copy(note.text(i).trim()) }, onClose = { editing = null }) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(note.name, maxLines = 1, overflow = TextOverflow.Ellipsis, style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.clickable(onClickLabel = "Rename note") { renaming = true })
                },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Filled.ArrowBack, contentDescription = "Back") } },
                actions = {
                    if (note.done && note.pieces.isNotEmpty()) IconButton(onClick = { share(context, note.allText()) }) {
                        Icon(Icons.Filled.Share, contentDescription = "Share text")
                    }
                    IconButton(onClick = { menu = true }) { Icon(Icons.Filled.MoreVert, contentDescription = "More options") }
                    DropdownMenu(expanded = menu, onDismissRequest = { menu = false }) {
                        if (note.done && note.pieces.isNotEmpty()) DropdownMenuItem(text = { Text("Ask my AI…") },
                            onClick = { menu = false; asking = true })
                        DropdownMenuItem(text = { Text("Rename") }, onClick = { menu = false; renaming = true })
                        if (note.done && note.pieces.isNotEmpty()) DropdownMenuItem(text = { Text("Save as subtitles (.srt)") },
                            onClick = { menu = false; exportSrt.launch("${note.name}.srt") })
                        DropdownMenuItem(text = { Text("Delete", color = MaterialTheme.colorScheme.error) },
                            onClick = { menu = false; confirmDelete = true })
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { pad ->
        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(pad),
            contentPadding = PaddingValues(start = Gutter, end = Gutter, top = 4.dp, bottom = 40.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            item {
                Column(Modifier.padding(bottom = 14.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("${clock(note.seconds)}  ·  ${DateUtils.getRelativeTimeSpanString(context, note.created, true)}",
                        style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    if (note.done && note.pieces.isNotEmpty()) {
                        Button(onClick = { copy(note.allText()) }, Modifier.fillMaxWidth().height(50.dp), shape = RoundedCornerShape(14.dp)) {
                            Text("Copy all text")
                        }
                        Text("Tap any paragraph to edit it, hear it or copy it.", style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant)
                    } else if (note.pending) {
                        LinearProgressIndicator(note.pieces.size / note.cuts.size.toFloat(), Modifier.fillMaxWidth().clip(CircleShape))
                        Text("Text appears part by part. You can leave the app; it keeps working.",
                            style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
            items(note.pieces, key = { it.i }) { p ->
                Paragraph(note, p, playing == p.i, onClick = { editing = p.i })
            }
            if (note.pending) item { Box(Modifier.padding(vertical = 10.dp)) { Writing() } }
        }
    }
}

@Composable
private fun Paragraph(note: Note, p: Piece, playing: Boolean, onClick: () -> Unit) {
    val edited = p.i in note.edits
    Column(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp))
            .background(if (playing) MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.5f) else MaterialTheme.colorScheme.background)
            .clickable(onClickLabel = "Edit, play or copy this part", onClick = onClick)
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(clock(p.startSec), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            if (edited) Text("  ·  edited", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
        }
        Text(note.text(p.i), style = MaterialTheme.typography.bodyLarge,
            color = if (p.junk && !edited) MaterialTheme.colorScheme.onSurfaceVariant else MaterialTheme.colorScheme.onBackground)
        if (p.flags.isNotEmpty() && !edited) FlagLine("Check: " + p.flags.joinToString(", ") { Guards.NOTE[it] ?: it })
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun EditSheet(note: Note, i: Int, playing: Boolean, onPlay: () -> Unit, onCopy: () -> Unit, onClose: () -> Unit) {
    val p = note.pieces[i]
    val sheet = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    var text by remember(note.id, i) { mutableStateOf(note.text(i)) }
    val edited = text != note.auto(i)
    val latest = rememberUpdatedState(text)
    DisposableEffect(note.id, i) {
        onDispose {  // save on close, wherever the sheet was dismissed from
            val t = latest.value
            if (t != note.text(i)) AppScope.launch(Dispatchers.IO) {
                Notes.saveEdit(note.id, i, if (t != note.auto(i)) t else null)
                Settings.learn(note.auto(i), t)?.let { Messages.suggest.tryEmit(it) }
            }
        }
    }
    ModalBottomSheet(onDismissRequest = onClose, sheetState = sheet, containerColor = MaterialTheme.colorScheme.surface) {
        Column(Modifier.fillMaxWidth().padding(horizontal = Gutter).padding(bottom = 28.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Part at ${clock(p.startSec)}", Modifier.weight(1f), style = MaterialTheme.typography.titleMedium)
                FilledTonalButton(onClick = onPlay) {
                    Icon(if (playing) Icons.Filled.Close else Icons.Filled.PlayArrow, contentDescription = null, modifier = Modifier.size(18.dp))
                    Text(if (playing) "  Stop" else "  Play")
                }
            }
            OutlinedTextField(value = text, onValueChange = { text = it },
                modifier = Modifier.fillMaxWidth().semantics { contentDescription = "Text from ${clock(p.startSec)}, editable" },
                textStyle = MaterialTheme.typography.bodyLarge, shape = RoundedCornerShape(14.dp), minLines = 3)
            if (p.flags.isNotEmpty()) FlagLine("Check: " + p.flags.joinToString(", ") { Guards.NOTE[it] ?: it })
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedButton(onClick = onCopy) { Text("Copy") }
                AnimatedVisibility(edited, enter = fadeIn(), exit = fadeOut()) {
                    OutlinedButton(onClick = { text = note.auto(i) }) { Text("Undo my edit") }
                }
                Spacer(Modifier.weight(1f))
                Button(onClick = onClose) { Text("Done") }
            }
        }
    }
}

@Composable
private fun RenameDialog(current: String, onDone: (String?) -> Unit) {
    var name by remember { mutableStateOf(current) }
    AlertDialog(
        onDismissRequest = { onDone(null) },
        title = { Text("Rename") },
        text = { OutlinedTextField(name, { name = it }, singleLine = true, modifier = Modifier.fillMaxWidth()) },
        confirmButton = { TextButton(onClick = { onDone(name) }, enabled = name.isNotBlank()) { Text("Save") } },
        dismissButton = { TextButton(onClick = { onDone(null) }) { Text("Cancel") } },
    )
}

@Composable
private fun FlagLine(text: String) = Row(verticalAlignment = Alignment.CenterVertically) {
    Icon(Icons.Filled.Warning, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(14.dp))
    Text("  $text", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
}

private fun clock(sec: Double) = sec.toInt().let { if (it >= 3600) "%d:%02d:%02d".format(it / 3600, it / 60 % 60, it % 60) else "%d:%02d".format(it / 60, it % 60) }

private fun share(context: Context, text: String) = context.startActivity(
    Intent.createChooser(Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, text), "Share text"))

/** Plays one piece of a note's audio. */
object Player {
    private var track: AudioTrack? = null

    /** Returns false if this part can't be played (missing audio, audio device busy). */
    fun play(id: String, start: Int, end: Int, onDone: () -> Unit): Boolean = try {
        stop()
        val pcm = Notes.readPcmShorts(id, start, end)
        require(pcm.isNotEmpty())
        val t = AudioTrack.Builder()
            .setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA)
                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
            .setAudioFormat(AudioFormat.Builder().setSampleRate(16000).setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                .setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build())
            .setTransferMode(AudioTrack.MODE_STATIC)
            .setBufferSizeInBytes(pcm.size * 2)
            .build()
        t.write(pcm, 0, pcm.size)
        t.notificationMarkerPosition = pcm.size
        t.setPlaybackPositionUpdateListener(object : AudioTrack.OnPlaybackPositionUpdateListener {
            override fun onMarkerReached(track: AudioTrack?) { stop(); onDone() }
            override fun onPeriodicNotification(track: AudioTrack?) {}
        })
        t.play()
        track = t
        true
    } catch (e: Exception) {
        stop()
        false
    }

    fun stop() {
        track?.run { try { stop() } catch (e: Exception) {}; release() }
        track = null
    }
}
