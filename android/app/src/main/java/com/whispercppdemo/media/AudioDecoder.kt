package com.whispercppdemo.media

import android.media.AudioFormat
import android.media.MediaCodec
import android.media.MediaExtractor
import android.media.MediaFormat
import java.io.BufferedOutputStream
import java.io.File
import java.io.FileOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Any audio Android can read (WhatsApp .opus voice notes, .m4a, .mp3, .wav, video sound) -> 16 kHz mono 16-bit PCM
 * written straight to `out`, a piece at a time, so an hour-long file never sits in memory. Returns the sample count.
 */
fun decodeToPcm(file: File, out: File): Int {
    val ex = MediaExtractor()
    try {
        ex.setDataSource(file.path)
        val track = (0 until ex.trackCount).firstOrNull {
            ex.getTrackFormat(it).getString(MediaFormat.KEY_MIME)?.startsWith("audio/") == true
        } ?: error("no audio track in this file")
        ex.selectTrack(track)
        val fmt = ex.getTrackFormat(track)
        val codec = MediaCodec.createDecoderByType(fmt.getString(MediaFormat.KEY_MIME)!!)
        var resampler = Resampler(fmt.getInteger(MediaFormat.KEY_SAMPLE_RATE), fmt.getInteger(MediaFormat.KEY_CHANNEL_COUNT), false)
        BufferedOutputStream(FileOutputStream(out), 1 shl 16).use { sink ->
            try {
                codec.configure(fmt, null, null, 0)
                codec.start()
                val info = MediaCodec.BufferInfo()
                var inputDone = false
                while (true) {
                    if (!inputDone) {
                        val i = codec.dequeueInputBuffer(10_000)
                        if (i >= 0) {
                            val n = ex.readSampleData(codec.getInputBuffer(i)!!, 0)
                            if (n < 0) {
                                codec.queueInputBuffer(i, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM)
                                inputDone = true
                            } else {
                                codec.queueInputBuffer(i, 0, n, ex.sampleTime, 0)
                                ex.advance()
                            }
                        }
                    }
                    val o = codec.dequeueOutputBuffer(info, 10_000)
                    if (o == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED) {
                        val f = codec.outputFormat
                        resampler = Resampler(f.getInteger(MediaFormat.KEY_SAMPLE_RATE), f.getInteger(MediaFormat.KEY_CHANNEL_COUNT),
                            f.containsKey(MediaFormat.KEY_PCM_ENCODING) && f.getInteger(MediaFormat.KEY_PCM_ENCODING) == AudioFormat.ENCODING_PCM_FLOAT)
                    } else if (o >= 0) {
                        val b = codec.getOutputBuffer(o)!!
                        b.position(info.offset)
                        b.limit(info.offset + info.size)
                        resampler.feed(b.slice().order(ByteOrder.LITTLE_ENDIAN), sink)
                        codec.releaseOutputBuffer(o, false)
                        if (info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0) break
                    }
                }
            } finally {
                codec.release()
            }
        }
        return (out.length() / 2).toInt()
    } finally {
        ex.release()
    }
}

/** Length of the file's audio in seconds, without decoding it (0 if unknown). */
fun durationSec(file: File): Double {
    val ex = MediaExtractor()
    return try {
        ex.setDataSource(file.path)
        (0 until ex.trackCount).map { ex.getTrackFormat(it) }
            .firstOrNull { it.getString(MediaFormat.KEY_MIME)?.startsWith("audio/") == true && it.containsKey(MediaFormat.KEY_DURATION) }
            ?.getLong(MediaFormat.KEY_DURATION)?.div(1e6) ?: 0.0
    } catch (e: Exception) { 0.0 } finally { ex.release() }
}

/** Downmix to mono and resample to 16 kHz (linear), across chunk boundaries. */
private class Resampler(private val rate: Int, private val channels: Int, private val floatPcm: Boolean) {
    private var prev = 0f      // last input sample of the previous chunk
    private var pos = 0.0      // next output position, in input samples, relative to `prev`
    private val step = rate / 16000.0
    private val bytes = ByteBuffer.allocate(1 shl 15).order(ByteOrder.LITTLE_ENDIAN)

    fun feed(b: ByteBuffer, sink: BufferedOutputStream) {
        val frames = b.remaining() / ((if (floatPcm) 4 else 2) * channels)
        val x = FloatArray(frames + 1)
        x[0] = prev
        for (f in 1..frames) {
            var s = 0f
            repeat(channels) { s += if (floatPcm) b.getFloat() else b.getShort() / 32768f }
            x[f] = s / channels
        }
        // x[0] is the previous chunk's last sample, so positions run from 0 up to frames.
        while (pos <= frames - 1) {
            val j = pos.toInt()
            val v = x[j] + (x[j + 1] - x[j]) * (pos - j).toFloat()
            if (bytes.remaining() < 2) flush(sink)
            bytes.putShort((v.coerceIn(-1f, 1f) * 32767).toInt().toShort())
            pos += step
        }
        pos -= frames
        prev = x[frames]
        flush(sink)
    }

    private fun flush(sink: BufferedOutputStream) {
        sink.write(bytes.array(), 0, bytes.position())
        bytes.clear()
    }
}
