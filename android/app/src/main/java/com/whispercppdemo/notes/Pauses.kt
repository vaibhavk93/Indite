package com.whispercppdemo.notes

import kotlin.math.ceil
import kotlin.math.min
import kotlin.math.sqrt

/**
 * Cut audio at pauses into pieces of at most 25 s, like the web app (indite/core.py cut_at_pauses).
 * ponytail: loudness-based pause finding; the web app uses Silero VAD. Swap in whisper.cpp's built-in VAD if cuts land mid-word.
 */
object Pauses {
    private const val FRAME = 480  // 30 ms at 16 kHz

    /** Each cut is [startSample, endSample, speechFrames]. Pieces with almost no speech are skipped (they only produce made-up text). */
    fun cut(x: FloatArray, maxSec: Double = 25.0, minGapSec: Double = 0.3): List<IntArray> {
        val n = x.size / FRAME
        if (n == 0) return emptyList()
        val rms = FloatArray(n) { f ->
            var s = 0.0
            for (k in f * FRAME until (f + 1) * FRAME) s += x[k] * x[k]
            sqrt(s / FRAME).toFloat()
        }
        val sorted = rms.sorted()
        val noise = sorted[n / 10]
        val loud = sorted[n * 9 / 10]
        val threshold = noise + 0.1f * (loud - noise)
        val speech = BooleanArray(n) { rms[it] > threshold }

        // Middle of every silent stretch of at least minGapSec: a good place to cut.
        val gaps = mutableListOf<Int>()
        var run = 0
        for (f in 0..n) {
            if (f < n && !speech[f]) { run++; continue }
            if (run >= minGapSec * 1000 / 30) gaps += f - run / 2
            run = 0
        }

        val maxF = (maxSec * 1000 / 30).toInt()
        val minF = 2000 / 30  // never cut a piece shorter than 2 s
        val cuts = mutableListOf<IntArray>()
        var start = 0
        while (start < n) {
            val limit = start + maxF
            val end = if (limit >= n) n else gaps.lastOrNull { it in (start + minF)..limit } ?: limit
            val spoken = (start until end).count { speech[it] }
            if (spoken * 30 >= 150) cuts += intArrayOf(start * FRAME, min(end * FRAME, x.size), spoken)
            start = end
        }
        return cuts
    }

    /** Audio window for whisper.cpp: 15 s for short pieces, else the piece length + 2 s (tested: 0 loops). 1500 = full 30 s. */
    fun audioCtx(samples: Int): Int {
        val sec = samples / 16000.0
        if (sec <= 13) return 768
        return min(1500, (ceil((sec + 2) * 50 / 64) * 64).toInt())
    }
}
