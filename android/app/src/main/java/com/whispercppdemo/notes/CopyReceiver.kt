package com.whispercppdemo.notes

import android.content.BroadcastReceiver
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.widget.Toast

/** "Copy" on the "Text ready" notification: puts the note's text on the clipboard without opening the app. */
class CopyReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        Settings.init(context)
        Notes.init(context)
        val note = Notes.note(intent.getStringExtra(EXTRA_NOTE) ?: return) ?: return
        context.getSystemService(ClipboardManager::class.java).setPrimaryClip(ClipData.newPlainText("indite", note.allText()))
        if (Build.VERSION.SDK_INT < 33) Toast.makeText(context, "Copied", Toast.LENGTH_SHORT).show()
    }

    companion object { const val EXTRA_NOTE = "note" }
}
