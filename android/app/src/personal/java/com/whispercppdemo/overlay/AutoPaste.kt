package com.whispercppdemo.overlay

import android.accessibilityservice.AccessibilityService
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.os.Build
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

/**
 * Personal build only (for now): "Type into the box for me". When a bubble dictation is ready, paste it into the text box
 * that had focus when the bubble was tapped, if that same box still has focus. Otherwise the green copy button, as before.
 * It never listens to screen events and never reads screen text: it only finds the focused box at two moments.
 */
object AutoPaste {
    const val available = true
    fun enabled() = PasteService.instance != null

    @Volatile private var target: AccessibilityNodeInfo? = null

    /** At the bubble tap: remember the focused text box (skip password and other sensitive boxes). */
    fun capture() {
        target = PasteService.instance?.rootInActiveWindow?.findFocus(AccessibilityNodeInfo.FOCUS_INPUT)?.takeIf {
            it.isEditable && !sensitive(it)
        }
    }

    fun forget() { target = null }

    /**
     * The box you're in is for a password, PIN or code: the bubble must not record into it. Some apps don't mark their
     * password boxes, so the input type, the hint and the box's id are checked too (founder found one on 10 Oct).
     */
    fun sensitiveFocus(): Boolean =
        PasteService.instance?.rootInActiveWindow?.findFocus(AccessibilityNodeInfo.FOCUS_INPUT)?.let(::sensitive) ?: false

    private fun sensitive(n: AccessibilityNodeInfo): Boolean {
        if (n.isPassword || (Build.VERSION.SDK_INT >= 34 && n.isAccessibilityDataSensitive)) return true
        val v = n.inputType and android.text.InputType.TYPE_MASK_VARIATION
        val cls = n.inputType and android.text.InputType.TYPE_MASK_CLASS
        if (cls == android.text.InputType.TYPE_CLASS_TEXT && v in setOf(android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD,
                android.text.InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD, android.text.InputType.TYPE_TEXT_VARIATION_WEB_PASSWORD)) return true
        if (cls == android.text.InputType.TYPE_CLASS_NUMBER && v == android.text.InputType.TYPE_NUMBER_VARIATION_PASSWORD) return true
        val words = listOfNotNull(n.hintText, n.viewIdResourceName, n.contentDescription, n.paneTitle).joinToString(" ")
        return Regex("pass(word|code)?|\\bpin\\b|otp|one.?time|cvv|secret", RegexOption.IGNORE_CASE).containsMatchIn(words)
    }

    /** Paste at the cursor (keeps undo). The text stays on the clipboard too, in case an app ignores the paste. */
    fun paste(c: Context, text: String): Boolean {
        val t = target ?: return false
        target = null
        if (!t.refresh() || !t.isFocused || !t.isEditable || sensitive(t)) return false
        c.getSystemService(ClipboardManager::class.java).setPrimaryClip(ClipData.newPlainText("indite", text))
        return t.performAction(AccessibilityNodeInfo.ACTION_PASTE)
    }
}

class PasteService : AccessibilityService() {
    override fun onServiceConnected() { instance = this }
    override fun onUnbind(intent: android.content.Intent?): Boolean { instance = null; return super.onUnbind(intent) }
    override fun onDestroy() { instance = null; super.onDestroy() }
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}  // no events subscribed
    override fun onInterrupt() {}

    companion object { @Volatile var instance: PasteService? = null }
}
