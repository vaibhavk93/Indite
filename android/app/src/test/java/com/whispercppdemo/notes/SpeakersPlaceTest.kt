package com.whispercppdemo.notes

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class SpeakersPlaceTest {
    @Test fun sentencesSplitAtFullStops() {
        assertEquals(listOf("Kal aana.", "Theek hai!", "Kab?"), Notes.sentences("Kal aana. Theek hai! Kab?"))
    }

    @Test fun boundarySnapsToThePauseBetweenTurns() {
        // two equal sentences, speech 0-3 s and 4-7 s: the cut lands in the pause (3.5 s), not mid-speech
        val sr = 16000
        val spans = Speakers.place(listOf("aaaa.", "bbbb."), 0, 7 * sr, listOf(0 to 3 * sr, 4 * sr to 7 * sr))!!
        assertEquals(listOf(0 to (3.5 * sr).toInt(), (3.5 * sr).toInt() to 7 * sr), spans)
    }

    @Test fun oneSentenceIsNotSplit() = assertNull(Speakers.place(listOf("Only one."), 0, 16000, listOf(0 to 16000)))
}
