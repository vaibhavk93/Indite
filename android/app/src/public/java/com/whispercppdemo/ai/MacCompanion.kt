package com.whispercppdemo.ai

import android.content.Context

/** Public build: no Mac connection, no internet. (The personal build has the real one.) */
object MacCompanion {
    const val available = false
    fun url(c: Context) = ""
    fun token(c: Context) = ""
    fun save(c: Context, url: String, token: String) {}
    fun configured(c: Context) = false
    fun via(c: Context) = "claude"
    fun setVia(c: Context, v: String) {}
    suspend fun ask(c: Context, prompt: String, text: String): String = error("Not available in this version.")
}
