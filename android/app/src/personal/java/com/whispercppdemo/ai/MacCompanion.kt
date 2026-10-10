package com.whispercppdemo.ai

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * PERSONAL BUILD ONLY (removed before launch). Sends a note + request to the founder's own Mac, where the indite web
 * app runs his own unmodified `claude -p` on his Claude subscription (allowed: his plan, Anthropic's tool, his machine).
 * Reached through Tailscale (https://<mac>.<tailnet>.ts.net), so it's private and works away from home Wi-Fi.
 */
object MacCompanion {
    const val available = true

    private fun prefs(c: Context) = c.getSharedPreferences("mac", Context.MODE_PRIVATE)
    fun url(c: Context) = prefs(c).getString("url", "")!!
    fun token(c: Context) = prefs(c).getString("token", "")!!
    fun save(c: Context, url: String, token: String) =
        prefs(c).edit().putString("url", url.trim().trimEnd('/')).putString("token", token.trim()).apply()
    fun configured(c: Context) = url(c).startsWith("https://") && token(c).isNotEmpty()

    /** Returns Claude's answer, or throws with a plain message. */
    suspend fun ask(c: Context, prompt: String, text: String): String = withContext(Dispatchers.IO) {
        val conn = (URL(url(c) + "/api/ask").openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 8_000
            readTimeout = 600_000  // claude can take a while on a long note
            doOutput = true
            setRequestProperty("Content-Type", "application/json")
            setRequestProperty("Authorization", "Bearer " + token(c))
        }
        try {
            conn.outputStream.use { it.write(JSONObject().put("prompt", prompt).put("text", text).toString().toByteArray()) }
            val code = conn.responseCode
            val body = (if (code in 200..299) conn.inputStream else conn.errorStream)?.bufferedReader()?.readText().orEmpty()
            if (code == 401) error("The Mac didn't accept the token. Copy it again from the Mac.")
            if (code !in 200..299) error(runCatching { JSONObject(body).getString("detail") }.getOrDefault("The Mac couldn't answer ($code)."))
            JSONObject(body).getString("answer")
        } catch (e: java.net.SocketTimeoutException) {
            error("Your Mac is taking too long to answer. Try a shorter note.")
        } catch (e: java.io.IOException) {
            error("Couldn't reach your Mac. Is it awake, with indite and Tailscale running?")
        } finally { conn.disconnect() }
    }
}
