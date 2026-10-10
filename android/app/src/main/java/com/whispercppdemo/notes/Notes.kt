package com.whispercppdemo.notes

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import com.whispercpp.whisper.SpeechDetector
import com.whispercppdemo.media.decodeToPcm
import com.whispercppdemo.media.durationSec
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder

const val SR = 16000

/** latencyMs: from the moment this part was cut (you paused) to its text being ready; engineMs: model time only. -1 = unknown. */
/** A sentence inside a piece, with its own start and end (samples from the start of the note). Used for speakers. */
data class Seg(val start: Int, val end: Int, val text: String)

data class Piece(val i: Int, val start: Int, val end: Int, val text: String, val flags: List<String>,
                 val latencyMs: Int = -1, val engineMs: Int = -1, val segs: List<Seg> = emptyList()) {
    val startSec get() = start / SR.toDouble()
    /** Nothing worth copying: the engine gave up, or wrote only "nan" for noise. */
    val junk get() = "unclear" in flags || text.trim().equals("nan", ignoreCase = true)
}

/** An answer from the user's own AI app (ChatGPT, Claude…), pasted back and kept with the note. */
data class AiReply(val label: String, val text: String, val created: Long)

data class Note(
    val id: String, val name: String, val created: Long, val samples: Int,
    val cuts: List<IntArray>, val pieces: List<Piece>, val edits: Map<Int, String>, val speed: String?,
    val recording: Boolean, val test: Boolean = false, val speakers: Speakers.Result? = null,
    val ai: List<AiReply> = emptyList(), val live: Boolean = false,
) {
    /** Speaker number of a paragraph (0-based), or null if speakers aren't labelled. */
    fun speakerOf(i: Int): Int? = speakers?.takeIf { !it.skipped }?.of?.get(i)

    /**
     * A paragraph as speaker turns: [(speaker or null, text)]. Uses the per-sentence speakers when the paragraph wasn't
     * edited; an edited paragraph (or one moved to a speaker) is one turn by its paragraph speaker.
     */
    fun turns(i: Int): List<Pair<Int?, String>> {
        val p = pieces[i]
        val each = speakers?.takeIf { !it.skipped }?.seg?.get(i)
        val sents = Notes.sentences(p.text)
        if (i in edits || each == null || each.size != sents.size || sents.size < 2) return listOf(speakerOf(i) to text(i).trim())
        val out = mutableListOf<Pair<Int?, String>>()
        sents.zip(each).forEach { (s, who) ->
            val t = Settings.applyFixes(s).trim()
            if (out.isNotEmpty() && out.last().first == who) out[out.size - 1] = who to (out.last().second + " " + t)
            else out += who to t
        }
        return out
    }
    val labelled get() = speakers != null && !speakers.skipped
    fun speakerName(n: Int) = speakers?.names?.get(n)?.takeIf { it.isNotBlank() } ?: "Speaker ${n + 1}"

    val seconds get() = samples / SR.toDouble()
    val done get() = !recording && pieces.size >= cuts.size
    val pending get() = pieces.size < cuts.size
    /** What the model wrote, with the user's word fixes applied (PTM -> Paytm). */
    fun auto(i: Int) = Settings.applyFixes(pieces[i].text)
    /** What the user sees: their own edit if they made one, else the auto text. */
    fun text(i: Int) = edits[i] ?: auto(i)
    /** Plain text for copying and sharing: edits applied, no "Check" labels, no junk pieces. */
    fun allText(): String {
        val kept = pieces.filter { !it.junk || it.i in edits }
        if (!labelled) return kept.joinToString(" ") { text(it.i).trim() }.replace(Regex("\\s+"), " ").trim()
        // with speakers: one line per turn, "Amit: ..." (turns can change inside a paragraph)
        val out = StringBuilder()
        var last: Int? = -2
        for (p in kept) for ((s, t) in turns(p.i)) {
            if (t.isEmpty()) continue
            if (s != last) { if (out.isNotEmpty()) out.append("\n\n"); out.append(s?.let { speakerName(it) + ": " } ?: ""); last = s }
            else out.append(" ")
            out.append(t)
        }
        return out.toString().trim()
    }
}

/**
 * Each note is a folder: audio.pcm (16 kHz mono 16-bit, no header), cuts.json, transcript.jsonl (one line per
 * finished piece, appended and flushed at once), attempt (crash-loop guard), edits.json (user's fixes; the
 * transcript itself is never changed), meta.json (written last, so a half-imported note is never listed).
 */
object Notes {
    val list = MutableStateFlow<List<Note>>(emptyList())
    val status = MutableStateFlow("")
    val working = MutableStateFlow(false)  // the queue is running (shows a progress bar under the status)
    val level = MutableStateFlow(0f)  // live mic loudness 0..1 while recording
    @Volatile var transcribing = false  // the recorder cuts short pieces only while the engine is free
    /** Notes the voice keyboard is transcribing itself (so it can type the text in); the queue leaves them alone. */
    val claimed: MutableSet<String> = java.util.concurrent.ConcurrentHashMap.newKeySet()
    private val cutLock = Any()
    private lateinit var root: File
    private var results: File? = null  // shell-readable folder for automated test results (test notes only)
    private val cutTimes = java.util.concurrent.ConcurrentHashMap<String, Long>()  // "id:i" -> when the cut was made

    /** Longest file we import for now: decoding is streamed, but the cut list and UI aren't tuned for longer. */
    const val MAX_IMPORT_MIN = 120

    fun init(context: Context) {
        if (!::root.isInitialized) root = File(context.filesDir, "notes").apply { mkdirs() }
        if (results == null) results = context.getExternalFilesDir("results")
        refresh()
    }

    fun dir(id: String) = File(root, id)

    @Synchronized
    fun refresh() {
        list.value = (root.listFiles() ?: emptyArray()).mapNotNull { load(it) }.sortedByDescending { it.created }
    }

    /** One note, read fresh from storage (the voice keyboard polls its own dictation this way). */
    fun note(id: String): Note? = load(dir(id))

    private fun load(d: File): Note? = try {
        val meta = JSONObject(File(d, "meta.json").readText())
        val cuts = JSONArray(File(d, "cuts.json").readText()).let { a ->
            List(a.length()) { a.getJSONArray(it).let { c -> IntArray(c.length()) { k -> c.getInt(k) } } }
        }
        val pieces = File(d, "transcript.jsonl").takeIf { it.exists() }?.readLines()?.mapNotNull { line ->
            try {  // a line cut short by a crash is ignored: that piece is simply redone
                val o = JSONObject(line)
                val f = o.getJSONArray("flags")
                val sg = o.optJSONArray("segs")
                Piece(o.getInt("i"), o.getInt("start"), o.getInt("end"), o.getString("text"), List(f.length()) { f.getString(it) },
                    o.optInt("ms", -1), o.optInt("engine", -1),
                    if (sg == null) emptyList() else List(sg.length()) { sg.getJSONArray(it).let { a -> Seg(a.getInt(0), a.getInt(1), a.getString(2)) } })
            } catch (e: Exception) { null }
        } ?: emptyList()
        val edits = File(d, "edits.json").takeIf { it.exists() }?.let { f ->
            JSONObject(f.readText()).let { o -> o.keys().asSequence().associate { it.toInt() to o.getString(it) } }
        } ?: emptyMap()
        val recording = meta.optBoolean("recording")
        val samples = if (recording) (File(d, "audio.pcm").length() / 2).toInt() else meta.getInt("samples")
        Note(d.name, meta.getString("name"), meta.getLong("created"), samples, cuts, pieces, edits,
            meta.optString("speed").ifEmpty { null }, recording, meta.optBoolean("test"), Speakers.load(d.name), loadAi(d), meta.optBoolean("live"))
    } catch (e: Exception) { null }

    /** Copy a shared or picked file in (shared links can expire), decode it and cut it at pauses. Returns the note id. */
    suspend fun import(context: Context, uri: Uri, test: Boolean = false): String = withContext(Dispatchers.IO) {
        val name = context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use {
            if (it.moveToFirst()) it.getString(0) else null
        }?.substringBeforeLast('.') ?: uri.lastPathSegment?.substringBeforeLast('.') ?: "Voice note"
        val id = System.currentTimeMillis().toString()
        val d = dir(id).apply { mkdirs() }
        try {
            status.value = "Opening $name…"
            val source = File(d, "source")
            context.contentResolver.openInputStream(uri)!!.use { i -> source.outputStream().use { i.copyTo(it) } }
            if (durationSec(source) > MAX_IMPORT_MIN * 60) throw ImportError("Files longer than $MAX_IMPORT_MIN minutes aren't supported yet. Split it, or use the indite web app.")
            status.value = "Reading the audio in $name…"
            val samples = decodeToPcm(source, File(d, "audio.pcm"))
            source.delete()
            if (samples < SR / 2) throw ImportError("This file has no audio indite can read.")
            status.value = "Finding the pauses in $name…"
            val cuts = cutRange(context, id, 0, samples)
            writeAtomic(File(d, "cuts.json"), JSONArray(cuts.map { JSONArray(it.toList()) }).toString())
            writeAtomic(File(d, "meta.json"), JSONObject().put("name", name).put("created", id.toLong()).put("samples", samples)
                .put("test", test).toString())
            status.value = ""
            refresh()
            id
        } catch (e: Throwable) {  // Throwable: an out-of-memory error must still remove the half-imported folder
            d.deleteRecursively()
            status.value = ""
            throw e
        }
    }

    class ImportError(message: String) : Exception(message)

    /**
     * Cut samples [from, to) of a note at pauses, using Silero in 10-minute chunks (so memory stays small).
     * Loudness is the fallback if the detector won't load.
     */
    fun cutRange(context: Context, id: String, from: Int, to: Int): List<IntArray> {
        val chunk = 10 * 60 * SR
        val detector = try { SpeechDetector(Engine.vadPath(context)) } catch (e: Exception) { null }
        val speech = mutableListOf<Boolean>()
        try {
            var s = from
            while (s < to) {
                val e = minOf(to, s + chunk)
                val x = readPcm(id, s, e)
                val part = detector?.let { Pauses.speechFromProbs(it.probs(x)) } ?: Pauses.speechFromLoudness(x)
                speech += part.toList()
                // keep windows aligned with samples when the detector returns fewer windows than the chunk holds
                repeat((e - s) / Pauses.WINDOW - part.size) { speech += false }
                s = e
            }
        } finally { detector?.release() }
        return Pauses.cut(speech.toBooleanArray(), to - from).map { intArrayOf(it[0] + from, it[1] + from, it[2]) }
    }

    /** A new, empty recording. The recorder appends audio.pcm and adds a cut at every pause. */
    fun startRecording(name: String? = null, test: Boolean = false): String {
        val id = System.currentTimeMillis().toString()
        val d = dir(id).apply { mkdirs() }
        File(d, "audio.pcm").createNewFile()
        writeAtomic(File(d, "cuts.json"), "[]")
        val title = name ?: java.text.SimpleDateFormat("EEE d MMM, h:mm a", java.util.Locale.getDefault()).format(java.util.Date(id.toLong()))
        writeAtomic(File(d, "meta.json"), JSONObject().put("name", title).put("created", id.toLong()).put("samples", 0)
            .put("recording", true).put("live", true).put("test", test).put("autoTitle", name == null || name.startsWith("Dictation")).toString())
        refresh()
        return id
    }

    fun addCut(id: String, cut: IntArray) = synchronized(cutLock) {
        val f = File(dir(id), "cuts.json")
        if (!f.exists()) return@synchronized  // note was deleted
        val a = JSONArray(f.readText())
        cutTimes["$id:${a.length()}"] = System.currentTimeMillis()
        writeAtomic(f, a.put(JSONArray(cut.toList())).toString())
    }

    /** Milliseconds since cut i of a note was made (live recordings), or -1. */
    fun sinceCut(id: String, i: Int): Int = cutTimes.remove("$id:$i")?.let { (System.currentTimeMillis() - it).toInt() } ?: -1

    fun rename(id: String, name: String) {
        val f = File(dir(id), "meta.json")
        if (!f.exists() || name.isBlank()) return
        writeAtomic(f, JSONObject(f.readText()).put("name", name.trim()).toString())
        refresh()
    }

    /** Subtitles (SRT) from each part's start and end, with the user's edits and word fixes. */
    fun srt(note: Note): String = note.pieces.filter { !it.junk || it.i in note.edits }.mapIndexed { k, p ->
        fun t(s: Int) = (s.toLong() * 1000 / SR).let { ms -> "%02d:%02d:%02d,%03d".format(ms / 3_600_000, ms / 60_000 % 60, ms / 1000 % 60, ms % 1000) }
        val who = note.speakerOf(p.i)?.let { note.speakerName(it) + ": " } ?: ""
        "${k + 1}\n${t(p.start)} --> ${t(p.end)}\n$who${note.text(p.i).trim()}\n"
    }.joinToString("\n")

    fun stopRecording(id: String, samples: Int) {
        val f = File(dir(id), "meta.json")
        if (!f.exists()) return  // note was deleted
        writeAtomic(f, JSONObject(f.readText()).put("recording", false).put("samples", samples).toString())
        refresh()
    }

    /** A recording cut off by a crash: keep the audio saved so far and cut the part after the last cut at pauses. */
    fun recoverRecording(context: Context, id: String) {
        val total = (File(dir(id), "audio.pcm").length() / 2).toInt()
        val from = list.value.firstOrNull { it.id == id }?.cuts?.lastOrNull()?.get(1) ?: 0
        if (total - from > SR) cutRange(context, id, from, total).forEach { addCut(id, it) }
        stopRecording(id, total)
    }

    /** Samples [start, end) as floats, clamped to what's actually on disk. */
    fun readPcm(id: String, start: Int, end: Int): FloatArray {
        RandomAccessFile(File(dir(id), "audio.pcm"), "r").use { f ->
            val have = (f.length() / 2).toInt()
            val s = start.coerceIn(0, have)
            val e = end.coerceIn(s, have)
            val bytes = ByteArray((e - s) * 2)
            f.seek(s * 2L)
            f.readFully(bytes)
            val b = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
            return FloatArray(e - s) { b.getShort() / 32768f }
        }
    }

    fun readPcmShorts(id: String, start: Int, end: Int): ShortArray {
        val f = readPcm(id, start, end)
        return ShortArray(f.size) { (f[it] * 32767).toInt().toShort() }
    }

    /** Count tries on piece i before running it. A crash inside the model kills the app before any error handler runs. */
    fun bumpAttempt(id: String, i: Int): Int {
        val f = File(dir(id), "attempt")
        val (pi, n) = f.takeIf { it.exists() }?.readText()?.split(" ")?.let { it[0].toInt() to it[1].toInt() } ?: (-1 to 0)
        val tries = if (pi == i) n + 1 else 1
        writeAtomic(f, "$i $tries")
        return tries
    }

    /** Recordings start with a date name; once real words arrive, use the first few of them as the title. */
    fun autoTitle(id: String, p: Piece) {
        if (p.junk || p.text.isBlank()) return
        val f = File(dir(id), "meta.json")
        val meta = runCatching { JSONObject(f.readText()) }.getOrNull() ?: return
        if (!meta.optBoolean("autoTitle")) return
        val words = Settings.applyFixes(p.text).replace(Regex("[^\\p{L}\\p{N}'₹ ]"), " ").split(Regex("\\s+")).filter { it.isNotBlank() }
        if (words.size < 2) return
        val title = words.take(6).joinToString(" ").replaceFirstChar { it.uppercase() } + if (words.size > 6) "…" else ""
        writeAtomic(f, meta.put("name", title).put("autoTitle", false).toString())
    }

    /** Every note as plain text, newest first: for "Export all notes" (there is no cloud backup). */
    fun exportAll(): String = list.value.filter { it.pieces.isNotEmpty() }.joinToString("\n\n" + "=".repeat(40) + "\n\n") { n ->
        val date = java.text.SimpleDateFormat("d MMM yyyy, h:mm a", java.util.Locale.getDefault()).format(java.util.Date(n.created))
        "${n.name}\n$date · ${(n.seconds / 60).toInt()} min\n\n${n.allText()}" +
            n.ai.joinToString("") { "\n\n--- ${it.label} (from your AI) ---\n${it.text}" }
    }

    fun freeBytes(): Long = android.os.StatFs(root.path).availableBytes

    fun appendPiece(id: String, p: Piece) {
        val line = JSONObject().put("i", p.i).put("start", p.start).put("end", p.end).put("text", p.text)
            .put("flags", JSONArray(p.flags)).put("ms", p.latencyMs).put("engine", p.engineMs)
            .put("segs", JSONArray(p.segs.map { JSONArray(listOf(it.start, it.end, it.text)) })).toString() + "\n"
        FileOutputStream(File(dir(id), "transcript.jsonl"), true).use { it.write(line.toByteArray()); it.fd.sync() }
    }

    fun finish(id: String, speed: String) {
        val f = File(dir(id), "meta.json")
        if (!f.exists()) return
        writeAtomic(f, JSONObject(f.readText()).put("speed", speed).toString())
        File(dir(id), "attempt").delete()
        refresh()
        exportTestResult(id)
    }

    /** A piece's text split into sentences (the unit speakers are labelled by; the model gives no sentence times). */
    fun sentences(text: String): List<String> = text.trim().split(Regex("(?<=[.?!])\\s+")).filter { it.isNotBlank() }

    /** Test notes only: copy the result where `adb pull` can read it, for the automated benchmark. */
    fun exportTestResult(id: String, extra: Pair<String, Any>? = null) {
        refresh()
        val note = list.value.firstOrNull { it.id == id }?.takeIf { it.test } ?: return
        val out = results ?: return
        val pieces = JSONArray(note.pieces.map {
            JSONObject().put("i", it.i).put("start", it.start).put("end", it.end).put("text", it.text).put("shown", note.text(it.i))
                .put("flags", JSONArray(it.flags)).put("ms", it.latencyMs).put("engine", it.engineMs)
                .put("speaker", note.speakerOf(it.i) ?: -1)
                .put("segs", JSONArray(note.speakers?.spans?.get(it.i)?.let { spans ->  // labelled sentences with their estimated times
                    sentences(it.text).zip(spans).mapIndexed { k, (t, s) -> JSONObject().put("start", s.first).put("end", s.second).put("text", t)
                        .put("speaker", note.speakers.seg[it.i]?.getOrNull(k) ?: -1) }
                } ?: listOf(JSONObject().put("start", it.start).put("end", it.end).put("text", it.text).put("speaker", note.speakerOf(it.i) ?: -1))))
        })
        val o = JSONObject().put("name", note.name).put("seconds", note.seconds).put("speed", note.speed).put("pieces", pieces)
        extra?.let { o.put(it.first, it.second) }
        File(out, "${note.name}.json").writeText(o.toString(1))
    }

    private fun loadAi(d: File): List<AiReply> = File(d, "ai.json").takeIf { it.exists() }?.let { f ->
        runCatching { JSONArray(f.readText()) }.getOrNull()?.let { a ->  // a damaged file must never hide the note itself
            List(a.length()) { a.optJSONObject(it) }.filterNotNull()
                .map { o -> AiReply(o.optString("label", "AI"), o.optString("text"), o.optLong("created")) }.filter { it.text.isNotBlank() }
        }
    } ?: emptyList()

    /** Keep an AI answer with the note (newest first). The transcript is never changed. */
    fun addAi(id: String, label: String, text: String) {
        if (!dir(id).exists() || text.isBlank()) return
        val f = File(dir(id), "ai.json")
        val a = f.takeIf { it.exists() }?.let { JSONArray(it.readText()) } ?: JSONArray()
        val all = JSONArray().put(JSONObject().put("label", label).put("text", text.trim()).put("created", System.currentTimeMillis()))
        for (k in 0 until a.length()) all.put(a.getJSONObject(k))
        writeAtomic(f, all.toString())
        refresh()
    }

    fun deleteAi(id: String, created: Long) {
        val f = File(dir(id), "ai.json")
        if (!f.exists()) return
        val a = JSONArray(f.readText())
        val keep = JSONArray()
        for (k in 0 until a.length()) a.getJSONObject(k).let { if (it.getLong("created") != created) keep.put(it) }
        writeAtomic(f, keep.toString())
        refresh()
    }

    /** Save the user's version of piece i; null removes the edit (back to the model's text). */
    fun saveEdit(id: String, i: Int, text: String?) {
        if (!dir(id).exists()) return
        val f = File(dir(id), "edits.json")
        val o = f.takeIf { it.exists() }?.let { JSONObject(it.readText()) } ?: JSONObject()
        if (text == null) o.remove(i.toString()) else o.put(i.toString(), text)
        writeAtomic(f, o.toString())
        refresh()
    }

    /** A note being recorded can't be deleted (stop it first); one being transcribed can, and the queue skips it. */
    fun delete(id: String) {
        if (id == Recording.id) return
        dir(id).deleteRecursively()
        refresh()
    }

    fun deleteAll() {
        root.listFiles()?.filter { it.name != Recording.id }?.forEach { it.deleteRecursively() }
        refresh()
    }

    fun bytesUsed(): Long = root.walkBottomUp().filter { it.isFile }.sumOf { it.length() }

    private fun writeAtomic(f: File, text: String) {
        val tmp = File(f.parentFile, f.name + ".tmp")
        FileOutputStream(tmp).use { it.write(text.toByteArray()); it.fd.sync() }
        tmp.renameTo(f)
    }
}
