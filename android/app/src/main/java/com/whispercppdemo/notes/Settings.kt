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

    fun init(context: Context) {
        if (::p.isInitialized) return
        p = context.getSharedPreferences("settings", Context.MODE_PRIVATE)
        theme.value = runCatching { Theme.valueOf(p.getString("theme", "SYSTEM")!!) }.getOrDefault(Theme.SYSTEM)
        fixes.value = JSONArray(p.getString("fixes", "[]")).let { a ->
            List(a.length()) { a.getJSONObject(it).let { o -> o.getString("from") to o.getString("to") } }
        }
    }

    fun setTheme(t: Theme) { theme.value = t; p.edit().putString("theme", t.name).apply() }

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

    fun applyFixes(text: String): String = fixes.value.fold(text) { t, (from, to) ->
        t.replace(Regex("(?<![\\p{L}\\p{N}])" + Regex.escape(from) + "(?![\\p{L}\\p{N}])", RegexOption.IGNORE_CASE), Regex.escapeReplacement(to))
    }
}
