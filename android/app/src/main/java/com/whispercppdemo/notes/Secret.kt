package com.whispercppdemo.notes

/**
 * Is this a box for a password, PIN or one-time code? Used by the voice keyboard and the floating mic, which must never
 * record into one. Looks at the box's type, then at whole words in its hint / id / label ("upi_pin", "etPassword",
 * "mpin"), so "passenger", "passport" or "footprint" don't count.
 */
object Secret {
    private val WORDS = setOf("password", "passwd", "passcode", "pass", "pin", "mpin", "upipin", "otp", "cvv", "cvc", "secret")

    fun inputType(t: Int): Boolean {
        val v = t and android.text.InputType.TYPE_MASK_VARIATION
        return when (t and android.text.InputType.TYPE_MASK_CLASS) {
            android.text.InputType.TYPE_CLASS_TEXT -> v == android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD ||
                v == android.text.InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD || v == android.text.InputType.TYPE_TEXT_VARIATION_WEB_PASSWORD
            android.text.InputType.TYPE_CLASS_NUMBER -> v == android.text.InputType.TYPE_NUMBER_VARIATION_PASSWORD
            else -> false
        }
    }

    /** Whole words only: split on anything that isn't a letter or digit, and on camelCase ("etPassword" -> et, password). */
    fun words(vararg labels: CharSequence?): Boolean = labels.filterNotNull().any { label ->
        label.toString().replace(Regex("([a-z])([A-Z])"), "$1 $2").lowercase()
            .split(Regex("[^a-z0-9]+")).any { it in WORDS || (it.endsWith("pin") && it.length <= 6) }
    }
}
