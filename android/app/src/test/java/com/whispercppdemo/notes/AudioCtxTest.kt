package com.whispercppdemo.notes

import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.ceil
import kotlin.math.max
import kotlin.math.min

/**
 * The audio window must never be shorter than the piece it is transcribing. A flat 512 was, and it cut the end off
 * every 11-second piece: word errors 18.3% -> 32.8% on the phone, 13 Oct. This is the test that would have caught it.
 */
class AudioCtxTest {
    private fun ctx(sec: Double) = min(1280, max(512, (ceil((sec + 2) * 50 / 256) * 256).toInt()))

    @Test fun `the test hook is off by default`() {
        // Shipped as 512 on 13 Oct: every piece, however long, got a 10.2 s window and two thirds of a 22 s piece
        // was thrown away. Words wrong on the 15-min file went 25.0% -> 75.7%.
        assertTrue("Pauses.shortCtx must be 0 (off) in a shipped build, not ${Pauses.shortCtx}", Pauses.shortCtx == 0)
    }

    @Test fun `the window always covers the audio, with room to spare`() {
        var sec = 1.0
        while (sec <= 25.0) {
            val windowSeconds = ctx(sec) / 50.0
            assertTrue("a %.1f s piece got a %.1f s window - its end would be cut off".format(sec, windowSeconds),
                windowSeconds >= sec)
            sec += 0.5
        }
    }

    @Test fun `a short piece does not pay for a long window`() {
        assertTrue("a 5 s sentence should not cost 15 s of encoder", ctx(5.0) <= 512)
        assertTrue("a 6 s sentence should not cost 15 s of encoder", ctx(6.0) <= 512)
    }

    @Test fun `every window is a multiple of 256, so the flash-attention fix holds`() {
        listOf(1.0, 5.0, 11.0, 13.0, 16.0, 21.0, 25.0).forEach {
            assertTrue("window for $it s is not a multiple of 256", ctx(it) % 256 == 0)
        }
    }
}
