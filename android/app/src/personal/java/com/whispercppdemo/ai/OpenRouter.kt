package com.whispercppdemo.ai

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * PERSONAL BUILD FIRST (critic-reviewed 2026-10-10): the user's own OpenRouter key, so AI answers are written inside indite
 * and saved with the note. Only the note's text is sent, never audio. The public build stays internet-free (stub).
 * ⚠ Many free models run on providers that may keep or train on what you send; the app warns once before the first use.
 */
object OpenRouter {
    const val available = true
    private const val API = "https://openrouter.ai/api/v1"

    private fun prefs(c: Context) = c.getSharedPreferences("openrouter", Context.MODE_PRIVATE)
    fun key(c: Context) = prefs(c).getString("key", "")!!
    fun model(c: Context) = prefs(c).getString("model", "")!!
    fun save(c: Context, key: String, model: String) = prefs(c).edit().putString("key", key.trim()).putString("model", model.trim()).apply()
    fun configured(c: Context) = key(c).startsWith("sk-") && model(c).isNotEmpty()
    fun warned(c: Context) = prefs(c).getBoolean("warned", false)
    fun setWarned(c: Context) = prefs(c).edit().putBoolean("warned", true).apply()

    private fun open(url: String, key: String) = (URL(url).openConnection() as HttpURLConnection).apply {
        connectTimeout = 10_000
        readTimeout = 180_000
        setRequestProperty("Authorization", "Bearer $key")
        setRequestProperty("X-Title", "indite")
    }

    /** Free models right now (price 0), so the list never goes stale. */
    suspend fun freeModels(c: Context): List<String> = withContext(Dispatchers.IO) {
        val conn = open("$API/models", key(c))
        try {
            val data = JSONObject(conn.inputStream.bufferedReader().readText()).getJSONArray("data")
            (0 until data.length()).map { data.getJSONObject(it) }.filter { m ->
                m.optJSONObject("pricing")?.let { it.optString("prompt") == "0" && it.optString("completion") == "0" } == true
            }.map { it.getString("id") }.sorted()
        } catch (e: java.io.IOException) { error("Couldn't reach OpenRouter. Check your internet.") } finally { conn.disconnect() }
    }

    /** The model's answer, or throws with a plain message. */
    suspend fun ask(c: Context, prompt: String, text: String): String = withContext(Dispatchers.IO) {
        val conn = open("$API/chat/completions", key(c)).apply {
            requestMethod = "POST"; doOutput = true
            setRequestProperty("Content-Type", "application/json")
        }
        val body = JSONObject().put("model", model(c))
            .put("messages", JSONArray().put(JSONObject().put("role", "user").put("content", "$prompt\n\n---\n$text")))
        try {
            conn.outputStream.use { it.write(body.toString().toByteArray()) }
            val code = conn.responseCode
            val reply = (if (code in 200..299) conn.inputStream else conn.errorStream)?.bufferedReader()?.readText().orEmpty()
            when (code) {
                401 -> error("OpenRouter didn't accept your key. Check it in Settings → AI.")
                402 -> error("This model needs credits on OpenRouter. Pick a free model in Settings → AI.")
                429 -> error("Free-model limit reached for now (about 50 a day). Try later, or send it to your AI app.")
            }
            if (code !in 200..299) error(runCatching { JSONObject(reply).getJSONObject("error").getString("message") }
                .getOrDefault("OpenRouter couldn't answer ($code)."))
            JSONObject(reply).getJSONArray("choices").getJSONObject(0).getJSONObject("message").getString("content").trim()
                .ifEmpty { error("The model sent back an empty answer. Try another model.") }
        } catch (e: java.net.SocketTimeoutException) {
            error("The model is taking too long. Try again, or a shorter note.")
        } catch (e: java.io.IOException) {
            error("Couldn't reach OpenRouter. Check your internet.")
        } finally { conn.disconnect() }
    }
}
