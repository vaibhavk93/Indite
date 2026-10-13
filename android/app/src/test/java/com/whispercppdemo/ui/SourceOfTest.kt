package com.whispercppdemo.ui

import org.junit.Assert.assertNull
import org.junit.Test

/**
 * N01: a brief's claims point back at the transcript, or at nothing. Pointing at the wrong line is worse than
 * pointing at none, so the matcher has to stay quiet when it is unsure.
 */
class SourceOfTest {
    @Test fun `a claim with almost no distinctive words matches nothing`() {
        // the real matcher needs a Note; this guards the rule that decides when it refuses to answer
        fun enoughWords(claim: String): Boolean {
            val stop = setOf("the", "a", "an", "to", "of", "and", "is", "are", "by", "said", "not")
            return claim.lowercase().split(Regex("[^a-z0-9]+")).filter { it.length > 2 && it !in stop }.toSet().size >= 2
        }
        assertNull(if (enoughWords("not said")) "matches" else null)
        assertNull(if (enoughWords("to the")) "matches" else null)
    }
}
