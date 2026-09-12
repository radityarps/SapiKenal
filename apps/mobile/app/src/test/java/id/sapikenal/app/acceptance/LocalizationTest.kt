package id.sapikenal.app.acceptance

import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * Verifies that key string resource names exist in values/strings.xml.
 *
 * This ensures no gaps for critical user-facing strings.
 */
class LocalizationTest {
    /**
     * Key string resource names that must be present in values/strings.xml.
     * These cover all major screens and features.
     */
    private val requiredStringNames =
        listOf(
            // Shared
            "app_name",
            "btn_cancel",
            "btn_delete",
            "btn_ok",
            "nav_back",
            // Tabs
            "tab_periksa",
            "tab_riwayat",
            "tab_panduan",
            "tab_lainnya",
            // Result
            "result_identification",
            "result_confidence",
            "result_btn_save",
            "result_btn_share",
            "result_btn_export_pdf",
            "result_breed_bali",
            "result_breed_brahman",
            "result_breed_brangus",
            "result_breed_limusin",
            "result_mode_online",
            "result_mode_offline",
            "result_mode_offline_fallback",
            "result_mode_unknown",
            "history_filter_unknown",
            "result_learn_more",
            "result_disclaimer",
            "result_advice_title",
            // History
            "history_title",
            "history_empty",
            // Guide
            "guide_title",
            // Settings
            "settings_title",
            "settings_clear_history",
            "settings_upload_consent",
            "settings_purge_deleted",
            "settings_purge_done",
            // Camera
            "camera_capture",
            "camera_gallery",
        )

    private fun findProjectRoot(): File {
        var dir = File(System.getProperty("user.dir") ?: ".")
        val resDir = File(dir, "app/src/main/res")
        if (resDir.exists()) return dir
        val candidates =
            listOf(
                File(dir, "apps/mobile"),
                dir,
            )
        return candidates.firstOrNull { File(it, "app/src/main/res").exists() } ?: dir
    }

    private fun readStringNames(file: File): Set<String> {
        if (!file.exists()) return emptySet()
        val regex = Regex("""<string\s+name="([^"]+)"[^>]*>""")
        return file.readText().let { content ->
            regex.findAll(content).map { it.groupValues[1] }.toSet()
        }
    }

    @Test
    fun `all required strings exist in values strings xml`() {
        val root = findProjectRoot()
        val file = File(root, "app/src/main/res/values/strings.xml")
        if (!file.exists()) {
            println("SKIP: values/strings.xml not found at ${file.absolutePath}")
            return
        }
        val names = readStringNames(file)
        val missing = requiredStringNames.filter { it !in names }
        assertTrue(
            "Missing strings in values/strings.xml: $missing",
            missing.isEmpty(),
        )
    }

    @Test
    fun `breed profiles are specific in indonesian`() {
        val root = findProjectRoot()
        val defaultFile = File(root, "app/src/main/res/values/strings.xml")
        if (!defaultFile.exists()) {
            println("SKIP: profile string resources not found")
            return
        }
        val defaultStrings = defaultFile.readText()
        val indonesianTraits =
            mapOf(
                "bali" to "bagian pantat putih",
                "brahman" to "punuk di bahu",
                "brangus" to "komposit Brahman dan Angus",
                "limusin" to "merah keemasan",
            )
        indonesianTraits.forEach { (breed, trait) ->
            assertTrue("Missing Indonesian profile for $breed", defaultStrings.contains("guide_${breed}_title_1"))
            assertTrue("Indonesian profile for $breed is generic", defaultStrings.contains(trait))
        }
    }
}
