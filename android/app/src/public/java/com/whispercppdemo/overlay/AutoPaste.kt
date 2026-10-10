package com.whispercppdemo.overlay

import android.content.Context

/** Public build: no accessibility service (decision pending on Google Play's review cost). The green copy button is used. */
object AutoPaste {
    const val available = false
    fun enabled() = false
    fun capture() {}
    fun forget() {}
    fun sensitiveFocus() = false  // the public build can't see which box you're in
    fun paste(c: Context, text: String) = false
}
