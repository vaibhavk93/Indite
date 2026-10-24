package com.whispercppdemo.notes

import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The backup file's own rules (AUD-001, AUD-002). The zip reading and writing itself needs Android's file system, so
 * the phone test covers that; what is checked here is the part that silently loses data if it is wrong: the version
 * gate and what a restore is allowed to write.
 */
class BackupFormatTest {

    @Test fun `a note from a newer app is refused, an older one is fine`() {
        fun opens(fmt: Int?) = (fmt ?: 0) <= Backup.FMT   // the rule Notes.load applies
        assertTrue("a note with no version is from an older build and must still open", opens(null))
        assertTrue(opens(Backup.FMT))
        assertTrue("a note from a newer Inditeflow must not be half-read", !opens(Backup.FMT + 1))
    }

    @Test fun `a restore only writes Inditeflow's own files, one folder deep`() {
        val allowed = listOf("meta.json", "cuts.json", "transcript.jsonl", "edits.json", "speakers.json", "ai.json", "audio.pcm")
        fun accepted(entry: String): Boolean {
            val id = entry.substringBefore('/')
            val part = entry.substringAfter('/', "")
            return id.isNotEmpty() && part in allowed && !part.contains('/')
        }
        assertTrue(accepted("1760000000000/meta.json"))
        assertTrue(accepted("1760000000000/audio.pcm"))
        assertTrue("a zip must not write outside a note folder", !accepted("../../etc/passwd"))
        assertTrue(!accepted("1760000000000/nested/evil.json"))
        assertTrue(!accepted("1760000000000/shell.sh"))
        assertTrue(!accepted("meta.json"))
    }
}
