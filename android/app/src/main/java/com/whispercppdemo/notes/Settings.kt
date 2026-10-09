package com.whispercppdemo.notes

import android.content.Context
import android.content.SharedPreferences
import kotlinx.coroutines.flow.MutableStateFlow
import org.json.JSONArray
import org.json.JSONObject

enum class Theme(val label: String) { SYSTEM("Same as phone"), LIGHT("Light"), DARK("Dark") }

/** App settings, stored on this phone only (backup is off). */
object Settings {
    private lateinit var p: SharedPreferences
    val theme = MutableStateFlow(Theme.SYSTEM)
    /** Word fixes: whole words, any case. "PTM" -> "Paytm". Applied to what you see and copy; the original is kept. */
    val fixes = MutableStateFlow<List<Pair<String, String>>>(emptyList())
    /** Everyday spelling (achha, maine, kyunki) instead of the model's formal one (achchha, mainne, kyonki). On by default:
     *  on the benchmark it cut word errors from 18.1% to 13.0%; on a real interview it changed 5 words, all for the better. */
    val chatSpelling = MutableStateFlow(true)
    private var spelling: Map<String, String> = emptyMap()
    private var spellingRx: Regex? = null

    fun init(context: Context) {
        if (::p.isInitialized) return
        p = context.getSharedPreferences("settings", Context.MODE_PRIVATE)
        theme.value = runCatching { Theme.valueOf(p.getString("theme", "SYSTEM")!!) }.getOrDefault(Theme.SYSTEM)
        chatSpelling.value = p.getBoolean("chatSpelling", true)
        spelling = context.resources.openRawResource(com.whispercppdemo.R.raw.spelling).bufferedReader().readLines()
            .filter { it.isNotBlank() && !it.startsWith("#") }.map { it.split("\t") }.filter { it.size == 2 }
            .associate { it[0].lowercase() to it[1] }
        spellingRx = Regex("(?<![\\p{L}\\p{N}'])(" + spelling.keys.sortedByDescending { it.length }.joinToString("|") { Regex.escape(it) } +
            ")(?![\\p{L}\\p{N}'])", RegexOption.IGNORE_CASE)
        fixes.value = JSONArray(p.getString("fixes", "[]")).let { a ->
            List(a.length()) { a.getJSONObject(it).let { o -> o.getString("from") to o.getString("to") } }
        }
    }

    fun setTheme(t: Theme) { theme.value = t; p.edit().putString("theme", t.name).apply() }
    fun setChatSpelling(v: Boolean) { chatSpelling.value = v; p.edit().putBoolean("chatSpelling", v).apply() }

    val onboarded get() = p.getBoolean("onboarded", false)
    fun setOnboarded() = p.edit().putBoolean("onboarded", true).apply()

    /**
     * The user changed `before` into `after`. If exactly one word changed, count it; the second time the same fix is
     * made, return it as a suggestion ("Always fix PTM -> Paytm?"). Already-saved fixes are not suggested again.
     */
    fun learn(before: String, after: String): Pair<String, String>? {
        val a = before.trim().split(Regex("\\s+"))
        val b = after.trim().split(Regex("\\s+"))
        if (a.size != b.size) return null
        val diff = a.indices.filter { a[it] != b[it] }
        if (diff.size != 1) return null
        val clean = { w: String -> w.trim { !it.isLetterOrDigit() } }
        val from = clean(a[diff[0]]); val to = clean(b[diff[0]])
        if (from.isEmpty() || to.isEmpty() || from.equals(to, ignoreCase = true)) return null
        if (fixes.value.any { it.first.equals(from, ignoreCase = true) }) return null
        val key = "learn:${from.lowercase()}>$to"
        val n = p.getInt(key, 0) + 1
        p.edit().putInt(key, n).apply()
        return if (n == 2) from to to else null
    }

    fun addFix(from: String, to: String) {
        val f = from.trim()
        val t = to.trim()
        if (f.isEmpty() || t.isEmpty()) return
        saveFixes(fixes.value.filterNot { it.first.equals(f, ignoreCase = true) } + (f to t))
    }

    fun removeFix(from: String) = saveFixes(fixes.value.filterNot { it.first == from })

    private fun saveFixes(list: List<Pair<String, String>>) {
        fixes.value = list
        p.edit().putString("fixes", JSONArray(list.map { JSONObject().put("from", it.first).put("to", it.second) }).toString()).apply()
    }

    /** What the user sees: everyday spelling (if on), then their own word fixes. The model's text is kept as is. */
    fun applyFixes(text: String): String = userFixes(if (chatSpelling.value) chat(text) else text)

    private fun chat(text: String): String = spellingRx?.replace(text) { m ->
        val c = spelling[m.value.lowercase()] ?: m.value
        if (m.value.first().isUpperCase()) c.replaceFirstChar { it.uppercase() } else c
    } ?: text

    private fun userFixes(text: String): String = fixes.value.fold(text) { t, (from, to) ->
        t.replace(Regex("(?<![\\p{L}\\p{N}])" + Regex.escape(from) + "(?![\\p{L}\\p{N}])", RegexOption.IGNORE_CASE), Regex.escapeReplacement(to))
    }
}
