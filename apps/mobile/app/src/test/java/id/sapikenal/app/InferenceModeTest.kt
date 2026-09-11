package sapikenal

import id.sapikenal.app.R
import id.sapikenal.app.domain.model.InferenceMode
import id.sapikenal.app.report.ReportContentBuilder
import id.sapikenal.app.ui.result.modeLabelRes
import org.junit.Assert.assertEquals
import org.junit.Test

class InferenceModeTest {
    @Test
    fun `enum contains required inference modes`() {
        assertEquals(
            setOf("ONLINE", "OFFLINE", "OFFLINE_FALLBACK", "UNKNOWN"),
            InferenceMode.entries.map { it.name }.toSet(),
        )
    }

    @Test
    fun `parser rejects unknown inference mode instead of treating it as offline`() {
        assertEquals(InferenceMode.OFFLINE, InferenceMode.parse("offline"))
        assertEquals(InferenceMode.UNKNOWN, InferenceMode.parse("corrupt"))
        assertEquals(R.string.result_mode_unknown, modeLabelRes("corrupt"))
    }

    @Test
    fun `labels distinguish every inference mode`() {
        val labels =
            ReportContentBuilder.ReportLabels.english()
        assertEquals("Online", labels.inferenceModeLabel(InferenceMode.ONLINE))
        assertEquals("Offline", labels.inferenceModeLabel(InferenceMode.OFFLINE))
        assertEquals("Offline fallback", labels.inferenceModeLabel(InferenceMode.OFFLINE_FALLBACK))
        assertEquals("Unknown mode", labels.inferenceModeLabel(InferenceMode.UNKNOWN))
    }
}
