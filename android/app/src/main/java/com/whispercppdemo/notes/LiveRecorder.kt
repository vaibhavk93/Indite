package com.whispercppdemo.notes

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Process
import android.util.Log
import com.whispercpp.whisper.SpeechDetector
import java.io.File
import java.io.FileOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

/**
 * Records 16 kHz mono straight into the note's audio.pcm and adds a cut at every pause, so each spoken stretch is
 * transcribed while you keep talking. Dictation and hour-long meetings use the same path.
 * Speech vs noise comes from Silero (a small neural speech detector), so fans, traffic and clatter don't count as speech.
 * Audio is flushed to storage every 5 s: a crash or power loss costs at most the last 5 s.
 */
class LiveRecorder(val id: String, private val vadPath: String) {
    @Volatile private var running = true
    private val thread = Thread(::run, "indite-recorder")

    fun start() = thread.start()

    /** Ask the recorder to finish; it saves the last piece and closes the file on its own thread. */
    fun stop() { running = false }

    val isAlive get() = thread.isAlive

    @SuppressLint("MissingPermission")  // the activity asks for the mic before starting
    private fun run() {
        // Audio priority and a 5 s buffer: the engine uses every big core, and a dropped buffer is lost speech.
        Process.setThreadPriority(Process.THREAD_PRIORITY_URGENT_AUDIO)
        val min = AudioRecord.getMinBufferSize(SR, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
        val rec = AudioRecord(MediaRecorder.AudioSource.VOICE_RECOGNITION, SR, AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT, max(min, SR * 2 * 5))
        val vad = try { SpeechDetector(vadPath) } catch (e: Exception) { Log.w("indite", e); null }
        val out = FileOutputStream(File(Notes.dir(id), "audio.pcm"), true)
        val frame = ShortArray(W)
        val floats = FloatArray(W)
        val bytes = ByteBuffer.allocate(W * 2).order(ByteOrder.LITTLE_ENDIAN)
        val recent = ArrayDeque<Float>()  // loudness fallback only
        var total = 0
        var pieceStart = 0
        var speech = 0     // speech windows (32 ms) in the current piece
        var silent = 0     // non-speech windows in a row
        var synced = 0
        try {
            rec.startRecording()
            while (running) {
                var got = 0
                while (got < W && running) {  // always hand the detector whole 32 ms windows
                    val n = rec.read(frame, got, W - got)
                    if (n < 0) error("microphone read failed ($n)")
                    got += n
                }
                if (got < W) break
                bytes.clear()
                var s = 0.0
                for (k in 0 until W) {
                    bytes.putShort(frame[k])
                    floats[k] = frame[k] / 32768f
                    s += floats[k] * floats[k]
                }
                out.write(bytes.array())
                total += W
                val rms = sqrt(s / W).toFloat()
                Notes.level.value = min(1f, rms * 12)

                val isSpeech = if (vad != null) (vad.probs(floats, stream = true).firstOrNull() ?: 0f) >= 0.5f else {
                    recent.addLast(rms)
                    if (recent.size > 94) recent.removeFirst()
                    rms > max(recent.sorted()[recent.size / 10] * 2.5f, 0.004f)
                }
                if (isSpeech) { speech++; silent = 0 } else silent++

                val len = total - pieceStart
                // Cut at a pause (0.6 s without speech after 0.3 s of speech). Each piece costs the engine about the same
                // whatever its length, so while it's busy let pieces grow to ~15 s: fewer pieces, and it keeps up.
                val pauseAfterSpeech = speech >= 10 && silent >= 19
                val minLen = if (Notes.transcribing) 15 * SR else SR
                if ((pauseAfterSpeech && len >= minLen) || len >= 25 * SR) {
                    if (speech * MS >= 250) Notes.addCut(id, intArrayOf(pieceStart, total, speech * MS))
                    pieceStart = total; speech = 0; silent = 0
                }
                if (total - synced >= 5 * SR) { out.fd.sync(); synced = total }
            }
            if (speech * MS >= 250 && total > pieceStart) Notes.addCut(id, intArrayOf(pieceStart, total, speech * MS))
        } catch (e: Exception) {
            Log.w("indite", e)
            Notes.status.value = "Recording stopped because the microphone stopped working. What was recorded is saved."
        } finally {
            try { out.fd.sync() } catch (_: Exception) {}
            out.close()
            try { rec.stop() } catch (_: Exception) {}
            rec.release()
            vad?.release()
            Notes.level.value = 0f
            Notes.stopRecording(id, total)
        }
    }

    private companion object {
        const val W = Pauses.WINDOW  // 512 samples = 32 ms
        const val MS = 32
    }
}
