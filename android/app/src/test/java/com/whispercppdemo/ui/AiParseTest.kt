package com.whispercppdemo.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class AiParseTest {
    @Test fun scoresWithMarkdown() = assertEquals(listOf(7, 6, 4, 8),
        practiceScores("Fixes...\n- **SCORES:** structure=7 clarity=6 numbers = 4  concise=8"))

    @Test fun scoresOutOfRangeOrMissing() {
        assertNull(practiceScores("SCORES: structure=11 clarity=6 numbers=4 concise=8"))
        assertNull(practiceScores("no scores here"))
    }

    @Test fun actionRowsParseAndSkipOtherLines() = assertEquals(
        listOf(Triple("Deck bhejna", "Priya", "Monday"), Triple("Vendor ko call", "not said", "not said")),
        actionRows("Here you go:\n1. Deck bhejna | Priya | Monday\n- Vendor ko call | | not said"))

    @Test fun actionRowsFromMarkdownTable() = assertEquals(
        listOf(Triple("Deck bhejna", "Priya", "Monday")),
        actionRows("| Task | Who | By when |\n|---|---|---|\n| **Deck bhejna** | Priya | Monday |"))
}
