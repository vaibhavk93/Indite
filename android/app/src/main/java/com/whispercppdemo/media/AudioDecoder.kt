package com.whispercppdemo.media

import android.media.AudioFormat
import android.media.MediaCodec
import android.media.MediaExtractor
import android.media.MediaFormat
import java.io.ByteArrayOutputStream
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder

/** 16 kHz mono samples plus what the file was (for the test report). */
class Decoded(val samples: FloatArray, val info: String)

/**
 * Any audio Android can read (WhatsApp .opus voice notes, .m4a, .mp3, .wav) -> 16 kHz mono, using the phone's own decoder.
 * ponytail: whole file in memory and linear resampling; fine for voice notes, stream it for hour-long files.
 */
fun decodeAudio(file: File): Decoded {
    val ex = MediaExtractor()
    try {
        ex.setDataSource(file.path)
        val track = (0 until ex.trackCount).firstOrNull {
            ex.getTrackFormat(it).getString(MediaFormat.KEY_MIME)?.startsWith("audio/") == true
        } ?: error("no audio track in this file")
        ex.selectTrack(track)
        val fmt = ex.getTrackFormat(track)
        val mime = fmt.getString(MediaFormat.KEY_MIME)!!
        var rate = fmt.getInteger(MediaFormat.KEY_SAMPLE_RATE)
        var channels = fmt.getInteger(MediaFormat.KEY_CHANNEL_COUNT)
        var floatPcm = false
        val pcm = ByteArrayOutputStream()
        val codec = MediaCodec.createDecoderByType(mime)
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
                    rate = f.getInteger(MediaFormat.KEY_SAMPLE_RATE)
                    channels = f.getInteger(MediaFormat.KEY_CHANNEL_COUNT)
                    floatPcm = f.containsKey(MediaFormat.KEY_PCM_ENCODING) &&
                        f.getInteger(MediaFormat.KEY_PCM_ENCODING) == AudioFormat.ENCODING_PCM_FLOAT
                } else if (o >= 0) {
                    val b = codec.getOutputBuffer(o)!!
                    val bytes = ByteArray(info.size)
                    b.position(info.offset)
                    b.get(bytes)
                    pcm.write(bytes)
                    codec.releaseOutputBuffer(o, false)
                    if (info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0) break
                }
            }
        } finally {
            codec.release()
        }
        val mono = toMono(pcm.toByteArray(), channels, floatPcm)
        return Decoded(resample(mono, rate, 16000), "$mime, $rate Hz, $channels channel(s)")
    } finally {
        ex.release()
    }
}

private fun toMono(bytes: ByteArray, channels: Int, floatPcm: Boolean): FloatArray {
    val buf = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
    val all = if (floatPcm) FloatArray(bytes.size / 4) { buf.getFloat() }
              else FloatArray(bytes.size / 2) { buf.getShort() / 32768f }
    return FloatArray(all.size / channels) { i -> (0 until channels).sumOf { all[i * channels + it].toDouble() }.toFloat() / channels }
}

private fun resample(x: FloatArray, from: Int, to: Int): FloatArray {
    if (from == to || x.isEmpty()) return x
    val n = (x.size.toLong() * to / from).toInt()
    return FloatArray(n) { i ->
        val p = i.toDouble() * from / to
        val j = p.toInt().coerceAtMost(x.size - 1)
        val k = (j + 1).coerceAtMost(x.size - 1)
        (x[j] + (x[k] - x[j]) * (p - j)).toFloat()
    }
}
