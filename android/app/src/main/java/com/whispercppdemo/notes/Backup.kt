package com.whispercppdemo.notes

import android.content.Context
import android.util.Log
import org.json.JSONObject
import java.io.File
import java.io.InputStream
import java.io.OutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipInputStream
import java.util.zip.ZipOutputStream

/**
 * A backup that can actually be restored. "Export all notes as text" throws away the timestamps, the speaker labels and
 * the audio, so it was never a backup — losing the phone lost everything (AUD-001).
 *
 * The file is a plain zip: one folder per note with the files Inditeflow already keeps, plus `inditeflow.json` saying which
 * format it is. Audio is optional because it is ~29 MB per 15 minutes and the text is a few KB.
 *
 * ponytail: no encryption and no cloud. The zip sits wherever the user put it, and that is their call to make.
 */
object Backup {
    /** Bumped only when the files inside a note change shape. A backup from the future is refused, never half-read. */
    const val FMT = 1
    private const val INDEX = "inditeflow.json"
    private const val LEGACY_INDEX = "indite.json"   // backups made before the rename (24 Oct) must still restore

    /** Everything a note needs to come back. Audio is added separately because of its size. */
    private val PARTS = listOf("meta.json", "cuts.json", "transcript.jsonl", "edits.json", "speakers.json", "ai.json")

    data class Written(val notes: Int, val bytes: Long)
    data class Read(val restored: Int, val skipped: Int, val problem: String? = null)

    fun write(out: OutputStream, withAudio: Boolean): Written {
        var notes = 0
        var bytes = 0L
        ZipOutputStream(out.buffered()).use { zip ->
            val ids = Notes.list.value.filter { !it.recording }.map { it.id }
            zip.putNextEntry(ZipEntry(INDEX))
            zip.write(JSONObject().put("fmt", FMT).put("app", "Inditeflow").put("notes", ids.size)
                .put("audio", withAudio).put("created", System.currentTimeMillis()).toString().toByteArray())
            zip.closeEntry()
            for (id in ids) {
                val d = Notes.dir(id)
                val parts = if (withAudio) PARTS + "audio.pcm" else PARTS
                var any = false
                for (name in parts) {
                    val f = File(d, name)
                    if (!f.exists()) continue
                    zip.putNextEntry(ZipEntry("$id/$name"))
                    f.inputStream().use { it.copyTo(zip) }
                    zip.closeEntry()
                    bytes += f.length()
                    any = true
                }
                if (any) notes++
            }
        }
        return Written(notes, bytes)
    }

    /**
     * Restores notes that aren't on this phone already; a note with the same id is left alone, so restoring twice is
     * safe. Returns a plain-language problem instead of throwing when the file isn't an Inditeflow backup.
     */
    fun read(input: InputStream): Read {
        var restored = 0
        var skipped = 0
        val seen = mutableSetOf<String>()
        val tmp = File(Notes.dir("restore.tmp").parentFile, ".restore").apply { deleteRecursively(); mkdirs() }
        try {
            ZipInputStream(input.buffered()).use { zip ->
                var entry: ZipEntry? = zip.nextEntry
                var index: JSONObject? = null
                while (entry != null) {
                    val name = entry.name
                    if (name == INDEX || name == LEGACY_INDEX) {
                        index = runCatching { JSONObject(zip.readBytes().decodeToString()) }.getOrNull()
                        if (index == null || !index.optString("app").let { it.equals("inditeflow", true) || it.equals("indite", true) })
                            return Read(0, 0, "That file isn't an Inditeflow backup.")
                        if (index.optInt("fmt", 0) > FMT)
                            return Read(0, 0, "That backup was made by a newer version of Inditeflow. Update the app first.")
                    } else if (!entry.isDirectory) {
                        val id = name.substringBefore('/')
                        val part = name.substringAfter('/', "")
                        // Only the files Inditeflow writes, only one level deep: a zip from anywhere else can't write around the folder.
                        if (id.isNotEmpty() && part in PARTS + "audio.pcm" && !part.contains('/')) {
                            if (Notes.dir(id).exists()) { if (seen.add(id)) skipped++ }
                            else {
                                val out = File(tmp, "$id/$part").apply { parentFile?.mkdirs() }
                                out.outputStream().use { zip.copyTo(it) }
                                if (seen.add(id)) restored++
                            }
                        }
                    }
                    zip.closeEntry()
                    entry = zip.nextEntry
                }
                if (index == null) return Read(0, 0, "That file isn't an Inditeflow backup.")
            }
            // Only move finished folders across, so a half-read zip can never leave a broken note behind.
            tmp.listFiles()?.forEach { folder ->
                if (File(folder, "meta.json").exists()) folder.renameTo(Notes.dir(folder.name))
                else { folder.deleteRecursively(); restored-- }
            }
        } catch (e: Exception) {
            Log.w("inditeflow", "restore failed", e)
            return Read(restored, skipped, "That backup couldn't be read. It may be damaged.")
        } finally {
            tmp.deleteRecursively()
            Notes.refresh()
        }
        return Read(restored.coerceAtLeast(0), skipped)
    }
}
