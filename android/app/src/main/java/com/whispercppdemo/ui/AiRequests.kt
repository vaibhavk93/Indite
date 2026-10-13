package com.whispercppdemo.ui

import android.content.Context
import com.whispercppdemo.notes.Note

/**
 * What AI can do with a note, and how its answers are read back. Pure logic with no Compose in it, so it can be
 * tested on a laptop; the screens that use it live in NotesApp.kt (AUD-015, first slice).
 */

/**
 * What AI can do with a note, in the user's words (AUD-026). Each row says what comes back, not what the prompt is
 * called; `asks` marks the two that need one more answer (a style, a language), so the journey announces itself.
 * This replaces a ten-item menu that explained nothing and repeated five of the buttons sitting just above it.
 */
internal data class AiAction(val label: String, val gets: String, val group: String, val asks: Boolean = false)

internal val AiActions = listOf(
    AiAction("Meeting notes", "Decisions, action items, open questions", "Turn it into something to read"),
    AiAction("Action items", "Every task as: task | who | by when", "Turn it into something to read"),
    AiAction("Summary", "Five short bullets", "Turn it into something to read"),
    AiAction("Lecture notes", "Topics, key ideas and revision questions", "Turn it into something to read"),
    AiAction("Brain dump", "Your thinking out loud, organised", "Turn it into something to read"),
    AiAction("Brain dump + questions", "It asks you 3 questions first, then organises it", "Turn it into something to read"),
    AiAction("Rewrite to send", "The same thing, in a style you pick", "Change the words", asks = true),
    AiAction("Translate", "The same thing, in another language", "Change the words", asks = true),
    AiAction("Clean it up", "Punctuation fixed, the umms removed", "Change the words"),
    AiAction("Practice answer", "A score out of 40 and three fixes", "Practise"),
)

/** What indite already knows about a note decides what it offers first. Nothing is hidden, only reordered. */
internal fun suggestedFor(note: Note): List<String> {
    val words = note.allText().split(Regex("\\s+")).count { it.isNotBlank() }
    val people = note.speakers?.takeIf { !it.skipped }?.k ?: 1
    return when {
        people >= 2 && note.seconds >= 120 -> listOf("Meeting notes", "Action items")
        words < 60 -> listOf("Rewrite to send", "Clean it up")
        note.name.trimEnd().endsWith("?") -> listOf("Practice answer", "Summary")
        else -> listOf("Summary", "Action items")
    }
}

internal fun actionRows(text: String): List<Triple<String, String, String>> = text.lines().mapNotNull(::actionRow)

/** One "task | who | by when" line; also a markdown table row ("| task | who | when |"). Header and --- lines are skipped. */
internal fun actionRow(line: String): Triple<String, String, String>? {
    val parts = line.trim().trimStart('-', '*', '•', ' ').replace(Regex("^\\d+[.)]\\s*"), "").trim().removePrefix("|").removeSuffix("|")
        .split("|").map { it.trim().trim('*') }
    if (parts.size != 3 || parts[0].isEmpty() || parts.all { it.matches(Regex(":?-{2,}:?")) }) return null
    if (parts[0].equals("task", true) && parts[1].equals("who", true)) return null  // table header
    return Triple(parts[0], parts[1].ifEmpty { "not said" }, parts[2].ifEmpty { "not said" })
}

internal fun isActionLine(line: String) = actionRow(line) != null || line.trim().matches(Regex("\\|?\\s*:?-{2,}.*")) ||
    line.replace(" ", "").equals("|task|who|bywhen|", true)

/** "SCORES: structure=7 clarity=6 numbers=4 concise=8" (markdown around it is fine) -> four 1-10 scores, or null. */
internal fun practiceScores(text: String): List<Int>? {
    val m = Regex("SCORES:?\\**\\s*structure\\s*=\\s*(\\d+)\\W+clarity\\s*=\\s*(\\d+)\\W+numbers\\s*=\\s*(\\d+)\\W+concise\\s*=\\s*(\\d+)",
        RegexOption.IGNORE_CASE).find(text) ?: return null
    return m.groupValues.drop(1).map { it.toInt() }.takeIf { v -> v.all { it in 1..10 } }
}

internal const val GOOGLE_TRANSLATE = "Google Translate app"
internal const val GOOGLE_TRANSLATE_PKG = "com.google.android.apps.translate"

/** Is this app on the phone? Needs the <queries> list in the manifest (Android 11+ hides everything else). */
internal fun installed(c: Context, pkg: String) =
    runCatching { c.packageManager.getPackageInfo(pkg, 0); true }.getOrDefault(false)

internal val Languages = listOf("Hindi (Devanagari)", "English", "Tamil", "Telugu", "Marathi", "Gujarati", "Bengali", "Kannada",
    "Malayalam", "Punjabi", "Urdu", "Arabic", "Chinese (Simplified)")

/**
 * Pick a language once; it's remembered. The request names it, so the AI translates straight away.
 *
 * indite has no translator of its own, so there are two routes and the dialog says which is which: the Google Translate
 * app (free, offline, installed on most phones) or whatever AI the user has set up. Google Translate goes first because
 * it needs no key and no internet.
 */
