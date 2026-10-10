package com.whispercppdemo.ai

import android.content.Context

/** Public build: no internet, so no API key. (The personal build has the real one.) */
object OpenRouter {
    const val available = false
    fun key(c: Context) = ""
    fun model(c: Context) = ""
    fun save(c: Context, key: String, model: String) {}
    fun configured(c: Context) = false
    fun warned(c: Context) = true
    fun setWarned(c: Context) {}
    suspend fun freeModels(c: Context): List<String> = emptyList()
    suspend fun ask(c: Context, prompt: String, text: String): String = error("Not available in this version.")
}
