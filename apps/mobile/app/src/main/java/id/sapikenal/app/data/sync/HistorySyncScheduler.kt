package id.sapikenal.app.data.sync

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import java.util.concurrent.TimeUnit

/** Enqueues metadata synchronization only when the device has network connectivity. */
object HistorySyncScheduler {
    private const val UNIQUE_WORK_NAME = "history-metadata-sync"

    fun enqueue(context: Context) {
        val constraints =
            Constraints
                .Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()
        val request =
            OneTimeWorkRequestBuilder<HistorySyncWorker>()
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    10,
                    TimeUnit.SECONDS,
                ).build()

        runCatching {
            WorkManager.getInstance(context.applicationContext).enqueueUniqueWork(
                UNIQUE_WORK_NAME,
                ExistingWorkPolicy.REPLACE,
                request,
            )
        }
    }
}
