package com.whispercppdemo.overlay

import android.content.Context

/** Public build: no accessibility service (decision pending on Google Play's review cost). The green copy button is used. */
object AutoPaste {
    const val available = false
    fun enabled() = false
    fun capture() {}
    fun forget() {}
    fun paste(c: Context, text: String) = false
}
