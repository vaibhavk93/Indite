package com.whispercppdemo.notes

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.util.Log
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
 * Audio is flushed to storage every 5 s: a crash or power loss costs at most the last 5 s.
 */
class LiveRecorder(private val id: String, private val onCut: () -> Unit) {
    @Volatile private var running = true
    private val thread = Thread(::run, "indite-recorder")

    fun start() = thread.start()

    fun stop() {
        running = false
        thread.join(5_000)
    }

    @SuppressLint("MissingPermission")  // the activity asks for the mic before starting
    private fun run() {
        val min = AudioRecord.getMinBufferSize(SR, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
        val rec = AudioRecord(MediaRecorder.AudioSource.VOICE_RECOGNITION, SR, AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT, max(min, SR * 2))
        val out = FileOutputStream(File(Notes.dir(id), "audio.pcm"), true)
        val frame = ShortArray(FRAME)
        val bytes = ByteBuffer.allocate(FRAME * 2).order(ByteOrder.LITTLE_ENDIAN)
        val recent = ArrayDeque<Float>()
        var total = 0
        var pieceStart = 0
        var speech = 0     // frames with speech in the current piece
        var silent = 0     // silent frames in a row
        var synced = 0
        try {
            rec.startRecording()
            while (running) {
                val n = rec.read(frame, 0, FRAME)
                if (n < 0) error("microphone read failed ($n)")
                if (n == 0) continue
                bytes.clear()
                for (k in 0 until n) bytes.putShort(frame[k])
                out.write(bytes.array(), 0, n * 2)
                total += n

                var s = 0.0
                for (k in 0 until n) s += (frame[k] / 32768.0) * (frame[k] / 32768.0)
                val rms = sqrt(s / n).toFloat()
                Notes.level.value = min(1f, rms * 12)
                recent.addLast(rms)
                if (recent.size > 100) recent.removeFirst()  // last 3 s sets the noise level
                val noise = recent.sorted()[recent.size / 10]
                if (rms > max(noise * 2.5f, 0.004f)) { speech++; silent = 0 } else silent++

                val len = total - pieceStart
                // Cut at a pause (0.6 s quiet after 0.3 s of speech). Each piece costs the engine about the same
                // whatever its length, so while it's busy let pieces grow to ~15 s: fewer pieces, and it keeps up.
                val pauseAfterSpeech = speech >= 10 && silent >= 20 && len >= SR
                val minLen = if (Notes.transcribing) 15 * SR else SR
                if ((pauseAfterSpeech && len >= minLen) || len >= 25 * SR) {
                    if (speech >= 5) Notes.addCut(id, intArrayOf(pieceStart, total, speech))
                    pieceStart = total; speech = 0; silent = 0
                    onCut()
                }
                if (total - synced >= 5 * SR) { out.fd.sync(); synced = total }
            }
            if (speech >= 5 && total > pieceStart) Notes.addCut(id, intArrayOf(pieceStart, total, speech))
        } catch (e: Exception) {
            Log.w("indite", e)
            Notes.status.value = "Recording stopped: ${e.localizedMessage}. What was recorded is saved."
        } finally {
            try { out.fd.sync() } catch (_: Exception) {}
            out.close()
            try { rec.stop() } catch (_: Exception) {}
            rec.release()
            Notes.level.value = 0f
            Notes.stopRecording(id, total)
            onCut()
        }
    }

    private companion object { const val FRAME = 480 }  // 30 ms
}
