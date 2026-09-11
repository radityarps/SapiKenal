package id.sapikenal.app.acceptance

import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * Verifies that key string resource names exist in both
 * values/strings.xml (Indonesian) and values-en/strings.xml (English).
 *
 * This ensures no localization gaps for critical user-facing strings.
 */
class LocalizationTest {
    /**
     * Key string resource names that must be present in both locale files.
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
            "settings_language",
            "settings_clear_history",
            "settings_upload_consent",
            "settings_crash_reporting",
            "settings_crash_reporting_description",
            "settings_purge_deleted",
            "settings_purge_done",
            // Camera
            "camera_capture",
            "camera_gallery",
        )

    private fun findProjectRoot(): File {
        // Walk up from the test class location to find the project root
        var dir = File(System.getProperty("user.dir") ?: ".")
        // If we're in the mobile project root, use it directly
        val resDir = File(dir, "app/src/main/res")
        if (resDir.exists()) return dir
        // Try common CI paths
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
            // Skip gracefully in environments where resource files aren't available
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
    fun `all required strings exist in values-en strings xml`() {
        val root = findProjectRoot()
        val file = File(root, "app/src/main/res/values-en/strings.xml")
        if (!file.exists()) {
            println("SKIP: values-en/strings.xml not found at ${file.absolutePath}")
            return
        }
        val names = readStringNames(file)
        val missing = requiredStringNames.filter { it !in names }
        assertTrue(
            "Missing strings in values-en/strings.xml: $missing",
            missing.isEmpty(),
        )
    }

    @Test
    fun `breed profiles are specific and bilingual`() {
        val root = findProjectRoot()
        val defaultFile = File(root, "app/src/main/res/values/strings.xml")
        val englishFile = File(root, "app/src/main/res/values-en/strings.xml")
        if (!defaultFile.exists() || !englishFile.exists()) {
            println("SKIP: profile string resources not found")
            return
        }
        val defaultStrings = defaultFile.readText()
        val englishStrings = englishFile.readText()
        val indonesianTraits =
            mapOf(
                "bali" to "bagian pantat putih",
                "brahman" to "punuk di bahu",
                "brangus" to "komposit Brahman dan Angus",
                "limusin" to "merah keemasan",
            )
        val englishTraits =
            mapOf(
                "bali" to "white rump patch",
                "brahman" to "shoulder hump",
                "brangus" to "composite of Brahman and Angus",
                "limusin" to "golden-red",
            )
        indonesianTraits.forEach { (breed, trait) ->
            assertTrue("Missing Indonesian profile for $breed", defaultStrings.contains("guide_${breed}_title_1"))
            assertTrue("Indonesian profile for $breed is generic", defaultStrings.contains(trait))
            assertTrue("Missing English profile for $breed", englishStrings.contains("guide_${breed}_title_1"))
            assertTrue("English profile for $breed is generic", englishStrings.contains(englishTraits.getValue(breed)))
        }
    }

    @Test
    fun `values and values-en have same string names`() {
        val root = findProjectRoot()
        val defaultFile = File(root, "app/src/main/res/values/strings.xml")
        val enFile = File(root, "app/src/main/res/values-en/strings.xml")
        if (!defaultFile.exists() || !enFile.exists()) {
            println("SKIP: string resource files not found")
            return
        }
        val defaultNames = readStringNames(defaultFile)
        val enNames = readStringNames(enFile)

        val missingInEn = defaultNames - enNames
        val missingInDefault = enNames - defaultNames

        assertTrue(
            "Strings in values/ but missing in values-en/: $missingInEn",
            missingInEn.isEmpty(),
        )
        assertTrue(
            "Strings in values-en/ but missing in values/: $missingInDefault",
            missingInDefault.isEmpty(),
        )
    }
}
