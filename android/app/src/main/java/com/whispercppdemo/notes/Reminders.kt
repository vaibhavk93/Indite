package com.whispercppdemo.notes

import android.app.AlarmManager
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.media.AudioAttributes
import android.media.AudioManager
import android.net.Uri
import android.os.Build
import com.whispercppdemo.MainActivity
import com.whispercppdemo.R
import kotlinx.coroutines.flow.MutableStateFlow
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/**
 * indite's own reminders (founder decision 2026-10-10: "remind me at 5 pm to buy vegetables").
 * Stored in reminders.json, fired by an exact alarm (an inexact one can be up to an hour late), shown as a notification
 * with Done / Snooze 1 h. Re-scheduled when the app opens, after a reboot and after an update, because a force-stop
 * (some phones do this on swipe-away) clears alarms.
 *
 * **The sound** (10 Oct, after "it is not giving me sound"): a reminder you set for a time is meant to be heard, so
 * "ring like an alarm" is now ON by default. It is the phone that makes the noise, from the channel: alarm volume,
 * alarm stream, and `FLAG_INSISTENT` repeats it until the notification is seen. Nothing here plays audio itself — an
 * earlier version used a foreground service for that, and it could lose a reminder when the service failed or when the
 * app was opened. If a device test ever shows the phone cutting the sound short, that is the time to add a player back.
 *
 * `fired` stops a reminder that was missed (phone off) from announcing itself again every time the app opens.
 */
data class Reminder(val id: Long, val noteId: String?, val text: String, val at: Long, val fired: Boolean = false)

object Reminders {
    val list = MutableStateFlow<List<Reminder>>(emptyList())

    // ⚠ Android freezes a channel's sound when it first creates the channel: setSound() on a channel that already
    // exists does nothing, and deleting a channel does not help either (recreating the same id restores the old
    // settings). So changing the sound means a new id. If it must change again, use _v3.
    private const val CHIME = "reminders_chime_v2"
    private const val ALARM = "reminders_ring_v2"
    private val OLD = listOf("reminders", "reminders_alarm", "reminders_ring")

    /** Settings → Reminders → "Test the sound" uses this; it is never saved to disk. */
    const val TEST_ID = -1L
    fun testReminder() = Reminder(TEST_ID, null, "Test reminder. This is how a reminder will sound.", System.currentTimeMillis())

    private fun file(c: Context) = File(c.filesDir, "reminders.json")
    private fun prefs(c: Context) = c.getSharedPreferences("settings", Context.MODE_PRIVATE)

    fun load(c: Context): List<Reminder> = runCatching {
        val a = JSONArray(file(c).readText())
        List(a.length()) { a.getJSONObject(it) }.map {
            Reminder(it.getLong("id"), it.optString("note").ifEmpty { null }, it.getString("text"), it.getLong("at"),
                it.optBoolean("fired", false))
        }
    }.getOrDefault(emptyList()).also { list.value = it.sortedBy { r -> r.at } }

    private fun save(c: Context, rs: List<Reminder>) = synchronized(this) {
        val a = JSONArray(rs.map { JSONObject().put("id", it.id).put("note", it.noteId ?: "").put("text", it.text)
            .put("at", it.at).put("fired", it.fired) })
        val tmp = File(c.filesDir, "reminders.json.tmp"); tmp.writeText(a.toString()); tmp.renameTo(file(c))
        list.value = rs.sortedBy { it.at }
    }

    /** Can this app fire on time? (Personal build: always, it holds USE_EXACT_ALARM. Public: the user allows it.) */
    fun canBeExact(c: Context) = Build.VERSION.SDK_INT < 31 || c.getSystemService(AlarmManager::class.java).canScheduleExactAlarms()

    fun add(c: Context, noteId: String?, text: String, at: Long): Reminder {
        val r = Reminder(System.currentTimeMillis(), noteId, text.trim().take(500), at)
        save(c, load(c).filter { it.id != r.id } + r)
        schedule(c, r)
        return r
    }

    fun remove(c: Context, id: Long) {
        c.getSystemService(AlarmManager::class.java).cancel(pending(c, id))
        save(c, load(c).filter { it.id != id })
    }

    private fun markFired(c: Context, id: Long) =
        save(c, load(c).map { if (it.id == id) it.copy(fired = true) else it })

    /**
     * Re-arm every future reminder (app open, reboot, update). A reminder missed while the phone was off is shown once,
     * quietly: it is already late, so it chimes rather than ringing, and `fired` keeps it from coming back on every open.
     */
    fun rescheduleAll(c: Context) {
        val now = System.currentTimeMillis()
        load(c).forEach {
            if (it.at > now) schedule(c, it)
            else if (!it.fired && show(c, it)) markFired(c, it.id)
        }
    }

    private fun pending(c: Context, id: Long) = PendingIntent.getBroadcast(c, id.toInt(),
        Intent(c, ReminderReceiver::class.java).putExtra("id", id), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)

    private fun schedule(c: Context, r: Reminder) {
        val am = c.getSystemService(AlarmManager::class.java)
        if (canBeExact(c)) am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, r.at, pending(c, r.id))
        else am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, r.at, pending(c, r.id))  // UI warns: may be late
    }

    // ---------------------------------------------------------------- the sound

    fun channelId(c: Context) = if (ringLikeAlarm(c)) ALARM else CHIME

    /** Make sure the right channel exists, and return its id. Old ids are deleted so they don't clutter Settings. */
    fun channel(c: Context): String {
        val nm = c.getSystemService(NotificationManager::class.java)
        OLD.forEach { runCatching { nm.deleteNotificationChannel(it) } }
        val alarm = ringLikeAlarm(c)
        val id = if (alarm) ALARM else CHIME
        // The sound is named, not numbered: resource numbers are a build detail and nothing should store one. (This is
        // belt and braces — `res/raw` has not changed since the channel was first made, so the old numeric URI still
        // resolved; it was never the reason a reminder was silent.) Going through getResourceEntryName also keeps a
        // real reference to R.raw.reminder, so resource shrinking can never strip the file.
        val sound = Uri.parse("android.resource://${c.packageName}/raw/${c.resources.getResourceEntryName(R.raw.reminder)}")
        nm.createNotificationChannel(NotificationChannel(id, if (alarm) "Reminders (alarm)" else "Reminders",
            NotificationManager.IMPORTANCE_HIGH).apply {
            setSound(sound, AudioAttributes.Builder()
                // USAGE_ALARM puts it on the alarm stream: alarm volume, and it gets through silent mode and through
                // Do Not Disturb wherever DND allows alarms (the default).
                .setUsage(if (alarm) AudioAttributes.USAGE_ALARM else AudioAttributes.USAGE_NOTIFICATION)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build())
            enableVibration(true)
            vibrationPattern = longArrayOf(0, 180, 120, 180, 700, 180, 120, 180, 700, 180, 120, 180)
        })
        return id
    }

    /** The reminder notification. `insistent`: the phone repeats the sound until the notification is seen. */
    private fun build(c: Context, r: Reminder, insistent: Boolean): Notification {
        val id = channel(c)
        val open = PendingIntent.getActivity(c, r.id.toInt(), Intent(c, MainActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
            .apply { r.noteId?.let { putExtra(MainActivity.EXTRA_NOTE, it) } }, PendingIntent.FLAG_IMMUTABLE)
        fun action(a: String) = PendingIntent.getBroadcast(c, (r.id + a.hashCode()).toInt(),
            Intent(c, ReminderReceiver::class.java).setAction(a).putExtra("id", r.id), PendingIntent.FLAG_IMMUTABLE)
        return Notification.Builder(c, id)
            .setSmallIcon(R.drawable.ic_mic)
            .setContentTitle("Reminder")
            .setContentText(r.text)
            .setStyle(Notification.BigTextStyle().bigText(r.text))
            .setContentIntent(open).setAutoCancel(true)
            .setCategory(Notification.CATEGORY_REMINDER)
            .addAction(Notification.Action.Builder(null, "Done", action(DONE)).build())
            .addAction(Notification.Action.Builder(null, "Snooze 1 h", action(SNOOZE)).build())
            .build().apply { if (insistent) flags = flags or Notification.FLAG_INSISTENT }
    }

    /** Put a reminder in the shade. false = the phone would not show it, so the caller must not mark it done with. */
    fun show(c: Context, r: Reminder, insistent: Boolean = false): Boolean {
        val nm = c.getSystemService(NotificationManager::class.java)
        if (!nm.areNotificationsEnabled()) return false
        return runCatching { nm.notify(r.id.toInt(), build(c, r, insistent)) }.isSuccess
    }

    /**
     * A reminder's time has come. Marked `fired` only once the phone has actually taken the notification, so a reminder
     * that could not be shown is not quietly thrown away.
     */
    fun fire(c: Context, r: Reminder) {
        val alarm = ringLikeAlarm(c)
        val shown = show(c, r, insistent = alarm)
        recordFire(c, (if (alarm) "ring like an alarm" else "chime") +
            (if (shown) ", shown" else ", NOT shown: notifications are off for indite"))
        if (shown && r.id != TEST_ID) markFired(c, r.id)
    }

    /** Settings → Reminders → "Test the sound": the real path, right now, without saving anything. */
    fun test(c: Context) = fire(c, testReminder())

    fun stopTest(c: Context) {
        runCatching { c.getSystemService(NotificationManager::class.java).cancel(TEST_ID.toInt()) }
    }

    /** What happened the last time a reminder went off, so the next "it didn't work" can be looked at, not guessed. */
    private fun recordFire(c: Context, what: String) = prefs(c).edit().putString("lastReminderFire",
        java.text.SimpleDateFormat("d MMM, h:mm a", java.util.Locale.ENGLISH).format(java.util.Date()) + " · " + what).apply()
    fun lastFire(c: Context) = prefs(c).getString("lastReminderFire", null)

    // Default ON (10 Oct): the founder asked for an alarm-like sound, and an opt-in switch that defaults to off meant
    // he kept hearing a chime he couldn't hear. Reminders are set deliberately for a time, so they should be heard.
    fun ringLikeAlarm(c: Context) = prefs(c).getBoolean("reminderAlarm", true)
    fun setRingLikeAlarm(c: Context, on: Boolean) = prefs(c).edit().putBoolean("reminderAlarm", on).apply()

    /**
     * Why a reminder might arrive without a sound, in plain words, or null if nothing looks wrong.
     * Every one of these is a phone setting that indite cannot change itself.
     */
    fun soundProblem(c: Context): String? {
        val nm = c.getSystemService(NotificationManager::class.java)
        if (!nm.areNotificationsEnabled()) return "Notifications are switched off for indite, so reminders can't appear at all."
        runCatching { channel(c) }  // the checks below need the channel to exist
        val ch = runCatching { nm.getNotificationChannel(channelId(c)) }.getOrNull()
        if (ch != null && ch.importance == NotificationManager.IMPORTANCE_NONE)
            return "Reminders are blocked in this phone's notification settings for indite."
        if (ch != null && ch.sound == null) return "This phone's notification settings have muted indite's reminder sound."
        val am = c.getSystemService(AudioManager::class.java)
        // Do Not Disturb: only report it when Android really says so. Without Do Not Disturb access the filter reads
        // UNKNOWN, which must not be shown as "Do Not Disturb is on".
        val dnd = runCatching { nm.currentInterruptionFilter in setOf(NotificationManager.INTERRUPTION_FILTER_PRIORITY,
            NotificationManager.INTERRUPTION_FILTER_NONE, NotificationManager.INTERRUPTION_FILTER_ALARMS) }.getOrDefault(false)
        if (ringLikeAlarm(c)) {
            if (runCatching { am.getStreamVolume(AudioManager.STREAM_ALARM) == 0 }.getOrDefault(false))
                return "This phone's alarm volume is at zero, so nothing will be heard."
            if (runCatching { nm.currentInterruptionFilter == NotificationManager.INTERRUPTION_FILTER_NONE }.getOrDefault(false))
                return "Do Not Disturb is set to total silence, which mutes alarms too."
            return null
        }
        if (runCatching { am.ringerMode != AudioManager.RINGER_MODE_NORMAL }.getOrDefault(false))
            return "This phone is on silent or vibrate, so a chime can't play. Turn on \"Ring like an alarm\" above to be " +
                "heard anyway."
        if (runCatching { am.getStreamVolume(AudioManager.STREAM_NOTIFICATION) == 0 }.getOrDefault(false))
            return "This phone's notification volume is at zero. Turn it up, or turn on \"Ring like an alarm\" above."
        if (dnd) return "Do Not Disturb is on, so notification sounds are muted. Turn on \"Ring like an alarm\" above to be " +
            "heard anyway."
        return null
    }

    const val DONE = "done"
    const val SNOOZE = "snooze"
}

/** Fires a reminder, or handles its Done / Snooze buttons. */
class ReminderReceiver : BroadcastReceiver() {
    override fun onReceive(c: Context, intent: Intent) {
        val id = intent.getLongExtra("id", 0)
        val nm = c.getSystemService(NotificationManager::class.java)
        // The test reminder is never saved, so its buttons are handled here.
        if (id == Reminders.TEST_ID) { nm.cancel(id.toInt()); return }
        val r = Reminders.load(c).firstOrNull { it.id == id } ?: return
        when (intent.action) {
            Reminders.DONE -> { nm.cancel(id.toInt()); Reminders.remove(c, id) }
            Reminders.SNOOZE -> {
                nm.cancel(id.toInt())
                Reminders.remove(c, id); Reminders.add(c, r.noteId, r.text, System.currentTimeMillis() + 60 * 60_000L)
            }
            else -> Reminders.fire(c, r)
        }
    }
}

/** After a reboot or an app update, alarms are gone: set them again. */
class ReminderBootReceiver : BroadcastReceiver() {
    override fun onReceive(c: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED || intent.action == Intent.ACTION_MY_PACKAGE_REPLACED ||
            intent.action == AlarmManager.ACTION_SCHEDULE_EXACT_ALARM_PERMISSION_STATE_CHANGED) Reminders.rescheduleAll(c)
    }
}
