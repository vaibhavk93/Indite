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

    override fun onDestroy() {
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
        val view = FrameLayout(this).apply {
            background = circle
            elevation = dp(6).toFloat()
            contentDescription = "indite: tap to dictate"
            addView(icon)
        }
        val lp = WindowManager.LayoutParams(
            dp(56), dp(56), WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT,
        ).apply { gravity = Gravity.TOP or Gravity.START; x = 0; y = dp(240) }

        // Drag anywhere; a short touch without movement is a tap. On release it snaps to the nearest side.
        var downX = 0f; var downY = 0f; var startX = 0; var startY = 0; var moved = false
        view.setOnTouchListener { v, e ->
            when (e.action) {
                MotionEvent.ACTION_DOWN -> { downX = e.rawX; downY = e.rawY; startX = lp.x; startY = lp.y; moved = false; true }
                MotionEvent.ACTION_MOVE -> {
                    if (abs(e.rawX - downX) + abs(e.rawY - downY) > dp(8)) moved = true
                    if (moved) { lp.x = startX + (e.rawX - downX).toInt(); lp.y = startY + (e.rawY - downY).toInt(); wm.updateViewLayout(v, lp) }
                    true
                }
                MotionEvent.ACTION_UP -> {
                    if (moved) {
                        val w = resources.displayMetrics.widthPixels
                        lp.x = if (lp.x + dp(28) < w / 2) 0 else w - dp(56)
                        wm.updateViewLayout(v, lp)
                    } else { v.performHapticFeedback(HapticFeedbackConstants.LONG_PRESS); tap() }
                    true
                }
                else -> false
            }
        }
        wm.addView(view, lp)
        bubble = view

        // Colour follows the state: amber = ready, red = recording, grey = writing the last part.
        scope.launch {
            var last = -1
            while (true) {
                val recording = Recording.active
                val state = when { recording -> 2; pending.isNotEmpty() -> 1; else -> 0 }
                if (state != last) {  // only touch the view when something changed
                    circle.setColor(getColor(when (state) { 2 -> R.color.kb_record; 1 -> R.color.kb_soft; else -> R.color.kb_accent }))
                    icon.setImageResource(if (recording) R.drawable.ic_stop else R.drawable.ic_mic)
                    view.contentDescription = if (recording) "indite: tap to stop" else "indite: tap to dictate"
                    last = state
                }
                delay(250)
            }
        }
    }

    private fun tap() {
        if (Recording.active) { NoteService.stopRecording(this); return }
        startActivity(Intent(this, StartMicActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_NO_ANIMATION))
    }

    private fun notification(): Notification {
        getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel(CHANNEL, "Floating mic", NotificationManager.IMPORTANCE_MIN))
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
        private const val CHANNEL = "bubble"
        private const val NOTE_ID = 7
        private const val ACTION_OFF = "off"

        /** Bubble dictations still being written; each one's text is copied when done (a second tap never loses the first). */
        val pending: MutableSet<String> = java.util.concurrent.ConcurrentHashMap.newKeySet()

        fun enabled(c: Context) = c.getSharedPreferences("settings", Context.MODE_PRIVATE).getBoolean("bubble", false)

        fun setEnabled(c: Context, on: Boolean) {
            c.getSharedPreferences("settings", Context.MODE_PRIVATE).edit().putBoolean("bubble", on).apply()
            if (on && AndroidSettings.canDrawOverlays(c)) c.startForegroundService(Intent(c, BubbleService::class.java))
            else if (!on) c.stopService(Intent(c, BubbleService::class.java))
        }
    }
}

/** Invisible, opens for a moment so Android lets indite start the microphone, then closes. */
class StartMicActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            startActivity(Intent(this, MainActivity::class.java))  // asks for the mic there
        } else {
            Notes.init(this)
            val stamp = java.text.SimpleDateFormat("EEE d MMM, h:mm a", java.util.Locale.getDefault()).format(java.util.Date())
            BubbleService.pending += NoteService.startRecording(this, name = "Dictation, $stamp")
        }
        finish()
        overridePendingTransition(0, 0)
    }
}
