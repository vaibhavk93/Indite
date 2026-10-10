package com.whispercppdemo.keyboard

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.inputmethodservice.InputMethodService
import android.os.Build
import android.util.Log
import android.util.TypedValue
import android.view.Gravity
import android.view.HapticFeedbackConstants
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.content.res.ResourcesCompat
import com.whispercppdemo.MainActivity
import com.whispercppdemo.R
import com.whispercppdemo.notes.Engine
import com.whispercppdemo.notes.NoteService
import com.whispercppdemo.notes.Notes
import com.whispercppdemo.notes.PhoneCheck
import com.whispercppdemo.notes.Recording
import com.whispercppdemo.notes.Settings
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * indite voice keyboard: dictate into any app. Tap the mic, talk; after each pause that part is typed into the text
 * box you're in. Each dictation is also kept as a note in the app, with its audio (as the founder asked).
 * Everything runs on the phone.
 */
class VoiceKeyboard : InputMethodService() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private var job: Job? = null
    private var noteId: String? = null
    /** The text box the dictation started in; text is only typed there (never into a box you moved to). */
    private var field: String? = null
    private lateinit var status: TextView
    private lateinit var mic: FrameLayout
    private lateinit var micIcon: ImageView

    override fun onCreate() {
        super.onCreate()
        Settings.init(this)
        Notes.init(this)
    }

    override fun onCreateInputView(): View {
        val c = this
        fun dp(v: Int) = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v.toFloat(), resources.displayMetrics).toInt()
        val font = ResourcesCompat.getFont(c, R.font.figtree)
        val bg = getColor(R.color.kb_bg)
        val key = getColor(R.color.kb_key)
        val ink = getColor(R.color.kb_ink)
        val soft = getColor(R.color.kb_soft)

        fun keyButton(label: String, desc: String, weight: Float, onClick: () -> Unit) = TextView(c).apply {
            text = label
            contentDescription = desc
            gravity = Gravity.CENTER
            setTextColor(ink)
            textSize = 16f
            typeface = Typeface.create(font, Typeface.BOLD)
            background = GradientDrawable().apply { cornerRadius = dp(12).toFloat(); setColor(key) }
            layoutParams = LinearLayout.LayoutParams(0, dp(48), weight).apply { setMargins(dp(4), 0, dp(4), 0) }
            setOnClickListener { performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP); onClick() }
        }

        status = TextView(c).apply {
            gravity = Gravity.CENTER
            setTextColor(soft)
            textSize = 14f
            typeface = font
            text = "Tap the mic and speak · Hindi, English or both"
        }
        micIcon = ImageView(c).apply {
            setImageResource(R.drawable.ic_mic)
            setColorFilter(getColor(R.color.kb_on_accent))
            layoutParams = FrameLayout.LayoutParams(dp(30), dp(30), Gravity.CENTER)
        }
        mic = FrameLayout(c).apply {
            contentDescription = "Start dictation"
            background = GradientDrawable().apply { shape = GradientDrawable.OVAL; setColor(getColor(R.color.kb_accent)) }
            addView(micIcon)
            layoutParams = LinearLayout.LayoutParams(dp(72), dp(72)).apply { gravity = Gravity.CENTER_HORIZONTAL; setMargins(0, dp(12), 0, dp(14)) }
            setOnClickListener { performHapticFeedback(HapticFeedbackConstants.LONG_PRESS); toggle() }
        }
        val keys = LinearLayout(c).apply {
            orientation = LinearLayout.HORIZONTAL
            addView(keyButton("ABC", "Switch to your other keyboard", 1.2f) { switchBack() })
            addView(keyButton("space", "Space", 3f) { currentInputConnection?.commitText(" ", 1) })
            addView(keyButton("⌫", "Delete", 1.2f) { sendDownUpKeyEvents(KeyEvent.KEYCODE_DEL) })
            addView(keyButton("↵", "Enter", 1.2f) { enter() })
        }
        return LinearLayout(c).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(bg)
            setPadding(dp(8), dp(14), dp(8), dp(12))
            addView(status)
            addView(mic)
            addView(keys)
        }
    }

    override fun onFinishInputView(finishingInput: Boolean) {
        super.onFinishInputView(finishingInput)
        if (Recording.id == noteId) Recording.stop()  // keyboard closed: stop listening; the rest still gets written
    }

    override fun onDestroy() {
        if (Recording.id == noteId) Recording.stop()
        scope.cancel()
        super.onDestroy()
    }

    private fun toggle() {
        if (noteId != null && Recording.id == noteId) { Recording.stop(); show("Writing the last part…", listening = false); return }
        if (job?.isActive == true) return  // still writing the previous dictation
        PhoneCheck.problem()?.let { show(it, listening = false); return }
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            show("Open indite once to allow the microphone", listening = false)
            startActivity(Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            return
        }
        if (Recording.active) { show("indite is already recording in the app", listening = false); return }
        val id = Notes.startRecording("Dictation, " + java.text.SimpleDateFormat("EEE d MMM, h:mm a", java.util.Locale.getDefault())
            .format(java.util.Date()))
        noteId = id
        field = currentInputEditorInfo?.let { "${it.packageName}:${it.fieldId}" }
        Notes.claimed += id
        Recording.start(this, id, Engine.vadPath(this))
        show("Listening… pause to type it in", listening = true)
        job = scope.launch { typeAsYouGo(id) }
    }

    /** Transcribe each part as soon as the recorder cuts it, and type it into the text box. */
    private suspend fun typeAsYouGo(id: String) {
        try {
            val w = Engine.get(this)  // first use loads the model (a second or two)
            var next = 0
            while (true) {
                val note = Notes.note(id) ?: break
                if (next < note.cuts.size) {
                    val piece = withContext(Dispatchers.Default) { NoteService.transcribePiece(w, note, next) } ?: break
                    next++
                    val here = currentInputEditorInfo?.let { "${it.packageName}:${it.fieldId}" }
                    if (!piece.junk && here == field) currentInputConnection?.commitText(Settings.applyFixes(piece.text).trim() + " ", 1)
                    if (Recording.id == id) show("Listening… pause to type it in", listening = true)
                } else if (Recording.id == id) {
                    delay(150)
                } else if (Notes.note(id)?.pending != true) break
            }
        } catch (e: Exception) {
            Log.w("indite", e)
            show("Couldn't type that in. It's saved in the indite app.", listening = false)
            return
        } finally {
            Notes.claimed -= id
            if (noteId == id) noteId = null
            Notes.refresh()
        }
        show("Tap the mic and speak · Hindi, English or both", listening = false)
    }

    private fun show(text: String, listening: Boolean) {
        if (!::status.isInitialized) return
        status.text = text
        (mic.background as GradientDrawable).setColor(getColor(if (listening) R.color.kb_record else R.color.kb_accent))
        micIcon.setImageResource(if (listening) R.drawable.ic_stop else R.drawable.ic_mic)
        mic.contentDescription = if (listening) "Stop dictation" else "Start dictation"
    }

    private fun enter() {
        val ei = currentInputEditorInfo
        val action = ei?.imeOptions?.and(EditorInfo.IME_MASK_ACTION) ?: EditorInfo.IME_ACTION_NONE
        if (action != EditorInfo.IME_ACTION_NONE && action != EditorInfo.IME_ACTION_UNSPECIFIED &&
            (ei!!.imeOptions and EditorInfo.IME_FLAG_NO_ENTER_ACTION) == 0) currentInputConnection?.performEditorAction(action)
        else sendDownUpKeyEvents(KeyEvent.KEYCODE_ENTER)
    }

    private fun switchBack() {
        if (Build.VERSION.SDK_INT >= 28 && switchToPreviousInputMethod()) return
        getSystemService(InputMethodManager::class.java).showInputMethodPicker()
    }
}
