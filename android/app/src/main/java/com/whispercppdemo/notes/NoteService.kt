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
    /** The mic is really capturing for note [id] (an older, finished recorder doesn't count). */
    fun listening(id: String) = recorder?.let { it.id == id && it.isAlive && it.listening } == true

    /** `simulate`: a 16 kHz PCM file played into the recorder in real time instead of the mic (automated tests only). */
    fun start(context: Context, id: String, vadPath: String, simulate: File? = null) {
        if (active) return
        recorder = LiveRecorder(id, vadPath, simulate, context.applicationContext).also { it.start() }
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
        // Keep the microphone type until the recorder has really finished: dropping it on "stop" cut the mic off
        // mid-read, the last piece was lost, and short dictations came out "No speech found" (2026-10-10).
        val recordingNow = recordId != null || Recording.active
        val n = notification(if (recordingNow) "Recording…" else "Getting ready…", ongoing = true, recording = recordingNow)
        val type = if (recordingNow) ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC or ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
                   else ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
        if (Build.VERSION.SDK_INT >= 30) startForeground(ONGOING, n, type) else startForeground(ONGOING, n)
        if (recordId != null) Recording.start(this, recordId, Engine.vadPath(this), intent.getStringExtra(EXTRA_SIMULATE)?.let(::File))
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
            var stamp = ""
            while (true) {
                // While only recording, re-read notes just when the recording's files changed (not 3x a second).
                val rid = Recording.id
                val now = rid?.let { val d = Notes.dir(it); "${File(d, "cuts.json").length()}:${File(d, "transcript.jsonl").length()}" } ?: ""
                if (rid == null || now != stamp) { Notes.refresh(); stamp = now }
                copyBubbleDictations()
                // A live recording always goes first (someone is waiting for each sentence); imports wait their turn.
                val waiting = Notes.list.value.filter { it.pending && it.id !in Notes.claimed }
                val note = waiting.firstOrNull { it.id == Recording.id }
                    ?: waiting.filter { it.live }.maxByOrNull { it.created }  // a recording that just ended: someone is waiting
                    ?: waiting.minByOrNull { it.created }
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
                    Recording.active -> { updateRecording(); delay(300); continue }  // still recording: wait for the next pause
                    else -> { copyBubbleDictations(); break }
                }
                Notes.refresh()
                Notes.list.value.filter { it.done && it.speed == null && it.id in busy }.forEach { finish(it) }
            }
            if (!failed) Notes.status.value = ""
        } catch (e: Exception) {
            Log.w(TAG, e)
            failed = true
            com.whispercppdemo.overlay.BubbleService.pending.clear()
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
            // a recording started meanwhile: stop this import after the current part; the queue picks the recording next
            if (!note.live && Notes.list.value.any { it.live && it.pending && it.id != note.id } && i > note.pieces.size) break
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

    /**
     * Floating-button dictations: once a note is done, copy its text so it's ready to paste. A note with no speech,
     * or one whose writing failed, is cleared too, with a short message instead of silence.
     */
    private fun copyBubbleDictations() {
        val bubble = com.whispercppdemo.overlay.BubbleService.pending
        if (bubble.isEmpty()) return
        val cancelled = com.whispercppdemo.overlay.BubbleService.cancelled
        for (id in bubble.toList()) {
            val n = Notes.note(id)
            if (n == null) { bubble -= id; cancelled -= id; continue }
            if (id in cancelled) {  // thrown away by the user: delete once the recorder has let go of it
                if (!n.recording && id != Recording.id) { bubble -= id; cancelled -= id; Notes.delete(id) }
                continue
            }
            if (!n.done) continue
            bubble -= id
            val text = n.allText()
            val msg = when {
                text.isBlank() -> "indite didn't hear any speech."
                com.whispercppdemo.overlay.AutoPaste.paste(this, text) -> "Typed in."
                com.whispercppdemo.overlay.BubbleService.autoCopy(this) -> {
                    getSystemService(android.content.ClipboardManager::class.java).setPrimaryClip(android.content.ClipData.newPlainText("indite", text))
                    if (Build.VERSION.SDK_INT >= 33) null else "Copied. Long-press a text box to paste."
                }
                else -> { com.whispercppdemo.overlay.BubbleService.readyText = text; "Text ready: tap the green button to copy." }
            }
            msg?.let { android.os.Handler(mainLooper).post { android.widget.Toast.makeText(this, it, android.widget.Toast.LENGTH_SHORT).show() } }
        }
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

    private fun notifyDone(note: Note) {
        val fresh = Notes.note(note.id) ?: return
        val text = fresh.allText()
        val n = notification("Text ready: ${note.name}", ongoing = false, recording = false, noteId = note.id)
        val b = Notification.Builder.recoverBuilder(this, n)
            .setVisibility(Notification.VISIBILITY_PRIVATE)
            .setPublicVersion(Notification.Builder(this, CHANNEL).setSmallIcon(R.drawable.ic_mic)
                .setContentTitle("indite").setContentText("Text ready").build())
        if (text.isNotEmpty()) {
            b.setContentText(text).setStyle(Notification.BigTextStyle().bigText(text.take(400)).setBigContentTitle("Text ready: ${note.name}"))
            val copy = PendingIntent.getBroadcast(this, note.id.hashCode(),
                Intent(this, CopyReceiver::class.java).putExtra(CopyReceiver.EXTRA_NOTE, note.id), PendingIntent.FLAG_IMMUTABLE)
            b.addAction(Notification.Action.Builder(Icon.createWithResource(this, R.drawable.ic_mic), "Copy text", copy).build())
        }
        getSystemService(NotificationManager::class.java).notify(note.id.hashCode(), b.build())
    }

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
                val segs = try {
                    val audio = Notes.readPcm(note.id, start, end)
                    // sentences with times, shifted to positions in the whole note (samples)
                    suspend fun run(x: FloatArray, from: Int, ctx: Int) =
                        w.transcribeSegments(x, ctx).map { Seg(from + it.startMs * SR / 1000, from + it.endMs * SR / 1000, it.text) }
                    var best = run(audio, start, Pauses.audioCtx(end - start))
                    // Dropped-text guard. On the phone test, 1 in 5 pieces silently lost words (0.4-0.9 words per second of
                    // speech; normal ones 1.9-2.6). Re-run those with the full window, then in two halves; keep whichever
                    // has the most words and doesn't loop.
                    // Live recordings only: on imports it made things worse (15-min test WER 25.5% -> 30.6%; "most words"
                    // picked noise gibberish and half-pieces). Imports have no one waiting, but the plain pass was best there.
                    if (note.live && sparse(best, speechMs)) {
                        best = better(best, run(audio, start, Pauses.FULL))  // largest window, still a multiple of 256
                        if (sparse(best, speechMs) && audio.size > 8 * SR) {
                            val mid = audio.size / 2
                            best = better(best, run(audio.copyOfRange(0, mid), start, Pauses.audioCtx(mid)) +
                                run(audio.copyOfRange(mid, audio.size), start + mid, Pauses.audioCtx(audio.size - mid)))
                        }
                    }
                    best
                } finally { Notes.transcribing = false }
                val text = segs.joinToString(" ") { it.text }.trim()
                Piece(i, start, end, text, Guards.flags(text, (end - start) / SR.toDouble(), speechMs / 1000.0),
                    latencyMs = Notes.sinceCut(note.id, i), engineMs = (System.currentTimeMillis() - e0).toInt(), segs = segs)
            }
            if (!Notes.dir(note.id).exists()) return null
            Notes.appendPiece(note.id, piece)
            Notes.autoTitle(note.id, piece)
            Notes.refresh()
            return piece
        }

        // Invented text in silence: the model gives no usable signal. Measured on the Mac (10 Oct, apex-q5_k):
        // pink noise -> "CTR tin percent aaya hai", no_speech_prob 0.000, word confidence 95.5%; pure silence ->
        // "Mummy office mein late ho jaega", 0.000 / 88.5%; real speech 0.000 / 94.9%. Neither the no-speech
        // probability nor confidence separates invented text from real text, so no filter after the model can work.
        // The only place left is before it: keep non-speech audio out (Silero, see Pauses.speechFromProbs).
        private fun words(s: List<Seg>) = s.sumOf { seg -> seg.text.split(Regex("\\s+")).count { it.isNotBlank() } }
        /** Under 1.2 words per second of detected speech (over at least 4 s): text was probably dropped. */
        private fun sparse(s: List<Seg>, speechMs: Int) = speechMs >= 4000 && words(s) < 1.2 * speechMs / 1000.0
        private fun better(a: List<Seg>, b: List<Seg>) =
            if (words(b) > words(a) && !Guards.hasLoop(b.joinToString(" ") { it.text })) b else a

        fun eta(seconds: Double): String = when {
            seconds < 60 -> "${seconds.toInt().coerceAtLeast(5)} s"
            else -> "${(seconds / 60).toInt() + 1} min"
        }
    }
}
