package com.whispercppdemo.ai

import android.content.Context

/**
 * Where an AI request goes, in one place. The note screen, the keyboard and the floating mic all used to work this
 * out for themselves, in slightly different ways (AUD-035). The public build has neither route, so `ready` is simply
 * false there and nothing offers what it cannot do.
 */
object Route {
    /** True when something on this phone can actually answer right now. */
    fun ready(c: Context) = MacCompanion.configured(c) || OpenRouter.configured(c)

    /** The founder's Mac first (it is free and private), then the user's own key. Throws with a plain message. */
    suspend fun ask(c: Context, prompt: String, text: String): String =
        if (MacCompanion.configured(c)) MacCompanion.ask(c, prompt, text) else OpenRouter.ask(c, prompt, text)
}
