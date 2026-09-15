package id.sapikenal.app.ui.result

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class BreedProfileParserTest {

    @Test
    fun `parse Pasundan article extracts authentic summary, strengths, limitations and disclaimer`() {
        val body = """
            Ringkasan Profil

            Sapi Pasundan adalah rumpun sapi lokal asli Jawa Barat yang telah beradaptasi berabad-abad di wilayah agroklimat tropis basah. Memiliki warna merah bata dengan ciri khas garis belut (garis hitam gelap) di sepanjang tulang punggung.

            Kelebihan

            • Toleransi tinggi terhadap kelembapan tinggi dan iklim tropis basah
            • Mampu memanfaatkan hijauan hutan dan limbah pertanian secara efisien
            • Garis belut pada punggung memberi penanda visual yang khas pada citra

            Kekurangan

            • Keragaman fenotip lokal cukup bervariasi di berbagai daerah penangkarannya
            • Garis belut dan warna kaki bisa kurang kontras jika citra diambil dari jarak jauh

            Ciri ini bersifat umum, bukan bukti silsilah atau rekomendasi mutlak.
        """.trimIndent()

        val parsed = BreedProfileParser.parse(body, fallbackSummary = "Fallback summary")

        assertTrue(parsed.summaryText.contains("Sapi Pasundan adalah rumpun sapi lokal"))
        assertTrue(parsed.summaryText.contains("garis belut"))
        assertEquals(3, parsed.strengths.size)
        assertEquals("Toleransi tinggi terhadap kelembapan tinggi dan iklim tropis basah", parsed.strengths[0])
        assertEquals("Mampu memanfaatkan hijauan hutan dan limbah pertanian secara efisien", parsed.strengths[1])
        assertEquals("Garis belut pada punggung memberi penanda visual yang khas pada citra", parsed.strengths[2])

        assertEquals(2, parsed.limitations.size)
        assertEquals("Keragaman fenotip lokal cukup bervariasi di berbagai daerah penangkarannya", parsed.limitations[0])
        assertEquals("Garis belut dan warna kaki bisa kurang kontras jika citra diambil dari jarak jauh", parsed.limitations[1])

        assertNotNull(parsed.disclaimer)
        assertTrue(parsed.disclaimer!!.contains("bukan bukti silsilah"))
    }

    @Test
    fun `parse Bali article extracts authentic summary with white rump characteristic`() {
        val body = """
            Ringkasan Profil

            Sapi Bali umumnya dikenali melalui tubuh yang relatif kompak, warna cokelat kemerahan, bagian pantat putih, dan warna putih pada kaki bawah.

            Kelebihan

            • Ciri warna khas dapat membantu perbandingan visual pada citra yang jelas
            • Bentuk tubuh kompak memberi konteks tambahan saat meninjau hasil model

            Kekurangan

            • Warna dapat berubah menurut jenis kelamin, umur, pencahayaan, dan individu
            • Ciri visual dapat tertutup sudut pengambilan, kotoran, atau persilangan

            Ciri ini bersifat umum, bukan bukti silsilah atau rekomendasi mutlak.
        """.trimIndent()

        val parsed = BreedProfileParser.parse(body, fallbackSummary = "Fallback Bali")

        assertTrue(parsed.summaryText.contains("pantat putih"))
        assertEquals(2, parsed.strengths.size)
        assertEquals(2, parsed.limitations.size)
        assertNotNull(parsed.disclaimer)
    }

    @Test
    fun `parse empty body falls back to fallbackSummary`() {
        val parsed = BreedProfileParser.parse("", fallbackSummary = "Kelebihan, kekurangan, dan ciri umum.")
        assertEquals("Kelebihan, kekurangan, dan ciri umum.", parsed.summaryText)
        assertTrue(parsed.strengths.isEmpty())
        assertTrue(parsed.limitations.isEmpty())
    }

    @Test
    fun `parse headers with colons works identically`() {
        val body = """
            Ringkasan Profil:
            Sapi PO memiliki punuk besar di pundak.

            Kelebihan:
            - Tahan panas
            - Daya adaptasi tinggi

            Kekurangan:
            - Pertumbuhan bobot sedang
        """.trimIndent()

        val parsed = BreedProfileParser.parse(body)
        assertEquals("Sapi PO memiliki punuk besar di pundak.", parsed.summaryText)
        assertEquals(listOf("Tahan panas", "Daya adaptasi tinggi"), parsed.strengths)
        assertEquals(listOf("Pertumbuhan bobot sedang"), parsed.limitations)
    }

    @Test
    fun `parse unstructured body gracefully extracts summary and bullet points`() {
        val body = """
            Sapi jenis tertentu dengan ciri khas unik.
            • Keunggulan pertama
            • Keunggulan kedua
            Catatan tambahan di akhir.
        """.trimIndent()

        val parsed = BreedProfileParser.parse(body)
        assertEquals("Sapi jenis tertentu dengan ciri khas unik.", parsed.summaryText)
        assertEquals(listOf("Keunggulan pertama", "Keunggulan kedua"), parsed.strengths)
        assertEquals("Catatan tambahan di akhir.", parsed.rawRemainingBody)
    }

    @Test
    fun `parse single sentence limitation with typo in header and disclaimer`() {
        val body = """
            Kekuranga:
            rentan terhadap penyakit bla bla bla.

            ciri ini bersifat umum, bukan bukti silsilah atau rekomendasi mutlak.
        """.trimIndent()

        val parsed = BreedProfileParser.parse(body, fallbackSummary = "Fallback Sapi")

        assertEquals("Fallback Sapi", parsed.summaryText)
        assertEquals(listOf("rentan terhadap penyakit bla bla bla."), parsed.limitations)
        assertTrue(parsed.strengths.isEmpty())
        assertNotNull(parsed.disclaimer)
        assertTrue(parsed.disclaimer!!.contains("bukan bukti silsilah"))
    }

    @Test
    fun `parse inline header with colon content on single line`() {
        val body = """
            Ringkasan: Sapi Pasundan tahan iklim basah.
            Kelebihan: Toleransi tinggi terhadap cuaca ekstrem.
            Kekurangan: Garis belut kurang kontras dari jauh.
        """.trimIndent()

        val parsed = BreedProfileParser.parse(body)
        assertEquals("Sapi Pasundan tahan iklim basah.", parsed.summaryText)
        assertEquals(listOf("Toleransi tinggi terhadap cuaca ekstrem."), parsed.strengths)
        assertEquals(listOf("Garis belut kurang kontras dari jauh."), parsed.limitations)
    }

    @Test
    fun `parse with contentBlocksJson extracts structured blocks with highest priority`() {
        val blocksJson = """
            [
                {"id": "b1", "type": "heading", "content": "Ringkasan Profil", "items": []},
                {"id": "b2", "type": "paragraph", "content": "Sapi Limusin berotot besar dan berdaging tebal.", "items": []},
                {"id": "b3", "type": "heading", "content": "Kelebihan", "items": []},
                {"id": "b4", "type": "bullet_list", "content": "", "items": ["Pertumbuhan cepat", "Karkas tinggi"]},
                {"id": "b5", "type": "heading", "content": "Kekurangan", "items": []},
                {"id": "b6", "type": "bullet_list", "content": "", "items": ["Butuh pakan berprotein tinggi"]},
                {"id": "b7", "type": "disclaimer", "content": "Ciri ini bersifat umum, bukan bukti silsilah atau rekomendasi mutlak.", "items": []}
            ]
        """.trimIndent()

        val parsed = BreedProfileParser.parse(
            body = "Old markdown body text",
            fallbackSummary = "Fallback summary",
            contentBlocksJson = blocksJson,
        )

        assertEquals("Sapi Limusin berotot besar dan berdaging tebal.", parsed.summaryText)
        assertEquals(listOf("Pertumbuhan cepat", "Karkas tinggi"), parsed.strengths)
        assertEquals(listOf("Butuh pakan berprotein tinggi"), parsed.limitations)
        assertEquals("Ciri ini bersifat umum, bukan bukti silsilah atau rekomendasi mutlak.", parsed.disclaimer)
    }

    @Test
    fun `parse with invalid contentBlocksJson falls back cleanly to markdown body`() {
        val invalidBlocksJson = "not a valid json {{"
        val body = """
            Ringkasan Profil
            Sapi Madura lincah dan tahan panas.

            Kelebihan
            • Sangat tangguh

            Kekurangan
            • Ukuran relatif sedang
        """.trimIndent()

        val parsed = BreedProfileParser.parse(
            body = body,
            fallbackSummary = "Fallback summary",
            contentBlocksJson = invalidBlocksJson,
        )

        assertEquals("Sapi Madura lincah dan tahan panas.", parsed.summaryText)
        assertEquals(listOf("Sangat tangguh"), parsed.strengths)
        assertEquals(listOf("Ukuran relatif sedang"), parsed.limitations)
    }
}
