package id.sapikenal.app.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import id.sapikenal.app.data.local.dao.DetectionDao
import id.sapikenal.app.data.local.entity.DetectionEntity

@Database(
    entities = [DetectionEntity::class],
    version = 11,
    exportSchema = true,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun detectionDao(): DetectionDao

    companion object {
        val MIGRATION_4_5 =
            object : Migration(4, 5) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.execSQL(
                        "ALTER TABLE detection_records ADD COLUMN consentStatus TEXT NOT NULL DEFAULT 'UNDECIDED'",
                    )
                }
            }

        val MIGRATION_5_6 =
            object : Migration(5, 6) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.execSQL(
                        "ALTER TABLE detection_records ADD COLUMN appVersion TEXT DEFAULT NULL",
                    )
                    db.execSQL(
                        "ALTER TABLE detection_records ADD COLUMN modelVersion TEXT DEFAULT NULL",
                    )
                }
            }

        val MIGRATION_6_7 =
            object : Migration(6, 7) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN imageSource TEXT DEFAULT NULL")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN preprocessingSummary TEXT DEFAULT NULL")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN latitude REAL DEFAULT NULL")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN longitude REAL DEFAULT NULL")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN deletedAt INTEGER DEFAULT NULL")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN pdfCachePath TEXT DEFAULT NULL")
                }
            }

        val MIGRATION_7_8 =
            object : Migration(7, 8) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN locationSource TEXT DEFAULT NULL")
                }
            }

        val MIGRATION_8_9 =
            object : Migration(8, 9) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    // Legacy score columns are removed by MIGRATION_10_11 after v9/v10 bookkeeping.
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN scoreNonCattle REAL NOT NULL DEFAULT 0.0")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN outcome TEXT NOT NULL DEFAULT 'ACCEPTED'")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN rejectionReason TEXT DEFAULT NULL")
                }
            }

        val MIGRATION_10_11 =
            object : Migration(10, 11) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.query("SELECT 1 FROM detection_records LIMIT 1").use { cursor ->
                        if (cursor.moveToFirst()) {
                            throw IllegalStateException(
                                "Cannot migrate populated legacy detection history; back it up or reset it explicitly",
                            )
                        }
                    }
                    db.execSQL("ALTER TABLE detection_records RENAME TO detection_records_legacy")
                    db.execSQL(
                        """
                        CREATE TABLE detection_records (
                            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                            timestamp INTEGER NOT NULL,
                            imagePath TEXT,
                            predictedClass TEXT NOT NULL,
                            displayLabel TEXT NOT NULL,
                            confidence REAL NOT NULL,
                            scoresJson TEXT NOT NULL,
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
                            pdfCachePath TEXT,
                            syncStatus TEXT NOT NULL
                        )
                        """.trimIndent(),
                    )
                    // Legacy model results cannot be mapped to the breed contract.
                    // The table was verified empty above, so rebuilding it is safe.
                    db.execSQL("DROP TABLE detection_records_legacy")
                }
            }

        val MIGRATION_9_10 =
            object : Migration(9, 10) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN syncStatus TEXT NOT NULL DEFAULT 'PENDING'")
                }
            }
    }
}
