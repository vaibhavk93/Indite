package com.whispercppdemo

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.lifecycleScope
import com.whispercppdemo.notes.NoteService
import com.whispercppdemo.notes.Notes
import com.whispercppdemo.notes.PhoneCheck
import com.whispercppdemo.ui.Messages
import com.whispercppdemo.ui.NotesApp
import com.whispercppdemo.ui.theme.WhisperCppDemoTheme
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    private var openNote by mutableStateOf<String?>(null)

    private val pickFile = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri -> uri?.let { import(it) } }
    private val askNotifications = registerForActivityResult(ActivityResultContracts.RequestPermission()) {}
    private val askMic = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) record() else Messages.flow.tryEmit("indite needs the microphone to record. You can allow it in Settings → Apps → indite.")
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Notes.init(this)
        NoteService.kick(this)  // resume anything cut short by a crash, a restart or the app being closed
        setContent {
            WhisperCppDemoTheme {
                NotesApp(openNote,
                    onOpenFile = { pickFile.launch(arrayOf("audio/*", "video/*")) },
                    onRecord = {
                        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) record()
                        else askMic.launch(Manifest.permission.RECORD_AUDIO)
                    },
                    onStop = { NoteService.stopRecording(this) })
            }
        }
        handle(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handle(intent)
    }

    private fun handle(intent: Intent?) {
        intent ?: return
        intent.getStringExtra(EXTRA_NOTE)?.let { openNote = it }
        @Suppress("DEPRECATION")
        val uri = when (intent.action) {
            Intent.ACTION_SEND -> intent.getParcelableExtra<Uri>(Intent.EXTRA_STREAM)
            Intent.ACTION_VIEW -> intent.data
            else -> null
        } ?: return
        intent.action = null  // don't import the same file again on rotation
        import(uri)
    }

    private fun record() {
        if (NoteService.recordingId != null) { openNote = NoteService.recordingId; return }  // one recording at a time
        askNotificationsOnce()
        openNote = NoteService.startRecording(this)
    }

    private fun askNotificationsOnce() {
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            askNotifications.launch(Manifest.permission.POST_NOTIFICATIONS)  // only to say "text ready"; optional
        }
    }

    private fun import(uri: Uri) {
        PhoneCheck.problem()?.let { Messages.flow.tryEmit(it); return }
        askNotificationsOnce()
        lifecycleScope.launch {
            try {
                openNote = Notes.import(this@MainActivity, uri)
                NoteService.kick(this@MainActivity)
            } catch (e: Exception) {
                Log.w("indite", e)
                Messages.flow.tryEmit("Couldn't open this file. Try sharing the voice note again, or pick another file.")
            }
        }
    }

    companion object {
        const val EXTRA_NOTE = "note"
    }
}
