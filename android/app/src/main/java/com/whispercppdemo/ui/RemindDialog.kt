package com.whispercppdemo.ui

import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.whispercppdemo.notes.Reminders
import java.util.Calendar

/** When to be reminded: a few quick picks, or any date and time. The text is filled in and can be edited. */
@Composable
fun RemindDialog(noteId: String?, initialText: String, onDone: () -> Unit) {
    val context = LocalContext.current
    var text by remember { mutableStateOf(initialText) }
    val exact = remember { Reminders.canBeExact(context) }
    val ringing = remember { Reminders.ringLikeAlarm(context) }
    val problem = remember { Reminders.soundProblem(context) }   // once per dialog: it creates the channel if needed
    // A reminder is a notification. Without this permission nothing appears and nothing sounds, and until now indite
    // only asked for it when you recorded or imported, so a reminder could be set that could never show up.
    val askNotifications = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {}
    LaunchedEffect(Unit) {
        if (Build.VERSION.SDK_INT >= 33 &&
            context.checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED)
            askNotifications.launch(android.Manifest.permission.POST_NOTIFICATIONS)
    }
    fun at(daysAhead: Int, hour: Int) = Calendar.getInstance().apply {
        add(Calendar.DAY_OF_MONTH, daysAhead); set(Calendar.HOUR_OF_DAY, hour); set(Calendar.MINUTE, 0); set(Calendar.SECOND, 0)
    }.timeInMillis
    fun set(time: Long) {
        Reminders.add(context, noteId, text, time)
        Messages.flow.tryEmit("Reminder set for " + android.text.format.DateUtils.formatDateTime(context, time,
            android.text.format.DateUtils.FORMAT_SHOW_TIME or android.text.format.DateUtils.FORMAT_SHOW_WEEKDAY))
        onDone()
    }
    val now = System.currentTimeMillis()
    val evening = at(0, 17).let { if (it > now + 10 * 60_000) it else at(0, 18).takeIf { t -> t > now + 10 * 60_000 } ?: at(1, 17) }
    AlertDialog(
        onDismissRequest = onDone,
        title = { Text("Remind me") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                OutlinedTextField(text, { text = it }, Modifier.fillMaxWidth(), label = { Text("About") }, maxLines = 5)
                FilledTonalButton(onClick = { set(now + 60 * 60_000L) }, Modifier.fillMaxWidth()) { Text("In 1 hour") }
                FilledTonalButton(onClick = { set(evening) }, Modifier.fillMaxWidth()) {
                    Text(android.text.format.DateUtils.formatDateTime(context, evening,
                        android.text.format.DateUtils.FORMAT_SHOW_TIME or android.text.format.DateUtils.FORMAT_SHOW_WEEKDAY))
                }
                FilledTonalButton(onClick = { set(at(1, 9)) }, Modifier.fillMaxWidth()) { Text("Tomorrow 9:00 am") }
                // Say how it will arrive, and name whatever is in the way, here rather than only in Settings.
                Text(if (ringing) "Will ring like an alarm, on the alarm volume."
                     else "Will play one soft chime at notification volume.",
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                problem?.let {
                    Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.error)
                }
                TextButton(onClick = {  // any date, then any time
                    val c = Calendar.getInstance()
                    android.app.DatePickerDialog(context, { _, y, m, d ->
                        android.app.TimePickerDialog(context, { _, h, min ->
                            val t = Calendar.getInstance().apply { set(y, m, d, h, min, 0) }.timeInMillis
                            if (t > System.currentTimeMillis()) set(t) else Messages.flow.tryEmit("That time has already passed.")
                        }, c.get(Calendar.HOUR_OF_DAY), c.get(Calendar.MINUTE), false).show()
                    }, c.get(Calendar.YEAR), c.get(Calendar.MONTH), c.get(Calendar.DAY_OF_MONTH))
                        .apply { datePicker.minDate = System.currentTimeMillis() - 1000 }.show()
                }, Modifier.fillMaxWidth()) { Text("Pick a date and time…") }
                // Without exact alarms Android may deliver a reminder up to an hour late: say so, and offer the fix.
                if (!exact) {
                    Text("This phone may deliver reminders up to an hour late until you allow indite to set exact alarms.",
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.error)
                    TextButton(onClick = {
                        runCatching { context.startActivity(Intent(android.provider.Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM,
                            android.net.Uri.parse("package:" + context.packageName))) }
                    }) { Text("Allow exact reminders") }
                }
            }
        },
        confirmButton = { TextButton(onClick = onDone) { Text("Cancel") } },
    )
}
