package id.sapikenal.app.report

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PdfTextLayoutTest {
    @Test
    fun `wrap keeps every measured line inside the available width`() {
        val text = "Cattle breed identification result from image classification"
        val lines = PdfTextLayout.wrap(text, maxWidth = 18f) { it.length.toFloat() }

        assertTrue(lines.size > 1)
        assertTrue(lines.all { it.length <= 18 })
        assertEquals(text, lines.joinToString(" "))
    }

    @Test
    fun `wrap splits long words and keeps continuation indentation`() {
        val lines =
            PdfTextLayout.wrapWithPrefixes(
                text = "metadata1234567890 value",
                maxWidth = 10f,
                measureText = { it.length.toFloat() },
                firstPrefix = "• ",
                continuationPrefix = "  ",
            )

        assertEquals(listOf("• metadata", "  12345678", "  90", "  value"), lines)
        assertTrue(lines.all { it.length <= 10 })
    }

    @Test
    fun `fits rejects content below the page margin`() {
        assertTrue(PdfTextLayout.fits(top = 800f, height = 2f, bottom = 802f))
        assertFalse(PdfTextLayout.fits(top = 800f, height = 3f, bottom = 802f))
    }

    @Test
    fun `scale stays within content width and height`() {
        val dimensions = PdfTextLayout.scaleWithinBounds(1_000, 500, maxWidth = 515f, maxHeight = 200f)

        assertEquals(400 to 200, dimensions)
        assertTrue(dimensions!!.first <= 515 && dimensions.second <= 200)
    }
}
