package sapikenal

import id.sapikenal.app.domain.model.InferenceMode
import org.junit.Assert.assertEquals
import org.junit.Test

class InferenceModeTest {
    @Test
    fun `enum contains required inference modes`() {
        assertEquals(
            setOf("ONLINE", "OFFLINE", "OFFLINE_FALLBACK"),
            InferenceMode.entries.map { it.name }.toSet(),
        )
    }
}
