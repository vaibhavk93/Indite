package com.whispercppdemo.notes

import android.content.Context
import com.k2fsa.sherpa.onnx.SpeakerEmbeddingExtractor
import com.k2fsa.sherpa.onnx.SpeakerEmbeddingExtractorConfig
import com.whispercpp.whisper.SpeechDetector
import kotlinx.coroutines.flow.MutableStateFlow
import org.json.JSONObject
import java.io.File
import kotlin.math.sqrt
import kotlin.random.Random

/**
 * Who spoke when, on the phone. Tested on the synthetic two-person dialogues: 98% of turns right, also with two
 * similar voices (the pyannote pipeline got 50% there). Recipe (bench_synth + scratchpad speaker/vadspk.py):
 * Silero finds speech, split at 0.25 s pauses -> 1.5 s windows -> TitaNet-small voice fingerprints (CC BY 4.0) ->
 * spherical k-means into the number of speakers the user gives -> each paragraph gets its majority speaker.
 * speakers.json = {"of": {"<piece>": n}, "names": {"<n>": "Amit"}, "k": K}
 */
object Speakers {
    private const val WIN = 512                 // Silero step: 32 ms
    private const val PIECE = (1.5 * SR).toInt() // fingerprint window

    /** of: one speaker per paragraph (majority); seg: one speaker per sentence inside it (a paragraph often holds several turns). */
    data class Result(val of: Map<Int, Int>, val names: Map<Int, String>, val k: Int = 0, val skipped: Boolean = false,
                      val seg: Map<Int, List<Int>> = emptyMap(), val spans: Map<Int, List<Pair<Int, Int>>> = emptyMap(),
                      /** indite guessed how many people spoke; the user hasn't confirmed it yet. */
                      val guessed: Boolean = false)

    /** Ids being labelled right now (so "Who spoke?" can't run twice on one note). */
    val running: MutableSet<String> = java.util.concurrent.ConcurrentHashMap.newKeySet()

    /** What a run started by indite itself is doing: note id -> message, null when nothing is running. */
    val status = MutableStateFlow<Pair<String, String>?>(null)

    /**
     * The first pass, run by [NoteService] as soon as the text is ready, without being asked (founder, 10 Oct:
     * "initial speaker diarization should be done by you"). The count is a guess, so the note screen then asks the
     * user to confirm or change it — that is the cheap half of the job, because the voice fingerprints stay in memory.
     *
     * One voice found (or no speech) is saved as nothing to label, so a note that is only the user talking never gets
     * a pointless "Speaker 1" on every paragraph.
     */
    fun labelAuto(context: Context, note: Note) {
        try { label(context, note, 0) { status.value = note.id to it } } finally { status.value = null }
    }

    /**
     * Only one voice in this recording: no labels. `k = 1` separates it from the user tapping "Just me" (which leaves k
     * at 0), and `guessed` says indite decided this by itself — together they let the note screen offer "two people
     * spoke?" once, on a recording long enough to be a conversation, without nagging someone who chose 1 themselves.
     */
    private fun heardOne(id: String, guessed: Boolean) {
        val f = File(Notes.dir(id), "speakers.json")
        val names = runCatching { JSONObject(f.readText()).optJSONObject("names") }.getOrNull()  // keep any names given
        write(f, JSONObject().put("skipped", true).put("k", 1).put("guessed", guessed)
            .put("names", names ?: JSONObject()).put("of", JSONObject()))
    }

    /** The user said it was just them: hide the "Who spoke?" card for this note. */
    fun skip(id: String) {
        File(Notes.dir(id), "speakers.json").writeText(JSONObject().put("skipped", true).put("of", JSONObject()).toString())
        Notes.refresh()
    }

    fun load(id: String): Result? = try {
        val o = JSONObject(File(Notes.dir(id), "speakers.json").readText())
        val of = o.getJSONObject("of").let { m -> m.keys().asSequence().associate { it.toInt() to m.getInt(it) } }
        val names = o.optJSONObject("names")?.let { m -> m.keys().asSequence().associate { it.toInt() to m.getString(it) } } ?: emptyMap()
        val seg = o.optJSONObject("seg")?.let { m -> m.keys().asSequence().associate { key ->
            key.toInt() to m.getJSONArray(key).let { a -> List(a.length()) { a.getInt(it) } } } } ?: emptyMap()
        val spans = o.optJSONObject("spans")?.let { m -> m.keys().asSequence().associate { key ->
            key.toInt() to m.getJSONArray(key).let { a -> List(a.length()) { a.getJSONArray(it).let { s -> s.getInt(0) to s.getInt(1) } } } } } ?: emptyMap()
        Result(of, names, o.optInt("k"), o.optBoolean("skipped"), seg, spans, o.optBoolean("guessed"))
    } catch (e: Exception) { null }

    /**
     * k = how many people spoke, or 0 to guess (picks 1-5 by how distinct the voices are) and let the user confirm or
     * change it. The voice fingerprints are kept in memory, so changing the count afterwards takes a moment.
     */
    fun label(context: Context, note: Note, k: Int, progress: (String) -> Unit) {
        if (!running.add(note.id)) return
        try {
            labelNow(context, note, k, progress)
            // One voice (or none) means labels add nothing: drop them rather than write "Speaker 1" on every paragraph.
            if ((load(note.id)?.of?.values?.distinct()?.size ?: 0) < 2) heardOne(note.id, guessed = k == 0)
        } finally { running.remove(note.id) }
        if (k > 0) context.getSharedPreferences("settings", Context.MODE_PRIVATE).edit().putInt("lastSpeakers", k).apply()
    }

    /** The user said the guessed count is right. */
    fun confirm(id: String) = update(id) { it.put("guessed", false) }

    /** Last note's fingerprints: (note id, samples) -> windows, stretches, fingerprints. */
    @Volatile private var cache: Triple<String, Triple<List<Pair<Int, Int>>, List<Pair<Int, Int>>, List<FloatArray>>, Unit>? = null

    fun lastCount(context: Context) = context.getSharedPreferences("settings", Context.MODE_PRIVATE).getInt("lastSpeakers", 2)

    private fun labelNow(context: Context, note: Note, k: Int, progress: (String) -> Unit) {
        val key = "${note.id}:${note.samples}"
        val (windows, stretches, emb) = cache?.takeIf { it.first == key }?.second ?: run {
        progress("Finding where people speak…")
        val (windows, stretches) = speechWindows(context, note)
        if (windows.isEmpty()) { save(note.id, emptyMap(), k); return }
        progress("Listening for different voices…")
        val ex = SpeakerEmbeddingExtractor(context.assets, SpeakerEmbeddingExtractorConfig(model = "models/titanet_small.onnx", numThreads = 4))
        val emb = try {
            windows.mapIndexed { n, (s, e) ->
                if (n % 50 == 0) progress("Listening for different voices… ${100 * n / windows.size}%")
                val st = ex.createStream()
                try {
                    st.acceptWaveform(Notes.readPcm(note.id, s, e), SR)
                    st.inputFinished()
                    normalize(ex.compute(st))
                } finally { st.release() }
            }
        } finally { ex.release() }
        Triple(windows, stretches, emb).also { cache = Triple(key, it, Unit) }
        }
        progress("Grouping voices…")
        val lab = if (k > 0) kmeans(emb, k) else auto(emb)
        val count = if (k > 0) k else lab.distinct().size
        // A 15-25 s paragraph often holds several turns, and the model gives no sentence times (one segment per piece).
        // So each sentence is placed over the piece's speech by its share of the characters, snapped to the nearest
        // pause, and gets the speaker who talks longest in it. Mac bench 2026-10-10: 51.7% -> 98.3% of turns right
        // (95.0% with two similar voices), on synthetic dialogue; real conversations will score lower.
        val order = mutableMapOf<Int, Int>()  // number speakers in order of first appearance
        fun who(start: Int, end: Int): Int? {
            val votes = mutableMapOf<Int, Int>()
            windows.indices.forEach { w ->
                val o = minOf(end, windows[w].second) - maxOf(start, windows[w].first)
                if (o > 0) votes[lab[w]] = (votes[lab[w]] ?: 0) + o
            }
            return votes.maxByOrNull { it.value }?.key?.let { order.getOrPut(it) { order.size } }
        }
        val of = mutableMapOf<Int, Int>()
        val seg = mutableMapOf<Int, List<Int>>()
        val spans = mutableMapOf<Int, List<Pair<Int, Int>>>()
        for (p in note.pieces) {
            val fallback = who(p.start, p.end) ?: continue
            of[p.i] = fallback
            val place = place(Notes.sentences(p.text), p.start, p.end, stretches) ?: continue
            val each = place.map { (s, e) -> who(s, e) ?: fallback }
            seg[p.i] = each
            spans[p.i] = place
            of[p.i] = place.zip(each).groupBy({ it.second }, { it.first.second - it.first.first }).maxByOrNull { (_, d) -> d.sum() }!!.key
        }
        save(note.id, of, count, seg, spans, guessed = k == 0)
    }

    fun rename(id: String, speaker: Int, name: String) = update(id) { it.getJSONObject("names").put(speaker.toString(), name.trim()) }
    /** The user moved a whole paragraph to one speaker: that overrides the per-sentence guess. */
    fun move(id: String, piece: Int, speaker: Int) = update(id) {
        it.getJSONObject("of").put(piece.toString(), speaker)
        it.optJSONObject("seg")?.remove(piece.toString())
    }

    private fun update(id: String, change: (JSONObject) -> Unit) {
        val f = File(Notes.dir(id), "speakers.json")
        if (!f.exists()) return
        val o = JSONObject(f.readText())
        if (!o.has("names")) o.put("names", JSONObject())
        change(o)
        write(f, o)
    }

    /**
     * Where each sentence was probably said: spread by character count over speech time only (never the pauses),
     * each boundary moved to the middle of the nearest pause within 0.75 s. Null if there's nothing to split.
     */
    internal fun place(sents: List<String>, start: Int, end: Int, stretches: List<Pair<Int, Int>>): List<Pair<Int, Int>>? {
        if (sents.size < 2) return null
        val sp = stretches.mapNotNull { (s, e) -> (maxOf(s, start) to minOf(e, end)).takeIf { it.second > it.first } }
        val total = sp.sumOf { it.second - it.first }
        if (total <= 0) return null
        fun atSpeech(t: Long): Int {  // speech-time offset -> sample position
            var left = t
            for ((s, e) in sp) { if (left <= e - s) return s + left.toInt(); left -= e - s }
            return sp.last().second
        }
        val chars = sents.map { it.length.toLong() }
        val all = chars.sum()
        val gaps = sp.zipWithNext { a, b -> (a.second + b.first) / 2 }
        val cuts = mutableListOf<Int>()
        var acc = 0L
        for (c in chars.dropLast(1)) {
            acc += c
            var b = atSpeech(total * acc / all)
            gaps.minByOrNull { kotlin.math.abs(it - b) }?.let { g -> if (kotlin.math.abs(g - b) <= (0.75 * SR).toInt()) b = g }
            cuts += maxOf(b, cuts.lastOrNull() ?: start)
        }
        val bounds = listOf(start) + cuts + listOf(end)
        return bounds.zipWithNext()
    }

    private fun save(id: String, of: Map<Int, Int>, k: Int, seg: Map<Int, List<Int>> = emptyMap(),
                     spans: Map<Int, List<Pair<Int, Int>>> = emptyMap(), guessed: Boolean = false) {
        // keep names the user already gave (re-labelling with a different count keeps "Speaker 1" = Amit)
        val old = runCatching { JSONObject(File(Notes.dir(id), "speakers.json").readText()).optJSONObject("names") }.getOrNull()
        val o = JSONObject().put("k", k).put("names", old ?: JSONObject()).put("guessed", guessed)
            .put("of", JSONObject().apply { of.forEach { (p, s) -> put(p.toString(), s) } })
            .put("seg", JSONObject().apply { seg.forEach { (p, s) -> put(p.toString(), org.json.JSONArray(s)) } })
            .put("spans", JSONObject().apply { spans.forEach { (p, s) ->
                put(p.toString(), org.json.JSONArray(s.map { org.json.JSONArray(listOf(it.first, it.second)) })) } })
        write(File(Notes.dir(id), "speakers.json"), o)
    }

    /** Written to a temp file and renamed, so a crash mid-write never leaves a broken file. */
    private fun write(f: File, o: JSONObject) {
        if (!f.parentFile!!.exists()) return
        val tmp = File(f.parentFile, f.name + ".tmp")
        tmp.writeText(o.toString())
        tmp.renameTo(f)
        Notes.refresh()
    }

    /** Speech stretches (split at 0.25 s pauses), cut into 1.5 s windows; tiny leftovers (< 0.4 s) dropped. */
    /** Returns the 1.5 s windows and the speech stretches they came from (split at 0.25 s pauses). */
    private fun speechWindows(context: Context, note: Note): Pair<List<Pair<Int, Int>>, List<Pair<Int, Int>>> {
        val det = SpeechDetector(Engine.vadPath(context))
        val out = mutableListOf<Pair<Int, Int>>()
        val stretches = mutableListOf<Pair<Int, Int>>()
        try {
            val chunk = 10 * 60 * SR
            var base = 0
            while (base < note.samples) {
                val end = minOf(note.samples, base + chunk)
                val probs = det.probs(Notes.readPcm(note.id, base, end))
                var start = -1
                var quiet = 0
                fun close(f: Int) {
                    val s = base + start * WIN
                    val e = base + f * WIN
                    stretches += s to e
                    var w = s
                    while (w < e) { val we = minOf(e, w + PIECE); if (we - w >= (0.4 * SR).toInt()) out += w to we; w = we }
                    start = -1
                }
                for (f in probs.indices) {
                    if (probs[f] >= 0.5f) { if (start < 0) start = f; quiet = 0 }
                    else if (start >= 0 && ++quiet >= 8) close(f - quiet + 1)
                }
                if (start >= 0) close(probs.size)
                base = end
            }
        } finally { det.release() }
        return out to stretches
    }

    private fun normalize(v: FloatArray): FloatArray {
        val n = sqrt(v.sumOf { (it * it).toDouble() }).toFloat().coerceAtLeast(1e-9f)
        return FloatArray(v.size) { v[it] / n }
    }

    private fun dot(a: FloatArray, b: FloatArray): Float { var s = 0f; for (i in a.indices) s += a[i] * b[i]; return s }

    /** Spherical k-means, 20 random restarts (fixed seed), best total similarity wins. */
    private fun kmeans(e: List<FloatArray>, k: Int): IntArray {
        if (e.size <= k) return IntArray(e.size) { it }
        val rnd = Random(0)
        var best: IntArray? = null
        var bestScore = Float.NEGATIVE_INFINITY
        repeat(20) {
            var c = e.indices.shuffled(rnd).take(k).map { e[it].copyOf() }
            var lab = IntArray(e.size)
            repeat(30) {
                lab = IntArray(e.size) { i -> c.indices.maxByOrNull { dot(e[i], c[it]) }!! }
                c = (0 until k).map { j ->
                    val members = e.indices.filter { lab[it] == j }
                    if (members.isEmpty()) e[rnd.nextInt(e.size)].copyOf()
                    else normalize(FloatArray(e[0].size) { d -> members.sumOf { e[it][d].toDouble() }.toFloat() })
                }
            }
            val score = e.indices.sumOf { dot(e[it], c[lab[it]]).toDouble() }.toFloat()
            if (score > bestScore) { bestScore = score; best = lab }
        }
        return best!!
    }

    /**
     * Beta: "not sure how many". Try 1-5 speakers and keep the most that are clearly different voices
     * (centres at least 0.35 apart) and each speak a fair share (5% of the talking, at least 5 s).
     */
    private fun auto(e: List<FloatArray>): IntArray {
        var pick = IntArray(e.size)
        for (k in 2..5) {
            if (e.size < k * 4) break
            val lab = kmeans(e, k)
            val sizes = (0 until k).map { j -> lab.count { it == j } }
            val minShare = maxOf((5.0 * SR / PIECE).toInt(), e.size / 20)
            if (sizes.any { it < minShare }) break
            val c = (0 until k).map { j -> normalize(FloatArray(e[0].size) { d -> e.indices.filter { lab[it] == j }.sumOf { e[it][d].toDouble() }.toFloat() }) }
            val closest = (0 until k).flatMap { a -> (a + 1 until k).map { b -> 1 - dot(c[a], c[b]) } }.minOrNull() ?: 0f
            if (closest < 0.35f) break
            pick = lab
        }
        return pick
    }
}
