package com.whispercppdemo.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The Ask AI surface (AUD-026). These are the rules that broke it before: an action listed in two places, an action
 * with no explanation, and a follow-up question that arrives without warning.
 */
class AiActionsTest {

    @Test fun `every action appears exactly once`() {
        val labels = AiActions.map { it.label }
        assertEquals("an action listed twice is the duplication this replaced", labels.size, labels.toSet().size)
    }

    @Test fun `every action says what it gives back`() {
        AiActions.forEach {
            assertTrue("${it.label} has no description", it.gets.length >= 10)
            assertTrue("${it.label} describes itself by its own name", !it.gets.equals(it.label, ignoreCase = true))
        }
    }

    @Test fun `only the two that ask a follow-up are marked`() {
        assertEquals(setOf("Translate", "Rewrite to send"), AiActions.filter { it.asks }.map { it.label }.toSet())
    }

    @Test fun `every action belongs to a named group`() {
        AiActions.forEach { assertTrue("${it.label} has no group", it.group.isNotBlank()) }
        assertTrue("too many groups stops being a grouping", AiActions.map { it.group }.toSet().size <= 4)
    }
}
