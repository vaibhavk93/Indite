package com.whispercppdemo.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.util.Calendar

class ClearDateTest {
    private val sat10Oct2026 = Calendar.getInstance().apply { set(2026, Calendar.OCTOBER, 10, 12, 0) }
    private fun day(ms: Long) = Calendar.getInstance().apply { timeInMillis = ms }.let { "${it.get(Calendar.DAY_OF_MONTH)}/${it.get(Calendar.MONTH) + 1}" }

    @Test fun weekdayIsTheNextOne() = assertEquals("12/10", day(clearDate("Monday", sat10Oct2026)!!))
    @Test fun dayMonth() = assertEquals("15/10", day(clearDate("by 15 Oct", sat10Oct2026)!!))
    @Test fun pastDateMeansNextYear() = assertEquals("2/1", day(clearDate("Jan 2", sat10Oct2026)!!))
    @Test fun hinglishLeftAlone() { assertNull(clearDate("kal shaam tak", sat10Oct2026)); assertNull(clearDate("not said", sat10Oct2026)) }
}
