package id.sapikenal.app.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import id.sapikenal.app.data.local.dao.DetectionDao
import id.sapikenal.app.data.local.entity.DetectionEntity

@Database(
    entities = [DetectionEntity::class],
    version = 10,
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
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN scoreNonCattle REAL NOT NULL DEFAULT 0.0")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN outcome TEXT NOT NULL DEFAULT 'ACCEPTED'")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN rejectionReason TEXT DEFAULT NULL")
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
