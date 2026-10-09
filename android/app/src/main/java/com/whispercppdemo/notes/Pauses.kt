package com.whispercppdemo.notes

import kotlin.math.ceil
import kotlin.math.min
import kotlin.math.sqrt

/** Cut audio at pauses into pieces of at most 25 s, like the web app (indite/core.py cut_at_pauses), using Silero. */
object Pauses {
    const val WINDOW = 512  // Silero's step: 32 ms at 16 kHz

    /**
     * Each cut is [startSample, endSample, speechMs]. Pieces with almost no speech are skipped: noise alone only
     * produces made-up text. `speech` has one entry per 32 ms window (from Silero, or loudness as a fallback).
     */
    fun cut(speech: BooleanArray, total: Int, maxSec: Double = 25.0, minGapSec: Double = 0.3): List<IntArray> {
        val n = speech.size
        if (n == 0) return emptyList()
        val ms = 1000.0 * WINDOW / SR
        // Middle of every silent stretch of at least minGapSec: a good place to cut.
        val gaps = mutableListOf<Int>()
        var run = 0
        for (f in 0..n) {
            if (f < n && !speech[f]) { run++; continue }
            if (run * ms >= minGapSec * 1000) gaps += f - run / 2
            run = 0
        }
        val maxF = (maxSec * 1000 / ms).toInt()
        val minF = (2000 / ms).toInt()  // never cut a piece shorter than 2 s
        val cuts = mutableListOf<IntArray>()
        var start = 0
        while (start < n) {
            val limit = start + maxF
            val end = if (limit >= n) n else gaps.lastOrNull { it in (start + minF)..limit } ?: limit
            val spokenMs = ((start until end).count { speech[it] } * ms).toInt()
            if (spokenMs >= 250) cuts += intArrayOf(start * WINDOW, if (end == n) total else end * WINDOW, spokenMs)
            start = end
        }
        return cuts
    }

    /** Silero says speech when its probability is >= 0.5 (its usual threshold). */
    fun speechFromProbs(probs: FloatArray) = BooleanArray(probs.size) { probs[it] >= 0.5f }

    /** Fallback if the detector can't load: loudness against the file's own noise floor. */
    fun speechFromLoudness(x: FloatArray): BooleanArray {
        val n = x.size / WINDOW
        if (n == 0) return BooleanArray(0)
        val rms = FloatArray(n) { f ->
            var s = 0.0
            for (k in f * WINDOW until (f + 1) * WINDOW) s += x[k] * x[k]
            sqrt(s / WINDOW).toFloat()
        }
        val sorted = rms.sorted()
        val noise = sorted[n / 10]
        // never below an absolute floor: in a quiet or steady-noise file the gap between "noise" and "loud" is tiny
        val threshold = maxOf(noise + 0.1f * (sorted[n * 9 / 10] - noise), noise * 2.5f, 0.004f)
        return BooleanArray(n) { rms[it] > threshold }
    }

    /** Audio window for whisper.cpp: 15 s for short pieces, else the piece length + 2 s (tested: 0 loops). 1500 = full 30 s. */
    fun audioCtx(samples: Int): Int {
        val sec = samples / 16000.0
        if (sec <= 13) return 768
        return min(1500, (ceil((sec + 2) * 50 / 64) * 64).toInt())
    }
}
