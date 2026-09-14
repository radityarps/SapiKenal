package id.sapikenal.app.ui.result

import id.sapikenal.app.ui.theme.SapiKenalColors
import org.junit.Assert.assertEquals
import org.junit.Test

class ResultConfidenceColorTest {

    @Test
    fun `scores greater than or equal to 60 percent return Pasundan Green`() {
        assertEquals(SapiKenalColors.Pasundan, confidenceColor(1.0f, isHighestScore = true))
        assertEquals(SapiKenalColors.Pasundan, confidenceColor(0.85f, isHighestScore = true))
        assertEquals(SapiKenalColors.Pasundan, confidenceColor(0.60f, isHighestScore = true))
        assertEquals(SapiKenalColors.Pasundan, confidenceColor(0.60f, isHighestScore = false))
    }

    @Test
    fun `scores approaching 60 percent (between 40 and 59 percent) return Warning Amber`() {
        assertEquals(SapiKenalColors.Warning, confidenceColor(0.59f, isHighestScore = true))
        assertEquals(SapiKenalColors.Warning, confidenceColor(0.50f, isHighestScore = true))
        assertEquals(SapiKenalColors.Warning, confidenceColor(0.40f, isHighestScore = true))
        assertEquals(SapiKenalColors.Warning, confidenceColor(0.59f, isHighestScore = false))
        assertEquals(SapiKenalColors.Warning, confidenceColor(0.40f, isHighestScore = false))
    }

    @Test
    fun `highest score below 40 percent returns Error Red`() {
        assertEquals(SapiKenalColors.Error, confidenceColor(0.39f, isHighestScore = true))
        assertEquals(SapiKenalColors.Error, confidenceColor(0.25f, isHighestScore = true))
        assertEquals(SapiKenalColors.Error, confidenceColor(0.00f, isHighestScore = true))
    }

    @Test
    fun `non highest score below 40 percent returns TextSecondary Gray`() {
        assertEquals(SapiKenalColors.TextSecondary, confidenceColor(0.39f, isHighestScore = false))
        assertEquals(SapiKenalColors.TextSecondary, confidenceColor(0.20f, isHighestScore = false))
        assertEquals(SapiKenalColors.TextSecondary, confidenceColor(0.01f, isHighestScore = false))
    }

    @Test
    fun `non cattle result returns TextSecondary Gray regardless of confidence`() {
        assertEquals(SapiKenalColors.TextSecondary, confidenceColor(0.95f, isHighestScore = true, isNonCattle = true))
        assertEquals(SapiKenalColors.TextSecondary, confidenceColor(0.50f, isHighestScore = true, isNonCattle = true))
        assertEquals(SapiKenalColors.TextSecondary, confidenceColor(0.20f, isHighestScore = true, isNonCattle = true))
    }
}
