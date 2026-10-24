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
        return com.whispercppdemo.notes.Secret.inputType(n.inputType) ||
            com.whispercppdemo.notes.Secret.words(n.hintText, n.viewIdResourceName?.substringAfter(":id/"), n.contentDescription, n.paneTitle)
    }

    /**
     * Paste at the cursor (keeps undo). The text stays on the clipboard too, in case an app ignores the paste.
     * Returns true if ACTION_PASTE was accepted. On false, the reason is in the log ("auto-paste fallback: <A-E>")
     * so we can tell apart "no box was focused when you tapped" from "the app refused the paste".
     */
    fun paste(c: Context, text: String): Boolean {
        val t = target
        target = null
        if (t == null) { log("A", "no focused editable box when bubble was tapped"); return false }
        if (!t.refresh()) { log("B", "target node could not be refreshed (view rebuilt)"); return false }
        if (!t.isFocused) { log("C", "focus moved away during the recording"); return false }
        if (!t.isEditable) { log("D1", "target is no longer editable"); return false }
        if (sensitive(t)) { log("D2", "target now looks sensitive (password / code box)"); return false }
        c.getSystemService(ClipboardManager::class.java).setPrimaryClip(ClipData.newPlainText("Inditeflow", text))
        if (!t.performAction(AccessibilityNodeInfo.ACTION_PASTE)) { log("E", "app refused ACTION_PASTE"); return false }
        return true
    }

    private fun log(code: String, why: String) =
        android.util.Log.i("inditeflow", "auto-paste fallback: $code — $why")
}

class PasteService : AccessibilityService() {
    // The accessibility shortcut (volume keys / button) turns this service on and off. The founder wants that to be the
    // floating mic's on/off switch, so the bubble follows the service. (Starting it from here may be blocked on some
    // Android versions; then it fails quietly and the Settings switch or the quick tile still work.)
    override fun onServiceConnected() {
        instance = this
        if (android.provider.Settings.canDrawOverlays(this))
            runCatching { BubbleService.setEnabled(this, true) }.onFailure { android.util.Log.w("inditeflow", "bubble from shortcut", it) }
    }
    override fun onUnbind(intent: android.content.Intent?): Boolean {
        instance = null
        runCatching { BubbleService.setEnabled(this, false) }
        return super.onUnbind(intent)
    }
    override fun onDestroy() { instance = null; super.onDestroy() }
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}  // no events subscribed
    override fun onInterrupt() {}

    companion object { @Volatile var instance: PasteService? = null }
}
