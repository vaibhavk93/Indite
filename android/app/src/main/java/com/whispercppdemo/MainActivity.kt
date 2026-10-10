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
import com.whispercppdemo.notes.NoteService
import com.whispercppdemo.notes.Notes
import com.whispercppdemo.notes.PhoneCheck
import com.whispercppdemo.notes.Settings
import com.whispercppdemo.notes.Theme
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.collectAsState
import com.whispercppdemo.ui.Messages
import com.whispercppdemo.ui.NotesApp
import com.whispercppdemo.ui.theme.WhisperCppDemoTheme
import com.whispercppdemo.media.decodeToPcm
import com.whispercppdemo.ui.AppScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    private var openRequest by mutableStateOf<String?>(null)

    private val pickFile = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri -> uri?.let { import(it) } }
    private val askNotifications = registerForActivityResult(ActivityResultContracts.RequestPermission()) {}
    private val askMic = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) record() else Messages.flow.tryEmit("indite needs the microphone to record. You can allow it in Settings → Apps → indite.")
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Settings.init(this)
        Notes.init(this)
        if (com.whispercppdemo.overlay.BubbleService.enabled(this)) com.whispercppdemo.overlay.BubbleService.setEnabled(this, true)
        NoteService.kick(this)  // resume anything cut short by a crash, a restart or the app being closed
        if (PhoneCheck.problem() == null) {  // warm the model up now, so the first dictation doesn't wait for it to load
            val app = applicationContext
            AppScope.launch(Dispatchers.Default) { runCatching { com.whispercppdemo.notes.Engine.get(app) } }
        }
        setContent {
            val theme by Settings.theme.collectAsState()
            WhisperCppDemoTheme(darkTheme = when (theme) {
                Theme.LIGHT -> false
                Theme.DARK -> true
                Theme.SYSTEM -> isSystemInDarkTheme()
            }) {
                NotesApp(openRequest, onOpenHandled = { openRequest = null },
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
        if (testHook(intent)) return
        intent.getStringExtra(EXTRA_NOTE)?.let { openRequest = it }
        intent.removeExtra(EXTRA_NOTE)  // don't reopen it on rotation
        @Suppress("DEPRECATION")
        val uri = when (intent.action) {
            Intent.ACTION_SEND -> intent.getParcelableExtra<Uri>(Intent.EXTRA_STREAM)
            Intent.ACTION_VIEW -> intent.data
            else -> null
        } ?: return
        intent.action = null  // don't import the same file again on rotation
        import(uri)
    }

    /**
     * Automated tests over USB (adb), restricted to files in the app's own test folder, which only the app and a
     * connected computer can write:  am start -n com.indite.app/com.whispercppdemo.MainActivity --es test_import NAME
     * (or --es test_live NAME: the file is played into the recorder in real time, as if spoken).
     */
    private fun testHook(intent: Intent): Boolean {
        val dir = getExternalFilesDir("tests") ?: return false
        intent.getStringExtra("test_label")?.let { name ->  // --es test_label NAME --ei k 2 : label speakers of a finished test note
            intent.removeExtra("test_label")
            val k = intent.getIntExtra("k", 2)
            val app = applicationContext
            AppScope.launch(Dispatchers.Default) {
                val note = Notes.list.value.firstOrNull { it.test && it.name == name && it.done } ?: return@launch
                val t0 = System.currentTimeMillis()
                runCatching { com.whispercppdemo.notes.Speakers.label(app, note, k) {} }.onFailure { Log.w("indite", "test label failed", it) }
                Notes.exportTestResult(note.id, extra = "label_ms" to (System.currentTimeMillis() - t0))
            }
            return true
        }
        val import = intent.getStringExtra("test_import")
        val live = intent.getStringExtra("test_live")
        val name = import ?: live ?: return false
        intent.removeExtra("test_import"); intent.removeExtra("test_live")
        val f = File(dir, name).canonicalFile
        if (f.parentFile != dir.canonicalFile || !f.exists()) { Log.w("indite", "test file not found: $name"); return true }
        val app = applicationContext
        AppScope.launch {
            try {
                if (import != null) {
                    Notes.import(app, Uri.fromFile(f), test = true)
                    NoteService.kick(app)
                } else {
                    val pcm = File(cacheDir, "sim-${System.currentTimeMillis()}.pcm")
                    withContext(Dispatchers.IO) { decodeToPcm(f, pcm) }
                    openRequest = NoteService.startRecording(app, simulate = pcm, name = "live " + f.nameWithoutExtension)
                }
            } catch (e: Throwable) { Log.w("indite", "test hook failed", e) }
        }
        return true
    }

    private fun record() {
        askNotificationsOnce()
        openRequest = NoteService.startRecording(this)  // if already recording, this reopens that recording
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
        val app = applicationContext
        AppScope.launch {  // app-wide, so rotating the phone doesn't cancel an import
            try {
                openRequest = Notes.import(app, uri)
                NoteService.kick(app)
            } catch (e: CancellationException) {
                throw e
            } catch (e: Notes.ImportError) {
                Messages.flow.tryEmit(e.message ?: "Couldn't open this file.")
            } catch (e: Throwable) {
                Log.w("indite", e)
                Messages.flow.tryEmit(if (e is OutOfMemoryError) "This file is too big for this phone. Try a shorter one."
                    else "Couldn't open this file. Try sharing it again, or pick another file.")
            }
        }
    }

    companion object {
        const val EXTRA_NOTE = "note"
    }
}
