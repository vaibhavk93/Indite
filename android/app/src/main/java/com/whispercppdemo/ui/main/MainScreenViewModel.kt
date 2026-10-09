package com.whispercppdemo.ui.main

import android.app.Application
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Build
import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.whispercpp.whisper.WhisperContext
import com.whispercppdemo.media.decodeWaveFile
import com.whispercppdemo.recorder.Recorder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import java.io.File

private const val LOG_TAG = "indite"

/** Pass bar for the speed test (unproven, set 2026-10-09): 15 min of audio in <= 15 min. */
const val PASS_SPEED = 1.0

/** 15 s audio window (whisper.cpp audio_ctx) for short clips; 7.7 s (384) started looping in the Mac test. */
const val SHORT_CTX = 768

enum class Phase { LOADING, READY, RUNNING, DONE, STOPPED, ERROR }

data class Result(
    val audioMin: Double, val tookMin: Double, val speed: Double,
    val startTemp: Float, val endTemp: Float, val peakMemory: String, val device: String,
    val shortSec: Double,  // time to turn one 4-s sentence into text: decides live dictation (<= 3 s good, > 8 s too slow)
    val shortSec15: Double,  // same sentence with a 15 s window instead of 30 s (tested on the Mac: 0 loops, 7% words differ)
    val shortDetail: String,  // what each window wrote + fast-window time by number of cores
) {
    val passed get() = speed >= PASS_SPEED
    fun shareText() = """
        indite phone speed test
        Phone: $device
        ${"%.1f".format(audioMin)} min of audio in ${"%.1f".format(tookMin)} min = ${"%.2f".format(speed)}x real time
        Result: ${if (passed) "PASS" else "TOO SLOW"} (bar: 1.0x or faster)
        One 4-s sentence: ${"%.1f".format(shortSec)} s to text (30 s window), ${"%.1f".format(shortSec15)} s (15 s window)
        Battery: ${startTemp} C -> ${endTemp} C
        Peak memory: $peakMemory
        $shortDetail
        Threads: ${com.whispercpp.whisper.WhisperCpuConfig.preferredThreadCount} · ${com.whispercpp.whisper.WhisperContext.getSystemInfo().trim()}
    """.trimIndent()
}

class MainScreenViewModel(private val application: Application) : ViewModel() {
    var phase by mutableStateOf(Phase.LOADING); private set
    var status by mutableStateOf("Getting ready…"); private set
    var piecesDone by mutableStateOf(0); private set
    var piecesTotal by mutableStateOf(0); private set
    var audioDoneSec by mutableStateOf(0.0); private set
    var audioTotalSec by mutableStateOf(0.0); private set
    var elapsedSec by mutableStateOf(0.0); private set
    var temp by mutableStateOf(0f); private set
    var result by mutableStateOf<Result?>(null); private set
    val lines = mutableStateListOf<String>()

    var isRecording by mutableStateOf(false); private set
    var voiceText by mutableStateOf(""); private set

    val device = "${Build.MANUFACTURER} ${Build.MODEL} · Android ${Build.VERSION.RELEASE} · " +
        "${Runtime.getRuntime().availableProcessors()} cores · ${totalRamGb()} GB RAM"

    private val samplesPath = File(application.filesDir, "samples")
    private var whisper: WhisperContext? = null
    private var job: Job? = null
    private val recorder = Recorder()
    private var recordedFile: File? = null

    init { load() }

    /** Unpack the test audio, then load the model. Also used by "Try again" after an error. */
    fun load() {
        phase = Phase.LOADING
        viewModelScope.launch {
            try {
                status = "Step 1 of 2: unpacking the test audio…"
                withContext(Dispatchers.IO) { application.copyAssets("samples", samplesPath) }
                val files = pieces()
                piecesTotal = files.size
                audioTotalSec = files.sumOf { (it.length() - 44) / 32000.0 }  // 16 kHz, 16-bit mono WAV
                if (whisper == null) {
                    val t0 = System.currentTimeMillis()
                    val ticker = launch {
                        while (true) {
                            status = "Step 2 of 2: loading the Hinglish model (547 MB). " +
                                "This can take a few minutes on first open… ${(System.currentTimeMillis() - t0) / 1000} s"
                            delay(1000)
                        }
                    }
                    try {
                        whisper = withContext(Dispatchers.IO) {
                            WhisperContext.createContextFromAsset(application.assets, "models/ggml-apex-q5_0.bin")
                        }
                    } finally { ticker.cancel() }
                }
                temp = batteryTemp()
                phase = Phase.READY
                status = "Ready. Read the tips below, then tap Start."
            } catch (e: Exception) {
                Log.w(LOG_TAG, e)
                phase = Phase.ERROR
                status = "Couldn't load: ${e.localizedMessage}. Close the app and open it again. " +
                    "If it fails again, the phone may not have enough free memory."
            }
        }
    }

    private fun pieces() = samplesPath.listFiles()!!.filter { it.extension == "wav" }.sortedBy { it.name }

    fun start() {
        if (phase != Phase.READY && phase != Phase.DONE && phase != Phase.STOPPED) return
        phase = Phase.RUNNING; result = null; lines.clear()
        piecesDone = 0; audioDoneSec = 0.0; elapsedSec = 0.0
        status = "Running. Keep this screen open and the phone unplugged."
        job = viewModelScope.launch {
            // Short sentence first: measured on a cool phone, and a bug in the new window setting shows in ~1 min, not after 28.
            val short30: Double
            val short15: Double
            try {
                status = "Step 1 of 2: timing one short sentence (a few minutes)…"
                short30 = shortClipSec(0)
                short15 = shortClipSec(SHORT_CTX)
                lines.add("One 4-s sentence: %.1f s normal, %.1f s fast window".format(short30, short15))
                lines.add("Normal window wrote: " + shortClipText(0))
                lines.add("Fast window wrote: " + shortClipText(SHORT_CTX))
                // Cores test: we use at most 4 today; this phone may have more fast cores.
                val n = Runtime.getRuntime().availableProcessors()
                val threadTimes = listOf(2, 4, 6, 8).filter { it <= n }.map { t -> t to shortClipSec(SHORT_CTX, t) }
                lines.add("Fast window by cores: " + threadTimes.joinToString(" · ") { (t, sec) -> "$t cores %.1f s".format(sec) })
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                Log.w(LOG_TAG, e)
                phase = Phase.ERROR
                status = "The short-sentence timing failed (${e.localizedMessage}). Tell Claude."
                return@launch
            }
            status = "Step 2: the 15-min test. Keep this screen open and the phone unplugged."
            val startTemp = batteryTemp()
            val t0 = System.currentTimeMillis()
            val clock = launch { while (true) { elapsedSec = (System.currentTimeMillis() - t0) / 1000.0; delay(1000) } }
            try {
                for (f in pieces()) {
                    if (!isActive) break
                    val data = withContext(Dispatchers.IO) { decodeWaveFile(f) }
                    val text = whisper?.transcribeData(data, printTimestamp = false)?.trim().orEmpty()  // full window: keeps before/after fair
                    piecesDone++
                    audioDoneSec += data.size / 16000.0
                    temp = batteryTemp()
                    if (text.isNotEmpty()) lines.add(text)
                }
                clock.cancel()
                elapsedSec = (System.currentTimeMillis() - t0) / 1000.0
                val r = Result(audioDoneSec / 60, elapsedSec / 60, audioDoneSec / elapsedSec,
                    startTemp, batteryTemp(), peakMemory(), device, short30, short15, lines.take(4).drop(1).joinToString("\n"))
                result = r
                phase = Phase.DONE
                status = if (r.passed) "Done. Your phone passed. Share the result with Claude."
                         else "Done. Your phone was too slow for long recordings. Share the result with Claude."
            } catch (e: CancellationException) {
                throw e  // the user tapped Stop: stop() already set the screen
            } catch (e: Exception) {
                Log.w(LOG_TAG, e)
                phase = Phase.ERROR
                status = "The test stopped unexpectedly (${e.localizedMessage}). Tap Try again."
            } finally {
                clock.cancel()
            }
        }
    }

    /** Average of 3 runs on the first 4 s of the first piece. Whisper pads every clip to 30 s, so this is the per-pause wait. */
    private suspend fun shortClip() = withContext(Dispatchers.IO) { decodeWaveFile(pieces().first()) }.copyOf(4 * 16000)

    private suspend fun shortClipSec(audioCtx: Int, threads: Int = 0): Double {
        val clip = shortClip()
        val t0 = System.currentTimeMillis()
        repeat(3) { whisper?.transcribeData(clip, printTimestamp = false, audioCtx = audioCtx, threads = threads) }
        return (System.currentTimeMillis() - t0) / 3000.0
    }

    private suspend fun shortClipText(audioCtx: Int) =
        whisper?.transcribeData(shortClip(), printTimestamp = false, audioCtx = audioCtx)?.trim().orEmpty().ifEmpty { "(nothing)" }

    fun stop() {
        job?.cancel()
        phase = Phase.STOPPED
        status = "Stopped. The piece in progress finishes in the background. Tap Start to run the full test again."
    }

    fun toggleRecord() = viewModelScope.launch {
        try {
            if (isRecording) {
                recorder.stopRecording()
                isRecording = false
                voiceText = "Turning your voice into text…"
                val data = withContext(Dispatchers.IO) { decodeWaveFile(recordedFile!!) }
                val t0 = System.currentTimeMillis()
                val ctx = if (data.size <= 14 * 16000) SHORT_CTX else 0  // 15 s window only fits clips under ~14 s
                val text = whisper?.transcribeData(data, printTimestamp = false, audioCtx = ctx)?.trim().orEmpty()
                val took = "(%.1f s of speech, %.1f s to text)".format(data.size / 16000.0, (System.currentTimeMillis() - t0) / 1000.0)
                voiceText = if (text.isEmpty()) "No speech heard. Try again, a little closer to the phone." else "$text\n\n$took"
            } else {
                val file = withContext(Dispatchers.IO) { File.createTempFile("voice", ".wav") }
                recorder.startRecording(file) { e -> viewModelScope.launch { voiceText = "Recording failed: ${e.localizedMessage}"; isRecording = false } }
                recordedFile = file
                isRecording = true
                voiceText = "Listening… speak in Hindi, English or both, then tap Stop."
            }
        } catch (e: Exception) {
            Log.w(LOG_TAG, e)
            isRecording = false
            voiceText = "Recording failed: ${e.localizedMessage}"
        }
    }

    private fun batteryTemp(): Float {
        val i = application.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        return (i?.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0) ?: 0) / 10f
    }

    private fun peakMemory() = File("/proc/self/status").readLines()
        .firstOrNull { it.startsWith("VmHWM") }?.substringAfter(":")?.trim() ?: "?"

    private fun totalRamGb() = File("/proc/meminfo").readLines().firstOrNull { it.startsWith("MemTotal") }
        ?.filter { it.isDigit() }?.toLongOrNull()?.let { Math.round(it / 1e6) } ?: 0

    override fun onCleared() {
        runBlocking { whisper?.release(); whisper = null }
    }

    companion object {
        fun factory() = viewModelFactory {
            initializer {
                MainScreenViewModel(this[ViewModelProvider.AndroidViewModelFactory.APPLICATION_KEY] as Application)
            }
        }
    }
}

private fun Context.copyAssets(dir: String, dest: File) {
    dest.mkdirs()
    assets.list(dir)?.forEach { name ->
        val out = File(dest, name)
        if (!out.exists()) assets.open("$dir/$name").use { i -> out.outputStream().use { i.copyTo(it) } }
    }
}
