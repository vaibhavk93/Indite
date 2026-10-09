package com.whispercppdemo.notes

/** Flag text the engine probably invented. Same rules as the web app (indite/guards.py). Flags only: nothing is deleted. */
object Guards {
    private val STOCK = listOf(
        "thanks for watching", "thank you for watching", "please subscribe", "like and subscribe",
        "subscribe to my channel", "subtitles by", "see you in the next video",
    )
    private val NAN = Regex("(?<![\\w'])nan(?![\\w'])")
    private val NON_ROMAN = Regex("[\\p{L}&&[^a-zA-Z\\u00C0-\\u024F]]")  // any letter that isn't Latin (accents allowed)

    val NOTE = mapOf(
        "no_speech" to "no speech heard here", "repeated" to "repeating text", "stock_phrase" to "possibly invented",
        "junk_word" to "junk text (nan)", "non_roman" to "not in Roman letters", "unclear" to "couldn't transcribe this part",
    )

    fun flags(text: String, seconds: Double, speechSeconds: Double): List<String> {
        val t = text.trim()
        if (t.isEmpty()) return emptyList()
        val lower = t.lowercase()
        return buildList {
            if (speechSeconds < minOf(0.3, 0.2 * seconds)) add("no_speech")
            if (hasLoop(t)) add("repeated")
            if (STOCK.any { it in lower }) add("stock_phrase")
            if (NAN.containsMatchIn(lower)) add("junk_word")
            if (NON_ROMAN.containsMatchIn(t)) add("non_roman")
        }
    }

    /** True if any 1-4 word phrase repeats `times` times back to back. */
    fun hasLoop(text: String, times: Int = 3): Boolean {
        val w = text.lowercase().replace(Regex("[^\\w\\s]"), " ").split(Regex("\\s+")).filter { it.isNotEmpty() }
        for (n in 1..4) for (i in 0..w.size - n * times) {
            if ((1 until times).all { k -> w.subList(i + k * n, i + (k + 1) * n) == w.subList(i, i + n) }) return true
        }
        return false
    }
}
