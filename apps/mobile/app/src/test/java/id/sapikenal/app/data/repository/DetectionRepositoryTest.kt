package id.sapikenal.app.data.repository

import android.content.Context
import android.net.Uri
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import id.sapikenal.app.data.local.AppDatabase
import id.sapikenal.app.data.local.dao.DetectionDao
import id.sapikenal.app.domain.model.ConsentStatus
import id.sapikenal.app.domain.model.DetectionResult
import id.sapikenal.app.domain.model.ImageSource
import id.sapikenal.app.domain.model.InferenceMode
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/**
 * Integration tests for DetectionRepository using in-memory Room DB.
 * Covers acceptance criteria: save/read metadata, update notes, filters, soft-delete.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33], manifest = Config.NONE)
class DetectionRepositoryTest {
    private lateinit var db: AppDatabase
    private lateinit var dao: DetectionDao
    private lateinit var repository: DetectionRepository

    @Before
    fun setup() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        db =
            Room
                .inMemoryDatabaseBuilder(context, AppDatabase::class.java)
                .allowMainThreadQueries()
                .build()
        dao = db.detectionDao()
        repository = DetectionRepository(dao, context)
    }

    @After
    fun teardown() {
        db.close()
    }

    private fun createResult(
        label: String = "FMD",
        confidence: Float = 0.92f,
        inferenceMode: InferenceMode = InferenceMode.ONLINE,
        consentStatus: ConsentStatus = ConsentStatus.ALLOWED,
        imageSource: ImageSource? = ImageSource.CAMERA,
        appVersion: String? = "1.0.0",
        modelVersion: String? = "MobileNetV2-v3",
        preprocessingSummary: String? = "EXIF correct, resize, normalize",
        outcome: String = "ACCEPTED",
        rejectionReason: String? = null,
    ) = DetectionResult(
        label = label,
        displayLabel = "PMK",
        confidence = confidence,
        isReliable = true,
        allScores = mapOf("FMD" to 0.92f, "LSD" to 0.05f, "healthy" to 0.03f, "non_cattle" to 0.0f),
        inferenceMode = inferenceMode,
        consentStatus = consentStatus,
        imageSource = imageSource,
        appVersion = appVersion,
        modelVersion = modelVersion,
        preprocessingSummary = preprocessingSummary,
        outcome = outcome,
        rejectionReason = rejectionReason,
    )

    // Use a content URI that the test context can resolve
    private val testUri: Uri = Uri.parse("content://test/image.jpg")

    // ── Save and read metadata roundtrip ──────────────────────────────

    @Test
    fun `saveDetection persists metadata and readback matches`() =
        runTest {
            val result =
                createResult(
                    consentStatus = ConsentStatus.DENIED,
                    imageSource = ImageSource.GALLERY,
                    appVersion = "2.0.0",
                    modelVersion = "v3-tflite",
                    preprocessingSummary = "resize 224x224",
                )
            val id = repository.saveDetection(result, testUri)

            val loaded = repository.observeDetection(id).first()
            assertNotNull(loaded)
            assertEquals("FMD", loaded!!.label)
            assertEquals(0.92f, loaded.confidence, 0.001f)
            assertEquals(InferenceMode.ONLINE, loaded.inferenceMode)
            assertEquals(ConsentStatus.DENIED, loaded.consentStatus)
            assertEquals(ImageSource.GALLERY, loaded.imageSource)
            assertEquals("2.0.0", loaded.appVersion)
            assertEquals("v3-tflite", loaded.modelVersion)
            assertEquals("resize 224x224", loaded.preprocessingSummary)
        }

    @Test
    fun `saveDetection with null optional fields persists nulls`() =
        runTest {
            val result =
                createResult(
                    imageSource = null,
                    appVersion = null,
                    modelVersion = null,
                    preprocessingSummary = null,
                )
            val id = repository.saveDetection(result, testUri)

            val loaded = repository.observeDetection(id).first()
            assertNotNull(loaded)
            assertNull(loaded!!.imageSource)
            assertNull(loaded.appVersion)
            assertNull(loaded.modelVersion)
            assertNull(loaded.preprocessingSummary)
        }

    // ── Update notes ──────────────────────────────────────────────────

    @Test
    fun `updateNote changes title and description`() =
        runTest {
            val id = repository.saveDetection(createResult(), testUri)

            repository.updateNote(id, "Sapi #3", "Lesi di mulut")

            val loaded = repository.observeDetection(id).first()
            assertEquals("Sapi #3", loaded!!.title)
            assertEquals("Lesi di mulut", loaded.description)
        }

    @Test
    fun `updateNote can clear notes to null`() =
        runTest {
            val id = repository.saveDetection(createResult(), testUri)
            repository.updateNote(id, "Title", "Desc")
            repository.updateNote(id, null, null)

            val loaded = repository.observeDetection(id).first()
            assertNull(loaded!!.title)
            assertNull(loaded.description)
        }

    // ── Filters ───────────────────────────────────────────────────────

    @Test
    fun `observeHistoryFiltered by class returns only matching`() =
        runTest {
            repository.saveDetection(createResult(label = "FMD"), testUri)
            repository.saveDetection(createResult(label = "LSD"), testUri)
            repository.saveDetection(createResult(label = "FMD"), testUri)

            val filtered = repository.observeHistoryFiltered("FMD", null).first()
            assertEquals(2, filtered.size)
            assertTrue(filtered.all { it.label == "FMD" })
        }

    @Test
    fun `observeHistoryFiltered by canonical healthy label returns healthy rows`() =
        runTest {
            repository.saveDetection(createResult(label = "healthy"), testUri)
            repository.saveDetection(createResult(label = "FMD"), testUri)

            val filtered = repository.observeHistoryFiltered("healthy", null).first()
            assertEquals(1, filtered.size)
            assertEquals("healthy", filtered.single().label)
        }

    @Test
    fun `observeHistoryFiltered by mode returns only matching`() =
        runTest {
            repository.saveDetection(createResult(inferenceMode = InferenceMode.ONLINE), testUri)
            repository.saveDetection(createResult(inferenceMode = InferenceMode.OFFLINE), testUri)

            val filtered = repository.observeHistoryFiltered(null, "ONLINE").first()
            assertEquals(1, filtered.size)
            assertEquals(InferenceMode.ONLINE, filtered[0].inferenceMode)
        }

    // ── Soft-delete ───────────────────────────────────────────────────

    @Test
    fun `softDelete excludes row from history`() =
        runTest {
            val id1 = repository.saveDetection(createResult(), testUri)
            repository.saveDetection(createResult(), testUri)

            repository.softDelete(id1)

            val history = repository.observeHistory().first()
            assertEquals(1, history.size)
            assertTrue(history.none { it.id == id1 })
        }

    @Test
    fun `softDelete excludes row from filtered history`() =
        runTest {
            val id1 = repository.saveDetection(createResult(label = "FMD"), testUri)
            repository.saveDetection(createResult(label = "FMD"), testUri)

            repository.softDelete(id1)

            val filtered = repository.observeHistoryFiltered("FMD", null).first()
            assertEquals(1, filtered.size)
        }

    @Test
    fun `restoreDeleted makes row visible again`() =
        runTest {
            val id = repository.saveDetection(createResult(), testUri)
            repository.softDelete(id)

            assertEquals(0, repository.observeHistory().first().size)

            repository.restoreDeleted(id)

            assertEquals(1, repository.observeHistory().first().size)
        }

    // ── PDF cache cleanup ─────────────────────────────────────────────

    @Test
    fun `deleteAll removes pdf cache files`() =
        runTest {
            // Create a result and persist it
            val id = repository.saveDetection(createResult(), testUri)

            // Create a fake PDF file and link it to the detection
            val pdfFile =
                java.io.File(
                    android.content.Context::class.java.let {
                        androidx.test.core.app.ApplicationProvider
                            .getApplicationContext<Context>()
                            .cacheDir
                    },
                    "test_report.pdf",
                )
            pdfFile.writeBytes("fake pdf content".toByteArray())
            assertTrue("PDF file should exist before deleteAll", pdfFile.exists())

            repository.updatePdfCachePath(id, pdfFile.absolutePath)

            // Trigger deleteAll
            repository.deleteAll()

            // PDF file should be gone
            assertTrue("PDF file should be deleted by deleteAll", !pdfFile.exists())
        }

    @Test
    fun `deleteDetection removes pdf cache file for that record`() =
        runTest {
            val id = repository.saveDetection(createResult(), testUri)

            val pdfFile =
                java.io.File(
                    androidx.test.core.app.ApplicationProvider
                        .getApplicationContext<Context>()
                        .cacheDir,
                    "test_report_single.pdf",
                )
            pdfFile.writeBytes("fake pdf content".toByteArray())
            repository.updatePdfCachePath(id, pdfFile.absolutePath)

            repository.deleteDetection(id)

            assertTrue("PDF file should be deleted by hard delete", !pdfFile.exists())
        }

    @Test
    fun `saveDetection persists rejected non_cattle detection and filters properly`() =
        runTest {
            val nonCattleResult =
                createResult(
                    label = "non_cattle",
                    confidence = 0.96f,
                    outcome = "REJECTED",
                    rejectionReason = "non_cattle",
                ).copy(
                    allScores = mapOf("FMD" to 0.01f, "healthy" to 0.02f, "LSD" to 0.01f, "non_cattle" to 0.96f),
                )

            val id = repository.saveDetection(nonCattleResult, testUri)
            val loaded = repository.observeDetection(id).first()
            assertNotNull(loaded)
            assertEquals("non_cattle", loaded!!.label)
            assertEquals("REJECTED", loaded.outcome)
            assertEquals("non_cattle", loaded.rejectionReason)
            assertEquals(0.96f, loaded.allScores["non_cattle"] ?: 0f, 0.001f)

            val filtered = repository.observeHistoryFiltered("non_cattle", null).first()
            assertEquals(1, filtered.size)
            assertEquals("non_cattle", filtered[0].label)
            assertEquals("REJECTED", filtered[0].outcome)
        }
}
