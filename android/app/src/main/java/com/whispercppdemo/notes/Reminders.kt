package com.whispercppdemo.notes

import android.app.AlarmManager
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
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
 */
data class Reminder(val id: Long, val noteId: String?, val text: String, val at: Long)

object Reminders {
    val list = MutableStateFlow<List<Reminder>>(emptyList())
    private const val CHANNEL = "reminders_alarm"  // new id: a channel's sound can't change once created

    private fun file(c: Context) = File(c.filesDir, "reminders.json")

    fun load(c: Context): List<Reminder> = runCatching {
        val a = JSONArray(file(c).readText())
        List(a.length()) { a.getJSONObject(it) }.map {
            Reminder(it.getLong("id"), it.optString("note").ifEmpty { null }, it.getString("text"), it.getLong("at"))
        }
    }.getOrDefault(emptyList()).also { list.value = it.sortedBy { r -> r.at } }

    private fun save(c: Context, rs: List<Reminder>) = synchronized(this) {
        val a = JSONArray(rs.map { JSONObject().put("id", it.id).put("note", it.noteId ?: "").put("text", it.text).put("at", it.at) })
        val tmp = File(c.filesDir, "reminders.json.tmp"); tmp.writeText(a.toString()); tmp.renameTo(file(c))
        list.value = rs.sortedBy { it.at }
    }

    /** Can this app fire on time? (Personal build: always. Public build: the user allows "Alarms & reminders".) */
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

    /** Re-arm every future reminder (app open, reboot, update); fire the ones missed while the phone was off. */
    fun rescheduleAll(c: Context) {
        val now = System.currentTimeMillis()
        load(c).forEach { if (it.at > now) schedule(c, it) else notify(c, it) }
    }

    private fun pending(c: Context, id: Long) = PendingIntent.getBroadcast(c, id.toInt(),
        Intent(c, ReminderReceiver::class.java).putExtra("id", id), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)

    private fun schedule(c: Context, r: Reminder) {
        val am = c.getSystemService(AlarmManager::class.java)
        if (canBeExact(c)) am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, r.at, pending(c, r.id))
        else am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, r.at, pending(c, r.id))  // UI warns: may be late
    }

    fun notify(c: Context, r: Reminder) {
        val nm = c.getSystemService(NotificationManager::class.java)
        // A soft chime with gentle double-buzz nudges. Default: notification volume (silent mode respected, so no loud ring
        // in a meeting). Optional "ring like an alarm": alarm volume, even on silent, repeating until you respond.
        val alarm = ringLikeAlarm(c)
        val channel = if (alarm) CHANNEL_ALARM else CHANNEL
        nm.deleteNotificationChannel("reminders")  // the first version's plain channel
        nm.createNotificationChannel(NotificationChannel(channel, if (alarm) "Reminders (alarm)" else "Reminders",
            NotificationManager.IMPORTANCE_HIGH).apply {
            setSound(android.net.Uri.parse("android.resource://${c.packageName}/${R.raw.reminder}"),
                android.media.AudioAttributes.Builder()
                    .setUsage(if (alarm) android.media.AudioAttributes.USAGE_ALARM else android.media.AudioAttributes.USAGE_NOTIFICATION_EVENT)
                    .setContentType(android.media.AudioAttributes.CONTENT_TYPE_SONIFICATION).build())
            enableVibration(true)
            vibrationPattern = longArrayOf(0, 180, 120, 180, 700, 180, 120, 180, 700, 180, 120, 180)
        })
        val open = PendingIntent.getActivity(c, r.id.toInt(), Intent(c, MainActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
            .apply { r.noteId?.let { putExtra(MainActivity.EXTRA_NOTE, it) } }, PendingIntent.FLAG_IMMUTABLE)
        fun action(a: String) = PendingIntent.getBroadcast(c, (r.id + a.hashCode()).toInt(),
            Intent(c, ReminderReceiver::class.java).setAction(a).putExtra("id", r.id), PendingIntent.FLAG_IMMUTABLE)
        nm.notify(r.id.toInt(), Notification.Builder(c, channel)
            .setSmallIcon(R.drawable.ic_mic)
            .setContentTitle("Reminder")
            .setContentText(r.text)
            .setStyle(Notification.BigTextStyle().bigText(r.text))
            .setContentIntent(open).setAutoCancel(true)
            .setCategory(Notification.CATEGORY_REMINDER)
            .addAction(Notification.Action.Builder(null, "Done", action(DONE)).build())
            .addAction(Notification.Action.Builder(null, "Snooze 1 h", action(SNOOZE)).build())
            .build().apply { if (alarm) flags = flags or Notification.FLAG_INSISTENT })  // repeats until seen
    }

    private const val CHANNEL_ALARM = "reminders_ring"
    fun ringLikeAlarm(c: Context) = c.getSharedPreferences("settings", Context.MODE_PRIVATE).getBoolean("reminderAlarm", false)
    fun setRingLikeAlarm(c: Context, on: Boolean) = c.getSharedPreferences("settings", Context.MODE_PRIVATE).edit().putBoolean("reminderAlarm", on).apply()

    const val DONE = "done"
    const val SNOOZE = "snooze"
}

/** Fires a reminder, or handles its Done / Snooze buttons. */
class ReminderReceiver : BroadcastReceiver() {
    override fun onReceive(c: Context, intent: Intent) {
        val id = intent.getLongExtra("id", 0)
        val r = Reminders.load(c).firstOrNull { it.id == id } ?: return
        when (intent.action) {
            Reminders.DONE -> { c.getSystemService(NotificationManager::class.java).cancel(id.toInt()); Reminders.remove(c, id) }
            Reminders.SNOOZE -> {
                c.getSystemService(NotificationManager::class.java).cancel(id.toInt())
                Reminders.remove(c, id); Reminders.add(c, r.noteId, r.text, System.currentTimeMillis() + 60 * 60_000L)
            }
            else -> Reminders.notify(c, r)
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
