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
    private lateinit var spinner: android.widget.ProgressBar
    private var startedAt = 0L
    /** What the keyboard is doing, shown the same way as the floating mic: listening / writing / typed in. */
    private enum class State { IDLE, LISTENING, WRITING, DONE }

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

        // Keys: soft pills that sink a little when pressed (spring back on release), with a light tick.
        // Words for the two keys people read ("ABC", "space"), drawn icons for the two they recognise by shape.
        fun keyPill(child: View, desc: String, weight: Float, onClick: () -> Unit) = FrameLayout(c).apply {
            contentDescription = desc
            background = GradientDrawable().apply { cornerRadius = dp(22).toFloat(); setColor(key) }
            elevation = dp(1).toFloat()
            addView(child)
            layoutParams = LinearLayout.LayoutParams(0, dp(46), weight).apply { setMargins(dp(4), 0, dp(4), 0) }
            setOnTouchListener { v, e ->
                when (e.actionMasked) {
                    android.view.MotionEvent.ACTION_DOWN -> v.animate().scaleX(0.92f).scaleY(0.92f).setDuration(70).start()
                    android.view.MotionEvent.ACTION_UP, android.view.MotionEvent.ACTION_CANCEL ->
                        v.animate().scaleX(1f).scaleY(1f).setDuration(220).setInterpolator(android.view.animation.OvershootInterpolator(3f)).start()
                }
                false
            }
            setOnClickListener { performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP); onClick() }
        }
        fun word(t: String) = TextView(c).apply {
            text = t
            gravity = Gravity.CENTER
            setTextColor(ink)
            textSize = 15f
            typeface = bold(font)   // real weight 700, not a faked bold
            letterSpacing = 0.02f
            layoutParams = FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT)
        }
        fun glyph(res: Int) = ImageView(c).apply {
            setImageResource(res)
            setColorFilter(ink)
            layoutParams = FrameLayout.LayoutParams(dp(22), dp(22), Gravity.CENTER)
        }

        // Status pill at the top: a coloured dot + what's happening.
        dot = View(c).apply {
            background = GradientDrawable().apply { shape = GradientDrawable.OVAL; setColor(getColor(R.color.kb_accent)) }
            layoutParams = LinearLayout.LayoutParams(dp(8), dp(8)).apply { setMargins(0, 0, dp(8), 0) }
        }
        status = TextView(c).apply {
            setTextColor(ink)
            textSize = 13f
            typeface = font
            text = READY
        }
        val pill = LinearLayout(c).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            background = GradientDrawable().apply { cornerRadius = dp(16).toFloat(); setColor(key) }
            setPadding(dp(14), dp(7), dp(16), dp(7))
            addView(dot); addView(status)
            layoutParams = LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT)
                .apply { gravity = Gravity.CENTER_HORIZONTAL }
        }

        // Live voice bars under the pill (move with your voice while listening).
        bars = LevelBars(c, getColor(R.color.kb_record)).apply {
            layoutParams = LinearLayout.LayoutParams(dp(120), dp(22)).apply { gravity = Gravity.CENTER_HORIZONTAL; setMargins(0, dp(8), 0, 0) }
            alpha = 0f
        }

        // The mic orb: a gradient circle with a soft halo that swells with your voice.
        micIcon = ImageView(c).apply {
            setImageResource(R.drawable.ic_mic)
            setColorFilter(getColor(R.color.kb_on_accent))
            layoutParams = FrameLayout.LayoutParams(dp(32), dp(32), Gravity.CENTER)
        }
        spinner = android.widget.ProgressBar(c).apply {
            isIndeterminate = true
            indeterminateTintList = android.content.res.ColorStateList.valueOf(getColor(R.color.kb_on_accent))
            layoutParams = FrameLayout.LayoutParams(dp(74), dp(74), Gravity.CENTER)
            visibility = View.GONE
        }
        halo = View(c).apply {
            background = GradientDrawable().apply { shape = GradientDrawable.OVAL; setColor(getColor(R.color.kb_record)) }
            alpha = 0f
            layoutParams = FrameLayout.LayoutParams(dp(80), dp(80), Gravity.CENTER)
        }
        mic = FrameLayout(c).apply {
            contentDescription = "Start dictation"
            background = orb(getColor(R.color.kb_accent))
            elevation = dp(6).toFloat()
            addView(micIcon)
            addView(spinner)
            layoutParams = FrameLayout.LayoutParams(dp(80), dp(80), Gravity.CENTER)
            setOnClickListener {
                performHapticFeedback(HapticFeedbackConstants.LONG_PRESS)
                animate().scaleX(0.9f).scaleY(0.9f).setDuration(80).withEndAction {
                    animate().scaleX(1f).scaleY(1f).setDuration(260).setInterpolator(android.view.animation.OvershootInterpolator(2.5f)).start()
                }.start()
                toggle()
            }
        }
        val stage = FrameLayout(c).apply {
            addView(halo); addView(mic)
            layoutParams = LinearLayout.LayoutParams(dp(104), dp(104)).apply { gravity = Gravity.CENTER_HORIZONTAL; setMargins(0, dp(2), 0, dp(6)) }
        }
        val keys = LinearLayout(c).apply {
            orientation = LinearLayout.HORIZONTAL
            addView(keyPill(word("ABC"), "Switch to your other keyboard", 1.2f) { switchBack() })
            addView(keyPill(word("space"), "Space", 3f) { currentInputConnection?.commitText(" ", 1) })
            addView(keyPill(glyph(R.drawable.ic_backspace), "Delete", 1.2f) { sendDownUpKeyEvents(KeyEvent.KEYCODE_DEL) })
            enterKey = word(actionWord())
            addView(keyPill(enterKey, "Enter", 1.4f) { enter() })
        }
        // Gentle top-to-bottom gradient with rounded top corners.
        return LinearLayout(c).apply {
            orientation = LinearLayout.VERTICAL
            background = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(bg, androidx.core.graphics.ColorUtils.blendARGB(bg, ink, 0.06f)))
                .apply { cornerRadii = floatArrayOf(dp(24).toFloat(), dp(24).toFloat(), dp(24).toFloat(), dp(24).toFloat(), 0f, 0f, 0f, 0f) }
            setPadding(dp(10), dp(14), dp(10), dp(12))
            addView(pill)
            addView(bars)
            addView(stage)
            addView(keys)
        }
    }

    private fun orb(color: Int) = GradientDrawable(GradientDrawable.Orientation.TL_BR,
        intArrayOf(androidx.core.graphics.ColorUtils.blendARGB(color, android.graphics.Color.WHITE, 0.18f), color,
            androidx.core.graphics.ColorUtils.blendARGB(color, android.graphics.Color.BLACK, 0.18f))).apply { shape = GradientDrawable.OVAL }

    private lateinit var dot: View
    private lateinit var halo: View
    private lateinit var bars: LevelBars

    /** Five rounded bars that follow the microphone level. */
    private class LevelBars(c: android.content.Context, private val color: Int) : View(c) {
        private val levels = FloatArray(5)
        private val paint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply { this.color = color }
        fun push(v: Float) { System.arraycopy(levels, 1, levels, 0, levels.size - 1); levels[levels.size - 1] = v.coerceIn(0f, 1f); invalidate() }
        override fun onDraw(canvas: android.graphics.Canvas) {
            val n = levels.size; val gap = width / (n * 3f); val w = gap * 2
            for (k in 0 until n) {
                val h = height * (0.2f + 0.8f * levels[(k * 2 + 1) % n])
                val x = k * (w + gap) + gap / 2
                canvas.drawRoundRect(x, (height - h) / 2, x + w, (height + h) / 2, w / 2, w / 2, paint)
            }
        }
    }

    /** Opening the keyboard always starts from "tap the mic", unless a dictation is actually still running. */
    override fun onStartInputView(info: EditorInfo?, restarting: Boolean) {
        super.onStartInputView(info, restarting)
        if (job?.isActive != true && Recording.id != noteId) state(State.IDLE, READY)
        if (::enterKey.isInitialized) enterKey.text = actionWord()
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
        if (noteId != null && Recording.id == noteId) { Recording.stop(); state(State.WRITING, "Writing the last part…"); return }
        if (sensitive(currentInputEditorInfo)) { state(State.IDLE, "Not for password or code boxes. Type it with your keyboard (ABC)."); return }
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
        startedAt = System.currentTimeMillis()
        state(State.LISTENING, "Listening… pause to type it in")
        job = scope.launch { typeAsYouGo(id) }
        scope.launch {  // a running clock, so it's obvious the mic is on
            while (Recording.id == id) {
                if (current == State.LISTENING) {
                    status.text = "Listening ${clock()} · pause to type it in"
                    val lv = Notes.level.value
                    bars.push(lv)
                    halo.alpha = 0.18f + 0.3f * lv
                    val sc = 1f + 0.35f * lv
                    halo.animate().scaleX(sc).scaleY(sc).setDuration(110).start()
                }
                delay(110)
            }
        }
    }

    /** Transcribe each part as soon as the recorder cuts it, and type it into the text box. */
    private suspend fun typeAsYouGo(id: String) {
        try {
            val w = Engine.get(this)  // first use loads the model (a second or two)
            var next = 0
            while (true) {
                val note = Notes.note(id) ?: break
                if (next < note.cuts.size) {
                    if (Recording.id == id) spinner.visibility = View.VISIBLE  // still listening, and writing the last part
                    else state(State.WRITING, "Writing your text…")
                    val piece = withContext(Dispatchers.Default) { NoteService.transcribePiece(w, note, next) } ?: break
                    next++
                    val here = currentInputEditorInfo?.let { "${it.packageName}:${it.fieldId}" }
                    val typed = !piece.junk && here == field
                    if (typed) currentInputConnection?.commitText(Settings.applyFixes(piece.text).trim() + " ", 1)
                    if (Recording.id == id) { spinner.visibility = View.GONE; state(State.LISTENING, "✓ Typed in · still listening") }
                } else if (Recording.id == id) {
                    delay(150)
                } else if (Notes.note(id)?.pending != true) break
            }
        } catch (e: Exception) {
            Log.w("indite", e)
            state(State.IDLE, "Couldn't type that in. It's saved in the indite app.")
            return
        } finally {
            Notes.claimed -= id
            if (noteId == id) noteId = null
            Notes.refresh()
        }
        state(State.DONE, "✓ Done · all typed in")
        delay(2500)
        // `job` IS this coroutine, so the old check (job?.isActive != true) was never true: the keyboard stayed on
        // "Done" with the tick for ever, and every later open still showed it.
        if (current == State.DONE) state(State.IDLE, READY)
    }

    private lateinit var enterKey: TextView

    /** Figtree is a variable font: Typeface.BOLD only slants/thickens it. Ask for weight 700 where Android allows. */
    private fun bold(font: android.graphics.Typeface?) =
        if (Build.VERSION.SDK_INT >= 28) Typeface.create(font, 700, false) else Typeface.create(font, Typeface.BOLD)

    /** What the Enter key will actually do in this text box, in a word. */
    private fun actionWord(): String = when (currentInputEditorInfo?.imeOptions?.and(EditorInfo.IME_MASK_ACTION)) {
        EditorInfo.IME_ACTION_SEND -> "send"
        EditorInfo.IME_ACTION_SEARCH -> "search"
        EditorInfo.IME_ACTION_GO -> "go"
        EditorInfo.IME_ACTION_NEXT -> "next"
        EditorInfo.IME_ACTION_DONE -> "done"
        else -> "enter"
    }

    private var current = State.IDLE
    private val READY = "Tap the mic and speak · Hindi, English or both"

    private fun clock(): String { val s = (System.currentTimeMillis() - startedAt) / 1000; return "%d:%02d".format(s / 60, s % 60) }

    /** Colour, icon and words follow the state: amber = ready, red = listening, grey + spinner = writing, green = typed in. */
    private fun state(st: State, text: String) {
        current = st
        if (!::status.isInitialized) return
        status.text = text
        val col = getColor(when (st) {
            State.LISTENING -> R.color.kb_record; State.WRITING -> R.color.kb_soft; State.DONE -> R.color.kb_ready; State.IDLE -> R.color.kb_accent
        })
        mic.background = orb(col)
        (dot.background as GradientDrawable).setColor(col)
        bars.animate().alpha(if (st == State.LISTENING) 1f else 0f).setDuration(200).start()
        if (st != State.LISTENING) halo.animate().alpha(0f).setDuration(200).start()
        if (st == State.DONE) {  // a little "done" pop; a tick, never the copy icon (nothing is copied here)
            micIcon.setImageResource(R.drawable.ic_check)
            mic.scaleX = 0.8f; mic.scaleY = 0.8f
            mic.animate().scaleX(1f).scaleY(1f).setDuration(380).setInterpolator(android.view.animation.OvershootInterpolator(3f)).start()
        }
        if (st != State.DONE) micIcon.setImageResource(if (st == State.LISTENING) R.drawable.ic_stop else R.drawable.ic_mic)
        spinner.visibility = if (st == State.WRITING) View.VISIBLE else View.GONE
        mic.contentDescription = when (st) {
            State.LISTENING -> "Stop dictation"; State.WRITING -> "Writing your text"; else -> "Start dictation"
        }
    }

    private fun show(text: String, listening: Boolean) = state(if (listening) State.LISTENING else State.IDLE, text)

    /** Password, PIN and one-time-code boxes: never dictated into. */
    private fun sensitive(ei: EditorInfo?): Boolean {
        ei ?: return false
        return com.whispercppdemo.notes.Secret.inputType(ei.inputType) || com.whispercppdemo.notes.Secret.words(ei.hintText, ei.fieldName)
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
