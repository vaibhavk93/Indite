package com.whispercppdemo.ui

import android.content.Context
import android.content.Intent
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.os.Build
import android.text.format.DateUtils
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Surface
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import com.whispercppdemo.R
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.whispercppdemo.notes.Guards
import com.whispercppdemo.notes.Note
import com.whispercppdemo.notes.Notes
import com.whispercppdemo.notes.PhoneCheck
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** One-off messages for the snackbar (import errors, "Copied"). */
object Messages {
    val flow = MutableSharedFlow<String>(extraBufferCapacity = 4)
}

@Composable
fun NotesApp(openNote: String?, onOpenFile: () -> Unit, onRecord: () -> Unit, onStop: () -> Unit) {
    var selected by remember(openNote) { mutableStateOf(openNote) }
    val notes by Notes.list.collectAsState()
    val snackbar = remember { SnackbarHostState() }
    LaunchedEffect(Unit) { Messages.flow.collect { snackbar.showSnackbar(it) } }

    val note = notes.firstOrNull { it.id == selected }
    if (note != null) {
        BackHandler { Player.stop(); selected = null }
        NoteScreen(note, snackbar, onStop, onBack = { Player.stop(); selected = null })
    } else {
        ListScreen(notes, snackbar, onOpenFile, onRecord, onOpen = { selected = it })
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ListScreen(notes: List<Note>, snackbar: SnackbarHostState, onOpenFile: () -> Unit, onRecord: () -> Unit, onOpen: (String) -> Unit) {
    val context = LocalContext.current
    val status by Notes.status.collectAsState()
    val problem = remember { PhoneCheck.problem() }
    val lowRam = remember { PhoneCheck.lowRam(context) }
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("indite", fontWeight = FontWeight.SemiBold) },
                actions = {
                    if (problem == null) TextButton(onClick = onOpenFile) {
                        Icon(Icons.Filled.Add, contentDescription = null, modifier = Modifier.size(18.dp))
                        Text(" Open file")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
        floatingActionButton = {
            if (problem == null) ExtendedFloatingActionButton(
                onClick = onRecord,
                icon = { Icon(painterResource(R.drawable.ic_mic), contentDescription = null) },
                text = { Text("Record") },
            )
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { pad ->
        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(pad),
            contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 4.dp, bottom = 96.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            if (problem != null) item { Banner(problem, error = true) }
            else if (lowRam) item { Banner("This phone has under 6 GB of memory. Transcription may be slow or stop on long recordings.", error = false) }
            if (status.isNotBlank()) item { StatusLine(status) }
            if (notes.isEmpty()) item { EmptyState() }
            items(notes, key = { it.id }) { NoteRow(it, onClick = { onOpen(it.id) }) }
        }
    }
}

@Composable
private fun EmptyState() {
    Column(Modifier.fillMaxWidth().padding(top = 32.dp, start = 8.dp, end = 8.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("Speak. Get the text.", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
        Text("Hindi, English or both, written in Roman letters.", style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant)
        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Step("1", "Tap Record and talk, as long as you like.")
                Step("2", "After each pause, that part turns into text.")
                Step("3", "Edit, copy or share it when you're done.")
            }
        }
        Text("You can also share a voice note or audio file to indite, or tap Open file.",
            style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text("Everything stays on this phone. Nothing is uploaded.", style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun Step(n: String, text: String) = Row(verticalAlignment = Alignment.Top) {
    Text(n, style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.primary,
        fontWeight = FontWeight.Bold, modifier = Modifier.width(24.dp))
    Text(text, style = MaterialTheme.typography.bodyLarge)
}

@Composable
private fun Banner(text: String, error: Boolean) = Card(
    colors = CardDefaults.cardColors(
        containerColor = if (error) MaterialTheme.colorScheme.errorContainer else MaterialTheme.colorScheme.primaryContainer,
        contentColor = if (error) MaterialTheme.colorScheme.onErrorContainer else MaterialTheme.colorScheme.onPrimaryContainer,
    ),
) {
    Row(Modifier.padding(16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Icon(Icons.Filled.Warning, contentDescription = null)
        Text(text, style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
private fun StatusLine(text: String) = Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
    Text(text, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    LinearProgressIndicator(Modifier.fillMaxWidth())
}

@Composable
private fun NoteRow(note: Note, onClick: () -> Unit) {
    val context = LocalContext.current
    Card(
        modifier = Modifier.fillMaxWidth().clickable(role = Role.Button, onClickLabel = "Open note", onClick = onClick),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(note.name, style = MaterialTheme.typography.titleMedium, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text("${clock(note.seconds)} · ${DateUtils.getRelativeTimeSpanString(context, note.created, true)}",
                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            when {
                note.cuts.isEmpty() -> Text("No speech found in this file.", style = MaterialTheme.typography.bodyMedium)
                !note.done -> {
                    LinearProgressIndicator(note.pieces.size / note.cuts.size.toFloat(), Modifier.fillMaxWidth().padding(top = 4.dp))
                    Text(if (note.pieces.isEmpty()) "Waiting to start…" else "Part ${note.pieces.size} of ${note.cuts.size} done",
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                else -> {
                    Text(note.allText(), style = MaterialTheme.typography.bodyMedium, maxLines = 2, overflow = TextOverflow.Ellipsis)
                    val toCheck = note.pieces.count { it.flags.isNotEmpty() }
                    if (toCheck > 0) FlagLine(if (toCheck == 1) "1 part to check" else "$toCheck parts to check")
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun NoteScreen(note: Note, snackbar: SnackbarHostState, onStop: () -> Unit, onBack: () -> Unit) {
    val context = LocalContext.current
    val clipboard = LocalClipboardManager.current
    var confirmDelete by remember { mutableStateOf(false) }
    var playing by remember { mutableStateOf<Int?>(null) }
    val scope = rememberCoroutineScope()
    val listState = rememberLazyListState()
    LaunchedEffect(note.pieces.size) {  // while recording, keep the newest text in view
        if (note.recording && note.pieces.isNotEmpty()) listState.animateScrollToItem(note.pieces.size)
    }

    if (confirmDelete) AlertDialog(
        onDismissRequest = { confirmDelete = false },
        title = { Text("Delete this note?") },
        text = { Text("The audio and text are removed from this phone. This can't be undone.") },
        confirmButton = { TextButton(onClick = { confirmDelete = false; Player.stop(); onBack(); Notes.delete(note.id) }) { Text("Delete") } },
        dismissButton = { TextButton(onClick = { confirmDelete = false }) { Text("Cancel") } },
    )

    fun copy(text: String) {
        clipboard.setText(AnnotatedString(text))
        if (Build.VERSION.SDK_INT < 33) scope.launch { snackbar.showSnackbar("Copied") }  // Android 13+ shows its own confirmation
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(note.name, maxLines = 1, overflow = TextOverflow.Ellipsis) },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Filled.ArrowBack, contentDescription = "Back") } },
                actions = {
                    if (note.done) IconButton(onClick = { share(context, note.allText()) }) {
                        Icon(Icons.Filled.Share, contentDescription = "Share text")
                    }
                    if (!note.recording) IconButton(onClick = { confirmDelete = true }) {
                        Icon(Icons.Filled.Delete, contentDescription = "Delete note")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
        bottomBar = { if (note.recording) RecordingBar(note.created, onStop) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { pad ->
        LazyColumn(
            state = listState,
            modifier = Modifier.fillMaxSize().padding(pad),
            contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 4.dp, bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("${clock(note.seconds)} · ${DateUtils.getRelativeTimeSpanString(context, note.created, true)}",
                        style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    if (note.done && note.pieces.isNotEmpty()) {
                        FilledTonalButton(onClick = { copy(note.allText()) }, modifier = Modifier.fillMaxWidth()) { Text("Copy all text") }
                    } else if (note.recording) {
                        Text("Talk naturally. Each part turns into text a few seconds after you pause.",
                            style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    } else if (!note.done) {
                        LinearProgressIndicator(note.pieces.size / note.cuts.size.toFloat(), Modifier.fillMaxWidth())
                        Text("Text appears part by part. You can leave the app; you'll get a notification when it's ready.",
                            style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
            items(note.pieces, key = { it.i }) { p ->
                PieceCard(
                    note = note, i = p.i, playing = playing == p.i,
                    onPlay = {
                        if (playing == p.i) { Player.stop(); playing = null }
                        else { playing = p.i; Player.play(note.id, p.start, p.end) { playing = null } }
                    },
                    onCopy = { copy(note.text(p.i).trim()) },
                )
            }
            if (!note.done) items(note.cuts.size - note.pieces.size) { k ->
                Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                    Text("${clock(note.cuts[note.pieces.size + k][0] / 16000.0)} · ${if (k == 0) "working on it…" else "waiting"}",
                        Modifier.padding(16.dp), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            note.speed?.let { item { Text("Speed: $it", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) } }
        }
    }
}

@Composable
private fun PieceCard(note: Note, i: Int, playing: Boolean, onPlay: () -> Unit, onCopy: () -> Unit) {
    val p = note.pieces[i]
    var text by remember(note.id, i) { mutableStateOf(note.text(i)) }
    LaunchedEffect(text) {  // save edits half a second after typing stops; the original text is kept separately
        if (text == note.text(i)) return@LaunchedEffect
        delay(500)
        withContext(Dispatchers.IO) { Notes.saveEdit(note.id, i, text) }
    }
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(start = 12.dp, end = 12.dp, top = 4.dp, bottom = 12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = onPlay) {
                    Icon(if (playing) Icons.Filled.Close else Icons.Filled.PlayArrow,
                        contentDescription = if (playing) "Stop playing" else "Play this part")
                }
                Text(clock(p.startSec), style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                if (text != p.text) Text("  · edited", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
                Spacer(Modifier.weight(1f))
                TextButton(onClick = onCopy) { Text("Copy") }
            }
            OutlinedTextField(value = text, onValueChange = { text = it }, modifier = Modifier.fillMaxWidth(),
                textStyle = MaterialTheme.typography.bodyLarge)
            if (p.flags.isNotEmpty()) FlagLine("Check: " + p.flags.joinToString(", ") { Guards.NOTE[it] ?: it }, Modifier.padding(top = 8.dp))
            if (text != p.text) Row(Modifier.padding(top = 4.dp)) {
                OutlinedButton(onClick = { text = p.text }) { Text("Undo my edit") }
            }
        }
    }
}

@Composable
private fun FlagLine(text: String, modifier: Modifier = Modifier) = Row(modifier, verticalAlignment = Alignment.CenterVertically) {
    Icon(Icons.Filled.Warning, contentDescription = null, tint = MaterialTheme.colorScheme.error, modifier = Modifier.size(16.dp))
    Text("  $text", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.error)
}

@Composable
private fun RecordingBar(started: Long, onStop: () -> Unit) {
    val level by Notes.level.collectAsState()
    var seconds by remember { mutableStateOf(0.0) }
    LaunchedEffect(started) { while (true) { seconds = (System.currentTimeMillis() - started) / 1000.0; delay(500) } }
    Surface(color = MaterialTheme.colorScheme.surfaceVariant, tonalElevation = 3.dp) {
        Row(Modifier.fillMaxWidth().navigationBarsPadding().padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Box(Modifier.size(10.dp).clip(CircleShape).background(MaterialTheme.colorScheme.error))
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("Recording  ${clock(seconds)}", style = MaterialTheme.typography.titleSmall)
                LinearProgressIndicator(level, Modifier.fillMaxWidth().semantics { contentDescription = "Microphone level" })
            }
            Button(onClick = onStop, colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error,
                contentColor = MaterialTheme.colorScheme.onError)) {
                Icon(painterResource(R.drawable.ic_stop), contentDescription = null, modifier = Modifier.size(18.dp))
                Text("  Stop")
            }
        }
    }
}

private fun clock(sec: Double) = "%d:%02d".format(sec.toInt() / 60, sec.toInt() % 60)

private fun share(context: Context, text: String) = context.startActivity(
    Intent.createChooser(Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, text), "Share text"))

/** Plays one piece of a note's audio. */
object Player {
    private var track: AudioTrack? = null

    fun play(id: String, start: Int, end: Int, onDone: () -> Unit) {
        stop()
        val pcm = Notes.readPcmShorts(id, start, end)
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
    }

    fun stop() {
        track?.run { try { stop() } catch (e: Exception) {}; release() }
        track = null
    }
}
