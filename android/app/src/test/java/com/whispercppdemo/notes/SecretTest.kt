package com.whispercppdemo.notes

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SecretTest {
    @Test fun catchesIndianPinAndPasswordBoxes() {
        listOf("upi_pin", "et_pin", "mpin", "etPassword", "Enter OTP", "CVV", "Passcode").forEach { assertTrue(it, Secret.words(it)) }
    }

    @Test fun ignoresLookalikes() {
        listOf("passenger name", "passport number", "footprint", "compass", "pincode", "Message").forEach { assertFalse(it, Secret.words(it)) }
    }
}
