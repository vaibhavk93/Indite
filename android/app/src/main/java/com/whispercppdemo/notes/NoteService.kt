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

/** Works through unfinished notes in the background, oldest first. Every finished piece is saved before the next starts. */
class NoteService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private var job: Job? = null
    private var recorder: LiveRecorder? = null
    private val busy = mutableMapOf<String, Pair<Double, Double>>()  // note id -> (audio s, transcribing s), for the speed log

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        channel(this)
        val recordId = intent?.getStringExtra(EXTRA_RECORD)
        val n = notification(if (recordId != null) "Recording…" else "Getting ready…", ongoing = true)
        val type = if (recordId != null || recorder != null)
            ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC or ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
        else ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
        if (Build.VERSION.SDK_INT >= 30) startForeground(ONGOING, n, type) else startForeground(ONGOING, n)
        when {
            intent?.action == ACTION_STOP -> { recorder?.stop(); recorder = null }
            recordId != null && recorder == null -> recorder = LiveRecorder(recordId) { job.let { if (it?.isActive != true) job = scope.launch { runQueue() } } }.also { it.start() }
        }
        if (job?.isActive != true) job = scope.launch { runQueue() }
        return START_STICKY
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    private suspend fun runQueue() {
        try {
            Notes.init(this)
            Notes.status.value = "Loading the Hinglish model…"
            update("Loading the Hinglish model…")
            val w = Engine.get(this)
            while (true) {
                Notes.refresh()
                val note = Notes.list.value.filter { it.pending }.minByOrNull { it.created }
                when {
                    note != null -> process(w, note)
                    recorder != null -> delay(300)  // still recording: wait for the next pause
                    else -> break
                }
                Notes.refresh()
                Notes.list.value.filter { it.done && it.speed == null && it.id in busy }.forEach { finish(it) }
            }
            Notes.status.value = ""
        } catch (e: Exception) {
            Log.w(TAG, e)
            Notes.status.value = "Transcription stopped: ${e.localizedMessage}. Open indite to try again."
        } finally {
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
        }
    }

    private suspend fun process(w: WhisperContext, note: Note) {
        val t0 = System.currentTimeMillis()
        var audioDone = 0
        for (i in note.pieces.size until note.cuts.size) {
            waitUntilSafe()
            val (start, end, speechFrames) = note.cuts[i].let { Triple(it[0], it[1], it[2]) }
            val tries = Notes.bumpAttempt(note.id, i)
            val piece = if (tries > 2) {
                Piece(i, start, end, "[unclear]", listOf("unclear"))  // this piece crashed the engine twice: skip it, keep going
            } else {
                Notes.transcribing = true
                val text = try {
                    w.transcribeData(Notes.readPcm(note.id, start, end), printTimestamp = false,
                        audioCtx = Pauses.audioCtx(end - start)).trim()
                } finally { Notes.transcribing = false }
                Piece(i, start, end, text, Guards.flags(text, (end - start) / SR.toDouble(), speechFrames * 0.03))
            }
            Notes.appendPiece(note.id, piece)
            Notes.refresh()
            audioDone += end - start
            val left = note.cuts.drop(i + 1).sumOf { it[1] - it[0] }
            val rate = audioDone / ((System.currentTimeMillis() - t0) / 1000.0)  // samples per second
            val msg = if (note.recording) "Recording · ${i + 1} part(s) turned into text"
                else "${note.name}: part ${i + 1} of ${note.cuts.size}" + if (left > 0) " · about ${eta(left / rate)} left" else ""
            Notes.status.value = msg
            update(msg)
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
                temp >= 41f -> "Phone is warm (%.0f °C). Pausing to cool down…".format(temp)
                level < 15 && !charging -> "Battery low ($level%). Plug in to continue."
                else -> return
            }
            Notes.status.value = wait
            update(wait)
            delay(30_000)
        }
    }

    private fun batteryTemp() = (registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        ?.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0) ?: 0) / 10f

    private fun update(text: String) =
        getSystemService(NotificationManager::class.java).notify(ONGOING, notification(text, ongoing = true))

    private fun notifyDone(note: Note) = getSystemService(NotificationManager::class.java)
        .notify(note.id.hashCode(), notification("Text ready: ${note.name}", ongoing = false, noteId = note.id))

    private fun notification(text: String, ongoing: Boolean, noteId: String? = null): Notification {
        val open = Intent(this, MainActivity::class.java).putExtra(MainActivity.EXTRA_NOTE, noteId)
            .addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
        val pi = PendingIntent.getActivity(this, noteId?.hashCode() ?: 0, open,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        return Notification.Builder(this, CHANNEL)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle(if (ongoing) "Turning speech into text" else "indite")
            .setContentText(text)
            .setContentIntent(pi)
            .setOngoing(ongoing)
            .setAutoCancel(!ongoing)
            .setOnlyAlertOnce(true)
            .build()
    }

    companion object {
        private const val TAG = "indite"
        private const val CHANNEL = "transcription"
        private const val ONGOING = 1
        private const val EXTRA_RECORD = "record"
        private const val ACTION_STOP = "stop"
        @Volatile var recordingId: String? = null; private set

        fun startRecording(context: Context): String {
            val id = Notes.startRecording()
            recordingId = id
            context.startForegroundService(Intent(context, NoteService::class.java).putExtra(EXTRA_RECORD, id))
            return id
        }

        fun stopRecording(context: Context) {
            recordingId = null
            context.startService(Intent(context, NoteService::class.java).setAction(ACTION_STOP))
        }

        fun channel(context: Context) = context.getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel(CHANNEL, "Transcription", NotificationManager.IMPORTANCE_LOW))

        /** Start (or wake) the queue if anything is unfinished. Safe to call often. */
        fun kick(context: Context) {
            if (PhoneCheck.problem() != null) return
            Notes.init(context)
            // A recording that says "recording" while nothing records was cut off by a crash: keep what was saved.
            Notes.list.value.filter { it.recording && it.id != recordingId }.forEach { Notes.recoverRecording(it.id) }
            if (Notes.list.value.any { !it.done }) context.startForegroundService(Intent(context, NoteService::class.java))
        }

        fun eta(seconds: Double): String = when {
            seconds < 60 -> "${seconds.toInt().coerceAtLeast(5)} s"
            else -> "${(seconds / 60).toInt() + 1} min"
        }
    }
}
