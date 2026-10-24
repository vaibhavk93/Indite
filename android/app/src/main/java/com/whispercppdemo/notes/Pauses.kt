package com.whispercppdemo.notes

import kotlin.math.ceil
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

/** Cut audio at pauses into pieces of at most 25 s, like the web app (inditeflow/core.py cut_at_pauses), using Silero. */
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

    /**
     * Audio window for whisper.cpp: 15 s (768) for short pieces, else the piece length + 2 s, always a MULTIPLE OF 256
     * and at most 1280 (25.6 s; pieces are cut at 25 s). With flash attention the decoder reads the window rounded up to
     * 256; any rows the encoder didn't write held the previous piece's audio, so the same audio gave different text
     * (Mac 10 Oct: 15-min file 10/39 parts repeatable -> 39/39, 27.6% -> 24.7% words wrong, same speed).
     */
    fun audioCtx(samples: Int): Int {
        val sec = samples / 16000.0
        if (shortCtx > 0) return shortCtx          // test hook only: --ei test_ctx 512|768
        // The window follows the piece, rounded up to the next multiple of 256, never below 512. A flat number was
        // wrong in both directions (measured 13 Oct): 768 made a 5 s sentence pay for 15 s of encoder, so the engine
        // fell behind and the wait compounded to 65 s; 512 was shorter than an 11 s piece, cut its end off, and word
        // errors jumped 18.3% -> 32.8% while re-runs pushed the wait to 91 s.
        return min(FULL, max(512, (ceil((sec + 2) * 50 / round) * round).toInt()))
    }

    /**
     * The window used for a short piece. 768 is 15 s, so a 5-second sentence paid for 15 seconds of encoder and the
     * engine could not keep pace: it fell behind and the wait compounded (13 Oct: 65.5 s median, 0.73x real time).
     * 512 is 10.2 s, still a multiple of 256 so the flash-attention fix holds. Measured on the phone, same audio,
     * same cuts: engine 8.3 -> 5.5 s per piece, wait 65.5 -> 16.6 s, 0.99x real time, words wrong 18.1 -> 18.3%
     * (unchanged). Personal-build test hook: --ei test_ctx 768 puts the old value back.
     */
    @Volatile var shortCtx = 0

    /** 256 (consistent text). Personal-build test hook can set 64 (the old rounding) for an A/B speed test. */
    @Volatile var round = 256

    /** The largest window used (a multiple of 256, unlike whisper's default 1500, which would leak). */
    const val FULL = 1280
}
