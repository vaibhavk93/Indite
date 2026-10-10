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
            it.isEditable && !it.isPassword && !(Build.VERSION.SDK_INT >= 34 && it.isAccessibilityDataSensitive)
        }
    }

    fun forget() { target = null }

    /** Paste at the cursor (keeps undo). The text stays on the clipboard too, in case an app ignores the paste. */
    fun paste(c: Context, text: String): Boolean {
        val t = target ?: return false
        target = null
        if (!t.refresh() || !t.isFocused || !t.isEditable) return false
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
