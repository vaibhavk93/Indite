package com.whispercppdemo.notes

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import com.whispercppdemo.media.decodeAudio
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

data class Piece(val i: Int, val start: Int, val end: Int, val text: String, val flags: List<String>) {
    val startSec get() = start / SR.toDouble()
}

data class Note(
    val id: String, val name: String, val created: Long, val samples: Int,
    val cuts: List<IntArray>, val pieces: List<Piece>, val edits: Map<Int, String>, val speed: String?,
    val recording: Boolean,
) {
    val seconds get() = samples / SR.toDouble()
    val done get() = !recording && pieces.size >= cuts.size
    val pending get() = pieces.size < cuts.size
    fun text(i: Int) = edits[i] ?: pieces[i].text
    /** Plain text for copying: edits applied, no "Check" labels. */
    fun allText() = pieces.indices.joinToString(" ") { text(it).trim() }.replace(Regex("\\s+"), " ").trim()
}

/**
 * Each note is a folder: audio.pcm (16 kHz mono 16-bit, no header), cuts.json, transcript.jsonl (one line per
 * finished piece, appended and flushed at once), attempt (crash-loop guard), edits.json (user's fixes; the
 * transcript itself is never changed), meta.json (written last, so a half-imported note is never listed).
 */
object Notes {
    val list = MutableStateFlow<List<Note>>(emptyList())
    val status = MutableStateFlow("")
    val level = MutableStateFlow(0f)  // live mic loudness 0..1 while recording
    @Volatile var transcribing = false  // the recorder cuts short pieces only while the engine is free
    private val cutLock = Any()
    private lateinit var root: File

    fun init(context: Context) {
        if (!::root.isInitialized) root = File(context.filesDir, "notes").apply { mkdirs() }
        refresh()
    }

    fun dir(id: String) = File(root, id)

    fun refresh() {
        list.value = (root.listFiles() ?: emptyArray()).mapNotNull { load(it) }.sortedByDescending { it.created }
    }

    private fun load(d: File): Note? = try {
        val meta = JSONObject(File(d, "meta.json").readText())
        val cuts = JSONArray(File(d, "cuts.json").readText()).let { a ->
            List(a.length()) { a.getJSONArray(it).let { c -> IntArray(c.length()) { k -> c.getInt(k) } } }
        }
        val pieces = File(d, "transcript.jsonl").takeIf { it.exists() }?.readLines()?.mapNotNull { line ->
            try {  // a line cut short by a crash is ignored: that piece is simply redone
                val o = JSONObject(line)
                val f = o.getJSONArray("flags")
                Piece(o.getInt("i"), o.getInt("start"), o.getInt("end"), o.getString("text"), List(f.length()) { f.getString(it) })
            } catch (e: Exception) { null }
        } ?: emptyList()
        val edits = File(d, "edits.json").takeIf { it.exists() }?.let { f ->
            JSONObject(f.readText()).let { o -> o.keys().asSequence().associate { it.toInt() to o.getString(it) } }
        } ?: emptyMap()
        val recording = meta.optBoolean("recording")
        val samples = if (recording) (File(d, "audio.pcm").length() / 2).toInt() else meta.getInt("samples")
        Note(d.name, meta.getString("name"), meta.getLong("created"), samples, cuts, pieces, edits,
            meta.optString("speed").ifEmpty { null }, recording)
    } catch (e: Exception) { null }

    /** Copy a shared or picked file in (shared links can expire), decode it and cut it at pauses. Returns the note id. */
    suspend fun import(context: Context, uri: Uri): String = withContext(Dispatchers.IO) {
        val name = context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use {
            if (it.moveToFirst()) it.getString(0) else null
        }?.substringBeforeLast('.') ?: "Voice note"
        val id = System.currentTimeMillis().toString()
        val d = dir(id).apply { mkdirs() }
        try {
            val source = File(d, "source")
            context.contentResolver.openInputStream(uri)!!.use { i -> source.outputStream().use { i.copyTo(it) } }
            val audio = decodeAudio(source).samples
            source.delete()
            if (audio.size < SR / 2) error("This file has no audio we can read.")
            File(d, "audio.pcm").outputStream().use { out ->
                val buf = ByteBuffer.allocate(audio.size * 2).order(ByteOrder.LITTLE_ENDIAN)
                for (v in audio) buf.putShort((v.coerceIn(-1f, 1f) * 32767).toInt().toShort())
                out.write(buf.array())
            }
            val cuts = Pauses.cut(audio)
            writeAtomic(File(d, "cuts.json"), JSONArray(cuts.map { JSONArray(it.toList()) }).toString())
            writeAtomic(File(d, "meta.json"), JSONObject().put("name", name).put("created", id.toLong()).put("samples", audio.size).toString())
            refresh()
            id
        } catch (e: Exception) {
            d.deleteRecursively()
            throw e
        }
    }

    /** A new, empty recording. The recorder appends audio.pcm and adds a cut at every pause. */
    fun startRecording(): String {
        val id = System.currentTimeMillis().toString()
        val d = dir(id).apply { mkdirs() }
        File(d, "audio.pcm").createNewFile()
        writeAtomic(File(d, "cuts.json"), "[]")
        val name = "Recording, " + java.text.SimpleDateFormat("d MMM, h:mm a", java.util.Locale.getDefault()).format(java.util.Date(id.toLong()))
        writeAtomic(File(d, "meta.json"), JSONObject().put("name", name).put("created", id.toLong()).put("samples", 0).put("recording", true).toString())
        refresh()
        return id
    }

    fun addCut(id: String, cut: IntArray) = synchronized(cutLock) {
        val f = File(dir(id), "cuts.json")
        writeAtomic(f, JSONArray(f.readText()).put(JSONArray(cut.toList())).toString())
    }

    fun stopRecording(id: String, samples: Int) {
        val f = File(dir(id), "meta.json")
        writeAtomic(f, JSONObject(f.readText()).put("recording", false).put("samples", samples).toString())
        refresh()
    }

    /** A recording cut off by a crash: keep the audio saved so far and cut the part after the last cut at pauses. */
    fun recoverRecording(id: String) {
        val total = (File(dir(id), "audio.pcm").length() / 2).toInt()
        val from = list.value.firstOrNull { it.id == id }?.cuts?.lastOrNull()?.get(1) ?: 0
        if (total - from > SR) Pauses.cut(readPcm(id, from, total)).forEach { addCut(id, intArrayOf(it[0] + from, it[1] + from, it[2])) }
        stopRecording(id, total)
    }

    fun readPcm(id: String, start: Int, end: Int): FloatArray {
        val bytes = ByteArray((end - start) * 2)
        RandomAccessFile(File(dir(id), "audio.pcm"), "r").use { it.seek(start * 2L); it.readFully(bytes) }
        val b = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
        return FloatArray(end - start) { b.getShort() / 32768f }
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

    fun appendPiece(id: String, p: Piece) {
        val line = JSONObject().put("i", p.i).put("start", p.start).put("end", p.end).put("text", p.text)
            .put("flags", JSONArray(p.flags)).toString() + "\n"
        FileOutputStream(File(dir(id), "transcript.jsonl"), true).use { it.write(line.toByteArray()); it.fd.sync() }
    }

    fun finish(id: String, speed: String) {
        val f = File(dir(id), "meta.json")
        writeAtomic(f, JSONObject(f.readText()).put("speed", speed).toString())
        File(dir(id), "attempt").delete()
        refresh()
    }

    fun saveEdit(id: String, i: Int, text: String) {
        val f = File(dir(id), "edits.json")
        val o = f.takeIf { it.exists() }?.let { JSONObject(it.readText()) } ?: JSONObject()
        writeAtomic(f, o.put(i.toString(), text).toString())
    }

    fun delete(id: String) {
        dir(id).deleteRecursively()
        refresh()
    }

    private fun writeAtomic(f: File, text: String) {
        val tmp = File(f.parentFile, f.name + ".tmp")
        FileOutputStream(tmp).use { it.write(text.toByteArray()); it.fd.sync() }
        tmp.renameTo(f)
    }
}
