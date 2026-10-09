package com.whispercppdemo.notes

import android.app.ActivityManager
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.ServiceInfo
import android.graphics.drawable.Icon
import android.os.BatteryManager
import android.os.Build
import android.os.IBinder
import android.util.Log
import com.whispercpp.whisper.WhisperContext
import com.whispercppdemo.MainActivity
import com.whispercppdemo.R
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import java.io.File

/** The model is loaded once per app process and shared. q5_K: same size as q5_0, ~48% faster on the phone (ARM fast path). */
object Engine {
    const val MODEL_ASSET = "models/ggml-apex-q5_k.bin"
    private var ctx: WhisperContext? = null
    private val lock = Mutex()

    suspend fun get(context: Context): WhisperContext = lock.withLock {
        ctx ?: withContext(Dispatchers.IO) {
            WhisperContext.createContextFromAsset(context.assets, MODEL_ASSET)
        }.also { ctx = it }
    }

    /** The Silero speech detector reads from a file path, so copy it out of the app once (885 KB). */
    @Synchronized
    fun vadPath(context: Context): String {
        val f = File(context.filesDir, "ggml-silero.bin")
        if (!f.exists()) {
            val tmp = File(context.filesDir, "ggml-silero.bin.tmp")
            context.assets.open("models/ggml-silero.bin").use { i -> tmp.outputStream().use { i.copyTo(it) } }
            tmp.renameTo(f)
        }
        return f.path
    }
}

/**
 * The one live recording, kept at app level (not inside the service), so the microphone can never outlive its
 * notification: the service stays in the foreground for as long as this is recording.
 */
object Recording {
    @Volatile private var recorder: LiveRecorder? = null
    /** Id of the note being recorded, or null. Derived from the recorder itself, so it can't go stale. */
    val id: String? get() = recorder?.takeIf { it.isAlive }?.id
    val active get() = id != null

    /** `simulate`: a 16 kHz PCM file played into the recorder in real time instead of the mic (automated tests only). */
    fun start(id: String, vadPath: String, simulate: File? = null) {
        if (active) return
        recorder = LiveRecorder(id, vadPath, simulate).also { it.start() }
    }

    fun stop() = recorder?.stop()
}

/** Old phones lack the chip features the engine is built for and would crash; say so plainly instead. */
object PhoneCheck {
    fun problem(): String? {
        val features = try {
            File("/proc/cpuinfo").readLines().firstOrNull { it.startsWith("Features") }.orEmpty()
        } catch (e: Exception) { "" }
        if (features.isNotEmpty() && !("asimddp" in features && "fphp" in features)) {
            return "This phone's processor is too old for indite's offline engine. You can still use the indite web app on a computer."
        }
        return null
    }

    fun lowRam(context: Context): Boolean {
        val m = ActivityManager.MemoryInfo()
        (context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager).getMemoryInfo(m)
        return m.totalMem < 5_500_000_000L
    }
}

/**
 * Keeps indite in the foreground while it records or transcribes, and works through unfinished notes, oldest first.
 * Every finished piece is saved before the next starts.
 */
class NoteService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private var job: Job? = null
    private val busy = mutableMapOf<String, Pair<Double, Double>>()  // note id -> (audio s, transcribing s), for the speed log

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        channel(this)
        val recordId = intent?.getStringExtra(EXTRA_RECORD)
        if (intent?.action == ACTION_STOP) Recording.stop()  // it saves the last piece on its own thread
        val recordingNow = recordId != null || Recording.active
        val n = notification(if (recordingNow) "Recording…" else "Getting ready…", ongoing = true, recording = recordingNow)
        val type = if (recordingNow) ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC or ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
                   else ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
        if (Build.VERSION.SDK_INT >= 30) startForeground(ONGOING, n, type) else startForeground(ONGOING, n)
        if (recordId != null) Recording.start(recordId, Engine.vadPath(this), intent.getStringExtra(EXTRA_SIMULATE)?.let(::File))
        if (job?.isActive != true) job = scope.launch { runQueue() }
        // Not sticky: if Android kills the app, it resumes the next time indite opens (restarting in the background isn't allowed).
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    private suspend fun runQueue() {
        Notes.working.value = true
        var failed = false
        try {
            Settings.init(this)
            Notes.init(this)
            // A note that says "recording" while nothing records was cut off by a crash: keep what was saved.
            Notes.list.value.filter { it.recording && it.id != Recording.id }.forEach {
                try { Notes.recoverRecording(this, it.id) } catch (e: Exception) { Log.w(TAG, e) }
            }
            var w: WhisperContext? = null
            while (true) {
                Notes.refresh()
                val note = Notes.list.value.filter { it.pending && it.id !in Notes.claimed }.minByOrNull { it.created }
                when {
                    note != null -> {
                        if (w == null) {
                            say("Loading the Hinglish model…")
                            w = Engine.get(this)
                        }
                        try { process(w, note) } catch (e: Exception) {
                            Log.w(TAG, e)
                            if (Notes.dir(note.id).exists()) {  // a deleted note is simply skipped
                                say("Couldn't finish \"${note.name}\". It will try again next time you open indite.")
                                failed = true
                                if (!Recording.active) break
                            }
                        }
                    }
                    Recording.active -> { updateRecording(); delay(300) }  // still recording: wait for the next pause
                    else -> break
                }
                Notes.refresh()
                Notes.list.value.filter { it.done && it.speed == null && it.id in busy }.forEach { finish(it) }
            }
            if (!failed) Notes.status.value = ""
        } catch (e: Exception) {
            Log.w(TAG, e)
            failed = true
            Notes.status.value = "Transcription stopped. Open indite to try again."
            while (Recording.active) delay(300)  // never leave the mic running without the notification
        } finally {
            Notes.refresh()
            if (!failed && (Recording.active || Notes.list.value.any { it.pending })) {
                job = scope.launch { runQueue() }  // new work arrived just as this run finished
            } else {
                Notes.working.value = false
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
            }
        }
    }

    private suspend fun process(w: WhisperContext, note: Note) {
        val t0 = System.currentTimeMillis()
        var audioDone = 0
        for (i in note.pieces.size until note.cuts.size) {
            waitUntilSafe()
            if (!Notes.dir(note.id).exists()) return  // deleted while waiting
            if (note.id in Notes.claimed) return  // the voice keyboard is handling this one
            val piece = transcribePiece(w, note, i) ?: return
            val (start, end) = piece.start to piece.end
            audioDone += end - start
            val left = note.cuts.drop(i + 1).sumOf { it[1] - it[0] }
            val rate = audioDone / ((System.currentTimeMillis() - t0) / 1000.0)  // samples per second
            say(if (note.recording || Recording.id == note.id) "Recording · ${i + 1} part(s) turned into text"
                else "${note.name}: part ${i + 1} of ${note.cuts.size}" + if (left > 0) " · about ${eta(left / rate)} left" else "")
        }
        val (a, t) = busy[note.id] ?: (0.0 to 0.0)
        busy[note.id] = (a + audioDone / SR.toDouble()) to (t + (System.currentTimeMillis() - t0) / 1000.0)
    }

    /** Speed log, kept on the phone only: every tester's phone becomes a benchmark. */
    private fun finish(note: Note) {
        val (audio, took) = busy.remove(note.id) ?: return
        Notes.finish(note.id, "%.0f s of speech in %.0f s (%.2fx) · %s · %.1f °C".format(
            audio, took, if (took > 0) audio / took else 0.0, "${Build.MANUFACTURER} ${Build.MODEL}", batteryTemp()))
        notifyDone(note)
    }

    /** Pause when the phone is hot (it slows itself down anyway) or the battery is low and not charging. */
    private suspend fun waitUntilSafe() {
        while (true) {
            val b = registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED)) ?: return
            val temp = b.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0) / 10f
            val level = b.getIntExtra(BatteryManager.EXTRA_LEVEL, 100) * 100 / b.getIntExtra(BatteryManager.EXTRA_SCALE, 100)
            val charging = b.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0) != 0
            val wait = when {
                temp >= 41f -> "Phone is warm (%.0f °C). Pausing to let it cool down…".format(temp)
                level < 15 && !charging -> "Battery low ($level%). Plug in to continue."
                else -> return
            }
            say(wait)
            delay(30_000)
        }
    }

    private fun updateRecording() {
        if (!Notes.status.value.startsWith("Recording")) say("Recording…")
    }

    private fun say(text: String) {
        Notes.status.value = text
        getSystemService(NotificationManager::class.java).notify(ONGOING, notification(text, ongoing = true, recording = Recording.active))
    }

    private fun batteryTemp() = (registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        ?.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0) ?: 0) / 10f

    private fun notifyDone(note: Note) = getSystemService(NotificationManager::class.java)
        .notify(note.id.hashCode(), notification("Text ready: ${note.name}", ongoing = false, recording = false, noteId = note.id))

    private fun notification(text: String, ongoing: Boolean, recording: Boolean, noteId: String? = null): Notification {
        val open = Intent(this, MainActivity::class.java).putExtra(MainActivity.EXTRA_NOTE, noteId ?: Recording.id)
            .addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
        val pi = PendingIntent.getActivity(this, (noteId ?: "open").hashCode(), open,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val b = Notification.Builder(this, CHANNEL)
            .setSmallIcon(R.drawable.ic_mic)
            .setContentTitle(when { recording -> "indite is recording"; ongoing -> "Turning speech into text"; else -> "indite" })
            .setContentText(text)
            .setContentIntent(pi)
            .setOngoing(ongoing)
            .setAutoCancel(!ongoing)
            .setOnlyAlertOnce(true)
        if (recording) {
            val stop = PendingIntent.getService(this, 1, Intent(this, NoteService::class.java).setAction(ACTION_STOP),
                PendingIntent.FLAG_IMMUTABLE)
            b.addAction(Notification.Action.Builder(Icon.createWithResource(this, R.drawable.ic_stop), "Stop recording", stop).build())
        }
        return b.build()
    }

    companion object {
        private const val TAG = "indite"
        private const val CHANNEL = "transcription"
        private const val ONGOING = 1
        private const val EXTRA_RECORD = "record"
        private const val EXTRA_SIMULATE = "simulate"
        private const val ACTION_STOP = "stop"

        fun channel(context: Context) = context.getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel(CHANNEL, "Recording and transcription", NotificationManager.IMPORTANCE_LOW))

        /** Start a recording (the activity has the mic permission and is on screen). Returns the note id. */
        fun startRecording(context: Context, simulate: File? = null, name: String? = null): String {
            Recording.id?.let { return it }  // one recording at a time
            val id = Notes.startRecording(name, test = simulate != null)
            context.startForegroundService(Intent(context, NoteService::class.java).putExtra(EXTRA_RECORD, id)
                .putExtra(EXTRA_SIMULATE, simulate?.path))
            return id
        }

        fun stopRecording(context: Context) {
            Recording.stop()
            context.startService(Intent(context, NoteService::class.java).setAction(ACTION_STOP))
        }

        /** Start (or wake) the queue if anything is unfinished. Safe to call often. */
        fun kick(context: Context) {
            if (PhoneCheck.problem() != null) return
            Notes.init(context)
            if (Notes.list.value.any { !it.done }) context.startForegroundService(Intent(context, NoteService::class.java))
        }

        /**
         * Transcribe part i of a note and save it. Shared by the queue and the voice keyboard.
         * Returns null if the note was deleted meanwhile.
         */
        suspend fun transcribePiece(w: WhisperContext, note: Note, i: Int): Piece? {
            val (start, end, speechMs) = note.cuts[i].let { Triple(it[0], it[1], it[2]) }
            val tries = Notes.bumpAttempt(note.id, i)
            val piece = if (tries > 2) {
                Piece(i, start, end, "[unclear]", listOf("unclear"))  // this piece crashed the engine twice: skip it, keep going
            } else {
                Notes.transcribing = true
                val e0 = System.currentTimeMillis()
                val text = try {
                    w.transcribeData(Notes.readPcm(note.id, start, end), printTimestamp = false,
                        audioCtx = Pauses.audioCtx(end - start)).trim()
                } finally { Notes.transcribing = false }
                Piece(i, start, end, text, Guards.flags(text, (end - start) / SR.toDouble(), speechMs / 1000.0),
                    latencyMs = Notes.sinceCut(note.id, i), engineMs = (System.currentTimeMillis() - e0).toInt())
            }
            if (!Notes.dir(note.id).exists()) return null
            Notes.appendPiece(note.id, piece)
            Notes.refresh()
            return piece
        }

        fun eta(seconds: Double): String = when {
            seconds < 60 -> "${seconds.toInt().coerceAtLeast(5)} s"
            else -> "${(seconds / 60).toInt() + 1} min"
        }
    }
}
