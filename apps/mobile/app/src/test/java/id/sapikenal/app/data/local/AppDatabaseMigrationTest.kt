package id.sapikenal.app.data.local

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import java.io.File

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33], manifest = Config.NONE)
class AppDatabaseMigrationTest {
    private lateinit var context: Context
    private lateinit var databaseFile: File

    @Before
    fun setUp() {
        context = ApplicationProvider.getApplicationContext()
        databaseFile = context.getDatabasePath(DATABASE_NAME)
        databaseFile.parentFile?.mkdirs()
        databaseFile.delete()
        createSchemaV8(databaseFile)
    }

    @After
    fun tearDown() {
        databaseFile.delete()
    }

    @Test
    fun `migration from Room schema v8 preserves records and adds v9 and v10 defaults`() {
        val database =
            Room
                .databaseBuilder(context, AppDatabase::class.java, DATABASE_NAME)
                .addMigrations(AppDatabase.MIGRATION_8_9, AppDatabase.MIGRATION_9_10)
                .build()

        val migratedDatabase = database.openHelper.writableDatabase
        migratedDatabase
            .query(
                "SELECT predictedClass, scoreNonCattle, outcome, rejectionReason, syncStatus " +
                    "FROM detection_records WHERE id = 42",
            ).use { cursor ->
                assertTrue(cursor.moveToFirst())
                assertEquals("FMD", cursor.getString(0))
                assertEquals(0f, cursor.getFloat(1), 0.001f)
                assertEquals("ACCEPTED", cursor.getString(2))
                assertTrue(cursor.isNull(3))
                assertEquals("PENDING", cursor.getString(4))
            }
        database.close()
    }

    private fun createSchemaV8(file: File) {
        val database = SQLiteDatabase.openOrCreateDatabase(file, null)
        database.execSQL(
            """
            CREATE TABLE IF NOT EXISTS detection_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                timestamp INTEGER NOT NULL,
                imagePath TEXT,
                predictedClass TEXT NOT NULL,
                displayLabel TEXT NOT NULL,
                confidence REAL NOT NULL,
                scoreHealthy REAL NOT NULL,
                scoreFmd REAL NOT NULL,
                scoreLsd REAL NOT NULL,
                inferenceMode TEXT NOT NULL,
                isReliable INTEGER NOT NULL,
                processingMs INTEGER,
                title TEXT,
                description TEXT,
                consentStatus TEXT NOT NULL,
                appVersion TEXT,
                modelVersion TEXT,
                imageSource TEXT,
                preprocessingSummary TEXT,
                latitude REAL,
                longitude REAL,
                locationSource TEXT,
                deletedAt INTEGER,
                pdfCachePath TEXT
            )
            """.trimIndent(),
        )
        database.execSQL(
            "CREATE TABLE room_master_table (id INTEGER PRIMARY KEY,identity_hash TEXT)",
        )
        database.execSQL(
            "INSERT INTO room_master_table (id, identity_hash) VALUES (42, '$SCHEMA_V8_IDENTITY_HASH')",
        )
        database.execSQL(
            """
            INSERT INTO detection_records (
                id, timestamp, imagePath, predictedClass, displayLabel, confidence,
                scoreHealthy, scoreFmd, scoreLsd, inferenceMode, isReliable,
                processingMs, consentStatus
            ) VALUES (
                42, 1700000000000, '/history/old.jpg', 'FMD', 'PMK', 0.92,
                0.03, 0.92, 0.05, 'ONLINE', 1, 120, 'ALLOWED'
            )
            """.trimIndent(),
        )
        database.execSQL("PRAGMA user_version = 8")
        database.close()
    }

    private companion object {
        const val DATABASE_NAME = "detection-records-v8.db"
        const val SCHEMA_V8_IDENTITY_HASH = "781674ad5c48e99f5b415341afae5d54"
    }
}
