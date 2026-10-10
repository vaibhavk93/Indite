package com.whispercppdemo.overlay

import android.app.Activity
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.graphics.PixelFormat
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.os.Bundle
import android.os.IBinder
import android.provider.Settings as AndroidSettings
import android.util.TypedValue
import android.view.Gravity
import android.view.HapticFeedbackConstants
import android.view.MotionEvent
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.ImageView
import com.whispercppdemo.MainActivity
import com.whispercppdemo.R
import com.whispercppdemo.notes.NoteService
import com.whispercppdemo.notes.Notes
import com.whispercppdemo.notes.Recording
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlin.math.abs

/**
 * Floating mic button over every app (like Wispr Flow's bubble), without the accessibility service.
 * Tap: a tiny invisible screen starts the recording (Android only lets an app use the mic from a visible screen).
 * Tap again: stop. When the text is ready it's copied, ready to paste (and saved as a note).
 * The idle bubble never holds the mic; it only keeps a quiet "Floating mic is on" notification.
 */
class BubbleService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private var bubble: FrameLayout? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_OFF) { setEnabled(this, false); stopSelf(); return START_NOT_STICKY }
        if (!AndroidSettings.canDrawOverlays(this)) { stopSelf(); return START_NOT_STICKY }
        val n = notification()
        if (Build.VERSION.SDK_INT >= 34) startForeground(NOTE_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        else startForeground(NOTE_ID, n)
        if (bubble == null) show()
        return START_STICKY
    }

    /** A round "X" at the bottom while dragging: drop the bubble on it to turn the floating mic off. */
    private var dropZone: android.widget.TextView? = null
    private fun showDropZone(over: Boolean) {
        val wm = getSystemService(WindowManager::class.java)
        val z = dropZone ?: android.widget.TextView(this).apply {
            text = "✕"; textSize = 22f; gravity = Gravity.CENTER
            setTextColor(getColor(R.color.kb_on_accent))
            background = GradientDrawable().apply { shape = GradientDrawable.OVAL; setColor(getColor(R.color.kb_soft)) }
            wm.addView(this, WindowManager.LayoutParams(dp(64), dp(64), WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE, PixelFormat.TRANSLUCENT)
                .apply { gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL; y = dp(48) })
            dropZone = this
        }
        (z.background as GradientDrawable).setColor(getColor(if (over) R.color.kb_record else R.color.kb_soft))
        z.scaleX = if (over) 1.2f else 1f; z.scaleY = z.scaleX
    }
    private fun hideDropZone() {
        dropZone?.let { getSystemService(WindowManager::class.java).removeView(it) }
        dropZone = null
    }

    override fun onDestroy() {
        hideDropZone()
        bubble?.let { getSystemService(WindowManager::class.java).removeView(it) }
        bubble = null
        scope.cancel()
        super.onDestroy()
    }

    private fun dp(v: Int) = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v.toFloat(), resources.displayMetrics).toInt()

    private fun show() {
        val wm = getSystemService(WindowManager::class.java)
        val icon = ImageView(this).apply {
            setImageResource(R.drawable.ic_mic)
            setColorFilter(getColor(R.color.kb_on_accent))
            layoutParams = FrameLayout.LayoutParams(dp(26), dp(26), Gravity.CENTER)
        }
        val circle = GradientDrawable().apply { shape = GradientDrawable.OVAL; setColor(getColor(R.color.kb_accent)) }
        // Spinning ring while the text is being written, so it's clear indite is still working.
        val spinner = android.widget.ProgressBar(this).apply {
            isIndeterminate = true
            indeterminateTintList = android.content.res.ColorStateList.valueOf(getColor(R.color.kb_on_accent))
            layoutParams = FrameLayout.LayoutParams(dp(50), dp(50), Gravity.CENTER)
            visibility = android.view.View.GONE
        }
        val view = FrameLayout(this).apply {
            background = circle
            elevation = dp(6).toFloat()
            contentDescription = "indite: tap to dictate"
            addView(icon)
            addView(spinner)
        }
        val lp = WindowManager.LayoutParams(
            dp(56), dp(56), WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT,
        ).apply { gravity = Gravity.TOP or Gravity.START; x = 0; y = dp(240) }

        // Drag anywhere; a short touch without movement is a tap. On release it snaps to the nearest side.
        var downX = 0f; var downY = 0f; var startX = 0; var startY = 0; var moved = false; var downAt = 0L
        view.setOnTouchListener { v, e ->
            lastTouch = System.currentTimeMillis()
            v.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(120).start()
            when (e.action) {
                MotionEvent.ACTION_DOWN -> {
                    downX = e.rawX; downY = e.rawY; startX = lp.x; startY = lp.y; moved = false; downAt = lastTouch; heldToCancel = false
                    // hold while recording = cancel, as soon as 0.4 s have passed (no need to lift the finger)
                    if (Recording.active) v.postDelayed({
                        if (!moved && downAt != 0L && Recording.active) {
                            heldToCancel = true; v.performHapticFeedback(HapticFeedbackConstants.LONG_PRESS); cancel()
                        }
                    }, 400)
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    if (abs(e.rawX - downX) + abs(e.rawY - downY) > dp(8)) moved = true
                    if (moved) {
                        lp.x = startX + (e.rawX - downX).toInt(); lp.y = startY + (e.rawY - downY).toInt(); wm.updateViewLayout(v, lp)
                        showDropZone(e.rawY > resources.displayMetrics.heightPixels - dp(120))
                    }
                    true
                }
                MotionEvent.ACTION_UP -> {
                    if (moved && e.rawY > resources.displayMetrics.heightPixels - dp(120)) {
                        // dropped on the X: the floating mic turns off (one switch, as the founder asked)
                        hideDropZone()
                        toast("Floating mic off. Turn it on from the quick settings tile or indite → Settings.")
                        setEnabled(this, false)
                    } else if (moved) {
                        hideDropZone()
                        val w = resources.displayMetrics.widthPixels
                        lp.x = if (lp.x + dp(28) < w / 2) 0 else w - dp(56)
                        wm.updateViewLayout(v, lp)
                    } else if (!heldToCancel) { v.performHapticFeedback(HapticFeedbackConstants.LONG_PRESS); tap() }
                    downAt = 0L
                    true
                }
                else -> false
            }
        }
        wm.addView(view, lp)
        bubble = view

        // Colour follows the state: amber = ready to listen, red = recording, grey = writing, green = text ready to copy.
        scope.launch {
            var last = -1
            while (true) {
                val recording = Recording.active
                val state = when { recording -> 2; pending.any { it !in cancelled } -> 1; readyText != null -> 3; else -> 0 }
                if (state != last) {  // only touch the view when something changed
                    circle.setColor(getColor(when (state) { 2 -> R.color.kb_record; 1 -> R.color.kb_soft; 3 -> R.color.kb_ready; else -> R.color.kb_accent }))
                    icon.setImageResource(when (state) { 2 -> R.drawable.ic_stop; 3 -> R.drawable.ic_copy; else -> R.drawable.ic_mic })
                    spinner.visibility = if (state == 1) android.view.View.VISIBLE else android.view.View.GONE
                    view.contentDescription = when (state) {
                        2 -> "indite: tap to stop, hold to cancel"; 1 -> "indite: writing your text"; 3 -> "indite: tap to copy the text"
                        else -> "indite: tap to dictate"
                    }
                    last = state
                    lastTouch = System.currentTimeMillis()
                }
                // idle for 5 s: shrink and fade so it covers less of the app underneath
                if (state == 0 && System.currentTimeMillis() - lastTouch > 5000 && view.scaleX == 1f)
                    view.animate().scaleX(0.6f).scaleY(0.6f).alpha(0.5f).setDuration(200).start()
                delay(250)
            }
        }
    }

    private var lastTouch = System.currentTimeMillis()
    private var heldToCancel = false

    private fun toast(msg: String) = android.widget.Toast.makeText(this, msg, android.widget.Toast.LENGTH_SHORT).show()

    private fun tap() {
        if (Recording.active) { NoteService.stopRecording(this); toast("Writing your text…"); return }
        readyText?.let { text ->
            getSystemService(android.content.ClipboardManager::class.java).setPrimaryClip(android.content.ClipData.newPlainText("indite", text))
            readyText = null
            if (Build.VERSION.SDK_INT < 33) toast("Copied. Long-press a text box to paste.")  // Android 13+ shows its own
            return
        }
        if (AutoPaste.sensitiveFocus()) { toast("Not for password or code boxes. Type it with your keyboard."); return }
        AutoPaste.capture()  // the box you're typing in, if "Type into the box for me" is on
        startActivity(Intent(this, StartMicActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_NO_ANIMATION))
    }

    /** Hold while recording: throw this dictation away (the note is deleted once the recorder has stopped). */
    private fun cancel() {
        Recording.id?.let { cancelled += it }
        AutoPaste.forget()
        NoteService.stopRecording(this)
        toast("Cancelled")
    }

    private fun notification(): Notification {
        // LOW (not MIN): the notification must be easy to find, because it's how a hidden bubble comes back
        getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel(CHANNEL, "Floating mic", NotificationManager.IMPORTANCE_LOW))
        val off = PendingIntent.getService(this, 2, Intent(this, BubbleService::class.java).setAction(ACTION_OFF), PendingIntent.FLAG_IMMUTABLE)
        val open = PendingIntent.getActivity(this, 3, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
        return Notification.Builder(this, CHANNEL)
            .setSmallIcon(R.drawable.ic_mic)
            .setContentTitle("Floating mic is on")
            .setContentText("Tap the bubble in any app to dictate.")
            .setContentIntent(open)
            .addAction(Notification.Action.Builder(null, "Turn off", off).build())
            .setOngoing(true)
            .build()
    }

    companion object {
        private const val CHANNEL = "bubble_low"  // new id: an existing channel's importance can't be raised
        private const val NOTE_ID = 7
        private const val ACTION_OFF = "off"

        /** Bubble dictations still being written; each one's text is copied when done (a second tap never loses the first). */
        val pending: MutableSet<String> = java.util.concurrent.ConcurrentHashMap.newKeySet()
        /** Dictations the user cancelled (hold while recording); deleted, never copied. */
        val cancelled: MutableSet<String> = java.util.concurrent.ConcurrentHashMap.newKeySet()
        /** The last dictation's text, waiting for a tap on the green copy button. */
        @Volatile var readyText: String? = null

        fun autoCopy(c: Context) = c.getSharedPreferences("settings", Context.MODE_PRIVATE).getBoolean("bubbleAutoCopy", false)
        fun setAutoCopy(c: Context, on: Boolean) = c.getSharedPreferences("settings", Context.MODE_PRIVATE).edit().putBoolean("bubbleAutoCopy", on).apply()

        fun enabled(c: Context) = c.getSharedPreferences("settings", Context.MODE_PRIVATE).getBoolean("bubble", false)

        fun setEnabled(c: Context, on: Boolean) {
            c.getSharedPreferences("settings", Context.MODE_PRIVATE).edit().putBoolean("bubble", on).apply()
            if (Build.VERSION.SDK_INT >= 24) android.service.quicksettings.TileService.requestListeningState(c,
                android.content.ComponentName(c, MicTile::class.java))  // keep the quick settings tile in step
            if (on && AndroidSettings.canDrawOverlays(c)) c.startForegroundService(Intent(c, BubbleService::class.java))
            else if (!on) c.stopService(Intent(c, BubbleService::class.java))
        }
    }
}

/**
 * Invisible, opens for a moment so Android lets indite start the microphone, then closes.
 * It must stay open until the mic is really capturing: Android feeds silence to a mic opened after the app's
 * screen is gone (phone test 2026-10-10: every bubble dictation came out "No speech found").
 */
class StartMicActivity : Activity() {
    private val handler = android.os.Handler(android.os.Looper.getMainLooper())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            startActivity(Intent(this, MainActivity::class.java))  // asks for the mic there
        } else {
            Notes.init(this)
            val stamp = java.text.SimpleDateFormat("EEE d MMM, h:mm a", java.util.Locale.getDefault()).format(java.util.Date())
            val id = NoteService.startRecording(this, name = "Dictation, $stamp")
            BubbleService.pending += id
            val until = System.currentTimeMillis() + 3000
            fun check() {
                if (Recording.listening(id) || System.currentTimeMillis() > until) close() else handler.postDelayed(::check, 50)
            }
            check()
            return
        }
        close()
    }

    private fun close() {
        finish()
        overridePendingTransition(0, 0)
    }
}

/**
 * Quick settings tile "indite mic": turns the floating mic on and off from the pull-down panel, in any app.
 * Turning on goes through a brief invisible screen, because Android only lets a visible app start it.
 */
class MicTile : android.service.quicksettings.TileService() {
    override fun onStartListening() {
        qsTile?.apply {
            state = if (BubbleService.enabled(this@MicTile)) android.service.quicksettings.Tile.STATE_ACTIVE
                else android.service.quicksettings.Tile.STATE_INACTIVE
            updateTile()
        }
    }

    override fun onClick() {
        if (BubbleService.enabled(this)) { BubbleService.setEnabled(this, false); onStartListening(); return }
        val i = Intent(this, MicOnActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        if (Build.VERSION.SDK_INT >= 34)
            startActivityAndCollapse(PendingIntent.getActivity(this, 5, i, PendingIntent.FLAG_IMMUTABLE))
        else @Suppress("DEPRECATION") startActivityAndCollapse(i)
    }
}

/** Invisible: turns the floating mic on (or opens the permission screen first), then closes. */
class MicOnActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (AndroidSettings.canDrawOverlays(this)) BubbleService.setEnabled(this, true)
        else startActivity(Intent(AndroidSettings.ACTION_MANAGE_OVERLAY_PERMISSION, android.net.Uri.parse("package:$packageName")))
        finish()
        overridePendingTransition(0, 0)
    }
}
